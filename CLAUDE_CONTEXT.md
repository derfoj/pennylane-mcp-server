# Contexte Projet : Serveur MCP Pennylane pour Expert-Comptable

## Vue d'ensemble

Serveur **MCP** (Model Context Protocol) en **Python / FastMCP** connectant un LLM à l'API comptable **Pennylane V2**. Destiné aux **experts-comptables** pour automatiser leurs opérations quotidiennes via un assistant IA.

**v2.0** : support multi-dossiers — gestion de plusieurs dossiers comptables simultanément, requêtes parallèles, et configuration dynamique.

## Contexte métier : Pennylane

Pennylane est une plateforme de comptabilité collaborative française. Elle centralise saisie comptable, facturation, banque et collaboration entreprise/expert-comptable.

### Concepts comptables clés

- **Plan Comptable Général (PCG)** : comptes normalisés par classe (1=capitaux, 2=immobilisations, 3=stocks, 4=tiers, 5=financier, 6=charges, 7=produits). Préfixes importants : 401=fournisseurs, 411=clients, 421=personnel, 44=TVA/État, 512=banque, 530=caisse.

- **Journaux** : registres par nature (VE=ventes, HA=achats, BQ=banque, OD=opérations diverses, PA=paie).

- **Écriture comptable** : pièce composée de lignes équilibrées (total débits = total crédits), chaque ligne imputée sur un compte du PCG.

- **Lettrage** : rapprochement facture/règlement sur un même compte tiers. Permet le suivi des impayés.

- **Balance générale** : synthèse de tous les comptes avec soldes débit/crédit sur une période. Outil de contrôle essentiel.

- **Exercice fiscal** : période comptable (12 mois), statuts possibles : ouvert, clôturé, gelé, réouvert.

- **Comptabilité analytique** : ventilation charges/produits par catégories avec poids (somme = 1).

- **Dossier comptable** : un dossier = une société/entreprise dans Pennylane. Un cabinet gère typiquement des dizaines de dossiers.

## Architecture technique

### API Pennylane V2

- **Base URL** : `https://app.pennylane.com/api/external/v2`
- **Auth** : Bearer token (un token Company API par dossier)
- **Pagination** : curseur (`cursor` + `limit` + `has_more` + `next_cursor`)
- **Filtres** : JSON array `[{field, operator, value}]`
- **Scopes** : permissions granulaires (`ledger_accounts:all`, `journals:readonly`, etc.)

### Modes de fonctionnement

1. **Multi-dossiers** (recommandé) : fichier `dossiers.json` avec N dossiers, chacun avec son token. Pool de clients httpx, switch à la volée, requêtes parallèles.
2. **Mono-dossier** (rétrocompatible) : variable `PENNYLANE_API_TOKEN`, crée un dossier "default" dans le manager.
3. **Mode initial** : ni fichier ni token, le serveur démarre vide et attend l'ajout d'un dossier via outil MCP.

### 158 outils, 8 prompts et 12 ressources MCP

| Domaine | Fichiers | Outils principaux |
|---------|----------|-------------------|
| Multi-dossiers | `tools/dossiers.py` | `list_dossiers`, `current_dossier`, `switch_dossier`, `add_dossier`, `remove_dossier`, `multi_dossier_query` |
| Connexion & Société | `tools/me.py` | `pennylane_whoami` |
| Plan comptable | `tools/accounts.py` | `list_accounts`, `get_account`, `create_account`, `update_account` |
| Journaux & Écritures | `tools/journals.py`, `entries.py`, `entry_lines.py` | CRUD journaux, écritures, lignes, lettrage, délettrage, ventilation analytique |
| Balance & Exercices | `tools/trial_balance.py` | `get_trial_balance`, `list_fiscal_years` |
| Tiers (Clients/Fournisseurs) | `tools/customers.py`, `suppliers.py` | CRUD tiers, catégorisation analytique |
| Facturation Clients | `tools/customer_invoices.py` | CRUD factures, finalisation, paiement, e-invoicing PA, templates, annexes |
| Facturation Fournisseurs | `tools/supplier_invoices.py` | Consultation, maj, paiement, statut e-invoicing PA, import OCR avec pièce jointe |
| Devis & Produits | `tools/quotes.py`, `products.py` | CRUD devis, envoi email, annexes, catalogue produits & services |
| Analytique & Abonnements | `tools/categories.py`, `billing_subscriptions.py` | Axes analytiques, abonnements récurrents |
| Banque & Trésorerie | `tools/bank_accounts.py`, `transactions.py`, `mandates.py` | Comptes bancaires, rapprochement, lettrage bancaire, mandats SEPA/GoCardless |
| Achats & Commerce | `tools/commercial_documents.py`, `purchase_requests.py` | Documents commerciaux, demandes d'achats, bons de commande |
| Administration & E-invoicing | `tools/exports.py`, `changelogs.py`, `pa_registrations.py`, `file_attachments.py` | Exports FEC/GL/AGL, changelogs, statut PA, gestion des pièces jointes |

### Structure du code

