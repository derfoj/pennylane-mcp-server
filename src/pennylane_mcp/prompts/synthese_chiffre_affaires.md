# Workflow MCP : Analyse et Ventilation du Chiffre d'Affaires

Ce workflow guide l'assistant IA (Claude) pour réaliser une analyse approfondie du Chiffre d'Affaires (CA), examiner la dynamique commerciale et rédiger une note de synthèse à destination du dirigeant ou du directeur financier (DAF).

## 📋 Instructions d'exécution étape par étape

### Étape 1 : Vérification du périmètre
- Appelle `pennylane_current_dossier` pour identifier l'entreprise concernée.
- Appelle `pennylane_list_fiscal_years` pour vérifier les dates de l'exercice fiscal actif.

### Étape 2 : Extraction de la Balance des Revenus (Classe 7)
- Appelle `pennylane_get_trial_balance` pour obtenir la balance de l'exercice en cours ou de la période spécifiée dans `periode`.
- Filtre et isole l'ensemble des comptes commençant par le chiffre `7` (Produits).
- Distingue :
  - **Chiffre d'Affaires opérationnel (`70x`)** : `701` Ventes de produits finis, `704` Travaux, `706` Prestations de services, `707` Ventes de marchandises, `708` Produits des activités annexes, `709` Rabais, remises et ristournes accordés (à soustraire !).
  - **Autres produits d'exploitation (`74x`, `75x`, `79x`)** : Subventions d'exploitation, autres produits de gestion courante, transferts de charges.
  - **Produits financiers et exceptionnels (`76x`, `77x`)**.

### Étape 3 : Croisement avec le carnet de commandes et devis (Optionnel mais recommandé)
- Appelle l'outil `pennylane_list_quotes` en filtrant par statut (`sent`, `accepted`, `invoiced`) pour évaluer le pipeline commercial en cours et le carnet d'affaires signé à venir.
- Appelle l'outil `pennylane_list_billing_subscriptions` (si pertinent) pour évaluer la part de Revenu Récurrent Mensuel (MRR / ARR).

### Étape 4 : Calculs des indicateurs clés
1. **CA Brut** : Somme des crédits des comptes `701` à `708`.
2. **CA Net** : CA Brut moins les RRR accordés (compte `709` débiteur).
3. **Part du chiffre d'affaires par activité** : Pourcentage de contribution de chaque sous-compte (`701`, `706`, etc.) au CA Net total.
4. Si `comparaison_annuelle` est activée et que l'historique le permet (via les exercices précédents dans la balance), calcule l'évolution en pourcentage (croissance ou baisse).

### Étape 5 : Restitution au format Markdown structuré
Présente un rapport de direction clair, visuel et parfaitement structuré :

1. **KPIs en coup d'œil** :
   - 📈 **Chiffre d'Affaires Net** : [Montant] €
   - 🏆 **Activité principale** : [Libellé compte 70x principal] ([X] % du total)
   - 📑 **Pipeline Devis en attente / signés** : [Montant ou Synthèse]

2. **Tableau de ventilation du CA par nature d'activité** :
   | Compte PCG | Libellé de l'activité | Montant Crédit (Revenus) | Montant Débit (Avoirs/RRR) | CA Net HT | Contribution (%) |
   |---|---|---|---|---|---|
   | 706000 | Prestations de services | 145 000,00 € | 2 500,00 € | 142 500,00 € | 82,5 % |
   | 707000 | Ventes de marchandises | 31 000,00 € | 750,00 € | 30 250,00 € | 17,5 % |
   | **TOTAL** | **Chiffre d'Affaires Opérationnel** | **176 000,00 €** | **3 250,00 €** | **172 750,00 €** | **100,0 %** |

3. **Analyse qualitative & Commentaires de gestion** :
   - Rédige une analyse concise en 3 ou 4 paragraphes mettant en avant les points forts de l'activité, la diversification des revenus, et les points d'attention éventuels (ex: dépendance à un seul type de prestation, poids important des remises accordées).
