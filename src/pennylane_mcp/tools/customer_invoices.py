"""Outils MCP : gestion des factures clients (Customer Invoices)."""

from __future__ import annotations

import json
from typing import Annotated, Optional

from pydantic import Field
from mcp.server.fastmcp import FastMCP

from ..api import api_get, api_post, api_put
from ..utils import pagination_summary, to_json, truncate_if_needed


def register(mcp: FastMCP) -> None:
    """Enregistre les outils de gestion des factures clients."""

    # ── Lister les factures clients ──────────────────────────────────────────

    @mcp.tool(
        name="pennylane_list_customer_invoices",
        annotations={
            "title": "Lister les factures clients",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_customer_invoices(
        cursor: Annotated[Optional[str], Field(default=None, description="Curseur pour la pagination.")] = None,
        limit: Annotated[int, Field(default=20, ge=1, le=100, description="Nombre de résultats (1-100, défaut: 20).")] = 20,
        status: Annotated[Optional[str], Field(
            default=None,
            description="Filtrer par statut : 'draft', 'finalized', 'paid', 'cancelled'.",
        )] = None,
        customer_id: Annotated[Optional[int], Field(
            default=None,
            description="Filtrer par ID client.",
        )] = None,
        sort: Annotated[Optional[str], Field(default=None, description="Tri: 'id', '-id' (défaut: '-id').")] = None,
    ) -> str:
        """Liste les factures clients avec filtres et pagination.
        Utile pour consulter les factures émises, filtrer par statut ou client.
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
            if customer_id:
                filters.append({"field": "customer_id", "operator": "eq", "value": customer_id})
            if filters:
                qp["filter"] = json.dumps(filters)

            data = await api_get("/customer_invoices", qp)
            items = data.get("items", [])
            result = {
                "customer_invoices": items,
                "pagination": pagination_summary(
                    data.get("has_more"), data.get("next_cursor"),
                    data.get("total_items"), len(items),
                ),
                "next_cursor": data.get("next_cursor"),
            }
            return truncate_if_needed(to_json(result))
        except Exception as exc:
            return f"❌ {exc}"

    # ── Récupérer une facture client ─────────────────────────────────────────

    @mcp.tool(
        name="pennylane_get_customer_invoice",
        annotations={
            "title": "Détail d'une facture client",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_get_customer_invoice(
        id: Annotated[int, Field(description="Identifiant unique de la facture client.")],
    ) -> str:
        """Récupère le détail complet d'une facture client par son identifiant.
        Retourne toutes les informations : montants, lignes, statut, client.
        """
        try:
            data = await api_get(f"/customer_invoices/{id}")
            return truncate_if_needed(to_json(data))
        except Exception as exc:
            return f"❌ {exc}"

    # ── Créer une facture client ─────────────────────────────────────────────

    @mcp.tool(
        name="pennylane_create_customer_invoice",
        annotations={
            "title": "Créer une facture client",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_create_customer_invoice(
        customer_id: Annotated[int, Field(description="ID du client à facturer.")],
        date: Annotated[str, Field(description="Date de la facture (YYYY-MM-DD).")],
        deadline: Annotated[str, Field(description="Date d'échéance (YYYY-MM-DD).")],
        invoice_lines: Annotated[list, Field(
            description="Lignes de facture. Chaque ligne : "
            "{product_id: int, quantity: number, label: str, unit: str, "
            "vat_rate: str, price_before_tax: str, discount: str (optionnel)}.",
        )],
        currency: Annotated[Optional[str], Field(default=None, description="Code devise (défaut: EUR).")] = None,
        special_mention: Annotated[Optional[str], Field(default=None, description="Mention spéciale sur la facture.")] = None,
        draft: Annotated[bool, Field(default=True, description="Créer en brouillon (défaut: true).")] = True,
    ) -> str:
        """Crée une nouvelle facture client (brouillon par défaut).
        Nécessite un client, une date, une échéance et au moins une ligne.
        """
        try:
            body: dict = {
                "customer_id": customer_id,
                "date": date,
                "deadline": deadline,
                "invoice_lines": invoice_lines,
                "draft": draft,
            }
            if currency:
                body["currency"] = currency
            if special_mention:
                body["special_mention"] = special_mention

            data = await api_post("/customer_invoices", body)
            status_label = "brouillon" if data.get("draft") or data.get("status") == "draft" else "finalisée"
            return (
                f"✅ Facture client créée ({status_label}) — "
                f"id: {data.get('id')}, numéro: {data.get('invoice_number', 'N/A')}.\n\n"
                f"{to_json(data)}"
            )
        except Exception as exc:
            return f"❌ {exc}"

    # ── Mettre à jour une facture client ─────────────────────────────────────

    @mcp.tool(
        name="pennylane_update_customer_invoice",
        annotations={
            "title": "Modifier une facture client",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_update_customer_invoice(
        id: Annotated[int, Field(description="Identifiant de la facture à modifier.")],
        date: Annotated[Optional[str], Field(default=None, description="Nouvelle date (YYYY-MM-DD).")] = None,
        deadline: Annotated[Optional[str], Field(default=None, description="Nouvelle échéance (YYYY-MM-DD).")] = None,
        customer_id: Annotated[Optional[int], Field(default=None, description="Nouvel ID client.")] = None,
        special_mention: Annotated[Optional[str], Field(default=None, description="Mention spéciale.")] = None,
        invoice_lines: Annotated[Optional[list], Field(
            default=None,
            description="Nouvelles lignes de facture (remplace les existantes).",
        )] = None,
    ) -> str:
        """Modifie une facture client (brouillon uniquement).
        Seuls les champs fournis sont mis à jour.
        """
        try:
            body: dict = {}
            if date is not None:
                body["date"] = date
            if deadline is not None:
                body["deadline"] = deadline
            if customer_id is not None:
                body["customer_id"] = customer_id
            if special_mention is not None:
                body["special_mention"] = special_mention
            if invoice_lines is not None:
                body["invoice_lines"] = invoice_lines

            data = await api_put(f"/customer_invoices/{id}", body)
            return f"✅ Facture client {id} mise à jour.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Lister les lignes d'une facture client ───────────────────────────────

    @mcp.tool(
        name="pennylane_list_customer_invoice_lines",
        annotations={
            "title": "Lignes d'une facture client",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_customer_invoice_lines(
        customer_invoice_id: Annotated[int, Field(description="ID de la facture client.")],
        cursor: Annotated[Optional[str], Field(default=None, description="Curseur pour la pagination.")] = None,
        limit: Annotated[int, Field(default=50, ge=1, le=100, description="Nombre de résultats (1-100, défaut: 50).")] = 50,
    ) -> str:
        """Liste les lignes (articles) d'une facture client spécifique."""
        try:
            qp: dict = {"limit": limit}
            if cursor:
                qp["cursor"] = cursor

            data = await api_get(f"/customer_invoices/{customer_invoice_id}/invoice_lines", qp)
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

    # ── Finaliser une facture client ─────────────────────────────────────────

    @mcp.tool(
        name="pennylane_finalize_customer_invoice",
        annotations={
            "title": "Finaliser une facture client",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_finalize_customer_invoice(
        id: Annotated[int, Field(description="Identifiant de la facture brouillon à finaliser.")],
    ) -> str:
        """Transforme un brouillon de facture client en facture finalisée.
        Attention : cette action est irréversible. La facture reçoit un numéro définitif.
        """
        try:
            data = await api_put(f"/customer_invoices/{id}/finalize", {})
            return (
                f"✅ Facture client {id} finalisée — "
                f"numéro: {data.get('invoice_number', 'N/A')}.\n\n{to_json(data)}"
            )
        except Exception as exc:
            return f"❌ {exc}"

    # ── Marquer comme payée ──────────────────────────────────────────────────

    @mcp.tool(
        name="pennylane_mark_customer_invoice_paid",
        annotations={
            "title": "Marquer une facture client comme payée",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_mark_customer_invoice_paid(
        id: Annotated[int, Field(description="Identifiant de la facture à marquer comme payée.")],
    ) -> str:
        """Marque une facture client finalisée comme payée."""
        try:
            data = await api_put(f"/customer_invoices/{id}/mark_as_paid", {})
            return f"✅ Facture client {id} marquée comme payée.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"
