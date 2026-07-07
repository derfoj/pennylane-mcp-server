"""Ressources MCP : lecture instantanée et passive pour le contexte de Claude.

Les ressources permettent d'attacher des informations structurelles ou dynamiques
sans consommer d'appel d'outil ni d'aller-retour LLM :
  - pennylane://dossier/current
  - pennylane://comptes/classes (chargé depuis comptes_classes.md)
  - pennylane://journaux/actifs
"""

from __future__ import annotations

from pathlib import Path
from mcp.server.fastmcp import FastMCP

from ..api import api_get
from ..dossier_manager import get_manager, has_manager
from ..utils import to_json

_RESOURCES_DIR = Path(__file__).parent


def _load_resource_md(filename: str) -> str:
    """Charge le contenu d'un fichier ressource Markdown (.md)."""
    file_path = _RESOURCES_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Fichier ressource introuvable : {file_path}")
    return file_path.read_text(encoding="utf-8").strip()


def register(mcp: FastMCP) -> None:
    """Enregistre toutes les ressources MCP pour Claude."""

    @mcp.resource(
        "pennylane://dossier/current",
        name="current-dossier",
        title="Dossier Client Actif",
        description="Expose les informations du dossier client en cours (slug, nom, infos société).",
        mime_type="application/json",
    )
    async def resource_current_dossier() -> str:
        """Expose les informations du dossier client en cours (slug, nom, infos société)."""
        try:
            info = {}
            if has_manager():
                manager = get_manager()
                curr = manager.current_dossier
                if curr:
                    info["dossier_config"] = {
                        "slug": curr.slug,
                        "name": curr.name,
                        "created_at": str(curr.created_at),
                        "notes": curr.notes,
                    }
                else:
                    info["dossier_config"] = "Aucun dossier sélectionné"

            # Tentative de récupération des infos live via l'API Pennylane
            try:
                me_data = await api_get("/me")
                info["pennylane_api_me"] = me_data
                info["status"] = "Connecté"
            except Exception as api_exc:
                info["status"] = f"Non connecté ou erreur API : {api_exc}"

            return to_json(info)
        except Exception as exc:
            return f"{{\"error\": \"Impossible de lire le dossier courant : {exc}\"}}"

    @mcp.resource(
        "pennylane://comptes/classes",
        name="comptes-classes",
        title="Plan Comptable Général (PCG)",
        description="Expose la structure et la logique du Plan Comptable Général pour guider la qualification des écritures.",
        mime_type="text/markdown",
    )
    def resource_comptes_classes() -> str:
        """Expose la structure et la logique du Plan Comptable Général (PCG) pour Pennylane."""
        return _load_resource_md("comptes_classes.md")

    @mcp.resource(
        "pennylane://journaux/actifs",
        name="journaux-actifs",
        title="Journaux Comptables Actifs",
        description="Expose la liste des journaux comptables actifs dans le dossier en cours.",
        mime_type="application/json",
    )
    async def resource_journaux_actifs() -> str:
        """Expose la liste des journaux comptables actifs dans le dossier en cours."""
        try:
            journals_data = await api_get("/journals")
            return to_json(journals_data)
        except Exception as exc:
            # Fallback en cas d'erreur ou d'absence de token connecté
            fallback = [
                {"code": "VE", "name": "Ventes", "type": "sales", "description": "Factures clients et avoirs"},
                {"code": "HA", "name": "Achats", "type": "purchases", "description": "Factures fournisseurs et notes de frais"},
                {"code": "BQ", "name": "Banque", "type": "bank", "description": "Mouvements bancaires et rapprochements"},
                {"code": "OD", "name": "Opérations Diverses", "type": "miscellaneous", "description": "Écritures de régularisation, TVA, salaires, à-nouveaux"},
                {"code": "PA", "name": "Paie", "type": "payroll", "description": "Écritures de paie et charges sociales"},
                {"code": "RB", "name": "Rejets bancaires", "type": "bank_rejects", "description": "Gestion des rejets et impayés"},
            ]
            return f"Liste standard (Fallback - API indisponible : {exc}):\n\n{to_json(fallback)}"

    # ── Resource Templates (Ressources dynamiques avec paramètres) ─────────

    @mcp.resource(
        "pennylane://dossier/{slug}/info",
        name="dossier-info",
        title="Métadonnées d'un Dossier",
        description="Expose les métadonnées et la configuration d'un dossier client spécifique via son slug.",
        mime_type="application/json",
    )
    def resource_dossier_info(slug: str) -> str:
        """Expose les informations d'un dossier client spécifique configuré dans le serveur."""
        try:
            if has_manager():
                manager = get_manager()
                dc = manager.get_dossier(slug)
                if dc:
                    return to_json({
                        "slug": dc.slug,
                        "name": dc.name,
                        "created_at": str(dc.created_at),
                        "notes": dc.notes,
                        "is_current": (slug == manager.current_slug),
                    })
                return f"{{\"error\": \"Dossier '{slug}' introuvable dans la configuration\"}}"
            return "{\"error\": \"Gestionnaire de dossiers non initialisé\"}"
        except Exception as exc:
            return f"{{\"error\": \"Erreur lors de la lecture du dossier {slug} : {exc}\"}}"

    @mcp.resource(
        "pennylane://compte/{account_number}",
        name="compte-detail",
        title="Détail Compte Comptable",
        description="Expose les informations d'un compte comptable spécifique à partir de son numéro (ex: 411, 401, 512).",
        mime_type="application/json",
    )
    async def resource_compte_detail(account_number: str) -> str:
        """Expose les informations d'un compte comptable spécifique dans le dossier actif."""
        try:
            import json
            filter_param = json.dumps([{"field": "number", "operator": "eq", "value": account_number}])
            data = await api_get("/ledger_accounts", {"filter": filter_param})
            items = data.get("items", [])
            if items:
                return to_json({"account": items[0], "status": "trouvé"})
            return to_json({"error": f"Compte '{account_number}' non trouvé dans le plan comptable", "status": "non_trouvé"})
        except Exception as exc:
            return f"{{\"error\": \"Impossible de lire le compte {account_number} : {exc}\"}}"

    @mcp.resource(
        "pennylane://guide/e-invoicing",
        name="guide-e-invoicing",
        title="Guide Facturation Électronique & PPF/PA",
        description="Expose les normes légales, formats (Factur-X, UBL, CII) et le cycle de vie e-invoicing dans Pennylane.",
        mime_type="text/markdown",
    )
    def resource_guide_einvoicing() -> str:
        """Expose le guide pratique et réglementaire sur la facturation électronique."""
        return _load_resource_md("guide_e_invoicing.md")

    @mcp.resource(
        "pennylane://guide/analytique",
        name="guide-analytique",
        title="Guide Comptabilité Analytique & Ventilation",
        description="Expose la logique des groupes, catégories, poids (weight=1.0) et le calcul de rentabilité par projet.",
        mime_type="text/markdown",
    )
    def resource_guide_analytique() -> str:
        """Expose le guide de structuration et lettrage analytique dans Pennylane."""
        return _load_resource_md("guide_analytique.md")

    @mcp.resource(
        "pennylane://guide/workflows",
        name="guide-workflows",
        title="Guide Synoptique des Workflows MCP",
        description="Expose le catalogue des commandes slash et prompts MCP pour aider l'IA à proposer le bon workflow au bon moment.",
        mime_type="text/markdown",
    )
    def resource_guide_workflows() -> str:
        """Expose le guide synoptique des 8 workflows et commandes slash MCP."""
        return _load_resource_md("guide_workflows.md")

    @mcp.resource(
        "pennylane://client/{customer_id}/encours",
        name="client-encours",
        title="Encours et Factures Impayées Client",
        description="Expose en temps réel le détail des factures en attente de règlement pour un client spécifique via son ID.",
        mime_type="application/json",
    )
    async def resource_client_encours(customer_id: str) -> str:
        """Expose les factures impayées et l'encours d'un client spécifique."""
        try:
            import json
            filter_param = json.dumps([{"field": "customer_id", "operator": "eq", "value": int(customer_id)}])
            data = await api_get("/customer_invoices", {"filter": filter_param})
            items = data.get("items", [])
            unpaid = [inv for inv in items if inv.get("status") in ("unpaid", "late", "sent")]
            total_unpaid = sum(float(inv.get("amount", 0)) for inv in unpaid)
            return to_json({
                "customer_id": customer_id,
                "unpaid_invoices_count": len(unpaid),
                "total_unpaid_amount": total_unpaid,
                "invoices": unpaid[:10],
                "status": "calculé",
            })
        except Exception as exc:
            return f"{{\"error\": \"Impossible de calculer l'encours pour le client {customer_id} : {exc}\"}}"

    @mcp.resource(
        "pennylane://fournisseur/{supplier_id}/encours",
        name="fournisseur-encours",
        title="Encours et Factures à Payer Fournisseur",
        description="Expose en temps réel le détail des factures fournisseurs en attente de paiement pour un fournisseur par son ID.",
        mime_type="application/json",
    )
    async def resource_fournisseur_encours(supplier_id: str) -> str:
        """Expose les factures à payer et l'encours d'un fournisseur spécifique."""
        try:
            import json
            filter_param = json.dumps([{"field": "supplier_id", "operator": "eq", "value": int(supplier_id)}])
            data = await api_get("/supplier_invoices", {"filter": filter_param})
            items = data.get("items", [])
            unpaid = [inv for inv in items if inv.get("status") in ("unpaid", "late", "to_pay", "pending")]
            total_unpaid = sum(float(inv.get("amount", 0) or inv.get("total_amount", 0)) for inv in unpaid)
            return to_json({
                "supplier_id": supplier_id,
                "unpaid_invoices_count": len(unpaid),
                "total_unpaid_amount": total_unpaid,
                "invoices": unpaid[:10],
                "status": "calculé",
            })
        except Exception as exc:
            return f"{{\"error\": \"Impossible de calculer l'encours pour le fournisseur {supplier_id} : {exc}\"}}"

    @mcp.resource(
        "pennylane://journal/{journal_code}/recent",
        name="journal-recent",
        title="Écritures Récentes d'un Journal",
        description="Expose les 20 dernières écritures comptables enregistrées dans un journal spécifique via son code (ex: VT, HA, BQ).",
        mime_type="application/json",
    )
    async def resource_journal_recent(journal_code: str) -> str:
        """Expose les écritures récentes d'un journal comptable donné."""
        try:
            import json
            filter_param = json.dumps([{"field": "journal_code", "operator": "eq", "value": journal_code.upper()}])
            data = await api_get("/ledger_entries", {"filter": filter_param, "limit": 20, "sort": "-date"})
            items = data.get("items", [])
            return to_json({
                "journal_code": journal_code.upper(),
                "entries_count": len(items),
                "recent_entries": items,
                "status": "récupéré",
            })
        except Exception as exc:
            return f"{{\"error\": \"Impossible de récupérer les écritures du journal {journal_code} : {exc}\"}}"

    @mcp.resource(
        "pennylane://devis/en_attente",
        name="devis-en-attente",
        title="Devis Client en Attente de Validation",
        description="Expose la liste des devis envoyés ou en cours de négociation en attente de signature client.",
        mime_type="application/json",
    )
    async def resource_devis_en_attente() -> str:
        """Expose en temps réel les devis clients en attente d'acceptation."""
        try:
            import json
            filter_param = json.dumps([{"field": "status", "operator": "in", "value": ["sent", "pending", "viewed"]}])
            data = await api_get("/quotes", {"filter": filter_param, "limit": 20})
            items = data.get("items", [])
            total_potential = sum(float(q.get("total_amount", 0) or q.get("amount", 0)) for q in items)
            return to_json({
                "pending_quotes_count": len(items),
                "total_potential_revenue": total_potential,
                "quotes": items,
                "status": "récupéré",
            })
        except Exception as exc:
            return f"{{\"error\": \"Impossible de lire la liste des devis en attente : {exc}\"}}"

