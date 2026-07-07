# Workflow MCP : Comparatif Synoptique Multi-Dossiers

Ce workflow guide l'assistant IA (Claude) pour réaliser une analyse comparative et un benchmark synoptique à l'échelle du cabinet sur l'ensemble (ou une sélection) des dossiers clients configurés.

## 📋 Instructions d'exécution étape par étape

### Étape 1 : Recensement des dossiers du cabinet
- Appelle l'outil `pennylane_list_dossiers` pour afficher la liste de tous les dossiers comptables configurés et obtenir leur `slug` et `name`.
- Si un seul dossier est configuré, informe l'utilisateur que le comparatif nécessite au moins 2 dossiers et propose d'en ajouter avec `pennylane_add_dossier`.

### Étape 2 : Collecte parallèle des balances (`multi_dossier_query`)
- Utilise l'outil ultra-rapide `pennylane_multi_dossier_query` en ciblant :
  - `endpoint`: `"/trial_balance"`
  - `method`: `"GET"`
- Cette requête interrogera simultanément tous les dossiers en parallèle et retournera la balance générale pour chacun d'eux.
- *Alternative si filtrage spécifique* : Si l'utilisateur souhaite comparer une liste restreinte de slugs, interroge-les séquentiellement via `pennylane_switch_dossier` puis `pennylane_get_trial_balance`.

### Étape 3 : Calcul des grands indicateurs financiers par dossier
Pour chaque dossier client, agrège les soldes de la balance pour extraire :
1. **Chiffre d'Affaires Net (Classe 70)** : Total crédits moins total débits des comptes `70x`.
2. **Charges d'exploitation (Classe 6)** : Total débits des comptes `60x` (achats), `61x`/`62x` (services extérieurs), `63x` (impôts), `64x` (personnel).
3. **Résultat d'exploitation approximatif (REX)** : CA Net - Charges d'exploitation.
4. **Trésorerie disponible (Classe 5)** : Total des soldes des comptes de banque (`512xxx`) et caisse (`530xxx`).
5. **Encours clients et fournisseurs** : Solde des comptes `411xxx` (créances clients) et `401xxx` (dettes fournisseurs).

### Étape 4 : Évaluation des risques et seuils d'alertes
Applique le paramètre `seuil_alertes` (`normal`, `strict`, ou `permissif`) pour attribuer un indicateur de santé à chaque dossier :
- 🚨 **Alerte rouge** : Trésorerie négative (découvert), ou REX fortement déficitaire, ou compte de caisse créditeur (anomalie légale).
- ⚠️ **Vigilance** : Charges de personnel (> 60% du CA), ou encours clients très élevé (> 30% du CA annuel).
- 🟢 **Sain** : Indicateurs équilibrés, trésorerie positive, marge positive.

### Étape 5 : Restitution sous forme de tableau synoptique Markdown
Présente le benchmark du cabinet avec un grand tableau comparatif :

| Dossier / Client | CA Net HT | Charges Expl. | REX Estimé | Trésorerie (512+530) | Encours Clients (411) | Encours Fourn. (401) | Statut / Santé |
|---|---|---|---|---|---|---|---|
| SARL Dupont | 240 000 € | 180 000 € | + 60 000 € | + 35 400 € | 18 200 € | 12 100 € | 🟢 Sain |
| SAS Martin | 110 000 € | 125 000 € | - 15 000 € | - 2 300 € | 42 000 € | 8 500 € | 🚨 Alerte Trésorerie |

### Étape 6 : Synthèse managériale pour l'associé du cabinet
Rédige une conclusion executive en 3 points :
1. **Dossier(s) prioritaire(s)** nécessitant un point d'urgence avec le dirigeant (ex: SAS Martin pour son découvert et ses impayés clients).
2. **Tendance globale du portefeuille** (croissance générale, tensions sur la trésorerie à l'échelle du cabinet, etc.).
3. **Recommandations d'accompagnement conseil** (mise en place de relances automatiques via `/relance_impayes_clients`, audit de coûts).
