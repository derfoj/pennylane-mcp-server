# 🎯 Guide Pratique : Comptabilité Analytique & Ventilation dans Pennylane V2

La comptabilité analytique dans Pennylane permet d'analyser la rentabilité d'une entreprise par projet, agence, département, ligne de produit ou centre de coût, indépendamment de la classification légale du Plan Comptable Général (PCG).

---

## 🏗️ Structure Hiérarchique de l'Analytique
Dans Pennylane, l'analytique s'organise en deux niveaux :
1. **Groupes de catégories (`category_groups`)** : L'axe d'analyse macroscopique (ex: *"Projets Clients"*, *"Agences Régionales"*, *"Départements de l'entreprise"*).
2. **Catégories (`categories`)** : Les sous-divisions de chaque groupe (ex: *"Projet Alpha"*, *"Projet Bêta"*, *"Agence de Lyon"*, *"Agence de Paris"*).

---

## ⚖️ Règle des Poids de Ventilation (`weight`)
Lorsqu'un article, un tiers ou une écriture est catégorisé, l'imputation se fait sous forme de liste d'objets contenant l'ID de la catégorie et un **poids (`weight`)** exprimé en nombre décimal sous forme de chaîne de caractères :
```json
[
  { "id": 59, "weight": "0.75" },
  { "id": 60, "weight": "0.25" }
]
```
- **Règle absolue** : La somme des poids (`weight`) sur un même axe pour une ligne donnée doit **impérativement être égale à 1.0 (soit 100%)**.
- Si la somme des poids diffère de 1.0, l'API Pennylane retournera une erreur 400 ou 422 (`Unprocessable Entity`).

---

## 🔄 3 Niveaux d'Automatisation Analytique dans Pennylane
Pour éviter au collaborateur comptable de devoir tagger manuellement chaque ligne de facture, Pennylane utilise un système d'héritage en cascade :

1. **Niveau Catalogue (Produits / Services)** :
   - Via `pennylane_categorize_product`, on affecte une ventilation par défaut à une prestation. Lorsqu'on crée une facture avec ce produit, la ligne hérite automatiquement de l'analytique.
2. **Niveau Tiers (Clients / Fournisseurs)** :
   - Via `pennylane_categorize_customer` ou `pennylane_categorize_supplier`, on affecte un axe à un sous-traitant ou client dédié. Toutes ses factures seront ventilées sur cet axe.
3. **Niveau Ligne d'écriture (Correction fine)** :
   - Via `pennylane_link_categories`, on peut écraser ou corriger manuellement la ventilation analytique sur une ligne d'écriture comptable spécifique (`ledger_entry_line`).

---

## 📊 Grand Livre Analytique (`pennylane_get_analytical_general_ledger`)
Pour auditer la rentabilité :
- L'outil `pennylane_get_analytical_general_ledger` croise les comptes de charges (classe 6) et de produits (classe 7) avec chaque catégorie analytique.
- Il permet d'établir en un instant un **Compte de Résultat par Projet (REX Analytique)**.