```
src/pennylane_mcp/
├── server.py            — FastMCP + lifespan multi-mode (avec Instructions de Serveur enrichies)
├── constants.py         — API_BASE_URL, CHARACTER_LIMIT, constantes multi-dossiers
├── models.py            — Modèles Pydantic (validation stricte + modèles typés pour listes : CategoryWeight, InvoiceLineInput, EntryLineInput)
├── api.py               — Client httpx async (multi-dossier + retry auto backoff 429/5xx + auto-correction /me + sérialisation dump_pydantic)
├── utils.py             — truncate_if_needed, pagination_summary, to_json, dump_pydantic
├── dossier_manager.py   — DossierManager : pool de clients, switch, CRUD dossiers, requêtes parallèles
├── prompts/             — 8 Workflows et commandes slash en fichiers Markdown (.md)
├── resources/           — 12 Ressources MCP et templates (7 directes + 5 templates en .md et JSON)
├── tools/               — 24 modules spécialisés, chacun avec register(mcp)
```

### Choix techniques

1. **Python + FastMCP** : framework MCP officiel, décorateurs `@mcp.tool` supportant 158 outils hautement structurés.
2. **Pydantic v2 intégral** : élimination de tous les types `list` non typés et `list[dict]` dans les signatures d'outils au profit de modèles Pydantic structurés (`CategoryWeight`, `InvoiceLineInput`, `EntryLineInput` avec `str_strip_whitespace=True`).
3. **Sérialisation universelle (`dump_pydantic`)** : transformation automatique de tous les modèles Pydantic et structures imbriquées en types compatibles JSON dans `api.py` (`mode="json"`), empêchant toute exception `TypeError: not JSON serializable`.
4. **Conformité API V2 stricte** : respect des chemins officiels et pluralisation (ex. `POST/GET /exports/general_ledgers`).
5. **httpx async & résilience** : requêtes HTTP non-bloquantes avec timeout 30s et retry auto sur `429 Too Many Requests` / `5xx`.
6. **Lifespan multi-mode** : détection auto du mode (`dossiers.json` → `PENNYLANE_API_TOKEN` → vide).
7. **DossierManager** : singleton gérant un pool de clients httpx, un par dossier, avec masquage des tokens.
8. **Requêtes parallèles** : `api_get_multi()` et `DossierManager.parallel_get()` via `asyncio.gather()`.
9. **Erreurs actionnables en français** : messages d'erreur formatés et explicites pour guider le LLM (`_format_error`).
10. **Transport stdio & SSE** : intégration locale (Claude Desktop) et distante sur HTTP via `MCP_TRANSPORT=sse`.

### Configuration multi-dossiers (dossiers.json)

```json
{
  "version": "1.0",
  "current_dossier": "sarl-dupont",
  "dossiers": [
    {
      "slug": "sarl-dupont",
      "name": "SARL Dupont",
      "token": "pl_xxx...",
      "created_at": "2025-02-10T12:00:00Z",
      "notes": "Client principal"
    }
  ]
}
```

Recherche du fichier : `PENNYLANE_CONFIG_PATH` env → `./dossiers.json` → `~/.config/pennylane-mcp/dossiers.json`.

## Cas d'usage expert-comptable

### Travaux courants
- Consultation / recherche dans le plan comptable
- Saisie d'écritures de journal (OD, à-nouveaux, corrections)
- Vérification de la balance par période
- Lettrage factures / règlements

### Travaux de clôture
- Revue de la balance et soldes anormaux
- Écritures de régularisation (provisions, amortissements, CCA, FNP)
- Vérification équilibre débit/crédit

### Analyse
- Mouvements d'un compte sur une période
- Suivi créances clients non lettrées (impayés)
- Ventilation analytique des charges

### Multi-dossiers (nouveau v2.0)
- Basculer entre dossiers clients à la volée
- Comparer des balances entre plusieurs clients
- Ajouter/supprimer des dossiers sans relancer le serveur
- Requêtes parallèles pour consolider des données

## Vision : Plateforme MCP multi-serveurs

Ce serveur est la brique fondatrice d'une **plateforme en ligne** :

```
Client LLM (API Claude, OpenAI, Mistral...)
       ↕ REST / WebSocket
   MCP Gateway Platform (multi-tenant)
       ↕ MCP Protocol
┌──────────────────────────────────┐
│ Pennylane MCP Server             │
│ Open Banking MCP Server          │
│ URSSAF MCP Server                │
│ Impots.gouv MCP Server           │
│ DSN / Paie MCP Server            │
└──────────────────────────────────┘
```

Pour passer en mode plateforme : changer `mcp.run()` en `mcp.run(transport="streamable_http", port=8000)`.

## Dépendances

- `mcp[cli]` >= 1.6.0 — SDK MCP officiel avec FastMCP
- `httpx` >= 0.27.0 — Client HTTP async
- `pydantic` >= 2.0.0 — Validation

## Comment étendre

1. Créer un modèle Pydantic dans `models.py`
2. Créer/enrichir un fichier dans `tools/`
3. Utiliser `@mcp.tool(name=..., annotations=...)` avec le modèle en paramètre
4. Appeler `register(mcp)` dans `server.py`

## Variables d'environnement

| Variable | Requis | Description |
|----------|--------|-------------|
| `PENNYLANE_API_TOKEN` | Non* | Token Bearer API Pennylane V2 (mode mono-dossier) |
| `PENNYLANE_CONFIG_PATH` | Non | Chemin vers dossiers.json |

\* Requis uniquement si pas de dossiers.json.
