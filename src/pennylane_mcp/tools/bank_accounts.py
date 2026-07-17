"""Outils MCP : comptes bancaires et établissements (Bank Accounts)."""

from __future__ import annotations

import json
from typing import Annotated, Optional

from pydantic import Field
from mcp.server.fastmcp import FastMCP

from ..api import api_get, api_post
from ..utils import pagination_summary, to_json, truncate_if_needed


def register(mcp: FastMCP) -> None:
    """Enregistre les outils de gestion des comptes bancaires et établissements."""

    # ── Lister les comptes bancaires ──────────────────────────────────────────

    @mcp.tool(
        name="pennylane_list_bank_accounts",
        description="Liste les comptes bancaires (comptes de trésorerie, IBAN, banques) avec pagination.",
        annotations={
            "title": "Lister les comptes bancaires",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_bank_accounts(
        cursor: Annotated[Optional[str], Field(default=None, description="Curseur pour la pagination.")] = None,
        limit: Annotated[int, Field(default=20, ge=1, le=100, description="Nombre de résultats (1-100, défaut: 20).")] = 20,
    ) -> str:
        """Liste tous les comptes bancaires connectés ou créés sur le dossier."""
        try:
            qp: dict = {"limit": limit}
            if cursor:
                qp["cursor"] = cursor

            data = await api_get("/bank_accounts", qp)
            items = data.get("items", [])
            result = {
                "bank_accounts": items,
                "pagination": pagination_summary(
                    data.get("has_more"), data.get("next_cursor"),
                    data.get("total_items"), len(items),
                ),
                "next_cursor": data.get("next_cursor"),
            }
            return truncate_if_needed(to_json(result))
        except Exception as exc:
            return f"❌ {exc}"

    # ── Détail d'un compte bancaire ───────────────────────────────────────────

    @mcp.tool(
        name="pennylane_get_bank_account",
        description="Récupère le détail d'un compte bancaire par son identifiant.",
        annotations={
            "title": "Détail d'un compte bancaire",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_get_bank_account(
        id: Annotated[int, Field(description="Identifiant unique du compte bancaire.")],
    ) -> str:
        """Récupère les informations détaillées d'un compte bancaire."""
        try:
            data = await api_get(f"/bank_accounts/{id}")
            return to_json(data)
        except Exception as exc:
            return f"❌ {exc}"

    # ── Créer un compte bancaire ──────────────────────────────────────────────

    @mcp.tool(
        name="pennylane_create_bank_account",
        description="Crée un nouveau compte bancaire (IBAN, nom de la banque, devise, libellé) dans Pennylane.",
        annotations={
            "title": "Créer un compte bancaire",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_create_bank_account(
        name: Annotated[str, Field(description="Nom du compte bancaire (champ API 'name', ex: 'Compte Principal BNP').")],
        iban: Annotated[Optional[str], Field(default=None, description="Numéro IBAN du compte bancaire.")] = None,
        bic: Annotated[Optional[str], Field(default=None, description="Code BIC / SWIFT.")] = None,
        bank_establishment_id: Annotated[Optional[int], Field(
            default=None,
            description="ID de l'établissement bancaire (voir pennylane_list_bank_establishments).",
        )] = None,
        currency: Annotated[Optional[str], Field(default=None, description="Devise du compte (ex: 'EUR').")] = None,
        account_type: Annotated[Optional[str], Field(
            default=None,
            description="Type de compte : 'current', 'checking', 'card', 'savings', 'shares', "
            "'loan', 'life_insurance', 'other'.",
        )] = None,
    ) -> str:
        """Crée un compte bancaire sur le dossier en cours (seul 'name' est requis par l'API)."""
        try:
            body: dict = {"name": name}
            if iban:
                body["iban"] = iban
            if bic:
                body["bic"] = bic
            if bank_establishment_id:
                body["bank_establishment_id"] = bank_establishment_id
            if currency:
                body["currency"] = currency
            if account_type:
                body["account_type"] = account_type

            data = await api_post("/bank_accounts", body)
            return f"✅ Compte bancaire créé avec succès (id: {data.get('id')}).\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Lister les établissements bancaires ───────────────────────────────────

    @mcp.tool(
        name="pennylane_list_bank_establishments",
        description="Liste les établissements bancaires supportés et reconnus par Pennylane.",
        annotations={
            "title": "Lister les établissements bancaires",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_bank_establishments(
        cursor: Annotated[Optional[str], Field(default=None, description="Curseur pour la pagination.")] = None,
        limit: Annotated[int, Field(default=20, ge=1, le=100, description="Nombre de résultats (1-100, défaut: 20).")] = 20,
    ) -> str:
        """Liste les banques et établissements de paiement compatibles."""
        try:
            qp: dict = {"limit": limit}
            if cursor:
                qp["cursor"] = cursor

            data = await api_get("/bank_establishments", qp)
            items = data.get("items", [])
            result = {
                "bank_establishments": items,
                "pagination": pagination_summary(
                    data.get("has_more"), data.get("next_cursor"),
                    data.get("total_items"), len(items),
                ),
                "next_cursor": data.get("next_cursor"),
            }
            return truncate_if_needed(to_json(result))
        except Exception as exc:
            return f"❌ {exc}"
