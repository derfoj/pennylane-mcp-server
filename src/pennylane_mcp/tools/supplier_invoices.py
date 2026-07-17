"""Outils MCP : gestion des factures fournisseurs (Supplier Invoices)."""

from __future__ import annotations

import json
from typing import Annotated, Optional

from pydantic import Field
from mcp.server.fastmcp import FastMCP

<<<<<<< HEAD
from ..api import api_get, api_post, api_put
from ..models import CategoryWeight
=======
import base64
from pathlib import Path

from ..api import api_get, api_post, api_post_multipart, api_put
>>>>>>> ed08eff7c35d9ba119021156f32b7e60b198f1d7
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
        payment_status: Annotated[Optional[str], Field(
            default=None,
            description="Filtrer par statut de paiement : 'to_be_processed', 'to_be_paid', "
            "'partially_paid', 'payment_error', 'payment_scheduled', 'payment_in_progress', "
            "'payment_emitted', 'payment_found', 'paid_offline', 'fully_paid'. "
            "(Il n'existe pas de filtre 'status' générique sur cet endpoint.)",
        )] = None,
        supplier_id: Annotated[Optional[int], Field(
            default=None,
            description="Filtrer par ID fournisseur.",
        )] = None,
        date_from: Annotated[Optional[str], Field(default=None, description="Date min (YYYY-MM-DD, filtre gteq).")] = None,
        date_to: Annotated[Optional[str], Field(default=None, description="Date max (YYYY-MM-DD, filtre lteq).")] = None,
        sort: Annotated[Optional[str], Field(default=None, description="Tri: 'id', '-id' (défaut: '-id').")] = None,
    ) -> str:
        """Liste les factures fournisseurs avec filtres et pagination.
        Utile pour consulter les factures reçues, filtrer par statut de paiement ou fournisseur.
        """
        try:
            qp: dict = {"limit": limit}
            if cursor:
                qp["cursor"] = cursor
            if sort:
                qp["sort"] = sort

            filters: list[dict] = []
            if payment_status:
                filters.append({"field": "payment_status", "operator": "eq", "value": payment_status})
            if supplier_id:
                filters.append({"field": "supplier_id", "operator": "eq", "value": supplier_id})
            if date_from:
                filters.append({"field": "date", "operator": "gteq", "value": date_from})
            if date_to:
                filters.append({"field": "date", "operator": "lteq", "value": date_to})
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
            description="Nouveau statut. L'API n'accepte que 'paid' ou 'to_be_paid' en écriture "
            "(les autres statuts — partially_paid, payment_emitted, etc. — sont en lecture seule).",
        )],
    ) -> str:
        """Met à jour le statut de paiement d'une facture fournisseur."""
        try:
            if payment_status not in ("paid", "to_be_paid"):
                return (
                    "❌ Statut invalide : l'API Pennylane n'accepte que 'paid' ou 'to_be_paid' "
                    "sur cet endpoint. Les autres statuts sont calculés automatiquement."
                )
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
        categories: Annotated[list[CategoryWeight], Field(description="Liste de catégories avec poids. Ex: [{'id': 59, 'weight': '1.0'}].")],
    ) -> str:
        """Affecte des axes analytiques à une facture fournisseur.
        Le body API est un tableau brut de {id, weight} ; les poids d'un même
        groupe de catégories doivent totaliser 1.0.
        """
        try:
            data = await api_put(f"/supplier_invoices/{id}/categories", categories)
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
            description="Options d'enrichissement (JSON) : {supplier_id: int, invoice_lines: "
            "[{e_invoice_line_id: str (BT-126), ledger_account_id?: int}]}.",
        )] = None,
    ) -> str:
        """Importe une facture fournisseur électronique via multipart/form-data
        (POST /supplier_invoices/e_invoices/imports). Fournir file_path OU file_content_base64.
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
                "/supplier_invoices/e_invoices/imports",
                file_name=file_name,
                file_bytes=file_bytes,
                content_type=content_type,
                extra_fields=extra,
            )
            return f"✅ Facture fournisseur électronique importée (id: {data.get('id')}).\n\n{to_json(data)}"
        except Exception as exc:
            return f"❌ {exc}"

    # ── Modifier le statut e-invoice d'une facture fournisseur ────────────────

    @mcp.tool(
        name="pennylane_update_supplier_einvoice_status",
        description="Applique une transition de cycle de vie e-invoicing : disputed, refused, approved.",
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
        status: Annotated[str, Field(
            description="Nouveau statut e-invoicing : 'disputed' (litige), 'refused' (refus), "
            "ou 'approved' (approbation / levée de litige). "
            "Statuts en lecture : waiting_for_validation, approved, rejected, disputed, refused, collected, partially_collected.",
        )],
        reason: Annotated[Optional[str], Field(default=None, description="Raison du litige ou du refus (REQUIS pour 'disputed' et 'refused').")] = None,
    ) -> str:
        """Change le statut PPF / PA d'une facture fournisseur reçue en e-invoicing."""
        try:
            if status in ("disputed", "refused") and not reason:
                return f"❌ Le champ 'reason' est requis par l'API pour le statut '{status}'."
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
        file_attachment_id: Annotated[int, Field(description="ID du fichier joint (créé via pennylane_create_file_attachment).")],
        supplier_id: Annotated[int, Field(description="ID du fournisseur (requis par l'API).")],
        date: Annotated[str, Field(description="Date d'émission de la facture (YYYY-MM-DD).")],
        deadline: Annotated[str, Field(description="Date d'échéance (YYYY-MM-DD).")],
        currency_amount_before_tax: Annotated[str, Field(description="Total HT en devise (string, ex: '1000.00').")],
        currency_amount: Annotated[str, Field(description="Total TTC en devise (string).")],
        currency_tax: Annotated[str, Field(description="Montant de TVA en devise (string).")],
        invoice_lines: Annotated[list, Field(
            description="Lignes (min 1). Chaque ligne : {currency_amount: str, currency_tax: str, "
            "vat_rate: str (ex: 'FR_200'), label?: str}.",
        )],
        invoice_number: Annotated[Optional[str], Field(default=None, description="Numéro de la facture fournisseur.")] = None,
        currency: Annotated[Optional[str], Field(default=None, description="Devise (défaut: EUR).")] = None,
        import_as_incomplete: Annotated[bool, Field(
            default=False,
            description="Importer avec le statut 'incomplete' (défaut: false).",
        )] = False,
        label: Annotated[Optional[str], Field(default=None, description="Libellé (≤2000 caractères).")] = None,
    ) -> str:
        """Importe une facture fournisseur avec son fichier et ses données comptables
        (POST /supplier_invoices/import — champs montants requis par l'API).
        """
        try:
            body: dict = {
                "file_attachment_id": file_attachment_id,
                "supplier_id": supplier_id,
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
            if import_as_incomplete:
                body["import_as_incomplete"] = True
            if label:
                body["label"] = label
            data = await api_post("/supplier_invoices/import", body)
            return f"✅ Facture fournisseur importée avec succès (id: {data.get('id')}).\n\n{to_json(data)}"
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

