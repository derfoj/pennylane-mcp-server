#!/usr/bin/env python3
"""Serveur MCP Pennylane — Point d'entrée principal.

Serveur MCP (Model Context Protocol) complet pour l'API comptable Pennylane.
Conçu pour les experts-comptables, il expose 120+ outils couvrant :
  - Plan comptable (CRUD)
  - Journaux comptables
  - Écritures comptables (CRUD + lignes)
  - Lignes d'écriture (lettrage, analytique)
  - Balance générale
  - Exercices fiscaux
  - Clients (entreprises et particuliers)
  - Fournisseurs
  - Factures clients (CRUD, finalisation, paiement, e-invoicing PA, annexes)
  - Factures fournisseurs (consultation, mise à jour, paiement, e-invoicing PA, OCR)
  - Produits / services (catalogue)
  - Devis (CRUD, envoi par email, statut, annexes)
  - Catégories analytiques (groupes et catégories)
  - Exports comptables (FEC, Grand Livre Général, Grand Livre Analytique)
  - Abonnements de facturation récurrente
  - Suivi des modifications (ChangeLogs)
  - Comptes bancaires & établissements (IBAN, BIC)
  - Transactions bancaires & lettrage / rapprochement
  - Mandats de prélèvement (SEPA, GoCardless, Pro Account)
  - Documents commerciaux non comptabilisés
  - Demandes d'achats & bons de commande
  - Statut d'immatriculation Plateforme Agréée (PA)
  - Pièces jointes / fichiers annexes (File Attachments)
  - Gestion multi-dossiers (v2.0)

Modes de transport :
  - stdio  : usage local (Claude Desktop, Claude Code) — par défaut
  - sse    : usage distant via URL (Dust, site web) — activé par MCP_TRANSPORT=sse

Modes de fonctionnement :
  1. Multi-dossiers : fichier dossiers.json (recommandé pour les cabinets)
  2. Mono-dossier : variable PENNYLANE_API_TOKEN (rétrocompatibilité)

Variables d'environnement :
    PENNYLANE_API_TOKEN   — Token Bearer (mode mono-dossier) : Company API
                            Token, ou Firm API Token si PENNYLANE_COMPANY_ID
                            est défini
    PENNYLANE_COMPANY_ID  — ID société Pennylane (header X-Company-Id),
                            requis avec un Firm API Token
    PENNYLANE_CONFIG_PATH — Chemin vers dossiers.json (optionnel)
    MCP_TRANSPORT         — Transport : 'stdio' (défaut) ou 'sse'
    MCP_HOST              — Hôte d'écoute SSE (défaut: 127.0.0.1)
    MCP_PORT              — Port d'écoute SSE (défaut: 8000)
"""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP

from .api import close_client, init_client
from .constants import SERVER_NAME, SERVER_VERSION
from .dossier_manager import DossierManager, set_manager
from . import prompts, resources
from .tools import (
    accounts,
    bank_accounts,
    billing_subscriptions,
    categories,
    changelogs,
    commercial_documents,
    customer_invoices,
    customers,
    dossiers,
    entries,
    entry_lines,
    exports,
    file_attachments,
    journals,
    mandates,
    me,
    pa_registrations,
    products,
    purchase_requests,
    quotes,
    supplier_invoices,
    suppliers,
    transactions,
    trial_balance,
)


def _default_config_path() -> Path:
    """Chemin par défaut (toujours accessible en écriture) pour dossiers.json.

    Ne JAMAIS utiliser le répertoire courant : les clients MCP (Claude
    Desktop, etc.) lancent souvent le serveur depuis un répertoire système
    non inscriptible (ex: C:\\WINDOWS\\system32).

    Windows : %APPDATA%\\pennylane-mcp\\dossiers.json
    Autres  : ~/.config/pennylane-mcp/dossiers.json
    """
    if os.name == "nt":
        base = Path(
            os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        )
        return base / "pennylane-mcp" / "dossiers.json"
    return Path.home() / ".config" / "pennylane-mcp" / "dossiers.json"


