"""Outils MCP : gestion des fichiers joints et pièces annexes (File Attachments)."""

from __future__ import annotations

from typing import Annotated, Optional

from pydantic import Field
from mcp.server.fastmcp import FastMCP

from ..api import api_get, api_post
from ..utils import to_json


def register(mcp: FastMCP) -> None:
    """Enregistre les outils de gestion des fichiers joints (File Attachments)."""

    # ── Créer / uploader un fichier joint ─────────────────────────────────────

    @mcp.tool(
        name="pennylane_create_file_attachment",
        description="Crée ou importe un fichier joint (PDF, image, XML) sur Pennylane pour utilisation dans les factures et devis.",
        annotations={
            "title": "Uploader / créer un fichier joint",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_create_file_attachment(
        file_name: Annotated[str, Field(description="Nom du fichier avec extension (ex: 'facture_123.pdf').")],
        file_content: Annotated[Optional[str], Field(default=None, description="Contenu du fichier encodé en Base64.")] = None,
        file_url: Annotated[Optional[str], Field(default=None, description="URL externe publique d'où télécharger le fichier (alternatif à file_content).")] = None,
        content_type: Annotated[Optional[str], Field(default="application/pdf", description="Type MIME du fichier (ex: 'application/pdf', 'image/png', 'application/xml').")] = "application/pdf",
    ) -> str:
        """Crée un nouvel attachement de fichier (File Attachment) dans Pennylane.
        L'identifiant retourné (`id`) permet ensuite de joindre ce fichier à une facture
        fournisseur, une facture client ou en tant qu'annexe d'un devis.
        """
        try:
            if not file_content and not file_url:
                return "❌ Erreur : vous devez fournir soit 'file_content' (en base64) soit 'file_url'."

            body: dict = {
                "file_name": file_name,
                "content_type": content_type,
            }
            if file_content:
                body["file_content"] = file_content
            if file_url:
                body["file_url"] = file_url

            data = await api_post("/file_attachments", body)
            return (
                f"✅ Fichier joint créé avec succès (id: {data.get('id', 'N/A')}).\n"
                f"Vous pouvez maintenant utiliser cet ID avec pennylane_import_supplier_invoice, "
                f"pennylane_upload_quote_appendix, etc.\n\n{to_json(data)}"
            )
        except Exception as exc:
            return f"❌ {exc}"

    # ── Récupérer un fichier joint ────────────────────────────────────────────

    @mcp.tool(
        name="pennylane_get_file_attachment",
        description="Récupère les détails et métadonnées d'un fichier joint existant dans Pennylane.",
        annotations={
            "title": "Détail d'un fichier joint",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_get_file_attachment(
        id: Annotated[int, Field(description="Identifiant unique du fichier joint.")],
    ) -> str:
        """Récupère les informations d'une pièce jointe par son ID."""
        try:
            data = await api_get(f"/file_attachments/{id}")
            return to_json(data)
        except Exception as exc:
            return f"❌ {exc}"
