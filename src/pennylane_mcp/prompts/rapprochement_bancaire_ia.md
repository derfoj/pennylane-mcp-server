# Workflow MCP : Assistance au Rapprochement Bancaire et Lettrage IA

Ce workflow guide l'assistant IA (Claude) pour auditer les flux bancaires non réconciliés, proposer des associations intelligentes (matching) entre transactions et factures, et automatiser le lettrage comptable sur le dossier actif.

## 📋 Instructions d'exécution étape par étape

### Étape 1 : Vérification de la banque et du dossier
- Appelle `pennylane_current_dossier` pour vérifier le dossier actif.
- Appelle `pennylane_list_bank_accounts` pour identifier les comptes bancaires connectés (IBAN, nom de la banque, solde en temps réel).

### Étape 2 : Extraction des transactions non rapprochées
- Appelle `pennylane_list_transactions` avec les filtres suivants :
  - `status`: `"unmatched"` (ou sans filtre si l'utilisateur veut tout analyser).
  - `limit`: `50` (pour examiner un lot représentatif de mouvements en attente).
- Isole pour chaque transaction : la date, le libellé bancaire brut, le montant (positif pour un encaissement, négatif pour un décaissement) et le compte bancaire associé.

### Étape 3 : Extraction des factures en attente de paiement
Pour identifier les correspondances potentielles, appelle en parallèle :
- `pennylane_list_customer_invoices` (filtre `status="unpaid"` ou `"late"`) pour les encaissements (+).
- `pennylane_list_supplier_invoices` (filtre `status="unpaid"` ou `"late"`) pour les décaissements (-).
- *Astuce de lettrage* : Vérifie également les lignes non lettrées des comptes tiers `411` et `401` via `pennylane_list_all_entry_lines` (`is_lettered: false`).

### Étape 4 : Moteur de rapprochement IA (Matching sémantique et numérique)
Pour chaque transaction non réconciliée, recherche un match exact ou probabiliste selon 3 critères :
1. **Correspondance de montant** : Le montant TTC de la facture équivaut exactement au montant de la transaction au centime près.
2. **Correspondance de tiers / libellé** : Le libellé bancaire contient le nom du client, du fournisseur ou le numéro de facture (ex: `VIR RECU DUPONT FACT-2026-042`).
3. **Proximité temporelle** : La date de la transaction intervient dans les 30 à 60 jours suivant l'émission de la facture.

### Étape 5 : Restitution au format Markdown structuré
Présente un rapport de rapprochement avec un tableau de propositions de lettrage :

| Date Trans. | Libellé Bancaire | Montant | Facture Proposée (Tiers & N°) | Score de Confiance | Action Proposée |
|---|---|---|---|---|---|
| 04/07/2026 | VIR SEPA EDF ENERGIE | - 245,00 € | Fournisseur EDF - Fact. FAC-9988 (245,00 €) | 🟢 100% (Exact) | Lettrer via `pennylane_match_transaction_invoice` |
| 02/07/2026 | CB STRIPE PAYMENTS | + 1 250,00 € | Client SARL Alpha - Fact. FAC-2026-012 | 🟡 85% (Montant) | À vérifier par l'utilisateur |
| 01/07/2026 | PRELEVEMENT URSSAF | - 3 400,00 € | *Aucune facture trouvée* | ⚪ 0% (Sans facture) | Créer règle via `pennylane_list_reconciliation_rules` |

### Étape 6 : Plan de régularisation et d'automatisation
1. Pour les correspondances à **100% de confiance**, propose à l'utilisateur d'exécuter immédiatement le lettrage en appelant `pennylane_match_transaction_invoice` (demande confirmation en précisant les IDs).
2. Pour les charges récurrentes sans facture (ex: loyer, prélèvements sociaux URSSAF, commissions bancaires), suggère de consulter ou de créer une règle d'imputation automatique avec `pennylane_list_reconciliation_rules`.