def _find_config_path() -> Path | None:
    """Recherche le fichier dossiers.json dans les emplacements habituels.

    Ordre de priorité :
    1. Variable d'environnement PENNYLANE_CONFIG_PATH
    2. Répertoire courant : ./dossiers.json (lecture seule, si déjà présent)
    3. Config utilisateur : %APPDATA%\\pennylane-mcp (Windows)
       ou ~/.config/pennylane-mcp (autres)
    """
    # 1. Variable d'environnement explicite
    env_path = os.environ.get("PENNYLANE_CONFIG_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p
        # Le chemin est spécifié mais n'existe pas encore → on l'utilisera
        # pour la création par add_dossier
        return p

    # 2. Répertoire courant
    cwd = Path.cwd() / "dossiers.json"
    if cwd.exists():
        return cwd

    # 3. Config utilisateur (APPDATA sous Windows, ~/.config ailleurs)
    default = _default_config_path()
    if default.exists():
        return default

    # Rétrocompatibilité : ancien emplacement ~/.config même sous Windows
    home_config = Path.home() / ".config" / "pennylane-mcp" / "dossiers.json"
    if home_config.exists():
        return home_config

    return None


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Cycle de vie du serveur : initialisation multi-dossiers ou mono-dossier."""

    manager = None
    config_path = _find_config_path()

    # ── Tentative mode multi-dossiers ─────────────────────────────────────
    if config_path and config_path.exists():
        manager = DossierManager(config_path)
        loaded = await manager.load_config()

        if loaded and manager.has_dossiers():
            # Mode multi-dossiers activé
            await manager.init_all_clients()

            # Auto-sélection du premier dossier si aucun n'est défini
            if manager.current_slug is None:
                slugs = manager.list_slugs()
                if slugs:
                    await manager.switch_dossier(slugs[0])

            set_manager(manager)
            print(
                f"🚀 {SERVER_NAME} v{SERVER_VERSION} démarré — "
                f"Mode multi-dossiers ({manager.dossier_count} dossier(s), "
                f"actif: {manager.current_slug})",
                file=sys.stderr,
            )
            try:
                yield {}
            finally:
                await manager.close_all()
                print(f"🛑 {SERVER_NAME} arrêté", file=sys.stderr)
            return

    # ── Fallback : mode mono-dossier (rétrocompatibilité) ─────────────────
    api_token = os.environ.get("PENNYLANE_API_TOKEN", "")

    if not api_token:
        # Aucune configuration trouvée — créer un manager vide pour
        # permettre l'ajout dynamique de dossiers via les outils
        if config_path is None:
            # Définir un chemin par défaut pour la sauvegarde
            config_path = _default_config_path()

        manager = DossierManager(config_path)
        set_manager(manager)

        print(
            f"🚀 {SERVER_NAME} v{SERVER_VERSION} démarré — "
            f"Mode initial (aucun dossier configuré).\n"
            f"   Utilisez pennylane_add_dossier pour ajouter un dossier,\n"
            f"   ou définissez PENNYLANE_API_TOKEN pour le mode mono-dossier.",
            file=sys.stderr,
        )
        try:
            yield {}
        finally:
            if manager.has_dossiers():
                await manager.close_all()
            print(f"🛑 {SERVER_NAME} arrêté", file=sys.stderr)
        return

    # Mode mono-dossier avec PENNYLANE_API_TOKEN
    # On crée quand même un DossierManager pour uniformiser l'accès
    if config_path is None:
        config_path = _default_config_path()

    # PENNYLANE_COMPANY_ID : à définir si PENNYLANE_API_TOKEN est un
    # Firm API Token (token cabinet) — envoyé via le header X-Company-Id.
    company_id_env = os.environ.get("PENNYLANE_COMPANY_ID", "").strip()
    company_id: int | None = None
    if company_id_env:
        try:
            company_id = int(company_id_env)
        except ValueError:
            print(
                f"⚠️  PENNYLANE_COMPANY_ID invalide (entier attendu) : "
                f"'{company_id_env}' — ignoré.",
                file=sys.stderr,
            )

    manager = DossierManager(config_path)
    await manager.add_dossier(
        slug="default",
        name="Dossier principal",
        token=api_token,
        company_id=company_id,
        save=False,  # Ne pas sauvegarder en mode legacy
    )
    set_manager(manager)

    mode_info = (
        f" (Firm token, X-Company-Id={company_id})" if company_id else ""
    )
    print(
        f"🚀 {SERVER_NAME} v{SERVER_VERSION} démarré — "
        f"Mode mono-dossier{mode_info}",
        file=sys.stderr,
    )
    try:
        yield {}
    finally:
        await manager.close_all()
        await close_client()
        print(f"🛑 {SERVER_NAME} arrêté", file=sys.stderr)


# ─── Instructions de serveur pour Claude ─────────────────────────────────────

INSTRUCTIONS_CLAUDE = """Tu es un assistant expert-comptable connecté à l'API comptable Pennylane V2 via le Model Context Protocol (MCP).
Règles impératives et piliers d'interaction avec ce serveur :
1. Équilibre comptable absolu : Toute écriture créée via `pennylane_create_entry` doit rigoureusement équilibrer le total des Débits et des Crédits (Total Débit == Total Crédit).
2. Référentiel du Plan Comptable Général (PCG) :
   - Classe 1 : Capitaux (101 Capital, 164 Emprunts)
   - Classe 2 : Immobilisations (218 Matériel)
   - Classe 4 : Tiers (401=Fournisseurs, 411=Clients, 421=Personnel, 43=Sécurité Sociale, 44=TVA)
   - Classe 5 : Trésorerie (512=Banque, 530=Caisse impérativement débitrice ou nulle, JAMAIS créditrice)
   - Classe 6 : Charges (60 Achats, 61/62 Services extérieurs, 63 Impôts, 64 Personnel)
   - Classe 7 : Produits/CA (701 Ventes produits finis, 706 Prestations, 707 Marchandises, 709 Rabais accordés)
3. Exploitation pro-active des Prompts et Workflows MCP :
   - Suggère et lance proactivement les workflows intégrés lorsque le cas s'y prête :
     * `/relance_impayes_clients` : pour l'analyse des créances et relances.
     * `/rapprochement_bancaire_ia` : pour réconcilier les mouvements bancaires non lettrés.
     * `/diagnostic_facturation_electronique` : pour auditer le SIRET/TVA et l'annuaire PA/PPF.
     * `/audit_analytique_rentabilite` : pour vérifier la ventilation (somme des weight == 1.0) et la marge projet.
     * `/audit_cloture_mensuelle`, `/synthese_chiffre_affaires`, `/comparatif_multi_dossiers`, `/verification_conformite_fec_tva`.
4. Exploitation des Ressources et Templates de Ressources (zéro consommation d'outil/jeton) :
   - Avant de requêter des listes lourdes, lis en priorité les guides : `pennylane://guide/workflows`, `pennylane://guide/e-invoicing`, `pennylane://guide/analytique`, `pennylane://comptes/classes`.
   - Utilise les templates dynamiques pour un diagnostic immédiat : `pennylane://client/{id}/encours`, `pennylane://fournisseur/{id}/encours`, `pennylane://compte/{numero}`, `pennylane://journal/{code}/recent`, `pennylane://devis/en_attente`.
5. Bonnes pratiques et Gestion Multi-dossiers :
   - Toujours rechercher ou vérifier le numéro de compte exact via `pennylane_list_accounts` avant de passer une écriture en cas de doute.
   - En cas d'écart sur la balance, vérifie en priorité les comptes d'attente (471/472/58) et la caisse (530).
   - En mode multi-dossiers, vérifie toujours le dossier actif avec `pennylane_current_dossier` avant toute opération sensible de création ou de modification.
"""

# ─── Création du serveur ─────────────────────────────────────────────────────

mcp = FastMCP(
    SERVER_NAME,
    instructions=INSTRUCTIONS_CLAUDE,
    lifespan=lifespan,
)

# ─── Enregistrement de tous les outils, prompts et ressources ────────────────

prompts.register(mcp)
resources.register(mcp)

me.register(mcp)
accounts.register(mcp)
journals.register(mcp)
entries.register(mcp)
entry_lines.register(mcp)
trial_balance.register(mcp)
customers.register(mcp)
suppliers.register(mcp)
customer_invoices.register(mcp)
supplier_invoices.register(mcp)
products.register(mcp)
quotes.register(mcp)
categories.register(mcp)
exports.register(mcp)
billing_subscriptions.register(mcp)
changelogs.register(mcp)
bank_accounts.register(mcp)
transactions.register(mcp)
mandates.register(mcp)
commercial_documents.register(mcp)
purchase_requests.register(mcp)
pa_registrations.register(mcp)
file_attachments.register(mcp)
dossiers.register(mcp)  # Outils multi-dossiers (v2.0)


# ─── Point d'entrée ─────────────────────────────────────────────────────────


def main() -> None:
    """Démarre le serveur MCP.

    Le mode de transport est déterminé par la variable MCP_TRANSPORT :
      - 'stdio' (défaut) : communication locale via stdin/stdout
      - 'sse'            : serveur HTTP avec Server-Sent Events

    En mode SSE, le serveur écoute sur MCP_HOST:MCP_PORT (défaut 127.0.0.1:8000).
    L'authentification est gérée par le middleware McpMiddleware (Bearer token).
    """
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip().lower()

    if transport == "sse":
        host = os.environ.get("MCP_HOST", "127.0.0.1")
        port = int(os.environ.get("MCP_PORT", "8000"))
        print(
            f"🌐 {SERVER_NAME} v{SERVER_VERSION} — Mode SSE\n"
            f"   Écoute sur http://{host}:{port}/sse\n"
            f"   Utilisez un reverse proxy (Nginx) avec HTTPS en production.",
            file=sys.stderr,
        )
        import uvicorn
        from mcp.server.fastmcp import FastMCP
        mcp_app = mcp.sse_app()

        # Token d'authentification (optionnel)
        auth_token = os.environ.get("MCP_AUTH_TOKEN", "")

        # Middleware reverse proxy + authentification
        class McpMiddleware:
            def __init__(self, app):
                self.app = app
            async def __call__(self, scope, receive, send):
                if scope["type"] == "http":
                    headers_dict = dict(scope.get("headers", []))
                    # Vérifier le token Bearer si configuré
                    if auth_token:
                        auth_header = headers_dict.get(b"authorization", b"").decode()
                        if auth_header != f"Bearer {auth_token}":
                            await send({"type": "http.response.start", "status": 401, "headers": [(b"content-type", b"text/plain")]})
                            await send({"type": "http.response.body", "body": b"Unauthorized"})
                            return
                    # Fix Host header pour Traefik
                    hdrs = [(k, b"localhost:8000" if k == b"host" else v) for k, v in scope.get("headers", [])]
                    scope = dict(scope, headers=hdrs)
                await self.app(scope, receive, send)

        mcp_app = McpMiddleware(mcp_app)
        uvicorn.run(mcp_app, host=host, port=port, log_level="info")
    else:
        print(
            f"🚀 {SERVER_NAME} v{SERVER_VERSION} — Mode stdio",
            file=sys.stderr,
        )
        mcp.run()


if __name__ == "__main__":
    main()
