# Workflow MCP : Diagnostic Préparatoire à la Facturation Électronique (E-Invoicing)

Ce workflow guide l'assistant IA (Claude) pour réaliser un diagnostic d'éligibilité et de conformité du dossier client face à la réforme de la facturation électronique (Plateforme Agréée PA / Portail Public de Facturation PPF / formats Factur-X, UBL, CII).

## 📋 Instructions d'exécution étape par étape

### Étape 1 : Vérification de la fiche société du dossier
- Appelle `pennylane_current_dossier` et `pennylane_whoami` pour vérifier les informations de l'entreprise (numéro de SIRET/SIREN, numéro de TVA intracommunautaire, adresse légale).
- Un numéro SIRET valide et un numéro de TVA sont **obligatoires** pour l'échanges de factures électroniques (e-invoicing et e-reporting). Si ces champs manquent, avertis immédiatement l'utilisateur.

### Étape 2 : Interrogation de l'annuaire officiel Plateforme Agréée (PA)
- Utilise l'outil `pennylane_check_pa_registration` avec le SIREN ou le SIRET de la société pour interroger l'annuaire PPF / PA.
- Vérifie si l'entreprise est déjà enregistrée sur une Plateforme Agréée (PA) partenaire ou si elle doit finaliser son enrôlement.

### Étape 3 : Audit de conformité des référentiels Tiers (Clients & Fournisseurs)
Pour garantir la bonne transmission sans rejet des futures factures électroniques :
1. **Audit Clients (`411`)** : Appelle `pennylane_list_customers` (avec limit=50). Vérifie pour les clients professionnels (B2B) la présence systématique de :
   - Numéro de SIRET (14 chiffres) ou SIREN (9 chiffres).
   - Numéro de TVA intracommunautaire (ex: `FRXX999999999`).
   - Adresse de facturation complète (rue, code postal, ville, pays).
2. **Audit Fournisseurs (`401`)** : Appelle `pennylane_list_suppliers` (limit=50). Vérifie que les fournisseurs réguliers disposent d'un identifiant légal propre.
3. *Alerte e-reporting* : Si des clients sont des particuliers (B2C) ou des clients étrangers (hors France / hors UE), rappelle qu'ils relèveront du flux **e-reporting** (transmission des données de transaction sans facture électronique normalisée).

### Étape 4 : Évaluation de la préparation aux formats structurés (Factur-X / UBL / CII)
- Appelle `pennylane_list_customer_invoices` (limit=20) pour vérifier le format des factures récemment émises.
- Rappelle que grâce aux outils Pennylane MCP, l'émission (`pennylane_send_customer_invoice_to_pa`) et la réception (`pennylane_import_supplier_einvoice`, `pennylane_import_customer_einvoice`) au format Factur-X sont nativement prises en charge.

### Étape 5 : Restitution au format Markdown structuré
Présente un rapport de diagnostic complet avec un score de préparation :

1. **Score d'éligibilité E-Invoicing** (sur 100%) :
   - 100% : SIRET/TVA société présents + 100% des clients/fournisseurs B2B avec SIRET/TVA validés.
   - Pénalité de -10% pour chaque information légale manquante sur le top 5 des clients/fournisseurs.

2. **Tableau des Tiers à régulariser en priorité** :
   | Type de Tiers | Nom / Raison Sociale | SIRET présent ? | N° TVA présent ? | Adresse complète ? | Action requise |
   |---|---|---|---|---|---|
   | Client B2B | SAS Gamma | ❌ Manquant | ✅ FR44556677889 | ✅ Oui | Mettre à jour via `pennylane_update_customer` |
   | Fournisseur | Papeterie Bureau | ✅ 12345678900012 | ❌ Manquant | ❌ Code postal | Compléter la fiche fournisseur |

3. **Feuille de route E-Invoicing pour le cabinet** :
   - Étape 1 : Compléter les SIRET manquants dans le référentiel clients avant la date butoir légale.
   - Étape 2 : Activer la connexion Plateforme Agréée via les paramètres Pennylane.
   - Étape 3 : Former les collaborateurs à l'import de flux Factur-X via `pennylane_import_supplier_einvoice`.
