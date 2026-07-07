"""Outils MCP : documents commerciaux non comptables (Commercial Documents)."""

from __future__ import annotations

import json
from typing import Annotated, Optional

from pydantic import Field
from mcp.server.fastmcp import FastMCP

from ..api import api_get
from ..utils import pagination_summary, to_json, truncate_if_needed


def register(mcp: FastMCP) -> None:
    """Enregistre les outils pour les documents commerciaux (bons de commande, livraison, proforma...)."""

    # ── Lister les documents commerciaux ──────────────────────────────────────

    @mcp.tool(
        name="pennylane_list_commercial_documents",
        description="Liste les documents commerciaux non comptables (bons de commande, de livraison, proformas) avec filtres et pagination.",
        annotations={
            "title": "Lister les documents commerciaux",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_commercial_documents(
        cursor: Annotated[Optional[str], Field(default=None, description="Curseur pour la pagination.")] = None,
        limit: Annotated[int, Field(default=20, ge=1, le=100, description="Nombre de résultats (1-100, défaut: 20).")] = 20,
        customer_id: Annotated[Optional[int], Field(default=None, description="Filtrer par ID de client.")] = None,
        sort: Annotated[Optional[str], Field(default=None, description="Tri: 'date', '-date', 'id', '-id'.")] = None,
    ) -> str:
        """Liste les documents commerciaux non comptabilisés."""
        try:
            qp: dict = {"limit": limit}
            if cursor:
                qp["cursor"] = cursor
            if sort:
                qp["sort"] = sort

            filters: list[dict] = []
            if customer_id is not None:
                filters.append({"field": "customer_id", "operator": "eq", "value": customer_id})
            if filters:
                qp["filter"] = json.dumps(filters)

            data = await api_get("/commercial_documents", qp)
            items = data.get("items", [])
            result = {
                "commercial_documents": items,
                "pagination": pagination_summary(
                    data.get("has_more"), data.get("next_cursor"),
                    data.get("total_items"), len(items),
                ),
                "next_cursor": data.get("next_cursor"),
            }
            return truncate_if_needed(to_json(result))
        except Exception as exc:
            return f"❌ {exc}"

    # ── Détail d'un document commercial ───────────────────────────────────────

    @mcp.tool(
        name="pennylane_get_commercial_document",
        description="Récupère le détail d'un document commercial par son identifiant.",
        annotations={
            "title": "Détail d'un document commercial",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_get_commercial_document(
        id: Annotated[int, Field(description="Identifiant unique du document commercial.")],
    ) -> str:
        """Récupère un document commercial spécifique."""
        try:
            data = await api_get(f"/commercial_documents/{id}")
            return to_json(data)
        except Exception as exc:
            return f"❌ {exc}"

    # ── Lister les lignes d'un document commercial ────────────────────────────

    @mcp.tool(
        name="pennylane_list_commercial_document_lines",
        description="Liste les lignes (produits, quantités, prix unitaire) d'un document commercial.",
        annotations={
            "title": "Lignes d'un document commercial",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_commercial_document_lines(
        id: Annotated[int, Field(description="Identifiant du document commercial.")],
        cursor: Annotated[Optional[str], Field(default=None, description="Curseur pour la pagination.")] = None,
        limit: Annotated[int, Field(default=20, ge=1, le=100, description="Nombre de résultats (1-100, défaut: 20).")] = 20,
    ) -> str:
        """Consulte les lignes d'articles d'un document commercial."""
        try:
            qp: dict = {"limit": limit}
            if cursor:
                qp["cursor"] = cursor

            data = await api_get(f"/commercial_documents/{id}/invoice_lines", qp)
            items = data.get("items", [])
            result = {
                "lines": items,
                "pagination": pagination_summary(
                    data.get("has_more"), data.get("next_cursor"),
                    data.get("total_items"), len(items),
                ),
                "next_cursor": data.get("next_cursor"),
            }
            return truncate_if_needed(to_json(result))
        except Exception as exc:
            return f"❌ {exc}"

    # ── Lister les sections d'un document commercial ──────────────────────────

    @mcp.tool(
        name="pennylane_list_commercial_document_sections",
        description="Liste les sections ou groupes de lignes d'un document commercial.",
        annotations={
            "title": "Sections d'un document commercial",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_commercial_document_sections(
        id: Annotated[int, Field(description="Identifiant du document commercial.")],
        cursor: Annotated[Optional[str], Field(default=None, description="Curseur pour la pagination.")] = None,
        limit: Annotated[int, Field(default=20, ge=1, le=100, description="Nombre de résultats (1-100, défaut: 20).")] = 20,
    ) -> str:
        """Consulte les sections structurant un document commercial."""
        try:
            qp: dict = {"limit": limit}
            if cursor:
                qp["cursor"] = cursor

            data = await api_get(f"/commercial_documents/{id}/invoice_line_sections", qp)
            items = data.get("items", [])
            result = {
                "sections": items,
                "pagination": pagination_summary(
                    data.get("has_more"), data.get("next_cursor"),
                    data.get("total_items"), len(items),
                ),
                "next_cursor": data.get("next_cursor"),
            }
            return truncate_if_needed(to_json(result))
        except Exception as exc:
            return f"❌ {exc}"

    # ── Lister les pièces jointes d'un document commercial ────────────────────

    @mcp.tool(
        name="pennylane_list_commercial_document_appendices",
        description="Liste les annexes et pièces jointes rattachées à un document commercial.",
        annotations={
            "title": "Annexes d'un document commercial",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_commercial_document_appendices(
        id: Annotated[int, Field(description="Identifiant du document commercial.")],
    ) -> str:
        """Liste les fichiers joints au document commercial."""
        try:
            data = await api_get(f"/commercial_documents/{id}/appendices")
            return to_json(data)
        except Exception as exc:
            return f"❌ {exc}"
