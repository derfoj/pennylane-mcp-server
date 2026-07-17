# 🌐 Guide de Déploiement en Cabinet (Mode SSE - Zéro Installation Locale)

Ce guide explique comment déployer le **Pennylane MCP Server** sur un serveur central ou un cloud afin que l'ensemble des experts-comptables et collaborateurs du cabinet puissent l'utiliser **sans aucune installation technique de Python, Git ou de dépendances sur leurs PC individuels**.

---

## 🏛️ 1. Architecture et Avantages du Mode SSE

Par défaut, un serveur MCP s'exécute en mode `stdio` (en ligne de commande sur chaque PC). Grâce au mode **SSE (Server-Sent Events over HTTP)**, le serveur s'exécute **une seule fois sur un serveur du cabinet** et communique avec les clients Claude par le réseau.

### ✨ Pourquoi c'est la meilleure solution pour un cabinet comptable :
1. **Zéro installation chez les utilisateurs :** Pas de Python, pas de Git, pas de ligne de commande pour les comptables.
2. **Maintenance centralisée :** Vous mettez à jour le code sur le serveur, et **100% de l'équipe bénéficie instantanément des nouvelles corrections et fonctionnalités**.
3. **Sécurité et protection de la propriété intellectuelle :** Vos clés API et votre configuration restent sur le serveur du cabinet.
4. **Multi-dossiers global :** Vous pouvez pré-charger tous les dossiers clients du cabinet dans le fichier `dossiers.json` du serveur central.

---

## 🚀 2. Étape 1 : Lancement du serveur (Côté Administrateur / IT)

### Option A : Déploiement instantané via Docker (Recommandé)
Sur le serveur du cabinet (NAS Synology, serveur Windows/Linux, ou Cloud de type Railway/Render/AWS) :

1. Copiez le dossier du projet ou clonez le dépôt Git.
2. Configurez vos variables d'environnement dans le fichier `docker-compose.yml` (ou créez un fichier `.env`) :
   ```yaml
   environment:
     - MCP_TRANSPORT=sse
     - MCP_PORT=8000
     - MCP_AUTH_TOKEN=secret_cabinet_2026 # Pour interdire l'accès public non autorisé
     - PENNYLANE_API_TOKEN=votre_token_api_ou_vide_si_multidossier
   ```
3. Lancez le conteneur en arrière-plan :
   ```bash
   docker compose up -d
   ```
Le serveur est désormais en ligne et écoute sur `http://votre-serveur:8000/sse`.

### Option B : Lancement direct en Python
Si vous exécutez le serveur directement sur un PC ou serveur sans Docker :
```bash
export MCP_TRANSPORT=sse
export MCP_HOST=0.0.0.0
export MCP_PORT=8000
export MCP_AUTH_TOKEN=secret_cabinet_2026

pennylane-mcp-server
```

*(Note : En production sur internet, il est vivement conseillé de placer un reverse proxy HTTPS comme Nginx ou Traefik devant le port 8000).*

---

## 💻 3. Étape 2 : Configuration chez les Collaborateurs (1 minute chrono)

Sur le PC de chaque collaborateur (Windows, Mac ou Linux) qui utilise **Claude Desktop** :

1. Ouvrez Claude Desktop.
2. Allez dans **Paramètres (Settings) > Développeur (Developer) > Modifier la configuration (Edit Config)**.
3. Ajoutez simplement l'URL de votre serveur centralisée :

```json
{
  "mcpServers": {
    "pennylane-cabinet": {
      "url": "http://adresse-ip-du-serveur:8000/sse"
    }
  }
}
```

*Si vous avez activé un token de sécurité (`MCP_AUTH_TOKEN`), passez-le dans les en-têtes (headers) ou selon le client MCP utilisé :*
```json
{
  "mcpServers": {
    "pennylane-cabinet": {
      "url": "http://adresse-ip-du-serveur:8000/sse",
      "headers": {
        "Authorization": "Bearer secret_cabinet_2026"
      }
    }
  }
}
```

4. **Enregistrez le fichier et redémarrez Claude Desktop.**  
   🎉 **C'est tout !** L'icône du marteau (🛠️) apparaît dans Claude. Le collaborateur a accès à l'ensemble des **157 outils, 8 commandes slash et 12 ressources** sans avoir installé aucune ligne de code !

---

## 🔒 4. Sécurité et Bonnes Pratiques en Cabinet

* **Isolation des accès :** N'exposez jamais le port de votre serveur MCP directement sur Internet sans HTTPS et sans un `MCP_AUTH_TOKEN` robuste, ou limitez l'accès au réseau local / VPN du cabinet.
* **Gestion Multi-dossiers :** Si vous montez un fichier `dossiers.json` sur le serveur central, tous les collaborateurs auront accès aux clients listés dans ce fichier et pourront basculer d'un client à l'autre via la commande `/switch_dossier` ou l'outil `pennylane_switch_dossier`.

---

## 🏢 5. Authentification par Firm API Token (token cabinet)

Depuis la v2.1, le serveur supporte **deux modes d'authentification** par dossier :

| Mode | Champ(s) dans dossiers.json | Avantage |
|---|---|---|
| **Company API Token** | `token` | Un token par société, périmètre isolé |
| **Firm API Token** | `token` (cabinet) + `company_id` | Un seul token pour tout le portefeuille |

Avec un Firm API Token (généré dans *Paramètres du cabinet > Firm Tokens*), le serveur ajoute automatiquement le header `X-Company-Id` à chaque requête API v2. Exemple de `dossiers.json` :

```json
{
  "version": "1.0",
  "current_dossier": "ze-astronaut",
  "dossiers": [
    {
      "slug": "ze-astronaut",
      "name": "Ze Astronaut",
      "token": "FIRM_API_TOKEN_DU_CABINET",
      "company_id": 22017564,
      "notes": "SIREN 847712056"
    },
    {
      "slug": "disgros",
      "name": "DISGROS",
      "token": "FIRM_API_TOKEN_DU_CABINET",
      "company_id": 22017551,
      "notes": "SIREN 894823343"
    }
  ]
}
```

* L'outil **`pennylane_list_firm_companies`** liste les sociétés du portefeuille avec leurs `company_id` (scope `companies:readonly` requis) — pratique pour construire ce fichier.
* En mode mono-dossier (variables d'environnement), définissez `PENNYLANE_API_TOKEN` (Firm token) **et** `PENNYLANE_COMPANY_ID` (ID de la société).
* ⚠️ Un Firm token donne accès à **tout le portefeuille** : si chaque collaborateur ne doit voir que ses clients, préférez les Company tokens par client, ou un `dossiers.json` restreint par collaborateur.
