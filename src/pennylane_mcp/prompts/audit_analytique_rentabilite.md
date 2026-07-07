# Workflow MCP : Audit Analytique et Analyse de Rentabilité

Ce workflow guide l'assistant IA (Claude) pour auditer la structure de comptabilité analytique du dossier client, vérifier la bonne ventilation des charges et produits par centre de profit ou projet, et calculer la marge contributive par axe.

## 📋 Instructions d'exécution étape par étape

### Étape 1 : Cartographie des axes et groupes analytiques
- Appelle `pennylane_list_category_groups` et `pennylane_list_categories` pour cartographier les axes analytiques configurés (ex: Projets, Agences, Départements, Lignes de produits).
- Si aucune catégorie analytique n'existe, propose d'en créer avec `pennylane_create_category_group` et `pennylane_create_category` selon l'activité du client.

### Étape 2 : Vérification de la configuration analytique par défaut
Pour garantir une affectation automatique et éviter les oublis de saisie :
1. **Produits / Services** : Appelle `pennylane_list_products` (limit=30) puis vérifie pour les articles phares s'ils disposent d'une ventilation analytique via `pennylane_list_product_categories`.
2. **Clients & Fournisseurs** : Vérifie si des tiers réguliers (sous-traitants, clients majeurs) ont des catégories affectées par défaut via `pennylane_list_customer_categories` ou `pennylane_list_supplier_categories`.
3. Si des articles ou tiers importants manquent de ventilation, propose de les catégoriser avec `pennylane_categorize_product`, `pennylane_categorize_customer` ou `pennylane_categorize_supplier` (en rappelant que la somme des poids `weight` doit égaler `1.0`).

### Étape 3 : Audit du lettrage et de l'imputation analytique sur les écritures
- Appelle `pennylane_list_all_entry_lines` (sur les comptes de charges classe `6` et produits classe `7`, limit=100) pour examiner si les lignes d'écritures récentes portent bien des tags analytiques (`categories` / `category_ids`).
- Calcule le **taux de couverture analytique** : pourcentage des lignes de charges et de produits qui possèdent au moins une catégorie analytique rattachée.

### Étape 4 : Calcul de rentabilité par axe / centre de profit
Si des lignes sont catégorisées, regroupe les montants par axe analytique :
1. **Chiffre d'Affaires analytique** : Somme des crédits des comptes `7` imputés sur l'axe.
2. **Charges directes & indirectes** : Somme des débits des comptes `6` imputés sur l'axe.
3. **Marge Contributive / Résultat par projet** : CA Analytique - Charges Analytiques.

### Étape 5 : Restitution au format Markdown structuré
Présente le compte de résultat analytique et le diagnostic sous forme de tableau :

1. **KPIs Analytiques** :
   - 🎯 **Taux de couverture analytique** : [X] % des flux ventilés
   - 🏗️ **Nombre de centres de profit / projets actifs** : [N]

2. **Compte de Résultat Analytique Synthétique** :
   | Centre de Profit / Projet | Chiffre d'Affaires (70x) | Charges imputées (60-68) | Marge (€) | Taux de Marge (%) | Contribution REX |
   |---|---|---|---|---|---|
   | Projet Alpha - Paris | 120 000,00 € | 85 000,00 € | + 35 000,00 € | 29,2 % | 🟢 Rentable |
   | Projet Bêta - Lyon | 45 000,00 € | 52 000,00 € | - 7 000,00 € | - 15,5 % | 🔴 Déficitaire |
   | *Non ventilé / Frais généraux*| 11 000,00 € | 39 000,00 € | - 28 000,00 € | N/A | ⚠️ À répartir |

3. **Recommandations d'optimisation pour le DAF / Dirigeant** :
   - Analyse des causes de déficit sur les projets en perte (ex: dérive des coûts de sous-traitance, sous-facturation).
   - Proposition d'automatisation : affecter des règles analytiques par défaut sur les fiches fournisseurs récurrents pour viser 100% de couverture.
