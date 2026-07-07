# 🗺️ Guide Synoptique des Workflows et Commandes Slash MCP

Le serveur Pennylane MCP intègre **8 workflows guidés (prompts MCP)** conçus comme des assistants métiers spécialisés pour les cabinets d'expertise comptable. L'assistant IA (Claude) doit s'appuyer sur ce guide pour suggérer proactivement le bon workflow au bon moment à l'utilisateur.

---

## 📅 Workflows Périodiques & Clôture

### 1. `/audit_cloture_mensuelle` (Audit Clôture Mensuelle / Annuelle)
- **Quand le suggérer ?** : Lors de la préparation des clôtures mensuelles, trimestrielles ou de la révision annuelle avant bilan.
- **Ce qu'il fait** : Vérifie l'équilibre de la balance, contrôle l'absence de solde créditeur en caisse (`530`), pointe la trésorerie (`512`), vérifie les comptes d'attente (`471`/`472`), et attribue une note de santé comptable (/10) avec un plan d'action.

### 2. `/verification_conformite_fec_tva` (Conformité FEC & TVA)
- **Quand le suggérer ?** : Avant l'export d'un Fichier des Écritures Comptables (FEC) légal ou lors de la préparation de la déclaration de TVA (CA3/CA12).
- **Ce qu'il fait** : Vérifie que l'exercice est bien clôturé/gelé (conformité LPF Art. A47 A-1), réalise le cadrage de TVA (rapprochement base 70x et taxe 44571), et valide l'équilibre mathématique.

---

## 💰 Trésorerie, Rapprochement & Impayés

### 3. `/rapprochement_bancaire_ia` (Rapprochement Bancaire IA)
- **Quand le suggérer ?** : Lorsqu'il y a des transactions bancaires non réconciliées, des relevés bancaires en attente ou un lettrage en retard.
- **Ce qu'il fait** : Analyse les mouvements bancaires non associés, croise avec les factures clients/fournisseurs impayées, attribue un score de confiance de matching et propose le lettrage automatique ou la création de règles d'imputation.

### 4. `/relance_impayes_clients` (Relance des Impayés Clients)
- **Quand le suggérer ?** : Lorsque le compte client (`411`) présente un solde débiteur élevé, ou sur demande de suivi du poste clients.
- **Ce qu'il fait** : Identifie les créances en retard (> 30 jours), calcule l'encours par tiers, classe le risque de recouvrement et rédige les projets d'emails de relance (amiable, ferme, mise en demeure).

---

## 📈 Analyse Commerciale & Rentabilité

### 5. `/synthese_chiffre_affaires` (Synthèse Chiffre d'Affaires)
- **Quand le suggérer ?** : Lors des rendez-vous bilan, pour un reporting de direction ou une analyse commerciale.
- **Ce qu'il fait** : Isole la classe 7, ventile le CA par nature d'activité (`701`, `706`, `707`), analyse la dynamique commerciale avec les devis en cours et rédige un commentaire de gestion DAF.

### 6. `/audit_analytique_rentabilite` (Audit Analytique & Rentabilité)
- **Quand le suggérer ?** : Pour évaluer la rentabilité d'un projet, d'une agence ou vérifier la bonne tenue de la comptabilité analytique.
- **Ce qu'il fait** : Cartographie les axes analytiques, mesure le taux de couverture analytique des charges/produits, et établit un compte de résultat (marge contributive) par centre de profit.

---

## 🏛️ Supervision Multi-Dossiers & Réforme Facturation

### 7. `/comparatif_multi_dossiers` (Comparatif Multi-Dossiers)
- **Quand le suggérer ?** : Pour un associé de cabinet souhaitant piloter son portefeuille ou faire un benchmark global.
- **Ce qu'il fait** : Lance une requête parallèle (`multi_dossier_query`) sur tous les dossiers clients configurés dans `dossiers.json`, compare le CA, les charges, le REX et la trésorerie dans un tableau synoptique et met en exergue les dossiers en alerte rouge.

### 8. `/diagnostic_facturation_electronique` (Diagnostic E-Invoicing)
- **Quand le suggérer ?** : Pour préparer un client à l'obligation de la facturation électronique (réforme E-Invoicing / PA & PPF).
- **Ce qu'il fait** : Audit la présence des SIRET et numéros de TVA sur la société et sur 100% des clients/fournisseurs B2B, interroge l'annuaire officiel des Plateformes Agréées (`check_pa_registration`) et délivre une feuille de route de mise en conformité.
