# 📚 Plan Comptable Général (PCG) — Synthèse & Logique Pennylane V2

Le Plan Comptable Général (PCG) français organise les comptes en 8 classes principales. Dans l'écosystème Pennylane et pour l'assistance IA par Claude, la qualification, le lettrage et les contrôles de clôture s'appuient sur cette logique :

---

## 🏛️ Classes de Bilan (Comptes de patrimoine)

### Classe 1 : Capitaux (Fonds propres, emprunts, provisions)
- **`101000`** : Capital social
- **`106000`** : Réserves légales et statutaires
- **`120000` / `129000`** : Résultat de l'exercice (Bénéfice / Perte)
- **`164000`** : Emprunts et dettes auprès des établissements de crédit
- *Règle Pennylane* : Les mouvements sur emprunts s'accompagnent souvent d'un lettrage avec l'échéancier bancaire.

### Classe 2 : Immobilisations (Biens durables > 500 € HT)
- **`205000`** : Concessions, logiciels et brevets (Incorporelles)
- **`218100`** : Installations générales, agencements
- **`218300`** : Matériel de bureau et informatique
- **`28...`** : Amortissements des immobilisations (toujours créditeurs en diminution de l'actif)
- *Règle Pennylane* : Tout achat de matériel > 500 € HT doit être immobilisé (classe 2) et non passé en charge courante.

### Classe 3 : Stocks et en-cours
- **`310000`** : Matières premières
- **`370000`** : Marchandises
- *Règle Pennylane* : Les variations de stocks se constatent en fin d'exercice via les comptes `603` (achats) ou `713` (produits).

### Classe 4 : Comptes de Tiers (Pivot central dans Pennylane)
- **`401...` : Fournisseurs** (Dettes d'achats).
  - *Comportement Pennylane* : Un sous-compte auxiliaire unique est créé pour chaque fournisseur (ex: `401001` EDF, `401002` ORANGE). Ne jamais saisir directement sur la racine `401000` sans affecter de tiers !
- **`411...` : Clients** (Créances de ventes).
  - *Comportement Pennylane* : Sous-comptes par client. C'est sur le compte `411xxx` que s'opère le **lettrage** (rapprochement facture émise et virement reçu via `pennylane_letter_lines`).
- **`421...`** : Personnel (rémunérations dues aux salariés).
- **`431...` / `437...`** : Sécurité sociale (URSSAF) et autres organismes sociaux (retraite, mutuelle).
- **`445...` : Téleservices et État (TVA - Très sensible !)**
  - `445660` : TVA déductible sur autres biens et services.
  - `445620` : TVA déductible sur immobilisations.
  - `445710` : TVA collectée sur ventes (à 20%, 10%, 5.5% ou 2.1%).
  - `445510` : TVA à décaisser (solde créditeur du mois/trimestre à payer à l'État).
  - `445670` : Crédit de TVA à reporter.
- **`471...` (Recettes à classer) / `472...` (Dépenses à classer)** :
  - *Règle critique* : Comptes d'attente utilisés par l'import bancaire lorsque l'IA ou l'utilisateur n'identifie pas le tiers. **Doivent impérativement être vidés et lettrés à 0 avant toute clôture de bilan.**

### Classe 5 : Comptes Financiers (Trésorerie & Rapprochement)
- **`512...` : Banques** (un compte par IBAN connecté dans Pennylane).
  - *Solde normal* : Débiteur (ou créditeur en cas de découvert autorisé).
- **`530...` : Caisse**.
  - *Règle absolue (Légale)* : **Une caisse ne peut jamais avoir un solde créditeur !** Si le crédit dépasse le débit, c'est une anomalie fiscale grave à corriger immédiatement.
- **`58...` : Virements internes** (transferts entre deux comptes bancaires du cabinet). Solde à 0 en fin de mois.

---

## 📈 Classes de Gestion (Comptes de résultat)

### Classe 6 : Charges d'exploitation (Dépenses)
- **`606xxx`** : Achats non stockés de matières et fournitures (électricité, eau, fournitures de bureau).
- **`613xxx`** : Locations immobilières et mobilières (loyers, leasing).
- **`615xxx`** : Entretien et réparations.
- **`616xxx`** : Primes d'assurances.
- **`622xxx`** : Rémunérations d'intermédiaires et honoraires (expert-comptable, avocat, consultants).
- **`623xxx`** : Publicité, publications, relations publiques.
- **`625xxx`** : Déplacements, missions et de réception (notes de frais, train, restaurant).
- **`627xxx`** : Services bancaires et assimilés (commissions, frais de tenue de compte, Stripe).
- **`635xxx`** : Autres impôts et taxes (CFE, CVAE).
- **`641xxx`** : Rémunérations du personnel (salaires bruts).
- **`645xxx`** : Charges de sécurité sociale et de prévoyance.
- **`681xxx`** : Dotations aux amortissements.

### Classe 7 : Produits d'exploitation (Revenus & CA)
- **`701000`** : Ventes de produits finis.
- **`706000`** : Prestations de services (conseil, ingénierie, services B2B).
- **`707000`** : Ventes de marchandises (négoce, e-commerce).
- **`708000`** : Produits des activités annexes (refacturations, ports).
- **`709000`** : Rabais, remises et ristournes accordés par l'entreprise (solde débiteur, en diminution du CA).
- **`740000`** : Subventions d'exploitation.

---

## ⚖️ Règles d'Or pour la Saisie MCP (`pennylane_create_entry`)
1. **Équilibre mathématique** : `Total Débit == Total Crédit`. Le serveur rejettera toute écriture déséquilibrée.
2. **Dates dans un exercice ouvert** : Vérifier avec `pennylane_list_fiscal_years` avant d'écrire.
3. **Journal approprié** :
   - `VE` pour les ventes (crédit classe 7, crédit 44571, débit 411).
   - `HA` pour les achats (débit classe 6, débit 44566, crédit 401).
   - `BQ` pour la banque (mouvements sur 512).
   - `OD` pour les salaires, TVA et corrections.
