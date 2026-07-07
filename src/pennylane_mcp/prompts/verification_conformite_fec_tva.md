# Workflow MCP : Vérification de Conformité FEC et Audit TVA

Ce workflow guide l'assistant IA (Claude) pour auditer la conformité fiscale d'un dossier avant l'export du Fichier des Écritures Comptables (FEC) et la souscription des déclarations de TVA (CA3 / CA12).

## 📋 Instructions d'exécution étape par étape

### Étape 1 : Vérification de l'exercice fiscal et de la clôture
- Appelle `pennylane_list_fiscal_years` pour vérifier l'état des exercices.
- Rappelle que pour générer un export FEC officiel conforme à l'article A47 A-1 du LPF via `pennylane_create_fec_export` ou `pennylane_get_fec_export`, l'exercice doit impérativement être dans un statut clôturé (`closed` ou `frozen`). Si l'exercice est encore ouvert (`open`), préviens qu'il s'agira d'un FEC provisoire de test.

### Étape 2 : Contrôles de conformité structurelle des écritures
Pour éviter tout rejet par le logiciel de contrôle de l'administration fiscale (Test Compta Demat / DGFIP) :
1. **Équilibre strict** : Appelle `pennylane_get_trial_balance` pour vérifier que le total des mouvements débits égale le total des mouvements crédits au centime près.
2. **Continuité des dates et chronologie** : Vérifie qu'il n'y a pas d'écritures passées sur des dates antérieures à un exercice déjà clôturé.
3. **Absence de comptes d'attente non soldés** : Vérifie impérativement le solde des comptes `471` (Recettes à classer), `472` (Dépenses à classer) et `58` (Virements internes). Dans un FEC définitif, ces comptes doivent avoir un solde égal à zéro.

### Étape 3 : Audit et cadrage de TVA (Rapprochement Base / Taxe)
1. Isole dans la balance générale :
   - Le Chiffre d'Affaires soumis à TVA (`701`, `706`, `707`).
   - Les comptes de TVA collectée (`44571...`).
   - Les comptes de TVA déductible sur biens et services (`44566...`) et sur immobilisations (`44562...`).
   - Le compte de TVA à décaisser (`44551...`) ou crédit de TVA (`44567...`).
2. Calcule le **taux apparent de TVA collectée** : `(Total Crédit 44571 / Total Crédit 70x soumis) * 100`. Il doit être cohérent avec les taux légaux français (20%, 10%, 5,5%, 2,1%).
3. Vérifie que les écritures d'OD de centralisation de TVA ont bien été passées à la fin de chaque mois ou trimestre.

### Étape 4 : Restitution sous forme de rapport d'audit fiscal Markdown
Présente le diagnostic officiel de pré-déclaration :

1. **Grille de conformité FEC (LPF Art. A47 A-1)** :
   - ✅ **Équilibre Débit / Crédit** : Conforme (Écart = 0,00 €)
   - ✅ **Statut de l'exercice** : Clôturé / Gelé (prêt pour export légal)
   - ⚠️ **Comptes temporaires (471/472)** : Solde de 450,00 € à purger avant génération

2. **Tableau de Cadrage de TVA** :
   | Nature de flux | Base HT estimée (Comptes 70/60) | TVA Théorique (à 20%) | TVA Comptabilisée (44571/44566) | Écart constaté | Évaluation |
   |---|---|---|---|---|---|
   | TVA Collectée (Ventes) | 150 000,00 € | 30 000,00 € | 29 850,00 € | - 150,00 € | 🟡 Écart minime (expliquer opérations exonérées ou taux réduits) |
   | TVA Déductible (Achats) | 80 000,00 € | 16 000,00 € | 15 920,00 € | - 80,00 € | 🟢 Conforme |

3. **Recommandations et validation finale** :
   - Si tous les voyants sont au vert, propose d'exécuter l'export officiel en appelant `pennylane_create_fec_export` ou le Grand Livre Général via `pennylane_get_general_ledger`.
   - Sinon, liste les écritures d'OD de régularisation à passer en priorité.
