"""Client HTTP pour l'API Pennylane V2.

Gère l'authentification Bearer, les requêtes, et les messages d'erreur
actionnables en français.

**Mode multi-dossiers** : les fonctions ``api_get/post/put/delete``
acceptent un paramètre optionnel ``dossier_slug`` pour cibler un dossier
spécifique. Si omis, le dossier actif est utilisé.

Rétrocompatibilité totale : tous les appels existants sans
``dossier_slug`` continuent de fonctionner.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import httpx

from .constants import API_BASE_URL
from .utils import dump_pydantic

# ─── Legacy : client unique (rétrocompatibilité) ─────────────────────────────

_client: Optional[httpx.AsyncClient] = None


def init_client(api_token: str) -> None:
    """Initialise le client httpx legacy avec le token Bearer."""
    global _client
    _client = httpx.AsyncClient(
        base_url=API_BASE_URL,
        timeout=30.0,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_token}",
            "X-Use-2026-API-Changes": "true",
        },
    )


async def close_client() -> None:
    """Ferme proprement le client HTTP legacy."""
    global _client
    if _client:
        await _client.aclose()
        _client = None


# ─── Résolution du client (multi-dossier ou legacy) ──────────────────────────


async def _resolve_client(
    dossier_slug: str | None = None,
) -> httpx.AsyncClient:
    """Résout le client httpx à utiliser.

    Priorité :
    1. Si ``dossier_slug`` est fourni → client du dossier spécifié.
    2. Si le DossierManager est initialisé → client du dossier actif.
    3. Sinon → client legacy ``_client``.
    """
    # Import ici pour éviter les imports circulaires
    from .dossier_manager import get_manager, has_manager

    if has_manager():
        return await get_manager().get_client(dossier_slug)

    # Mode legacy
    if _client is None:
        raise RuntimeError(
            "Le client API n'est pas initialisé. "
            "Vérifiez la variable PENNYLANE_API_TOKEN ou le fichier dossiers.json."
        )
    return _client


# ─── Méthodes HTTP (multi-dossier & retry automatique - Pilier 4) ─────────────


async def _request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs: Any,
) -> httpx.Response:
    """Exécute une requête HTTP avec retry automatique et backoff exponentiel sur quota/surcharge."""
    max_retries = 3
    for attempt in range(max_retries + 1):
        try:
            resp = await client.request(method, url, **kwargs)
            # Retry automatique sur 429 (Too Many Requests) ou erreurs serveur 500, 502, 503, 504
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                retry_after = resp.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    wait_time = float(retry_after)
                else:
                    wait_time = 1.0 * (2 ** attempt)  # Backoff: 1s, 2s, 4s
                await asyncio.sleep(wait_time)
                continue
            resp.raise_for_status()
            return resp
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            if attempt < max_retries:
                await asyncio.sleep(1.0 * (2 ** attempt))
                continue
            raise


async def api_get(
    endpoint: str,
    params: Optional[dict[str, Any]] = None,
    *,
    dossier_slug: Optional[str] = None,
) -> Any:
    """GET vers l'API Pennylane avec retry automatique."""
    try:
        client = await _resolve_client(dossier_slug)
        if params is not None:
            params = dump_pydantic(params)
        resp = await _request_with_retry(client, "GET", endpoint, params=params)
        return resp.json()
    except httpx.HTTPStatusError as exc:
        raise _format_error(exc, dossier_slug) from exc
    except httpx.TimeoutException as exc:
        raise RuntimeError(
            _prefix_dossier("Timeout : la requête vers Pennylane a expiré après retries. Réessayez.", dossier_slug)
        ) from exc
    except httpx.ConnectError as exc:
        raise RuntimeError(
            _prefix_dossier("Connexion refusée : impossible de joindre l'API Pennylane.", dossier_slug)
        ) from exc


async def api_post(
    endpoint: str,
    data: Optional[dict[str, Any]] = None,
    *,
    dossier_slug: Optional[str] = None,
) -> Any:
    """POST vers l'API Pennylane avec retry automatique."""
    try:
        client = await _resolve_client(dossier_slug)
        if data is not None:
            data = dump_pydantic(data)
        resp = await _request_with_retry(client, "POST", endpoint, json=data)
        # Certains POST renvoient 204 ou un body vide (ex: send_by_email)
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()
    except httpx.HTTPStatusError as exc:
        raise _format_error(exc, dossier_slug) from exc
    except httpx.TimeoutException as exc:
        raise RuntimeError(
            _prefix_dossier("Timeout : requête expirée après retries.", dossier_slug)
        ) from exc


async def api_put(
    endpoint: str,
    data: Optional[dict[str, Any]] = None,
    *,
    dossier_slug: Optional[str] = None,
) -> Any:
    """PUT vers l'API Pennylane avec retry automatique."""
    try:
        client = await _resolve_client(dossier_slug)
        if data is not None:
            data = dump_pydantic(data)
        resp = await _request_with_retry(client, "PUT", endpoint, json=data)
        # Certains PUT renvoient 204 ou un body vide
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()
    except httpx.HTTPStatusError as exc:
        raise _format_error(exc, dossier_slug) from exc
    except httpx.TimeoutException as exc:
        raise RuntimeError(
            _prefix_dossier("Timeout : requête expirée après retries.", dossier_slug)
        ) from exc


