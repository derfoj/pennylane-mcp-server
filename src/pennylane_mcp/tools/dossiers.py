"""Outils MCP : gestion multi-dossiers comptables Pennylane.

Permet de lister, ajouter, supprimer et basculer entre plusieurs
dossiers comptables (chacun avec son propre token Company API).
Inclut également un outil de requête parallèle multi-dossiers.
"""

from __future__ import annotations

from typing import Annotated, Any, Optional

from pydantic import Field
from mcp.server.fastmcp import FastMCP

from ..api import api_get, api_get_multi
from ..dossier_manager import get_manager
from ..utils import to_json, truncate_if_needed


def register(mcp: FastMCP) -> None:
    """Enregistre les 6 outils de gestion multi-dossiers."""

    # ── Lister les dossiers ──────────────────────────────────────────────

    @mcp.tool(
        name="pennylane_list_dossiers",
        annotations={
            "title": "Lister les dossiers comptables",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def pennylane_list_dossiers() -> str:
        """Liste tous les dossiers comptables configurés avec leur statut.
        Les tokens sont masqués pour la sécurité.
        """
        try:
            manager = get_manager()
            dossiers = manager.list_dossiers()

            if not dossiers:
                return (
                    "📁 Aucun dossier configuré.\n"
                    "Utilisez pennylane_add_dossier pour en ajouter un."
                )

            result = {
                "total": len(dossiers),
                "current": manager.current_slug,
                "dossiers": [d.model_dump() for d in dossiers],
            }
            return f"📁 {len(dossiers)} dossier(s) configuré(s).\n\n{to_json(result)}"

        except Exception as exc:
            return f"❌ {exc}"

    # ── Dossier actif ────────────────────────────────────────────────────

    @mcp.tool(
        name="pennylane_current_dossier",
        annotations={
            "title": "Dossier comptable actif",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_current_dossier() -> str:
        """Affiche le dossier comptable actuellement actif avec les
        informations de connexion Pennylane (via /me).
        """
        try:
            manager = get_manager()
            info = manager.get_current_info()

            if info is None:
                return (
                    "⚠️ Aucun dossier actif.\n"
                    "Utilisez pennylane_switch_dossier ou "
                    "pennylane_add_dossier pour en sélectionner un."
                )

            # Vérifier la connexion avec /me
            try:
                me_data = await api_get("/me")
            except Exception as me_exc:
                me_data = {"error": str(me_exc)}

            result = {
                "dossier": info.model_dump(),
                "connexion_pennylane": me_data,
            }
            return (
                f"📁 Dossier actif : {info.name} ({info.slug})\n\n"
                f"{to_json(result)}"
            )

        except Exception as exc:
            return f"❌ {exc}"

    # ── Basculer de dossier ──────────────────────────────────────────────

    @mcp.tool(
        name="pennylane_switch_dossier",
        annotations={
            "title": "Changer de dossier comptable",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_switch_dossier(
        slug: Annotated[str, Field(description="Slug du dossier vers lequel basculer.")],
    ) -> str:
        """Bascule vers un autre dossier comptable. Toutes les requêtes
        suivantes utiliseront ce dossier par défaut.
        Vérifie la connexion avec l'endpoint /me après le switch.
        """
        try:
            manager = get_manager()
            info = await manager.switch_dossier(slug)

            # Vérifier la connexion
            try:
                me_data = await api_get("/me")
                company_info = (
                    me_data.get("company_name")
                    or me_data.get("email")
                    or "connexion OK"
                )
            except Exception:
                company_info = "⚠️ connexion non vérifiée"

            result = {
                "dossier": info.model_dump(),
                "verification": company_info,
            }
            return (
                f"✅ Dossier actif : {info.name} ({info.slug})\n\n"
                f"{to_json(result)}"
            )

        except ValueError as exc:
            return f"❌ {exc}"
        except Exception as exc:
            return f"❌ Erreur lors du switch : {exc}"

    # ── Ajouter un dossier ───────────────────────────────────────────────

    @mcp.tool(
        name="pennylane_add_dossier",
        annotations={
            "title": "Ajouter un dossier comptable",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def pennylane_add_dossier(
        slug: Annotated[str, Field(
            min_length=1,
            max_length=50,
            description="Identifiant unique (minuscules, chiffres, tirets). Ex: 'sarl-dupont'.",
        )],
        name: Annotated[str, Field(
            min_length=1,
            max_length=200,
            description="Nom d'affichage. Ex: 'SARL Dupont'.",
        )],
        token: Annotated[str, Field(
            min_length=10,
            description=(
                "Token API Pennylane : Company API Token, ou Firm API Token "
                "(token cabinet) si company_id est fourni."
            ),
        )],
        company_id: Annotated[Optional[int], Field(
            default=None,
            description=(
                "ID de la société Pennylane (header X-Company-Id). "
                "Obligatoire avec un Firm API Token. "
                "Utilisez pennylane_list_firm_companies pour trouver les IDs."
            ),
        )] = None,
        notes: Annotated[Optional[str], Field(
            default=None,
            max_length=500,
            description="Notes libres sur le dossier.",
        )] = None,
    ) -> str:
        """Ajoute un nouveau dossier comptable à la configuration.
        Le token est vérifié avec l'endpoint /me avant l'ajout.
        Si c'est le premier dossier, il devient automatiquement actif.

        Deux modes d'authentification :
        - Company API Token seul (un token par société)
        - Firm API Token (token cabinet) + company_id de la société cible
        """
        try:
            manager = get_manager()

            # Vérifier le token avant d'ajouter
            from ..dossier_manager import _build_client

            test_client = _build_client(token, company_id)
            try:
                resp = await test_client.get("/me")
                resp.raise_for_status()
                me_data = resp.json()
            except Exception as verify_exc:
                await test_client.aclose()
                hint = (
                    "Si vous utilisez un Firm API Token (token cabinet), "
                    "fournissez aussi company_id."
                    if company_id is None
                    else "Vérifiez que company_id correspond bien à une "
                    "société du portefeuille du cabinet."
                )
                return (
                    f"❌ Token invalide pour '{slug}' : {verify_exc}\n"
                    f"   {hint}\n"
                    "   Tokens : Pennylane > Paramètres > Connectivité > "
                    "Développeurs (société) ou Paramètres du cabinet > "
                    "Firm Tokens (cabinet)."
                )
            finally:
                await test_client.aclose()

            # Ajouter le dossier
            config = await manager.add_dossier(
                slug=slug,
                name=name,
                token=token,
                notes=notes,
                company_id=company_id,
            )

            company = me_data.get("company") or {}
            company_info = (
                company.get("name")
                or me_data.get("company_name")
                or me_data.get("email")
                or "vérifié"
            )

            mode = (
                f"Firm token + X-Company-Id {company_id}"
                if company_id is not None
                else "Company token"
            )
            return (
                f"✅ Dossier '{name}' ({slug}) ajouté.\n"
                f"   Connexion Pennylane : {company_info} ({mode})\n"
                f"   Dossier actif : {manager.current_slug}"
            )

        except ValueError as exc:
            return f"❌ {exc}"
        except Exception as exc:
            return f"❌ Erreur lors de l'ajout : {exc}"

    # ── Supprimer un dossier ─────────────────────────────────────────────

    @mcp.tool(
        name="pennylane_remove_dossier",
        annotations={
            "title": "Supprimer un dossier comptable",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def pennylane_remove_dossier(
        slug: Annotated[str, Field(description="Slug du dossier à supprimer.")],
    ) -> str:
        """Supprime un dossier comptable de la configuration.
        Si le dossier supprimé était actif, le premier dossier restant
        devient actif automatiquement.
        """
        try:
            manager = get_manager()
            was_current = manager.current_slug == slug
            name = manager.get_dossier_name(slug) or slug

            await manager.remove_dossier(slug)

            msg = f"✅ Dossier '{name}' ({slug}) supprimé."
            if was_current:
                new_current = manager.current_slug
                if new_current:
                    new_name = manager.get_dossier_name(new_current)
                    msg += f"\n   Nouveau dossier actif : {new_name} ({new_current})"
                else:
                    msg += "\n   ⚠️ Plus aucun dossier actif."

            msg += f"\n   Dossiers restants : {manager.dossier_count}"
            return msg

        except ValueError as exc:
            return f"❌ {exc}"
        except Exception as exc:
            return f"❌ Erreur lors de la suppression : {exc}"

    # ── Requête parallèle multi-dossiers ─────────────────────────────────

    @mcp.tool(
        name="pennylane_multi_dossier_query",
        annotations={
            "title": "Requête parallèle multi-dossiers",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_multi_dossier_query(
        dossier_slugs: Annotated[list[str], Field(
            min_length=1,
            description="Liste des slugs de dossiers à interroger.",
        )],
        endpoint: Annotated[str, Field(
            description="Endpoint API à appeler (ex: '/me', '/ledger_accounts', '/trial_balance').",
        )],
        params: Annotated[Optional[dict[str, Any]], Field(
            default=None,
            description="Paramètres de requête optionnels (query string).",
        )] = None,
    ) -> str:
        """Exécute une requête GET en parallèle sur plusieurs dossiers.
        Utile pour comparer des données entre clients ou consolider
        des informations (ex: balances, comptes, exercices).
        """
        try:
            results = await api_get_multi(
                endpoint=endpoint,
                dossier_slugs=dossier_slugs,
                params=params,
            )

            successes = sum(
                1 for r in results.values() if r.get("error") is None
            )
            errors = len(results) - successes

            summary = (
                f"📊 Requête parallèle sur {len(dossier_slugs)} dossier(s) "
                f"— {successes} succès, {errors} erreur(s).\n"
                f"   Endpoint : {endpoint}\n\n"
            )

            return truncate_if_needed(
                summary + to_json(results),
                hint="Réduisez le nombre de dossiers ou utilisez des filtres plus restrictifs.",
            )

        except Exception as exc:
            return f"❌ {exc}"

    # ── Lister les sociétés du cabinet (API Firm) ────────────────────────

    @mcp.tool(
        name="pennylane_list_firm_companies",
        annotations={
            "title": "Lister les sociétés du cabinet (API Firm)",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def pennylane_list_firm_companies(
        token: Annotated[Optional[str], Field(
            default=None,
            description=(
                "Firm API Token (token cabinet). Si omis, utilise le token "
                "du dossier actif (qui doit être un Firm token)."
            ),
        )] = None,
        page: Annotated[int, Field(
            default=1, ge=1,
            description="Page à récupérer (pagination classique, débute à 1).",
        )] = 1,
        per_page: Annotated[int, Field(
            default=100, ge=1, le=1000,
            description="Nombre de sociétés par page (max 1000).",
        )] = 100,
    ) -> str:
        """Liste les sociétés (dossiers clients) du portefeuille du cabinet
        via l'API Firm Pennylane. Nécessite un Firm API Token avec le scope
        `companies:readonly`.

        Utile pour récupérer les company_id à passer à pennylane_add_dossier
        (mode Firm token + X-Company-Id).
        """
        import httpx as _httpx

        from ..constants import FIRM_API_BASE_URL
        from ..dossier_manager import get_manager as _get_manager

        try:
            firm_token = token
            if firm_token is None:
                manager = _get_manager()
                slug = manager.current_slug
                if slug is None:
                    return (
                        "❌ Aucun token fourni et aucun dossier actif. "
                        "Passez le Firm API Token en paramètre."
                    )
                firm_token = manager._dossiers[slug].token  # noqa: SLF001

            async with _httpx.AsyncClient(
                base_url=FIRM_API_BASE_URL,
                timeout=30.0,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {firm_token}",
                },
            ) as client:
                resp = await client.get(
                    "/companies",
                    params={"page": page, "per_page": per_page},
                )
                resp.raise_for_status()
                data = resp.json()

            items = data.get("items", [])
            companies = [
                {
                    "company_id": c.get("id"),
                    "name": c.get("name"),
                    "siren": c.get("siren"),
                    "client_code": c.get("client_code"),
                    "city": c.get("city"),
                }
                for c in items
            ]
            result = {
                "total_items": data.get("total_items"),
                "current_page": data.get("current_page"),
                "total_pages": data.get("total_pages"),
                "companies": companies,
            }
            return truncate_if_needed(
                f"🏢 {data.get('total_items', len(companies))} société(s) "
                f"dans le portefeuille du cabinet.\n\n{to_json(result)}",
                hint="Utilisez page/per_page pour paginer.",
            )

        except _httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                return (
                    "❌ Token invalide ou non-Firm (401). Cet outil requiert "
                    "un Firm API Token (Paramètres du cabinet > Firm Tokens)."
                )
            if exc.response.status_code == 403:
                return (
                    "❌ Scope manquant (403) : le Firm token doit avoir "
                    "`companies:readonly`."
                )
            return f"❌ Erreur API Firm ({exc.response.status_code}) : {exc}"
        except Exception as exc:
            return f"❌ {exc}"
