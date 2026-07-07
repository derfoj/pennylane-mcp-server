"""Outils MCP : gestion des factures fournisseurs (Supplier Invoices)."""

from __future__ import annotations

import json
from typing import Annotated, Optional

from pydantic import Field
from mcp.server.fastmcp import FastMCP

from ..api import api_get, api_post, api_put
from ..utils import pagination_summary, to_json, truncate_if_needed


def register(mcp: FastMCP) -> None:
    """Enregistre les outils de gestion des factures fournisseurs."""

    # ── Lister les factures fournisseurs ─────────────────────────────────────

    @mcp.tool(
        name="pennylane_list_supplier_invoices",
        annotations={
            "title": "Lister les factures fournisseurs",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_supplier_invoices(
        cursor: Annotated[Optional[str], Field(default=None, description="Curseur pour la pagination.")] = None,
        limit: Annotated[int, Field(default=20, ge=1, le=100, description="Nombre de résultats (1-100, défaut: 20).")] = 20,
        status: Annotated[Optional[str], Field(
            default=None,
            description="Filtrer par statut : 'pending', 'accounted', 'paid'.",
        )] = None,
        supplier_id: Annotated[Optional[int], Field(
            default=None,
            description="Filtrer par ID fournisseur.",
        )] = None,
        sort: Annotated[Optional[str], Field(default=None, description="Tri: 'id', '-id' (défaut: '-id').")] = None,
    ) -> str:
        """Liste les factures fournisseurs avec filtres et pagination.
        Utile pour consulter les factures reçues, filtrer par statut ou fournisseur.
        """
        try:
            qp: dict = {"limit": limit}
            if cursor:
                qp["cursor"] = cursor
            if sort:
                qp["sort"] = sort

            filters: list[dict] = []
            if status:
                filters.append({"field": "status", "operator": "eq", "value": status})
            if supplier_id:
                filters.append({"field": "supplier_id", "operator": "eq", "value": supplier_id})
            if filters:
                qp["filter"] = json.dumps(filters)

            data = await api_get("/supplier_invoices", qp)
            items = data.get("items", [])
            result = {
                "supplier_invoices": items,
                "pagination": pagination_summary(
                    data.get("has_more"), data.get("next_cursor"),
                    data.get("total_items"), len(items),
                ),
                "next_cursor": data.get("next_cursor"),
            }
            return truncate_if_needed(to_json(result))
        except Exception as exc:
            return f"❌ {exc}"

    # ── Récupérer une facture fournisseur ────────────────────────────────────

    @mcp.tool(
        name="pennylane_get_supplier_invoice",
        annotations={
            "title": "Détail d'une facture fournisseur",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_get_supplier_invoice(
        id: Annotated[int, Field(description="Identifiant unique de la facture fournisseur.")],
    ) -> str:
        """Récupère le détail complet d'une facture fournisseur.
        Retourne toutes les informations : montants, lignes, statut, fournisseur.
        """
        try:
            data = await api_get(f"/supplier_invoices/{id}")
            return truncate_if_needed(to_json(data))
        except Exception as exc:
            return f"❌ {exc}"

    # ── Mettre à jour une facture fournisseur ────────────────────────────────

    @mcp.tool(
        name="pennylane_update_supplier_invoice",
        annotations={
            "title": "Modifier une facture fournisseur",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_update_supplier_invoice(
        id: Annotated[int, Field(description="Identifiant de la facture fournisseur à modifier.")],
        date: Annotated[Optional[str], Field(default=None, description="Nouvelle date (YYYY-MM-DD).")] = None,
        deadline: Annotated[Optional[str], Field(default=None, description="Nouvelle échéance (YYYY-MM-DD).")] = None,
        supplier_id: Annotated[Optional[int], Field(default=None, description="Nouvel ID fournisseur.")] = None,
        invoice_number: Annotated[Optional[str], Field(default=None, description="Numéro de facture.")] = None,
    ) -> str:
        """Modifie une facture fournisseur. Seuls les champs fournis sont mis à jour."""
        try:
            body: dict = {}
            if date is not None:
                body["date"] = date
            if deadline is not None:
                body["deadline"] = deadline
            if supplier_id is not None:
                body["supplier_id"] = supplier_id
            if invoice_number is not None:
                body["invoice_number"] = invoice_number

            data = await api_put(f"/supplier_invoices/{id}", body)
            return f"✅ Facture fournisseur {id} mise à jour.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Lister les lignes d'une facture fournisseur ──────────────────────────

    @mcp.tool(
        name="pennylane_list_supplier_invoice_lines",
        annotations={
            "title": "Lignes d'une facture fournisseur",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_supplier_invoice_lines(
        supplier_invoice_id: Annotated[int, Field(description="ID de la facture fournisseur.")],
        cursor: Annotated[Optional[str], Field(default=None, description="Curseur pour la pagination.")] = None,
        limit: Annotated[int, Field(default=50, ge=1, le=100, description="Nombre de résultats (1-100, défaut: 50).")] = 50,
    ) -> str:
        """Liste les lignes (articles) d'une facture fournisseur spécifique."""
        try:
            qp: dict = {"limit": limit}
            if cursor:
                qp["cursor"] = cursor

            data = await api_get(f"/supplier_invoices/{supplier_invoice_id}/invoice_lines", qp)
            items = data.get("items", [])
            result = {
                "invoice_lines": items,
                "pagination": pagination_summary(
                    data.get("has_more"), data.get("next_cursor"),
                    data.get("total_items"), len(items),
                ),
                "next_cursor": data.get("next_cursor"),
            }
            return truncate_if_needed(to_json(result))
        except Exception as exc:
            return f"❌ {exc}"

    # ── Mettre à jour le statut de paiement ──────────────────────────────────

    @mcp.tool(
        name="pennylane_update_supplier_invoice_payment_status",
        annotations={
            "title": "Modifier le statut de paiement d'une facture fournisseur",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_update_supplier_invoice_payment_status(
        supplier_invoice_id: Annotated[int, Field(description="ID de la facture fournisseur.")],
        payment_status: Annotated[str, Field(
            description="Nouveau statut : 'unpaid', 'paid', 'partially_paid'.",
        )],
    ) -> str:
        """Met à jour le statut de paiement d'une facture fournisseur."""
        try:
            body = {"payment_status": payment_status}
            data = await api_put(
                f"/supplier_invoices/{supplier_invoice_id}/payment_status",
                body,
            )
            return (
                f"✅ Statut de paiement de la facture fournisseur {supplier_invoice_id} "
                f"mis à jour → {payment_status}.\n\n{to_json(data)}"
            )
        except Exception as exc:
            return f"❌ {exc}"

    # ── Catégoriser une facture fournisseur ───────────────────────────────────

    @mcp.tool(
        name="pennylane_categorize_supplier_invoice",
        description="Met à jour la ventilation analytique (catégories et poids) d'une facture fournisseur.",
        annotations={
            "title": "Catégoriser une facture fournisseur",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_categorize_supplier_invoice(
        id: Annotated[int, Field(description="Identifiant de la facture fournisseur.")],
        categories: Annotated[list[dict], Field(description="Liste de catégories avec poids. Ex: [{'id': 59, 'weight': '1.0'}].")],
    ) -> str:
        """Affecte des axes analytiques à une facture fournisseur."""
        try:
            body = {"categories": categories}
            data = await api_put(f"/supplier_invoices/{id}/categories", body)
            return f"✅ Catégories de la facture fournisseur {id} mises à jour.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Lister les catégories d'une facture fournisseur ───────────────────────

    @mcp.tool(
        name="pennylane_list_supplier_invoice_categories",
        description="Consulte les axes analytiques associés à une facture fournisseur.",
        annotations={
            "title": "Catégories d'une facture fournisseur",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_supplier_invoice_categories(
        id: Annotated[int, Field(description="Identifiant de la facture fournisseur.")],
    ) -> str:
        """Liste la ventilation analytique d'une facture fournisseur."""
        try:
            data = await api_get(f"/supplier_invoices/{id}/categories")
            return to_json(data)
        except Exception as exc:
            return f"❌ {exc}"

    # ── Importer une facture fournisseur électronique (e-invoice) ─────────────

    @mcp.tool(
        name="pennylane_import_supplier_einvoice",
        description="Importe une facture fournisseur au format Factur-X PDF ou XML (UBL/CII).",
        annotations={
            "title": "Importer facture fournisseur électronique",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_import_supplier_einvoice(
        file_attachment_id: Annotated[int, Field(description="ID du fichier uploadé contenant la facture Factur-X/XML.")],
    ) -> str:
        """Importe et convertit une facture fournisseur électronique reçue."""
        try:
            body = {"file_attachment_id": file_attachment_id}
            data = await api_post("/supplier_invoices/e_invoice_import", body)
            return f"✅ Facture fournisseur électronique importée (id: {data.get('id')}).\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Modifier le statut e-invoice d'une facture fournisseur ────────────────

    @mcp.tool(
        name="pennylane_update_supplier_einvoice_status",
        description="Applique une transition de cycle de vie e-invoicing : dispute, refuse, undispute (approuvé).",
        annotations={
            "title": "Statut e-invoice facture fournisseur",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_update_supplier_einvoice_status(
        id: Annotated[int, Field(description="Identifiant de la facture fournisseur.")],
        status: Annotated[str, Field(description="Nouveau statut e-invoicing : 'dispute', 'refuse', ou 'undispute'.")],
        reason: Annotated[Optional[str], Field(default=None, description="Raison en cas de refus ou litige (requis pour dispute/refuse).")] = None,
    ) -> str:
        """Change le statut PPF / PA d'une facture fournisseur reçue en e-invoicing."""
        try:
            body: dict = {"status": status}
            if reason:
                body["reason"] = reason
            data = await api_put(f"/supplier_invoices/{id}/e_invoice_status", body)
            return f"✅ Statut e-invoicing de la facture {id} mis à jour → {status}.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Valider la comptabilisation d'une facture fournisseur ─────────────────

    @mcp.tool(
        name="pennylane_validate_supplier_invoice_accounting",
        description="Valide l'écriture comptable d'une facture fournisseur pour la faire passer en statut Complete.",
        annotations={
            "title": "Valider comptabilité facture fournisseur",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_validate_supplier_invoice_accounting(
        id: Annotated[int, Field(description="Identifiant de la facture fournisseur à valider comptablement.")],
    ) -> str:
        """Clôture la révision comptable d'une facture d'achat."""
        try:
            data = await api_put(f"/supplier_invoices/{id}/validate_accounting", {})
            return f"✅ Facture fournisseur {id} validée comptablement (statut: Complete).\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Importer une facture fournisseur avec fichier joint ───────────────────

    @mcp.tool(
        name="pennylane_import_supplier_invoice",
        description="Importe une facture fournisseur classique avec un ID de fichier joint.",
        annotations={
            "title": "Importer facture fournisseur avec fichier",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_import_supplier_invoice(
        file_attachment_id: Annotated[int, Field(description="ID du fichier joint (ex: PDF de la facture).")],
        supplier_id: Annotated[Optional[int], Field(default=None, description="ID du fournisseur si connu.")] = None,
    ) -> str:
        """Importe un document d'achat dans l'OCR / module factures fournisseurs."""
        try:
            body: dict = {"file_attachment_id": file_attachment_id}
            if supplier_id:
                body["supplier_id"] = supplier_id
            data = await api_post("/supplier_invoices/import", body)
            return f"✅ Facture fournisseur importée avec succès.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Transactions rapprochées d'une facture fournisseur ────────────────────

    @mcp.tool(
        name="pennylane_list_supplier_invoice_matched_transactions",
        description="Liste les règlements bancaires rapprochés d'une facture fournisseur.",
        annotations={
            "title": "Transactions rapprochées facture fournisseur",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_supplier_invoice_matched_transactions(
        id: Annotated[int, Field(description="Identifiant de la facture fournisseur.")],
    ) -> str:
        """Consulte les paiements bancaires lettrés sur l'achat."""
        try:
            data = await api_get(f"/supplier_invoices/{id}/matched_transactions")
            return to_json(data)
        except Exception as exc:
            return f"❌ {exc}"

    # ── Paiements d'une facture fournisseur ───────────────────────────────────

    @mcp.tool(
        name="pennylane_list_supplier_invoice_payments",
        description="Liste l'historique des paiements enregistrés pour une facture fournisseur.",
        annotations={
            "title": "Paiements d'une facture fournisseur",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_supplier_invoice_payments(
        id: Annotated[int, Field(description="Identifiant de la facture fournisseur.")],
    ) -> str:
        """Liste tous les décaissements associés à la facture."""
        try:
            data = await api_get(f"/supplier_invoices/{id}/payments")
            return to_json(data)
        except Exception as exc:
            return f"❌ {exc}"

