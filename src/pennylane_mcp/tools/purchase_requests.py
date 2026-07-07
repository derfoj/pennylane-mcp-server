"""Outils MCP : demandes d'achat et commandes fournisseurs (Purchase Requests)."""

from __future__ import annotations

import json
from typing import Annotated, Any, Optional

from pydantic import Field
from mcp.server.fastmcp import FastMCP

from ..api import api_get, api_post
from ..utils import pagination_summary, to_json, truncate_if_needed


def register(mcp: FastMCP) -> None:
    """Enregistre les outils pour les demandes d'achat et l'import de bons de commande."""

    # ── Lister les demandes d'achat ───────────────────────────────────────────

    @mcp.tool(
        name="pennylane_list_purchase_requests",
        description="Liste les demandes d'achat et bons de commande fournisseurs avec pagination.",
        annotations={
            "title": "Lister les demandes d'achat",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_purchase_requests(
        cursor: Annotated[Optional[str], Field(default=None, description="Curseur pour la pagination.")] = None,
        limit: Annotated[int, Field(default=20, ge=1, le=100, description="Nombre de résultats (1-100, défaut: 20).")] = 20,
        sort: Annotated[Optional[str], Field(default=None, description="Tri: 'id', '-id', 'created_at', '-created_at'.")] = None,
    ) -> str:
        """Liste les demandes d'achat initiées ou validées dans le cabinet/société."""
        try:
            qp: dict = {"limit": limit}
            if cursor:
                qp["cursor"] = cursor
            if sort:
                qp["sort"] = sort

            data = await api_get("/purchase_requests", qp)
            items = data.get("items", [])
            result = {
                "purchase_requests": items,
                "pagination": pagination_summary(
                    data.get("has_more"), data.get("next_cursor"),
                    data.get("total_items"), len(items),
                ),
                "next_cursor": data.get("next_cursor"),
            }
            return truncate_if_needed(to_json(result))
        except Exception as exc:
            return f"❌ {exc}"

    # ── Détail d'une demande d'achat ──────────────────────────────────────────

    @mcp.tool(
        name="pennylane_get_purchase_request",
        description="Récupère le détail complet d'une demande d'achat par son identifiant.",
        annotations={
            "title": "Détail d'une demande d'achat",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_get_purchase_request(
        id: Annotated[int, Field(description="Identifiant unique de la demande d'achat.")],
    ) -> str:
        """Récupère une demande d'achat spécifique."""
        try:
            data = await api_get(f"/purchase_requests/{id}")
            return to_json(data)
        except Exception as exc:
            return f"❌ {exc}"

    # ── Importer un bon de commande ───────────────────────────────────────────

    @mcp.tool(
        name="pennylane_import_purchase_order",
        description="Importe un bon de commande fournisseur. Crée automatiquement une demande d'achat validée.",
        annotations={
            "title": "Importer un bon de commande",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_import_purchase_order(
        supplier_id: Annotated[int, Field(description="ID du fournisseur rattaché au bon de commande.")],
        document_number: Annotated[str, Field(description="Numéro du bon de commande (ex: 'PO-2026-0042').")],
        issue_date: Annotated[str, Field(description="Date du bon de commande (YYYY-MM-DD).")],
        total_tax_included: Annotated[str, Field(description="Montant TTC du bon de commande (ex: '1200.00').")],
        currency: Annotated[str, Field(default="EUR", description="Devise (défaut: 'EUR').")] = "EUR",
        notes: Annotated[Optional[str], Field(default=None, description="Notes ou commentaires internes.")] = None,
    ) -> str:
        """Crée une demande d'achat directement validée avec son bon de commande."""
        try:
            body: dict[str, Any] = {
                "supplier_id": supplier_id,
                "document_number": document_number,
                "issue_date": issue_date,
                "total_tax_included": total_tax_included,
                "currency": currency,
            }
            if notes:
                body["notes"] = notes

            data = await api_post("/purchase_requests/import", body)
            return f"✅ Bon de commande importé et demande d'achat validée (id: {data.get('id')}).\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Lier une demande d'achat à une facture fournisseur ────────────────────

    @mcp.tool(
        name="pennylane_link_purchase_request_supplier_invoice",
        description="Lie une demande d'achat à une facture fournisseur (rapprochement commande -> facture).",
        annotations={
            "title": "Lier demande d'achat -> facture fournisseur",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_link_purchase_request_supplier_invoice(
        supplier_invoice_id: Annotated[int, Field(description="ID de la facture fournisseur.")],
        purchase_request_id: Annotated[int, Field(description="ID de la demande d'achat à associer.")],
    ) -> str:
        """Associe une commande fournisseur validée à sa facture de réception."""
        try:
            body = {"purchase_request_id": purchase_request_id}
            data = await api_post(f"/supplier_invoices/{supplier_invoice_id}/linked_purchase_requests", body)
            return f"✅ Demande d'achat {purchase_request_id} liée à la facture fournisseur {supplier_invoice_id}.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"