async def api_delete(
    endpoint: str,
    data: Optional[dict[str, Any]] = None,
    *,
    dossier_slug: Optional[str] = None,
) -> Any:
    """DELETE vers l'API Pennylane avec retry automatique."""
    try:
        client = await _resolve_client(dossier_slug)
        if data is not None:
            data = dump_pydantic(data)
        resp = await _request_with_retry(client, "DELETE", endpoint, json=data)
        # Certains DELETE renvoient 204 sans body
        if resp.status_code == 204:
            return {}
        return resp.json()
    except httpx.HTTPStatusError as exc:
        raise _format_error(exc, dossier_slug) from exc
    except httpx.TimeoutException as exc:
        raise RuntimeError(
            _prefix_dossier("Timeout : requête expirée après retries.", dossier_slug)
        ) from exc


# ─── Requête parallèle multi-dossiers ────────────────────────────────────────


async def api_get_multi(
    endpoint: str,
    dossier_slugs: list[str],
    params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """GET en parallèle sur plusieurs dossiers.

    Args:
        endpoint: Chemin API.
        dossier_slugs: Liste des slugs à interroger.
        params: Paramètres de query string communs.

    Returns:
        dict[slug → {"dossier": name, "data": ..., "error": ...}]
    """
    from .dossier_manager import get_manager

    return await get_manager().parallel_get(endpoint, dossier_slugs, params)


# ─── Formatage des erreurs ────────────────────────────────────────────────────


def _prefix_dossier(msg: str, slug: str | None) -> str:
    """Préfixe un message d'erreur avec le nom du dossier si disponible."""
    if slug:
        return f"[{slug}] {msg}"
    return msg


def _format_error(
    exc: httpx.HTTPStatusError,
    dossier_slug: str | None = None,
) -> RuntimeError:
    """Transforme une erreur HTTP en message français actionnable avec conseils pour Claude."""
    status = exc.response.status_code
    try:
        body = exc.response.json()
    except Exception:
        body = {}

    msg = body.get("message") or body.get("error") or ""

    # Extraction détaillée des erreurs (ex: {"errors": {"credit": ["must equal debit"]}})
    errors_detail = body.get("errors")
    detail_str = ""
    if isinstance(errors_detail, dict):
        parts = [f"{k}: {', '.join(v) if isinstance(v, list) else v}" for k, v in errors_detail.items()]
        detail_str = " | ".join(parts)
    elif isinstance(errors_detail, list):
        detail_str = " | ".join([str(e) for e in errors_detail])
    elif errors_detail:
        detail_str = str(errors_detail)

    full_msg = msg
    if detail_str:
        full_msg = f"{msg} ({detail_str})" if msg else detail_str
    if not full_msg:
        full_msg = exc.response.text[:300] if exc.response.text else "Raison non spécifiée par l'API"

    messages = {
        400: (
            f"Requête invalide (400) : {full_msg}. "
            "Action recommandée pour Claude : Vérifiez la syntaxe des paramètres, le format des dates (YYYY-MM-DD), "
            "ou la validité des filtres fournis."
        ),
        401: (
            "Authentification échouée (401) : token manquant, invalide ou expiré. "
            "Action recommandée : Vérifiez le token API dans dossiers.json ou dans la variable PENNYLANE_API_TOKEN."
        ),
        403: (
            f"Accès refusé (403) : {full_msg}. "
            "Action recommandée : Vérifiez que le token API Pennylane dispose des scopes requis (ex: ledger_entries:all, trial_balance:readonly)."
        ),
        404: (
            f"Ressource introuvable (404) : {full_msg}. "
            "Action recommandée pour Claude : Vérifiez l'identifiant ou le code utilisé (ex: numéro de compte, code journal, ID facture) via les outils d'exploration (`pennylane_list_*`)."
        ),
        409: (
            f"Conflit (409) : {full_msg}. "
            "Action recommandée pour Claude : Vérifiez s'il ne s'agit pas d'un doublon (numéro de facture, code compte) ou d'une ressource déjà existante/modifiée."
        ),
        422: (
            f"Erreur de validation Pennylane (422) : {full_msg}. "
            "Action recommandée pour Claude : "
            "1) S'il s'agit d'une écriture comptable, vérifiez rigoureusement qu'elle est équilibrée (Total Débits == Total Crédits). "
            "2) Vérifiez l'existence et le bon préfixe des comptes PCG avec `pennylane_list_accounts`. "
            "3) Assurez-vous que les champs obligatoires ne sont pas vides et sont correctement typés."
        ),
        429: "Trop de requêtes (429) : Le quota de l'API Pennylane est atteint. Attendez quelques secondes avant de réessayer.",
    }

    text = messages.get(
        status,
        f"Erreur API Pennylane ({status}) : {full_msg}. Action recommandée : Analysez la réponse et ajustez les arguments de l'outil.",
    )
    return RuntimeError(_prefix_dossier(text, dossier_slug))
