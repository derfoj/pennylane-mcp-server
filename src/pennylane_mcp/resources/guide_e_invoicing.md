# ⚡ Guide Pratique & Normes : Réforme Facturation Électronique (E-Invoicing) dans Pennylane

Ce guide ressource permet à l'assistant IA (Claude) d'orienter les experts-comptables et leurs clients sur la mise en conformité face à la réforme de la facturation électronique (e-invoicing et e-reporting en France et en Europe).

---

## 🏛️ Architecture de la Réforme en France
1. **PPF (Portail Public de Facturation)** : Annuaires national centralisant les identifiants légaux (SIREN, SIRET, code routage) et gérant les flux e-reporting.
2. **PA (Plateforme Agréée) / PDP** : Opérateurs privés immatriculés par l'administration (comme **Pennylane**) habilités à transmettre, valider et convertir les factures électroniques en temps réel.
3. **L'Annuaire Central** : Chaque entreprise doit être identifiable par son SIRET. Sans SIRET dans l'annuaire, l'envoi d'une facture électronique échouera avec un statut de rejet (`rejected`).

---

## 📑 Formats Officiels Supportés dans Pennylane V2
Lors de l'utilisation des outils MCP d'import et d'export (`pennylane_import_supplier_einvoice`, `pennylane_import_customer_einvoice`, `pennylane_send_customer_invoice_to_pa`), les formats suivants sont reconnus :

- **Factur-X** : Standard hybride franco-allemand (PDF lisible par l'humain contenant un fichier XML structuré embarqué selon la norme EN 16931). **Format recommandé par défaut dans Pennylane.**
- **UBL (Universal Business Language)** : Format 100% XML international standardisé ISO/IEC 19845.
- **CII (Cross Industry Invoice)** : Standard XML développé par l'UN/CEFACT.

---

## 🔄 Cycle de Vie et Statuts E-Invoicing (`pennylane_get_supplier_einvoice_status`)
Le cycle de vie normalisé d'une facture électronique suit les statuts suivants :
- 🟡 **`draft`** : Brouillon en cours de rédaction dans Pennylane.
- 🔵 **`sent` / `issued`** : Émise et transmise à la Plateforme Agréée (PA) émettrice.
- 🟣 **`in_transit`** : En cours d'acheminement via le réseau d'interopérabilité vers la PA du destinataire ou le PPF.
- 🟢 **`received` / `available`** : Mise à disposition avec succès sur le portail ou le logiciel de l'acheteur.
- 🟢 **`approved`** : Approuvée par le client (bon à payer).
- 🟢 **`paid`** : Paiement rapproché et notifié à l'administration (fin du cycle e-reporting de paiement).
- 🔴 **`rejected` / `refused`** : Rejetée par le contrôle syntaxique de la plateforme ou refusée commercialement par l'acheteur. Nécessite l'émission d'une note de crédit (avoir) via `pennylane_create_customer_invoice_credit_note`.

---

## 🛠️ Outils MCP dédiés dans le serveur
- `pennylane_check_pa_registration` : Vérifier en 1 clic l'inscription d'un SIREN/SIRET sur l'annuaire PA.
- `pennylane_send_customer_invoice_to_pa` : Déclencher la transmission électronique officielle d'une facture client finalisée.
- `pennylane_import_supplier_einvoice` / `pennylane_import_customer_einvoice` : Intégrer un flux XML ou un Factur-X externe.
- `pennylane_get_supplier_einvoice_status` : Suivre la traçabilité et l'historique des statuts de traitement.
