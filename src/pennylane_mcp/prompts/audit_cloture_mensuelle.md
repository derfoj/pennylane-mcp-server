# Workflow MCP : Audit de Santé pour la Clôture Mensuelle / Annuelle

Ce workflow guide l'assistant IA (Claude) pour réaliser une revue comptable exhaustive et un audit de santé avant la clôture mensuelle ou annuelle d'un dossier client.

## 📋 Instructions d'exécution étape par étape

### Étape 1 : Cadrage et vérification de la période
- Appelle `pennylane_current_dossier` pour vérifier les informations du dossier en cours.
- Appelle `pennylane_list_fiscal_years` pour identifier l'exercice fiscal concerné et vérifier si la période est ouverte, clôturée ou gelée.

### Étape 2 : Extraction de la Balance Générale
- Appelle `pennylane_get_trial_balance` pour obtenir la balance de tous les comptes sur l'exercice en cours (ou sur la période mensuelle spécifiée dans `exercice`).
- Vérifie l'équilibre global de la balance : la somme de tous les soldes débiteurs doit être rigoureusement égale à la somme de tous les soldes créditeurs.

### Étape 3 : Audit de Trésorerie et Banque (Classe 5)
1. Appelle `pennylane_list_bank_accounts` pour vérifier la liste des comptes bancaires connectés au dossier.
2. Vérifie dans la balance que les comptes de banques (`512xxx`) correspondent à la réalité de la trésorerie.
3. **Contrôle critique Caisse (`530xxx`)** : Un compte de caisse ne doit **jamais** présenter un solde créditeur en comptabilité française. Si le solde est créditeur, signale une **anomalie majeure** (erreur de saisie, omission d'apport de caisse).
4. Vérifie les comptes de virements internes (`58xxx`) : ils doivent impérativement être soldés (solde égal à 0) à la date de clôture.

### Étape 4 : Audit de TVA (Comptes 445)
1. Analyse les soldes de TVA : TVA collectée (`44571`), TVA déductible (`44566`), TVA intracommunautaire (`4452` / `44562`).
2. Vérifie la cohérence du compte de TVA à décaisser (`44551`) ou de crédit de TVA (`44567`).

### Étape 5 : Audit des Comptes de Tiers (Classe 4) & Lettrage
1. **Comptes Fournisseurs (`401xxx`)** : Vérifie l'absence de soldes débiteurs anormaux sur les fournisseurs (sauf acomptes versés ou avoirs non reçus).
2. **Comptes Clients (`411xxx`)** : Vérifie l'absence de soldes créditeurs anormaux sur les clients (sauf règlements anticipés sans facture ou doubles règlements).
3. Utilise l'outil `pennylane_list_all_entry_lines` avec `is_lettered: false` sur les comptes `401` et `411` pour estimer le volume d'écritures en attente de lettrage.

### Étape 6 : Audit des Comptes d'Attente et de Transit (`471`, `472`)
- Les comptes `471` (Recettes à classer) et `472` (Dépenses à classer / virements en suspens) sont utilisés par Pennylane lors de l'intégration bancaire lorsque le tiers n'est pas identifié.
- Vérifie si ces comptes présentent un solde. Si oui, détaille les lignes non soldées afin de solliciter les pièces justificatives ou indications du client.

### Étape 7 : Rapport d'Audit & Score de Santé Synthétique
Présente un rapport complet au format Markdown sous la forme :

1. **Score de santé comptable global** (sur 10) calculé selon :
   - 10/10 : Balance équilibrée, comptes d'attente à 0, caisse débitrice, aucun solde tiers aberrant.
   - -2 points par compte d'attente (`471`/`472`/`58`) non soldé.
   - -3 points si caisse (`530`) créditrice.
   - -2 points pour un volume excessif de lignes non lettrées (> 50 lignes en souffrance).

2. **Tableau des anomalies détectées** :
   | Priorité | Compte concerné | Nature de l'anomalie | Solde / Montant | Action corrective recommandée |
   |---|---|---|---|---|
   | 🚨 Haute | ex: 530000 Caisse | Solde créditeur interdit | -1 450,00 € | Vérifier les apports en espèces ou erreurs de saisie |
   | ⚠️ Moyenne | ex: 471000 Attente | Recettes bancaires non identifiées | 3 200,00 € | Pointer les virements clients avec les factures émises |

3. **Plan d'action avant clôture** : Liste à puces ordonnée des étapes à réaliser par le collaborateur comptable pour valider définitivement la clôture.
