"""Outils MCP : gestion des factures clients (Customer Invoices)."""

from __future__ import annotations

import json
from typing import Annotated, Optional

from pydantic import Field
from mcp.server.fastmcp import FastMCP

import base64
from pathlib import Path

from ..api import api_delete, api_get, api_post, api_post_multipart, api_put
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
            description="Filtrer par statut. Valeurs API : 'draft', 'upcoming', 'late', 'paid', "
            "'partially_paid', 'cancelled', 'partially_cancelled', 'incomplete', 'archived', "
            "'credit_note', 'proforma', 'shipping_order', 'purchasing_order', "
            "'estimate_pending', 'estimate_accepted', 'estimate_invoiced', 'estimate_denied'.",
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
            description="Lignes de facture (min 1). Deux formes possibles : "
            "1) Avec produit : {product_id: int, quantity: number} (label/prix/TVA auto-remplis, surchargeables). "
            "2) Manuelle : {label: str, quantity: number, raw_currency_unit_price: str (≤6 décimales), "
            "unit: str, vat_rate: str (ex: 'FR_200')}. "
            "Optionnels : description, discount: {type: 'absolute'|'relative', value}, section_rank.",
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
        """Affecte des catégories analytiques à une facture client.
        Le body API est un tableau brut de {id, weight} ; les poids d'un même
        groupe de catégories doivent totaliser 1.0.
        """
        try:
            data = await api_put(f"/customer_invoices/{id}/categories", categories)
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
        file_path: Annotated[Optional[str], Field(
            default=None,
            description="Chemin local du fichier e-invoice (Factur-X PDF, UBL XML ou CII XML).",
        )] = None,
        file_content_base64: Annotated[Optional[str], Field(
            default=None,
            description="Contenu du fichier encodé en base64 (alternative à file_path).",
        )] = None,
        file_name: Annotated[str, Field(
            default="e_invoice.pdf",
            description="Nom du fichier (extension .pdf ou .xml).",
        )] = "e_invoice.pdf",
        invoice_options: Annotated[Optional[dict], Field(
            default=None,
            description="Options d'enrichissement (JSON) : {customer_id: int, invoice_lines: "
            "[{e_invoice_line_id: str (BT-126), ledger_account_id?: int, product_id?: int}]}.",
        )] = None,
    ) -> str:
        """Importe une facture client électronique via multipart/form-data
        (POST /customer_invoices/e_invoices/imports). Fournir file_path OU file_content_base64.
        """
        try:
            if bool(file_path) == bool(file_content_base64):
                return "❌ Fournissez exactement un des deux : file_path ou file_content_base64."
            if file_path:
                p = Path(file_path)
                if not p.is_file():
                    return f"❌ Fichier introuvable : {file_path}"
                file_bytes = p.read_bytes()
                file_name = p.name
            else:
                file_bytes = base64.b64decode(file_content_base64)

            content_type = "text/xml" if file_name.lower().endswith(".xml") else "application/pdf"
            extra = {"invoice_options": json.dumps(invoice_options)} if invoice_options else None
            data = await api_post_multipart(
                "/customer_invoices/e_invoices/imports",
                file_name=file_name,
                file_bytes=file_bytes,
                content_type=content_type,
                extra_fields=extra,
            )
            return f"✅ Facture électronique importée avec succès (id: {data.get('id')}).\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Importer une facture client (fichier + données) ───────────────────────

    @mcp.tool(
        name="pennylane_import_customer_invoice",
        description="Importe une facture client existante (PDF déjà uploadé via file_attachments) avec ses données comptables.",
        annotations={
            "title": "Importer une facture client",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_import_customer_invoice(
        file_attachment_id: Annotated[int, Field(description="ID du fichier (créé via pennylane_create_file_attachment).")],
        customer_id: Annotated[int, Field(description="ID du client.")],
        date: Annotated[str, Field(description="Date d'émission (YYYY-MM-DD).")],
        deadline: Annotated[str, Field(description="Date d'échéance (YYYY-MM-DD).")],
        currency_amount_before_tax: Annotated[str, Field(description="Total HT en devise (string, ex: '1000.00').")],
        currency_amount: Annotated[str, Field(description="Total TTC en devise (string).")],
        currency_tax: Annotated[str, Field(description="Montant de TVA en devise (string).")],
        invoice_lines: Annotated[list, Field(
            description="Lignes (min 1). Chaque ligne : {currency_amount: str, currency_tax: str, "
            "quantity: number, raw_currency_unit_price: str (≤6 décimales), unit: str, vat_rate: str (ex: 'FR_200'), label?: str}.",
        )],
        invoice_number: Annotated[Optional[str], Field(
            default=None,
            description="Numéro de facture (≤35 caractères alphanumériques et -+_/ si convert_to_e_invoice).",
        )] = None,
        currency: Annotated[Optional[str], Field(default=None, description="Devise (défaut: EUR).")] = None,
        convert_to_e_invoice: Annotated[bool, Field(
            default=False,
            description="Convertir en e-invoice Factur-X PDF/A-3 (asynchrone, défaut: false).",
        )] = False,
        import_as_incomplete: Annotated[bool, Field(
            default=False,
            description="Importer avec le statut 'incomplete' (défaut: false).",
        )] = False,
    ) -> str:
        """Importe une facture client via POST /customer_invoices/import.
        Tolérance de rapprochement : ≤1 centime d'écart par ligne vs totaux.
        """
        try:
            body: dict = {
                "file_attachment_id": file_attachment_id,
                "customer_id": customer_id,
                "date": date,
                "deadline": deadline,
                "currency_amount_before_tax": currency_amount_before_tax,
                "currency_amount": currency_amount,
                "currency_tax": currency_tax,
                "invoice_lines": invoice_lines,
            }
            if invoice_number:
                body["invoice_number"] = invoice_number
            if currency:
                body["currency"] = currency
            if convert_to_e_invoice:
                body["convert_to_e_invoice"] = True
            if import_as_incomplete:
                body["import_as_incomplete"] = True

            data = await api_post("/customer_invoices/import", body)
            return f"✅ Facture client importée (id: {data.get('id')}).\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Envoyer une facture client par email ──────────────────────────────────

    @mcp.tool(
        name="pennylane_send_customer_invoice_by_email",
        description="Envoie une facture client finalisée (ou importée) par email à des destinataires.",
        annotations={
            "title": "Envoyer facture client par email",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_send_customer_invoice_by_email(
        id: Annotated[int, Field(description="Identifiant de la facture client à envoyer.")],
        recipients: Annotated[Optional[list[str]], Field(
            default=None,
            description="Adresses email destinataires. Si vide, envoi aux adresses de la fiche client.",
        )] = None,
    ) -> str:
        """Envoie la facture par email (POST /customer_invoices/{id}/send_by_email).
        Un code 409 signifie que le PDF n'est pas encore généré : réessayez dans quelques minutes.
        """
        try:
            body: dict = {}
            if recipients:
                body["recipients"] = recipients
            await api_post(f"/customer_invoices/{id}/send_by_email", body)
            dest = ", ".join(recipients) if recipients else "les adresses de la fiche client"
            return f"✅ Facture client {id} envoyée par email à {dest}."
        except Exception as exc:
            return f"❌ {exc}"

    # ── Uploader une annexe sur une facture client ────────────────────────────

    @mcp.tool(
        name="pennylane_upload_customer_invoice_appendix",
        description="Ajoute un fichier annexe (PDF/image) à une facture client via multipart/form-data.",
        annotations={
            "title": "Uploader annexe facture client",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_upload_customer_invoice_appendix(
        id: Annotated[int, Field(description="Identifiant de la facture client.")],
        file_path: Annotated[Optional[str], Field(
            default=None, description="Chemin local du fichier (png/jpeg/tiff/bmp/gif/pdf).",
        )] = None,
        file_content_base64: Annotated[Optional[str], Field(
            default=None, description="Contenu du fichier en base64 (alternative à file_path).",
        )] = None,
        file_name: Annotated[str, Field(default="annexe.pdf", description="Nom du fichier.")] = "annexe.pdf",
        content_type: Annotated[str, Field(
            default="application/pdf",
            description="Type MIME : image/png, image/jpeg, image/tiff, image/bmp, image/gif, application/pdf.",
        )] = "application/pdf",
    ) -> str:
        """Uploade une annexe sur la facture (POST /customer_invoices/{id}/appendices)."""
        try:
            if bool(file_path) == bool(file_content_base64):
                return "❌ Fournissez exactement un des deux : file_path ou file_content_base64."
            if file_path:
                p = Path(file_path)
                if not p.is_file():
                    return f"❌ Fichier introuvable : {file_path}"
                file_bytes = p.read_bytes()
                file_name = p.name
            else:
                file_bytes = base64.b64decode(file_content_base64)

            data = await api_post_multipart(
                f"/customer_invoices/{id}/appendices",
                file_name=file_name,
                file_bytes=file_bytes,
                content_type=content_type,
            )
            return f"✅ Annexe ajoutée à la facture client {id}.\n\n{to_json(data)}"
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
        draft: Annotated[bool, Field(
            default=True,
            description="Créer la facture en brouillon (true) ou finalisée (false). Champ requis par l'API.",
        )] = True,
        external_reference: Annotated[Optional[str], Field(
            default=None, description="Référence externe unique (suivi).",
        )] = None,
        customer_invoice_template_id: Annotated[Optional[int], Field(
            default=None, description="ID du modèle de facture à appliquer.",
        )] = None,
    ) -> str:
        """Transforme un devis (quote) en facture client."""
        try:
            body: dict = {"quote_id": quote_id, "draft": draft}
            if external_reference:
                body["external_reference"] = external_reference
            if customer_invoice_template_id:
                body["customer_invoice_template_id"] = customer_invoice_template_id
            data = await api_post("/customer_invoices/create_from_quote", body)
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
            data = await api_post(f"/customer_invoices/{id}/link_credit_note", body)
            return f"✅ Avoir {credit_note_id} rattaché à la facture client {id}.\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

