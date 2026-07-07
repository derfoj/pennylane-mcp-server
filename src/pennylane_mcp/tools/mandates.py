"""Outils MCP : mandats de prélèvement (SEPA, GoCardless, Pro Account Mandates)."""

from __future__ import annotations

import json
from typing import Annotated, Any, Optional

from pydantic import Field
from mcp.server.fastmcp import FastMCP

from ..api import api_delete, api_get, api_post, api_put
from ..utils import pagination_summary, to_json, truncate_if_needed


def register(mcp: FastMCP) -> None:
    """Enregistre les outils de gestion des mandats bancaires (SEPA, GoCardless, Compte Pro)."""

    # ── Lister les mandats SEPA ───────────────────────────────────────────────

    @mcp.tool(
        name="pennylane_list_sepa_mandates",
        description="Liste tous les mandats de prélèvement SEPA de la société avec pagination.",
        annotations={
            "title": "Lister les mandats SEPA",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_sepa_mandates(
        cursor: Annotated[Optional[str], Field(default=None, description="Curseur pour la pagination.")] = None,
        limit: Annotated[int, Field(default=20, ge=1, le=100, description="Nombre de résultats (1-100, défaut: 20).")] = 20,
    ) -> str:
        """Liste les mandats de prélèvement SEPA configurés."""
        try:
            qp: dict = {"limit": limit}
            if cursor:
                qp["cursor"] = cursor

            data = await api_get("/sepa_mandates", qp)
            items = data.get("items", [])
            result = {
                "sepa_mandates": items,
                "pagination": pagination_summary(
                    data.get("has_more"), data.get("next_cursor"),
                    data.get("total_items"), len(items),
                ),
                "next_cursor": data.get("next_cursor"),
            }
            return truncate_if_needed(to_json(result))
        except Exception as exc:
            return f"❌ {exc}"

    # ── Détail d'un mandat SEPA ───────────────────────────────────────────────

    @mcp.tool(
        name="pennylane_get_sepa_mandate",
        description="Récupère le détail d'un mandat de prélèvement SEPA par son identifiant.",
        annotations={
            "title": "Détail d'un mandat SEPA",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_get_sepa_mandate(
        id: Annotated[int, Field(description="Identifiant unique du mandat SEPA.")],
    ) -> str:
        """Récupère un mandat SEPA spécifique."""
        try:
            data = await api_get(f"/sepa_mandates/{id}")
            return to_json(data)
        except Exception as exc:
            return f"❌ {exc}"

    # ── Créer un mandat SEPA ──────────────────────────────────────────────────

    @mcp.tool(
        name="pennylane_create_sepa_mandate",
        description="Crée un nouveau mandat SEPA pour autoriser les prélèvements bancaires d'un client.",
        annotations={
            "title": "Créer un mandat SEPA",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_create_sepa_mandate(
        customer_id: Annotated[int, Field(description="ID du client rattaché au mandat.")],
        iban: Annotated[str, Field(description="IBAN du compte bancaire client à prélever.")],
        rum: Annotated[str, Field(description="Référence Unique de Mandat (RUM).")],
        signature_date: Annotated[str, Field(description="Date de signature au format YYYY-MM-DD.")],
        bic: Annotated[Optional[str], Field(default=None, description="Code BIC / SWIFT.")] = None,
    ) -> str:
        """Crée un mandat SEPA direct pour un client."""
        try:
            body: dict[str, Any] = {
                "customer_id": customer_id,
                "iban": iban,
                "rum": rum,
                "signature_date": signature_date,
            }
            if bic:
                body["bic"] = bic

            data = await api_post("/sepa_mandates", body)
            return f"✅ Mandat SEPA créé avec succès (id: {data.get('id')}).\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Modifier un mandat SEPA ───────────────────────────────────────────────

    @mcp.tool(
        name="pennylane_update_sepa_mandate",
        description="Modifie un mandat SEPA existant (IBAN, BIC, RUM, date de signature).",
        annotations={
            "title": "Modifier un mandat SEPA",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_update_sepa_mandate(
        id: Annotated[int, Field(description="Identifiant du mandat SEPA à modifier.")],
        iban: Annotated[Optional[str], Field(default=None, description="Nouvel IBAN.")] = None,
        rum: Annotated[Optional[str], Field(default=None, description="Nouvelle RUM.")] = None,
        signature_date: Annotated[Optional[str], Field(default=None, description="Nouvelle date YYYY-MM-DD.")] = None,
        bic: Annotated[Optional[str], Field(default=None, description="Nouveau BIC.")] = None,
    ) -> str:
        """Met à jour un mandat SEPA."""
        try:
            body: dict[str, Any] = {}
            if iban is not None:
                body["iban"] = iban
            if rum is not None:
                body["rum"] = rum
            if signature_date is not None:
                body["signature_date"] = signature_date
            if bic is not None:
                body["bic"] = bic

            data = await api_put(f"/sepa_mandates/{id}", body)
            return f"✅ Mandat SEPA mis à jour.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Supprimer un mandat SEPA ──────────────────────────────────────────────

    @mcp.tool(
        name="pennylane_delete_sepa_mandate",
        description="Supprime définitivement un mandat de prélèvement SEPA.",
        annotations={
            "title": "Supprimer un mandat SEPA",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_delete_sepa_mandate(
        id: Annotated[int, Field(description="Identifiant du mandat SEPA à supprimer.")],
    ) -> str:
        """Supprime un mandat SEPA."""
        try:
            await api_delete(f"/sepa_mandates/{id}")
            return f"✅ Mandat SEPA {id} supprimé avec succès."
        except Exception as exc:
            return f"❌ {exc}"

    # ── Lister les mandats GoCardless ─────────────────────────────────────────

    @mcp.tool(
        name="pennylane_list_gocardless_mandates",
        description="Liste les mandats de prélèvement GoCardless de la société avec pagination.",
        annotations={
            "title": "Lister les mandats GoCardless",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_gocardless_mandates(
        cursor: Annotated[Optional[str], Field(default=None, description="Curseur pour la pagination.")] = None,
        limit: Annotated[int, Field(default=20, ge=1, le=100, description="Nombre de résultats (1-100, défaut: 20).")] = 20,
    ) -> str:
        """Liste les mandats GoCardless configurés."""
        try:
            qp: dict = {"limit": limit}
            if cursor:
                qp["cursor"] = cursor

            data = await api_get("/gocardless_mandates", qp)
            items = data.get("items", [])
            result = {
                "gocardless_mandates": items,
                "pagination": pagination_summary(
                    data.get("has_more"), data.get("next_cursor"),
                    data.get("total_items"), len(items),
                ),
                "next_cursor": data.get("next_cursor"),
            }
            return truncate_if_needed(to_json(result))
        except Exception as exc:
            return f"❌ {exc}"

    # ── Détail d'un mandat GoCardless ─────────────────────────────────────────

    @mcp.tool(
        name="pennylane_get_gocardless_mandate",
        description="Récupère le détail d'un mandat GoCardless par son identifiant.",
        annotations={
            "title": "Détail d'un mandat GoCardless",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_get_gocardless_mandate(
        id: Annotated[int, Field(description="Identifiant unique du mandat GoCardless.")],
    ) -> str:
        """Récupère un mandat GoCardless."""
        try:
            data = await api_get(f"/gocardless_mandates/{id}")
            return to_json(data)
        except Exception as exc:
            return f"❌ {exc}"

    # ── Associer un mandat GoCardless ─────────────────────────────────────────

    @mcp.tool(
        name="pennylane_associate_gocardless_mandate",
        description="Associe un mandat GoCardless existant à une fiche client Pennylane.",
        annotations={
            "title": "Associer mandat GoCardless à un client",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_associate_gocardless_mandate(
        customer_id: Annotated[int, Field(description="ID du client Pennylane.")],
        gocardless_mandate_id: Annotated[int, Field(description="ID du mandat GoCardless.")],
    ) -> str:
        """Lie un mandat GoCardless à un client."""
        try:
            body = {"customer_id": customer_id, "gocardless_mandate_id": gocardless_mandate_id}
            data = await api_post("/gocardless_mandate_associations", body)
            return f"✅ Mandat GoCardless associé au client {customer_id}.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Annuler un mandat GoCardless ──────────────────────────────────────────

    @mcp.tool(
        name="pennylane_cancel_gocardless_mandate",
        description="Annule ou résilie un mandat GoCardless (statut 'pending_submission', 'submitted' ou 'active').",
        annotations={
            "title": "Annuler un mandat GoCardless",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_cancel_gocardless_mandate(
        gocardless_mandate_id: Annotated[int, Field(description="ID du mandat GoCardless à annuler.")],
    ) -> str:
        """Annule un mandat GoCardless."""
        try:
            body = {"gocardless_mandate_id": gocardless_mandate_id}
            data = await api_post("/gocardless_mandate_cancellations", body)
            return f"✅ Mandat GoCardless {gocardless_mandate_id} annulé avec succès.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Envoyer demande de mandat GoCardless par email ────────────────────────

    @mcp.tool(
        name="pennylane_send_gocardless_mandate_request",
        description="Envoie par email une invitation / demande de signature de mandat GoCardless à un destinataire.",
        annotations={
            "title": "Envoyer demande mandat GoCardless",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_send_gocardless_mandate_request(
        customer_id: Annotated[int, Field(description="ID du client.")],
        recipient_email: Annotated[str, Field(description="Adresse email du destinataire.")],
    ) -> str:
        """Envoie un email de demande de signature GoCardless."""
        try:
            body = {"customer_id": customer_id, "recipient_email": recipient_email}
            data = await api_post("/gocardless_mandate_mail_requests", body)
            return f"✅ Demande de mandat GoCardless envoyée par email à {recipient_email}.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Lister les mandats de paiement Compte Pro ─────────────────────────────

    @mcp.tool(
        name="pennylane_list_pro_account_mandates",
        description="Liste les mandats de paiement associés au Compte Pro Pennylane de la société.",
        annotations={
            "title": "Lister les mandats Compte Pro",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_pro_account_mandates(
        cursor: Annotated[Optional[str], Field(default=None, description="Curseur pour la pagination.")] = None,
        limit: Annotated[int, Field(default=20, ge=1, le=100, description="Nombre de résultats (1-100, défaut: 20).")] = 20,
    ) -> str:
        """Liste les mandats Compte Pro."""
        try:
            qp: dict = {"limit": limit}
            if cursor:
                qp["cursor"] = cursor

            data = await api_get("/pro_account_mandates", qp)
            items = data.get("items", [])
            result = {
                "pro_account_mandates": items,
                "pagination": pagination_summary(
                    data.get("has_more"), data.get("next_cursor"),
                    data.get("total_items"), len(items),
                ),
                "next_cursor": data.get("next_cursor"),
            }
            return truncate_if_needed(to_json(result))
        except Exception as exc:
            return f"❌ {exc}"

    # ── Lister les candidats à la migration de mandat Compte Pro ──────────────

    @mcp.tool(
        name="pennylane_list_mandate_migrations",
        description="Liste les mandats éligibles à une migration vers un Compte Pro Pennylane.",
        annotations={
            "title": "Candidats migration mandats Compte Pro",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_mandate_migrations(
        cursor: Annotated[Optional[str], Field(default=None, description="Curseur pour la pagination.")] = None,
        limit: Annotated[int, Field(default=20, ge=1, le=100, description="Nombre de résultats (1-100, défaut: 20).")] = 20,
    ) -> str:
        """Liste les mandats disponibles pour migration au Compte Pro."""
        try:
            qp: dict = {"limit": limit}
            if cursor:
                qp["cursor"] = cursor

            data = await api_get("/pro_account_mandate_migrations", qp)
            items = data.get("items", [])
            result = {
                "mandate_migrations": items,
                "pagination": pagination_summary(
                    data.get("has_more"), data.get("next_cursor"),
                    data.get("total_items"), len(items),
                ),
                "next_cursor": data.get("next_cursor"),
            }
            return truncate_if_needed(to_json(result))
        except Exception as exc:
            return f"❌ {exc}"

    # ── Migrer un mandat vers le Compte Pro ───────────────────────────────────

    @mcp.tool(
        name="pennylane_migrate_mandate_pro_account",
        description="Migre un mandat éligible vers le Compte Pro Pennylane.",
        annotations={
            "title": "Migrer mandat vers Compte Pro",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_migrate_mandate_pro_account(
        mandate_id: Annotated[int, Field(description="ID du mandat à migrer vers le Compte Pro.")],
    ) -> str:
        """Migre un mandat existant sur le Compte Pro de la société."""
        try:
            body = {"mandate_id": mandate_id}
            data = await api_post("/pro_account_mandate_migrations", body)
            return f"✅ Mandat {mandate_id} migré vers le Compte Pro.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Envoyer demande de mandat SEPA Compte Pro par email ───────────────────

    @mcp.tool(
        name="pennylane_send_pro_account_mandate_request",
        description="Envoie par email une demande de signature de mandat SEPA pour Compte Pro à un client.",
        annotations={
            "title": "Envoyer demande mandat Compte Pro",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_send_pro_account_mandate_request(
        customer_id: Annotated[int, Field(description="ID du client destinataire.")],
        recipient_email: Annotated[str, Field(description="Adresse email du client.")],
    ) -> str:
        """Envoie un email de demande de mandat Compte Pro."""
        try:
            body = {"customer_id": customer_id, "recipient_email": recipient_email}
            data = await api_post("/pro_account_mandate_mail_requests", body)
            return f"✅ Demande de mandat Compte Pro envoyée par email à {recipient_email}.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"
