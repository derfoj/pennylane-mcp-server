# Workflow MCP : Gestion et Relance des Impayés Clients

Ce workflow guide l'assistant IA (Claude) pour auditer les créances clients en retard sur le dossier actif, analyser l'antériorité des impayés, et préparer des relances personnalisées et professionnelles.

## 📋 Instructions d'exécution étape par étape

### Étape 1 : Vérification du contexte et du dossier actif
- Appelle impérativement l'outil `pennylane_current_dossier` pour confirmer le dossier comptable sur lequel s'effectue l'analyse.
- Si aucun dossier n'est actif, demande à l'utilisateur de sélectionner un dossier avec `pennylane_switch_dossier` ou de consulter la liste avec `pennylane_list_dossiers`.

### Étape 2 : Extraction des lignes de créances non lettrées (Compte 411)
- Appelle l'outil `pennylane_list_all_entry_lines` avec les paramètres suivants :
  - `account_number`: `"411"` (comptes clients du Plan Comptable Général).
  - `is_lettered`: `false` (pour isoler uniquement les factures et règlements non soldés).
  - `limit`: `100` (pour obtenir une vue large).
- *Gestion de la pagination* : Si la réponse indique `has_more: true` ou fournit un `next_cursor`, utilise ce curseur pour récupérer les pages suivantes si nécessaire afin de ne manquer aucune créance significative.

### Étape 3 : Croisement avec les factures clients (Optionnel mais recommandé)
- Pour enrichir les coordonnées (email, nom du contact, numéro de facture officiel, date d'échéance contractuelle), tu peux utiliser l'outil `pennylane_list_customer_invoices` en filtrant sur les statuts impayés (`unpaid`, `late`).

### Étape 4 : Analyse d'antériorité et calcul de l'encours
1. Calcule le nombre de jours de retard par rapport à la date d'échéance (ou à défaut la date de comptabilisation).
2. Filtre les créances pour ne conserver que celles dont le retard est supérieur ou égal au paramètre `jours_retard_min` (par défaut 30 jours) et correspondant au filtre `client_prefix` si fourni.
3. Regroupe les créances par client (via `third_party_id` ou libellé client) et calcule :
   - L'encours total en retard par tiers.
   - La créance la plus ancienne (date et montant).

### Étape 5 : Restitution au format Markdown structuré
Présente un rapport de synthèse professionnel en Markdown comprenant :
1. **Un encadré de synthèse** : Nombre de clients en retard, montant total TTC de l'encours échu, créance la plus critique.
2. **Un tableau synoptique de l'encours** :
   | Client / Tiers | N° Pièce / Facture | Date d'émission | Date d'échéance | Retard estimé | Montant TTC | Statut / Risque |
   |---|---|---|---|---|---|---|
3. **Classification du risque** :
   - 🟢 *Retard modéré* (< 30 jours)
   - 🟡 *Retard significatif* (30 à 60 jours) — Relance amiable 1 ou 2
   - 🔴 *Retard critique / Contentieux* (> 60 jours) — Mise en demeure

### Étape 6 : Rédaction des projets de relance
Pour chaque client en situation de retard significatif ou critique, propose un modèle d'email de relance prêt à l'emploi :
- **Objet** : Rappel de paiement - Facture(s) [Numéros] - [Nom de votre société/cabinet]
- **Corps** : Rappel courtois et ferme des factures en souffrance, rappel des références bancaires (IBAN à consulter via `pennylane_list_bank_accounts` si besoin), et demande de régularisation sous 8 jours.
- Prévois une tonalité adaptée au niveau de risque (Amiable -> Ferme -> Pré-contentieux).
