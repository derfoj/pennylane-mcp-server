"""Outils MCP : gestion des factures clients (Customer Invoices)."""

from __future__ import annotations

import json
from typing import Annotated, Optional

from pydantic import Field
from mcp.server.fastmcp import FastMCP

from ..api import api_delete, api_get, api_post, api_put
from ..models import CategoryWeight, InvoiceLineInput
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
        invoice_lines: Annotated[list[InvoiceLineInput], Field(
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

    # ── Supprimer un brouillon de facture client ──────────────────────────────

    @mcp.tool(
        name="pennylane_delete_draft_customer_invoice",
        description="Supprime définitivement un brouillon de facture client.",
        annotations={
            "title": "Supprimer un brouillon de facture client",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_delete_draft_customer_invoice(
        id: Annotated[int, Field(description="Identifiant de la facture brouillon à supprimer.")],
    ) -> str:
        """Supprime une facture client en statut brouillon (draft)."""
        try:
            await api_delete(f"/customer_invoices/{id}")
            return f"✅ Facture client brouillon {id} supprimée avec succès."
        except Exception as exc:
            return f"❌ {exc}"

    # ── Catégoriser une facture client ────────────────────────────────────────

    @mcp.tool(
        name="pennylane_categorize_customer_invoice",
        description="Met à jour la ventilation analytique (catégories et poids) d'une facture client.",
        annotations={
            "title": "Catégoriser une facture client",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_categorize_customer_invoice(
        id: Annotated[int, Field(description="Identifiant de la facture client.")],
        categories: Annotated[list[CategoryWeight], Field(description="Liste de catégories avec poids. Ex: [{'id': 59, 'weight': '1.0'}].")],
    ) -> str:
        """Affecte des catégories analytiques à une facture client."""
        try:
            body = {"categories": categories}
            data = await api_put(f"/customer_invoices/{id}/categories", body)
            return f"✅ Catégories de la facture client {id} mises à jour.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Lister les catégories d'une facture client ────────────────────────────

    @mcp.tool(
        name="pennylane_list_customer_invoice_categories",
        description="Consulte les catégories analytiques associées à une facture client.",
        annotations={
            "title": "Catégories d'une facture client",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_customer_invoice_categories(
        id: Annotated[int, Field(description="Identifiant de la facture client.")],
    ) -> str:
        """Liste la ventilation analytique d'une facture client."""
        try:
            data = await api_get(f"/customer_invoices/{id}/categories")
            return to_json(data)
        except Exception as exc:
            return f"❌ {exc}"

    # ── Envoyer facture électronique au PA ────────────────────────────────────

    @mcp.tool(
        name="pennylane_send_customer_invoice_to_pa",
        description="Envoie une facture client électronique finalisée à la Plateforme Agréée (PA).",
        annotations={
            "title": "Envoyer facture client au PA (e-invoicing)",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_send_customer_invoice_to_pa(
        id: Annotated[int, Field(description="Identifiant de la facture client à envoyer au PA.")],
    ) -> str:
        """Transmet une facture électronique client vers le réseau PA / PPF."""
        try:
            data = await api_post(f"/customer_invoices/{id}/send_to_pa", {})
            return f"✅ Facture client {id} transmise avec succès à la Plateforme Agréée.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Importer une facture client électronique (e-invoice) ──────────────────

    @mcp.tool(
        name="pennylane_import_customer_einvoice",
        description="Importe une facture client électronique au format Factur-X PDF ou XML (UBL/CII).",
        annotations={
            "title": "Importer facture client électronique",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_import_customer_einvoice(
        file_attachment_id: Annotated[int, Field(description="ID du fichier uploadé contenant la facture Factur-X/XML.")],
    ) -> str:
        """Importe et convertit une facture électronique émise."""
        try:
            body = {"file_attachment_id": file_attachment_id}
            data = await api_post("/customer_invoices/e_invoice_import", body)
            return f"✅ Facture électronique importée avec succès (id: {data.get('id')}).\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Lister les modèles de facture client ──────────────────────────────────

    @mcp.tool(
        name="pennylane_list_customer_invoice_templates",
        description="Liste les modèles (templates) de facturation client disponibles sur le dossier.",
        annotations={
            "title": "Modèles de facture client",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_customer_invoice_templates(
        cursor: Annotated[Optional[str], Field(default=None, description="Curseur pour la pagination.")] = None,
        limit: Annotated[int, Field(default=20, ge=1, le=100, description="Nombre de résultats (1-100, défaut: 20).")] = 20,
    ) -> str:
        """Consulte les templates pour la création de factures clients."""
        try:
            qp: dict = {"limit": limit}
            if cursor:
                qp["cursor"] = cursor
            data = await api_get("/customer_invoice_templates", qp)
            items = data.get("items", [])
            result = {
                "templates": items,
                "pagination": pagination_summary(
                    data.get("has_more"), data.get("next_cursor"),
                    data.get("total_items"), len(items),
                ),
                "next_cursor": data.get("next_cursor"),
            }
            return truncate_if_needed(to_json(result))
        except Exception as exc:
            return f"❌ {exc}"

    # ── Créer une facture client depuis un devis ──────────────────────────────

    @mcp.tool(
        name="pennylane_create_customer_invoice_from_quote",
        description="Crée automatiquement une nouvelle facture client en brouillon à partir d'un devis accepté.",
        annotations={
            "title": "Créer facture depuis un devis",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_create_customer_invoice_from_quote(
        quote_id: Annotated[int, Field(description="Identifiant du devis à facturer.")],
    ) -> str:
        """Transforme un devis (quote) en facture client brouillon."""
        try:
            body = {"quote_id": quote_id}
            data = await api_post("/customer_invoices/from_quote", body)
            return f"✅ Facture créée à partir du devis {quote_id} (id: {data.get('id')}).\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Annexes d'une facture client ──────────────────────────────────────────

    @mcp.tool(
        name="pennylane_list_customer_invoice_appendices",
        description="Liste les pièces jointes et annexes d'une facture client.",
        annotations={
            "title": "Annexes d'une facture client",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_customer_invoice_appendices(
        id: Annotated[int, Field(description="Identifiant de la facture client.")],
    ) -> str:
        """Liste les fichiers annexes rattachés à la facture."""
        try:
            data = await api_get(f"/customer_invoices/{id}/appendices")
            return to_json(data)
        except Exception as exc:
            return f"❌ {exc}"

    # ── Transactions rapprochées d'une facture client ─────────────────────────

    @mcp.tool(
        name="pennylane_list_customer_invoice_matched_transactions",
        description="Liste les règlements bancaires rapprochés d'une facture client.",
        annotations={
            "title": "Transactions rapprochées facture client",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_customer_invoice_matched_transactions(
        id: Annotated[int, Field(description="Identifiant de la facture client.")],
    ) -> str:
        """Consulte les paiements bancaires rattachés à la facture client."""
        try:
            data = await api_get(f"/customer_invoices/{id}/matched_transactions")
            return to_json(data)
        except Exception as exc:
            return f"❌ {exc}"

    # ── Paiements d'une facture client ────────────────────────────────────────

    @mcp.tool(
        name="pennylane_list_customer_invoice_payments",
        description="Liste l'historique des paiements et règlements enregistrés pour une facture client.",
        annotations={
            "title": "Paiements d'une facture client",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_customer_invoice_payments(
        id: Annotated[int, Field(description="Identifiant de la facture client.")],
    ) -> str:
        """Consulte les règlements affectés à la facture."""
        try:
            data = await api_get(f"/customer_invoices/{id}/payments")
            return to_json(data)
        except Exception as exc:
            return f"❌ {exc}"

    # ── Lier un avoir à une facture client ────────────────────────────────────

    @mcp.tool(
        name="pennylane_link_customer_invoice_credit_note",
        description="Associe un avoir (credit note) à une facture client.",
        annotations={
            "title": "Lier un avoir à une facture client",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_link_customer_invoice_credit_note(
        id: Annotated[int, Field(description="Identifiant de la facture client.")],
        credit_note_id: Annotated[int, Field(description="Identifiant de l'avoir à lier.")],
    ) -> str:
        """Lie une note de crédit / avoir à la facture d'origine."""
        try:
            body = {"credit_note_id": credit_note_id}
            data = await api_post(f"/customer_invoices/{id}/linked_credit_notes", body)
            return f"✅ Avoir {credit_note_id} rattaché à la facture client {id}.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

