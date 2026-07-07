"""Outils MCP : enregistrements PA / Plateforme Agréée e-invoicing (PA Registrations)."""

from __future__ import annotations

import json
from typing import Annotated, Optional

from pydantic import Field
from mcp.server.fastmcp import FastMCP

from ..api import api_get
from ..utils import pagination_summary, to_json, truncate_if_needed


def register(mcp: FastMCP) -> None:
    """Enregistre l'outil de consultation des statuts d'enregistrement PA (Plateforme Agréée)."""

    @mcp.tool(
        name="pennylane_list_pa_registrations",
        description="Liste les enregistrements et statuts d'activation sur la Plateforme Agréée (PA) pour la facturation électronique.",
        annotations={
            "title": "Lister les enregistrements PA (e-invoicing)",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_pa_registrations(
        cursor: Annotated[Optional[str], Field(default=None, description="Curseur pour la pagination.")] = None,
        limit: Annotated[int, Field(default=20, ge=1, le=100, description="Nombre de résultats (1-100, défaut: 20).")] = 20,
    ) -> str:
        """Consulte le statut d'onboarding PA (e-invoicing) de la société et de ses établissements."""
        try:
            qp: dict = {"limit": limit}
            if cursor:
                qp["cursor"] = cursor

            data = await api_get("/pa_registrations", qp)
            items = data.get("items", [])
            result = {
                "pa_registrations": items,
                "pagination": pagination_summary(
                    data.get("has_more"), data.get("next_cursor"),
                    data.get("total_items"), len(items),
                ),
                "next_cursor": data.get("next_cursor"),
            }
            return truncate_if_needed(to_json(result))
        except Exception as exc:
            return f"❌ {exc}"
