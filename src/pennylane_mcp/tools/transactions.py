"""Outils MCP : transactions bancaires et rapprochement (Transactions & Matching)."""

from __future__ import annotations

import json
from typing import Annotated, Any, Optional

from pydantic import Field
from mcp.server.fastmcp import FastMCP

from ..api import api_delete, api_get, api_post, api_put
from ..models import CategoryWeight
from ..utils import pagination_summary, to_json, truncate_if_needed


def register(mcp: FastMCP) -> None:
    """Enregistre les outils de gestion des transactions bancaires et du rapprochement."""

    # ── Lister les transactions ───────────────────────────────────────────────

    @mcp.tool(
        name="pennylane_list_transactions",
        description="Liste les transactions bancaires avec filtres (date, compte bancaire, montant, statut) et pagination.",
        annotations={
            "title": "Lister les transactions bancaires",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_transactions(
        cursor: Annotated[Optional[str], Field(default=None, description="Curseur pour la pagination.")] = None,
        limit: Annotated[int, Field(default=20, ge=1, le=100, description="Nombre de résultats (1-100, défaut: 20).")] = 20,
        bank_account_id: Annotated[Optional[int], Field(default=None, description="Filtrer par ID de compte bancaire.")] = None,
        sort: Annotated[Optional[str], Field(default=None, description="Tri: 'date', '-date', 'id', '-id'.")] = None,
    ) -> str:
        """Liste les opérations bancaires du dossier."""
        try:
            qp: dict = {"limit": limit}
            if cursor:
                qp["cursor"] = cursor
            if sort:
                qp["sort"] = sort

            filters: list[dict] = []
            if bank_account_id is not None:
                filters.append({"field": "bank_account_id", "operator": "eq", "value": bank_account_id})
            if filters:
                qp["filter"] = json.dumps(filters)

            data = await api_get("/transactions", qp)
            items = data.get("items", [])
            result = {
                "transactions": items,
                "pagination": pagination_summary(
                    data.get("has_more"), data.get("next_cursor"),
                    data.get("total_items"), len(items),
                ),
                "next_cursor": data.get("next_cursor"),
            }
            return truncate_if_needed(to_json(result))
        except Exception as exc:
            return f"❌ {exc}"

    # ── Détail d'une transaction ──────────────────────────────────────────────

    @mcp.tool(
        name="pennylane_get_transaction",
        description="Récupère le détail d'une transaction bancaire par son identifiant.",
        annotations={
            "title": "Détail d'une transaction",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_get_transaction(
        id: Annotated[int, Field(description="Identifiant de la transaction.")],
    ) -> str:
        """Récupère les informations complètes d'une transaction bancaire."""
        try:
            data = await api_get(f"/transactions/{id}")
            return to_json(data)
        except Exception as exc:
            return f"❌ {exc}"

    # ── Créer une transaction ─────────────────────────────────────────────────

    @mcp.tool(
        name="pennylane_create_transaction",
        description="Crée manuellement une transaction bancaire (date, montant, libellé, compte bancaire).",
        annotations={
            "title": "Créer une transaction bancaire",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_create_transaction(
        date: Annotated[str, Field(description="Date de la transaction au format YYYY-MM-DD.")],
        label: Annotated[str, Field(description="Libellé bancaire de la transaction.")],
        amount: Annotated[str, Field(description="Montant de la transaction (ex: '150.00' ou '-45.50').")],
        bank_account_id: Annotated[int, Field(description="Identifiant du compte bancaire rattaché.")],
        currency: Annotated[str, Field(default="EUR", description="Devise (défaut: 'EUR').")] = "EUR",
    ) -> str:
        """Crée une nouvelle opération bancaire sur un compte."""
        try:
            body = {
                "date": date,
                "label": label,
                "amount": amount,
                "bank_account_id": bank_account_id,
                "currency": currency,
            }
            data = await api_post("/transactions", body)
            return f"✅ Transaction créée avec succès (id: {data.get('id')}).\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Modifier une transaction ──────────────────────────────────────────────

    @mcp.tool(
        name="pennylane_update_transaction",
        description="Modifie une transaction bancaire existante (libellé, date, montant).",
        annotations={
            "title": "Modifier une transaction",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_update_transaction(
        id: Annotated[int, Field(description="Identifiant de la transaction à modifier.")],
        label: Annotated[Optional[str], Field(default=None, description="Nouveau libellé.")] = None,
        date: Annotated[Optional[str], Field(default=None, description="Nouvelle date YYYY-MM-DD.")] = None,
        amount: Annotated[Optional[str], Field(default=None, description="Nouveau montant.")] = None,
    ) -> str:
        """Met à jour les attributs d'une transaction bancaire."""
        try:
            body: dict[str, Any] = {}
            if label is not None:
                body["label"] = label
            if date is not None:
                body["date"] = date
            if amount is not None:
                body["amount"] = amount

            data = await api_put(f"/transactions/{id}", body)
            return f"✅ Transaction mise à jour.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Catégoriser une transaction ───────────────────────────────────────────

    @mcp.tool(
        name="pennylane_categorize_transaction",
        description="Met à jour ou remplace la ventilation analytique (catégories et poids) d'une transaction bancaire.",
        annotations={
            "title": "Catégoriser une transaction",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_categorize_transaction(
        id: Annotated[int, Field(description="Identifiant de la transaction.")],
        categories: Annotated[list[CategoryWeight], Field(
            description="Liste de catégories avec poids. Ex: [{'id': 59, 'weight': '1.0'}]. La somme des poids par groupe doit valoir 1.",
        )],
    ) -> str:
        """Affecte des catégories analytiques à une transaction bancaire."""
        try:
            body = {"categories": categories}
            data = await api_put(f"/transactions/{id}/categories", body)
            return f"✅ Catégories de la transaction {id} mises à jour.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Lister les catégories d'une transaction ───────────────────────────────

    @mcp.tool(
        name="pennylane_list_transaction_categories",
        description="Liste les catégories analytiques actuellement associées à une transaction bancaire.",
        annotations={
            "title": "Catégories d'une transaction",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_transaction_categories(
        id: Annotated[int, Field(description="Identifiant de la transaction.")],
    ) -> str:
        """Consulte la ventilation analytique d'une transaction."""
        try:
            data = await api_get(f"/transactions/{id}/categories")
            return to_json(data)
        except Exception as exc:
            return f"❌ {exc}"

    # ── Factures rapprochées d'une transaction ────────────────────────────────

    @mcp.tool(
        name="pennylane_list_transaction_matched_invoices",
        description="Liste toutes les factures (clients ou fournisseurs) rattachées et rapprochées à une transaction bancaire.",
        annotations={
            "title": "Factures rapprochées d'une transaction",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_transaction_matched_invoices(
        id: Annotated[int, Field(description="Identifiant de la transaction.")],
    ) -> str:
        """Liste les factures associées au paiement bancaire."""
        try:
            data = await api_get(f"/transactions/{id}/matched_invoices")
            return to_json(data)
        except Exception as exc:
            return f"❌ {exc}"

    # ── Rapprocher une transaction d'une facture client ───────────────────────

    @mcp.tool(
        name="pennylane_match_transaction_customer_invoice",
        description="Rapproche (associe) une transaction bancaire à une facture client spécifique pour lettrer le paiement.",
        annotations={
            "title": "Rapprocher transaction -> facture client",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_match_transaction_customer_invoice(
        customer_invoice_id: Annotated[int, Field(description="ID de la facture client.")],
        transaction_id: Annotated[int, Field(description="ID de la transaction bancaire.")],
    ) -> str:
        """Rapproche un encaissement bancaire d'une facture client."""
        try:
            body = {"transaction_id": transaction_id}
            data = await api_post(f"/customer_invoices/{customer_invoice_id}/matched_transactions", body)
            return f"✅ Transaction {transaction_id} rapprochée de la facture client {customer_invoice_id}.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Dé-rapprocher une transaction d'une facture client ────────────────────

    @mcp.tool(
        name="pennylane_unmatch_transaction_customer_invoice",
        description="Supprime le rapprochement entre une transaction bancaire et une facture client.",
        annotations={
            "title": "Supprimer rapprochement transaction -> facture client",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_unmatch_transaction_customer_invoice(
        customer_invoice_id: Annotated[int, Field(description="ID de la facture client.")],
        transaction_id: Annotated[int, Field(description="ID de la transaction bancaire à dissocier.")],
    ) -> str:
        """Dissocie une transaction bancaire d'une facture client."""
        try:
            await api_delete(f"/customer_invoices/{customer_invoice_id}/matched_transactions/{transaction_id}")
            return f"✅ Rapprochement supprimé entre la facture client {customer_invoice_id} et la transaction {transaction_id}."
        except Exception as exc:
            return f"❌ {exc}"

    # ── Rapprocher une transaction d'une facture fournisseur ──────────────────

    @mcp.tool(
        name="pennylane_match_transaction_supplier_invoice",
        description="Rapproche (associe) une transaction bancaire à une facture fournisseur pour lettrer le règlement.",
        annotations={
            "title": "Rapprocher transaction -> facture fournisseur",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_match_transaction_supplier_invoice(
        supplier_invoice_id: Annotated[int, Field(description="ID de la facture fournisseur.")],
        transaction_id: Annotated[int, Field(description="ID de la transaction bancaire.")],
    ) -> str:
        """Rapproche un décaissement bancaire d'une facture fournisseur."""
        try:
            body = {"transaction_id": transaction_id}
            data = await api_post(f"/supplier_invoices/{supplier_invoice_id}/matched_transactions", body)
            return f"✅ Transaction {transaction_id} rapprochée de la facture fournisseur {supplier_invoice_id}.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Dé-rapprocher une transaction d'une facture fournisseur ───────────────

    @mcp.tool(
        name="pennylane_unmatch_transaction_supplier_invoice",
        description="Supprime le rapprochement entre une transaction bancaire et une facture fournisseur.",
        annotations={
            "title": "Supprimer rapprochement transaction -> facture fournisseur",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_unmatch_transaction_supplier_invoice(
        supplier_invoice_id: Annotated[int, Field(description="ID de la facture fournisseur.")],
        transaction_id: Annotated[int, Field(description="ID de la transaction bancaire à dissocier.")],
    ) -> str:
        """Dissocie une transaction bancaire d'une facture fournisseur."""
        try:
            await api_delete(f"/supplier_invoices/{supplier_invoice_id}/matched_transactions/{transaction_id}")
            return f"✅ Rapprochement supprimé entre la facture fournisseur {supplier_invoice_id} et la transaction {transaction_id}."
        except Exception as exc:
            return f"❌ {exc}"
