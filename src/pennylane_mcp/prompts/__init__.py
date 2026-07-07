"""Prompts MCP : workflows guidés et commandes slash pour Claude Desktop / Claude UI.

Cette architecture modulaire charge dynamiquement le contenu des prompts
depuis les fichiers Markdown (.md) séparés situés dans ce répertoire.
"""

from __future__ import annotations

from pathlib import Path
from mcp.server.fastmcp import FastMCP

_PROMPTS_DIR = Path(__file__).parent


def _load_prompt(filename: str) -> str:
    """Charge le contenu d'un fichier prompt Markdown (.md)."""
    file_path = _PROMPTS_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Fichier prompt introuvable : {file_path}")
    return file_path.read_text(encoding="utf-8").strip()


def register(mcp: FastMCP) -> None:
    """Enregistre tous les prompts MCP pour Claude depuis les fichiers .md."""

    @mcp.prompt(
        "relance_impayes_clients",
        title="Relance des Impayés Clients",
        description="Workflow : Analyse des créances clients en retard et rédaction de relances professionnelles et adaptées.",
    )
    def relance_impayes(jours_retard_min: int = 30, client_prefix: str = "") -> str:
        """Workflow : Analyse des créances clients en retard et rédaction de relances."""
        base_md = _load_prompt("relance_impayes_clients.md")
        params_info = f"> **Paramètres choisis pour l'analyse** : Retard minimal = **{jours_retard_min} jours**"
        if client_prefix:
            params_info += f" | Filtre client = **'{client_prefix}'**"
        return f"{params_info}\n\n{base_md}"

    @mcp.prompt(
        "audit_cloture_mensuelle",
        title="Audit Clôture Mensuelle",
        description="Workflow : Audit de cohérence pour la clôture mensuelle (TVA, rapprochement bancaire, comptes d'attente).",
    )
    def audit_cloture(exercice: str = "exercice en cours", verifier_tva: bool = True) -> str:
        """Workflow : Audit de cohérence pour la clôture mensuelle du dossier en cours."""
        base_md = _load_prompt("audit_cloture_mensuelle.md")
        params_info = f"> **Paramètres d'audit** : Période / Exercice = **{exercice}** | Vérification TVA = **{'Oui' if verifier_tva else 'Non'}**"
        return f"{params_info}\n\n{base_md}"

    @mcp.prompt(
        "synthese_chiffre_affaires",
        title="Synthèse Chiffre d'Affaires",
        description="Workflow : Analyse et ventilation du Chiffre d'Affaires sur la période sélectionnée.",
    )
    def synthese_ca(periode: str = "30 derniers jours", comparaison_annuelle: bool = False) -> str:
        """Workflow : Analyse et ventilation du Chiffre d'Affaires sur la période."""
        base_md = _load_prompt("synthese_chiffre_affaires.md")
        params_info = f"> **Paramètres d'analyse CA** : Période = **{periode}** | Comparaison N-1 = **{'Active' if comparaison_annuelle else 'Désactivée'}**"
        return f"{params_info}\n\n{base_md}"

    @mcp.prompt(
        "comparatif_multi_dossiers",
        title="Comparatif Multi-Dossiers",
        description="Workflow : Comparaison comparative de la balance et de l'état des comptes entre tous les dossiers configurés.",
    )
    def comparatif_dossiers(seuil_alertes: str = "normal", inclure_details: bool = False) -> str:
        """Workflow : Comparaison comparative de la balance entre tous les dossiers clients configurés."""
        base_md = _load_prompt("comparatif_multi_dossiers.md")
        params_info = f"> **Paramètres comparatifs** : Niveau d'alerte = **{seuil_alertes}** | Inclure détails des écritures = **{'Oui' if inclure_details else 'Non'}**"
        return f"{params_info}\n\n{base_md}"

    @mcp.prompt(
        "rapprochement_bancaire_ia",
        title="Rapprochement Bancaire IA",
        description="Workflow : Audit des transactions non réconciliées, matching intelligent avec les factures et lettrage.",
    )
    def rapprochement_bancaire(seuil_confiance: int = 80, inclure_regles_recurrentes: bool = True) -> str:
        """Workflow : Audit et matching intelligent pour la réconciliation bancaire."""
        base_md = _load_prompt("rapprochement_bancaire_ia.md")
        params_info = f"> **Paramètres de rapprochement** : Seuil de confiance minimal = **{seuil_confiance}%** | Analyse des règles récurrentes = **{'Active' if inclure_regles_recurrentes else 'Désactivée'}**"
        return f"{params_info}\n\n{base_md}"

    @mcp.prompt(
        "diagnostic_facturation_electronique",
        title="Diagnostic Facturation Électronique (E-Invoicing)",
        description="Workflow : Audit d'éligibilité et de conformité SIRET/TVA des clients et fournisseurs face à la réforme.",
    )
    def diagnostic_einvoicing(verifier_annuaire_pa: bool = True, seuil_top_tiers: int = 20) -> str:
        """Workflow : Audit d'éligibilité et de préparation à la réforme de la facturation électronique."""
        base_md = _load_prompt("diagnostic_facturation_electronique.md")
        params_info = f"> **Paramètres de diagnostic E-Invoicing** : Interrogation annuaire PA/PPF = **{'Oui' if verifier_annuaire_pa else 'Non'}** | Analyse Top Tiers = **Top {seuil_top_tiers}**"
        return f"{params_info}\n\n{base_md}"

    @mcp.prompt(
        "audit_analytique_rentabilite",
        title="Audit Analytique & Rentabilité",
        description="Workflow : Cartographie des axes analytiques, audit du lettrage analytique et calcul de marge par projet.",
    )
    def audit_analytique(axe_prioritaire: str = "tous", inclure_non_ventiles: bool = True) -> str:
        """Workflow : Audit analytique et calcul de rentabilité par centre de profit / projet."""
        base_md = _load_prompt("audit_analytique_rentabilite.md")
        params_info = f"> **Paramètres analytiques** : Axe prioritaire = **'{axe_prioritaire}'** | Inclure charges générales / non ventilées = **{'Oui' if inclure_non_ventiles else 'Non'}**"
        return f"{params_info}\n\n{base_md}"

    @mcp.prompt(
        "verification_conformite_fec_tva",
        title="Vérification Conformité FEC & TVA",
        description="Workflow : Contrôle de conformité avant export FEC et cadrage de la déclaration de TVA (CA3/CA12).",
    )
    def conformite_fec_tva(type_fec: str = "definitif", controle_cadrage_tva: bool = True) -> str:
        """Workflow : Contrôle de conformité avant export officiel FEC et audit TVA."""
        base_md = _load_prompt("verification_conformite_fec_tva.md")
        params_info = f"> **Paramètres de contrôle** : Type d'export visé = **{type_fec}** | Cadrage TVA = **{'Actif' if controle_cadrage_tva else 'Désactivé'}**"
        return f"{params_info}\n\n{base_md}"

