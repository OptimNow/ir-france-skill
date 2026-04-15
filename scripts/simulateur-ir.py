#!/usr/bin/env python3
"""
Simulateur d'Impôt sur le Revenu -- France
Revenus 2025 (déclaration 2026)

Usage:
    python simulateur-ir.py

Ce script est conçu pour être exécuté par Claude dans le cadre de la skill ir-france.
Claude doit adapter les paramètres en fonction du contexte de l'utilisateur avant exécution.

IMPORTANT: Les barèmes et seuils ci-dessous sont indicatifs et basés sur les projections
de la loi de finances 2026 pour les revenus 2025. Vérifier les montants exacts via
le fichier references/bareme-et-seuils.md ou via web search.
"""

from dataclasses import dataclass, field
from typing import Optional


# ============================================================
# PARAMETRES ANNUELS (à mettre à jour chaque année)
# ============================================================

# Barème progressif (borne supérieure, taux marginal)
BAREME_IR = [
    (11_497, 0.00),
    (29_315, 0.11),
    (83_823, 0.30),
    (180_294, 0.41),
    (float("inf"), 0.45),
]

# Décote
DECOTE_SEUIL_CELIBATAIRE = 1_929
DECOTE_SEUIL_COUPLE = 3_191
DECOTE_COEFF_CELIBATAIRE = 873
DECOTE_COEFF_COUPLE = 1_444
DECOTE_TAUX = 0.4525

# Quotient familial
PLAFOND_AVANTAGE_QF_PAR_DEMI_PART = 1_791

# PFU
TAUX_PFU_IR = 0.128
TAUX_PS = 0.172
TAUX_PFU_GLOBAL = 0.30

# Prélèvements sociaux patrimoine
TAUX_CSG = 0.092
TAUX_CRDS = 0.005
TAUX_PRELEVEMENT_SOLIDARITE = 0.075
TAUX_CSG_DEDUCTIBLE = 0.068

# CEHR
CEHR_TRANCHES_CELIBATAIRE = [
    (250_000, 0.00),
    (500_000, 0.03),
    (float("inf"), 0.04),
]
CEHR_TRANCHES_COUPLE = [
    (500_000, 0.00),
    (1_000_000, 0.03),
    (float("inf"), 0.04),
]

# Abattements micro
ABATTEMENT_MICRO_BNC = 0.34
ABATTEMENT_MICRO_BIC_SERVICES = 0.50
ABATTEMENT_MICRO_BIC_VENTES = 0.71
ABATTEMENT_MICRO_FONCIER = 0.30
ABATTEMENT_MINIMUM = 305

# Abattement salaires
ABATTEMENT_SALAIRES_TAUX = 0.10
ABATTEMENT_SALAIRES_MIN = 504
ABATTEMENT_SALAIRES_MAX = 14_426

# Abattement dividendes (option barème)
ABATTEMENT_DIVIDENDES = 0.40


# ============================================================
# STRUCTURES DE DONNEES
# ============================================================

@dataclass
class SituationFamiliale:
    """Situation familiale du foyer fiscal."""
    statut: str = "celibataire"  # celibataire, marie, pacse, divorce, veuf
    nombre_parts: float = 1.0
    parent_isole: bool = False


@dataclass
class RevenusSalaires:
    """Revenus salariaux."""
    net_imposable: float = 0.0
    frais_reels: Optional[float] = None  # None = abattement 10%, sinon montant


@dataclass
class RevenusBNC:
    """Revenus BNC."""
    regime: str = "micro"  # micro ou reel
    recettes_brutes: float = 0.0  # si micro
    benefice_net: float = 0.0  # si réel


@dataclass
class RevenusBIC:
    """Revenus BIC."""
    regime: str = "micro"  # micro ou reel
    type_activite: str = "services"  # services ou ventes
    ca_brut: float = 0.0  # si micro
    benefice_net: float = 0.0  # si réel


@dataclass
class RevenusCapitaux:
    """Revenus de capitaux mobiliers."""
    dividendes_bruts: float = 0.0
    interets_bruts: float = 0.0
    pv_mobilieres: float = 0.0  # plus-value nette
    mv_mobilieres: float = 0.0  # moins-value nette (positif)
    pv_crypto: float = 0.0
    acompte_pfu_verse: float = 0.0  # acompte déjà prélevé à la source


@dataclass
class RevenusFonciers:
    """Revenus fonciers."""
    regime: str = "micro"  # micro ou reel
    revenus_bruts: float = 0.0  # si micro
    benefice_foncier: float = 0.0  # si réel
    deficit_foncier: float = 0.0  # si réel


@dataclass
class ChargesDeductibles:
    """Charges déductibles du revenu global."""
    versements_per: float = 0.0
    pensions_alimentaires: float = 0.0
    csg_deductible: float = 0.0  # calculé automatiquement si option barème


@dataclass
class ReductionsCredits:
    """Réductions et crédits d'impôt."""
    dons_66: float = 0.0  # montant des dons (pas la réduction)
    dons_75: float = 0.0
    emploi_domicile: float = 0.0  # dépenses (pas le crédit)
    garde_enfants: float = 0.0
    investissement_pme: float = 0.0
    frais_scolarite: float = 0.0  # montant de la réduction directement
    autres_reductions: float = 0.0
    autres_credits: float = 0.0


@dataclass
class FoyerFiscal:
    """Ensemble des données du foyer fiscal."""
    situation: SituationFamiliale = field(default_factory=SituationFamiliale)
    salaires: RevenusSalaires = field(default_factory=RevenusSalaires)
    bnc: RevenusBNC = field(default_factory=RevenusBNC)
    bic: RevenusBIC = field(default_factory=RevenusBIC)
    capitaux: RevenusCapitaux = field(default_factory=RevenusCapitaux)
    fonciers: RevenusFonciers = field(default_factory=RevenusFonciers)
    charges: ChargesDeductibles = field(default_factory=ChargesDeductibles)
    reductions: ReductionsCredits = field(default_factory=ReductionsCredits)


# ============================================================
# FONCTIONS DE CALCUL
# ============================================================

def calcul_abattement_salaires(net_imposable: float, frais_reels: Optional[float]) -> float:
    """Calcule le revenu net de salaires après abattement ou frais réels."""
    if frais_reels is not None:
        return max(0, net_imposable - frais_reels)
    abattement = net_imposable * ABATTEMENT_SALAIRES_TAUX
    abattement = max(ABATTEMENT_SALAIRES_MIN, min(abattement, ABATTEMENT_SALAIRES_MAX))
    return max(0, net_imposable - abattement)


def calcul_revenu_bnc(bnc: RevenusBNC) -> float:
    """Calcule le revenu BNC imposable."""
    if bnc.regime == "micro":
        abattement = max(ABATTEMENT_MINIMUM, bnc.recettes_brutes * ABATTEMENT_MICRO_BNC)
        return max(0, bnc.recettes_brutes - abattement)
    return max(0, bnc.benefice_net)


def calcul_revenu_bic(bic: RevenusBIC) -> float:
    """Calcule le revenu BIC imposable."""
    if bic.regime == "micro":
        taux = ABATTEMENT_MICRO_BIC_VENTES if bic.type_activite == "ventes" else ABATTEMENT_MICRO_BIC_SERVICES
        abattement = max(ABATTEMENT_MINIMUM, bic.ca_brut * taux)
        return max(0, bic.ca_brut - abattement)
    return max(0, bic.benefice_net)


def calcul_revenu_foncier(fonciers: RevenusFonciers) -> float:
    """Calcule le revenu foncier imposable (peut être négatif si déficit)."""
    if fonciers.regime == "micro":
        abattement = fonciers.revenus_bruts * ABATTEMENT_MICRO_FONCIER
        return max(0, fonciers.revenus_bruts - abattement)
    return fonciers.benefice_foncier - fonciers.deficit_foncier


def calcul_ir_bareme(revenu_imposable_par_part: float) -> float:
    """Calcule l'IR brut pour UNE part selon le barème progressif."""
    ir = 0.0
    borne_precedente = 0
    for borne, taux in BAREME_IR:
        if revenu_imposable_par_part <= borne:
            ir += (revenu_imposable_par_part - borne_precedente) * taux
            break
        else:
            ir += (borne - borne_precedente) * taux
            borne_precedente = borne
    return ir


def calcul_decote(ir_brut: float, est_couple: bool) -> float:
    """Calcule la décote."""
    seuil = DECOTE_SEUIL_COUPLE if est_couple else DECOTE_SEUIL_CELIBATAIRE
    coeff = DECOTE_COEFF_COUPLE if est_couple else DECOTE_COEFF_CELIBATAIRE

    if ir_brut >= seuil:
        return 0.0

    decote = coeff - ir_brut * DECOTE_TAUX
    return max(0, min(decote, ir_brut))


def calcul_cehr(rfr: float, est_couple: bool) -> float:
    """Calcule la contribution exceptionnelle sur les hauts revenus."""
    tranches = CEHR_TRANCHES_COUPLE if est_couple else CEHR_TRANCHES_CELIBATAIRE
    cehr = 0.0
    borne_precedente = 0
    for borne, taux in tranches:
        if rfr <= borne:
            cehr += (rfr - borne_precedente) * taux
            break
        else:
            cehr += (borne - borne_precedente) * taux
            borne_precedente = borne
    return cehr


def calcul_plafonnement_qf(ir_sans_qf: float, ir_avec_qf: float,
                            parts: float, est_couple: bool) -> float:
    """Applique le plafonnement du quotient familial."""
    parts_base = 2.0 if est_couple else 1.0
    demi_parts_sup = (parts - parts_base) * 2  # nombre de demi-parts supplémentaires
    if demi_parts_sup <= 0:
        return ir_avec_qf

    plafond_avantage = demi_parts_sup * PLAFOND_AVANTAGE_QF_PAR_DEMI_PART
    avantage_qf = ir_sans_qf - ir_avec_qf

    if avantage_qf > plafond_avantage:
        return ir_sans_qf - plafond_avantage
    return ir_avec_qf


def simuler_ir(foyer: FoyerFiscal, option_bareme: bool = False) -> dict:
    """
    Simule le montant d'IR pour un foyer fiscal.

    Args:
        foyer: données du foyer
        option_bareme: True = option barème pour les revenus de capitaux, False = PFU

    Returns:
        dict avec le détail du calcul
    """
    est_couple = foyer.situation.statut in ("marie", "pacse")
    parts = foyer.situation.nombre_parts

    # --- Revenus catégoriels ---
    rev_salaires = calcul_abattement_salaires(
        foyer.salaires.net_imposable, foyer.salaires.frais_reels
    )
    rev_bnc = calcul_revenu_bnc(foyer.bnc)
    rev_bic = calcul_revenu_bic(foyer.bic)
    rev_foncier = calcul_revenu_foncier(foyer.fonciers)

    # Déficit foncier imputable sur revenu global (max 10 700 EUR)
    deficit_imputable = 0
    if rev_foncier < 0:
        deficit_imputable = min(abs(rev_foncier), 10_700)
        rev_foncier = 0

    # --- Revenus de capitaux ---
    dividendes = foyer.capitaux.dividendes_bruts
    interets = foyer.capitaux.interets_bruts
    pv_mob = max(0, foyer.capitaux.pv_mobilieres - foyer.capitaux.mv_mobilieres)
    pv_crypto = foyer.capitaux.pv_crypto

    ir_pfu = 0.0
    ps_capitaux = 0.0
    rev_capitaux_bareme = 0.0
    csg_deductible_capitaux = 0.0

    if option_bareme:
        # Dividendes avec abattement 40%
        div_imposable = dividendes * (1 - ABATTEMENT_DIVIDENDES)
        int_imposable = interets
        rev_capitaux_bareme = div_imposable + int_imposable + pv_mob + pv_crypto
        # PS sur totalité brute
        ps_capitaux = (dividendes + interets + pv_mob + pv_crypto) * TAUX_PS
        # CSG déductible
        csg_deductible_capitaux = (dividendes + interets + pv_mob + pv_crypto) * TAUX_CSG_DEDUCTIBLE
    else:
        # PFU : IR forfaitaire + PS
        total_capitaux = dividendes + interets + pv_mob + pv_crypto
        ir_pfu = total_capitaux * TAUX_PFU_IR
        ps_capitaux = total_capitaux * TAUX_PS

    # --- Revenu brut global ---
    revenu_brut_global = (
        rev_salaires + rev_bnc + rev_bic + max(0, rev_foncier) + rev_capitaux_bareme
    )

    # --- Charges déductibles ---
    total_charges = (
        foyer.charges.versements_per
        + foyer.charges.pensions_alimentaires
        + csg_deductible_capitaux
        + deficit_imputable
    )

    # --- Revenu net imposable ---
    revenu_net_imposable = max(0, revenu_brut_global - total_charges)

    # --- Calcul IR barème ---
    revenu_par_part = revenu_net_imposable / parts
    ir_par_part = calcul_ir_bareme(revenu_par_part)
    ir_brut = ir_par_part * parts

    # Plafonnement QF
    if parts > (2.0 if est_couple else 1.0):
        parts_base = 2.0 if est_couple else 1.0
        revenu_par_part_base = revenu_net_imposable / parts_base
        ir_sans_qf = calcul_ir_bareme(revenu_par_part_base) * parts_base
        ir_brut = calcul_plafonnement_qf(ir_sans_qf, ir_brut, parts, est_couple)

    # Décote
    decote = calcul_decote(ir_brut, est_couple)
    ir_apres_decote = max(0, ir_brut - decote)

    # --- Réductions d'impôt ---
    red_dons_66 = foyer.reductions.dons_66 * 0.66
    red_dons_75 = min(foyer.reductions.dons_75, 1_000) * 0.75
    red_pme = foyer.reductions.investissement_pme * 0.25
    total_reductions = (
        red_dons_66 + red_dons_75 + red_pme
        + foyer.reductions.frais_scolarite
        + foyer.reductions.autres_reductions
    )

    ir_apres_reductions = max(0, ir_apres_decote - total_reductions)

    # --- Crédits d'impôt ---
    credit_domicile = min(foyer.reductions.emploi_domicile, 12_000) * 0.50
    credit_garde = min(foyer.reductions.garde_enfants, 3_500) * 0.50
    total_credits = (
        credit_domicile + credit_garde + foyer.reductions.autres_credits
    )

    ir_net = max(0, ir_apres_reductions - total_credits)

    # Plafonnement niches fiscales (simplifié)
    total_niches = total_reductions + total_credits - red_dons_66 - red_dons_75
    plafond_niches = 10_000
    if total_niches > plafond_niches:
        depassement = total_niches - plafond_niches
        ir_net += depassement

    # Ajouter l'IR PFU si applicable
    ir_total = ir_net + ir_pfu

    # CEHR
    rfr = revenu_net_imposable + (
        (dividendes + interets + pv_mob + pv_crypto) if not option_bareme else 0
    )
    cehr = calcul_cehr(rfr, est_couple)

    # --- PS sur revenus fonciers ---
    rev_foncier_pour_ps = 0
    if foyer.fonciers.regime == "micro":
        rev_foncier_pour_ps = foyer.fonciers.revenus_bruts * (1 - ABATTEMENT_MICRO_FONCIER)
    else:
        rev_foncier_pour_ps = max(0, foyer.fonciers.benefice_foncier - foyer.fonciers.deficit_foncier)
    ps_foncier = rev_foncier_pour_ps * TAUX_PS

    # --- Total ---
    total_impot = ir_total + cehr + ps_capitaux + ps_foncier
    acomptes_verses = foyer.capitaux.acompte_pfu_verse
    reste_a_payer = total_impot - acomptes_verses

    # TMI
    tmi = 0
    for borne, taux in BAREME_IR:
        if revenu_par_part <= borne:
            tmi = taux
            break

    return {
        "regime": "Option barème" if option_bareme else "PFU (flat tax)",
        "situation": {
            "statut": foyer.situation.statut,
            "parts": parts,
        },
        "revenus": {
            "salaires_net": rev_salaires,
            "bnc": rev_bnc,
            "bic": rev_bic,
            "foncier": max(0, rev_foncier),
            "capitaux_au_bareme": rev_capitaux_bareme,
            "total_brut_global": revenu_brut_global,
        },
        "charges_deductibles": {
            "per": foyer.charges.versements_per,
            "pensions": foyer.charges.pensions_alimentaires,
            "csg_deductible": round(csg_deductible_capitaux, 2),
            "deficit_foncier": deficit_imputable,
            "total": round(total_charges, 2),
        },
        "revenu_net_imposable": round(revenu_net_imposable, 2),
        "tmi": f"{int(tmi * 100)} %",
        "ir_detail": {
            "ir_brut_bareme": round(ir_brut, 2),
            "decote": round(decote, 2),
            "ir_apres_decote": round(ir_apres_decote, 2),
            "reductions": round(total_reductions, 2),
            "credits": round(total_credits, 2),
            "ir_net_bareme": round(ir_net, 2),
            "ir_pfu": round(ir_pfu, 2),
            "ir_total": round(ir_total, 2),
        },
        "cehr": round(cehr, 2),
        "prelevements_sociaux": {
            "ps_capitaux": round(ps_capitaux, 2),
            "ps_foncier": round(ps_foncier, 2),
            "total_ps": round(ps_capitaux + ps_foncier, 2),
        },
        "total_impot": round(total_impot, 2),
        "acomptes_verses": round(acomptes_verses, 2),
        "reste_a_payer": round(reste_a_payer, 2),
        "rfr_estime": round(rfr, 2),
    }


def comparer_pfu_bareme(foyer: FoyerFiscal) -> dict:
    """Compare PFU et option barème et recommande le meilleur choix."""
    resultat_pfu = simuler_ir(foyer, option_bareme=False)
    resultat_bareme = simuler_ir(foyer, option_bareme=True)

    diff = resultat_pfu["total_impot"] - resultat_bareme["total_impot"]

    return {
        "pfu": resultat_pfu,
        "bareme": resultat_bareme,
        "difference": round(diff, 2),
        "recommandation": (
            "Option barème plus avantageuse"
            if diff > 0
            else "PFU plus avantageux" if diff < 0
            else "Équivalent"
        ),
        "economie": round(abs(diff), 2),
    }


def afficher_resultat(resultat: dict) -> None:
    """Affiche le résultat de la simulation de manière lisible."""
    print(f"\n{'='*60}")
    print(f"  SIMULATION IR -- {resultat['regime']}")
    print(f"{'='*60}")
    print(f"  Statut: {resultat['situation']['statut']} | Parts: {resultat['situation']['parts']}")
    print(f"{'─'*60}")

    rev = resultat["revenus"]
    print(f"  Revenus:")
    if rev["salaires_net"]: print(f"    Salaires (net)        : {rev['salaires_net']:>12,.2f} EUR")
    if rev["bnc"]: print(f"    BNC                   : {rev['bnc']:>12,.2f} EUR")
    if rev["bic"]: print(f"    BIC                   : {rev['bic']:>12,.2f} EUR")
    if rev["foncier"]: print(f"    Foncier               : {rev['foncier']:>12,.2f} EUR")
    if rev["capitaux_au_bareme"]: print(f"    Capitaux (barème)     : {rev['capitaux_au_bareme']:>12,.2f} EUR")
    print(f"    Total brut global     : {rev['total_brut_global']:>12,.2f} EUR")

    ch = resultat["charges_deductibles"]
    if ch["total"] > 0:
        print(f"{'─'*60}")
        print(f"  Charges déductibles     : {ch['total']:>12,.2f} EUR")

    print(f"{'─'*60}")
    print(f"  Revenu net imposable    : {resultat['revenu_net_imposable']:>12,.2f} EUR")
    print(f"  TMI                     : {resultat['tmi']:>12}")

    ir = resultat["ir_detail"]
    print(f"{'─'*60}")
    print(f"  IR brut (barème)        : {ir['ir_brut_bareme']:>12,.2f} EUR")
    if ir["decote"]: print(f"  Décote                  : {ir['decote']:>12,.2f} EUR")
    if ir["reductions"]: print(f"  Réductions              : {ir['reductions']:>12,.2f} EUR")
    if ir["credits"]: print(f"  Crédits d'impôt         : {ir['credits']:>12,.2f} EUR")
    if ir["ir_pfu"]: print(f"  IR PFU (capitaux)       : {ir['ir_pfu']:>12,.2f} EUR")
    print(f"  IR total                : {ir['ir_total']:>12,.2f} EUR")

    if resultat["cehr"]:
        print(f"  CEHR                    : {resultat['cehr']:>12,.2f} EUR")

    ps = resultat["prelevements_sociaux"]
    if ps["total_ps"]:
        print(f"  Prélèvements sociaux    : {ps['total_ps']:>12,.2f} EUR")

    print(f"{'='*60}")
    print(f"  TOTAL IMPOT             : {resultat['total_impot']:>12,.2f} EUR")
    if resultat["acomptes_verses"]:
        print(f"  Acomptes déjà versés    : {resultat['acomptes_verses']:>12,.2f} EUR")
        print(f"  RESTE A PAYER           : {resultat['reste_a_payer']:>12,.2f} EUR")
    print(f"  RFR estimé              : {resultat['rfr_estime']:>12,.2f} EUR")
    print(f"{'='*60}\n")


# ============================================================
# EXEMPLE D'UTILISATION
# ============================================================

if __name__ == "__main__":
    # Exemple : célibataire, freelance BNC micro + dividendes + crypto
    foyer = FoyerFiscal(
        situation=SituationFamiliale(statut="celibataire", nombre_parts=1.0),
        bnc=RevenusBNC(regime="micro", recettes_brutes=60_000),
        capitaux=RevenusCapitaux(
            dividendes_bruts=5_000,
            interets_bruts=1_000,
            pv_crypto=3_000,
            acompte_pfu_verse=2_700,
        ),
        charges=ChargesDeductibles(versements_per=4_000),
        reductions=ReductionsCredits(dons_66=500),
    )

    print("\n>>> Comparaison PFU vs Option barème <<<")
    comparaison = comparer_pfu_bareme(foyer)

    afficher_resultat(comparaison["pfu"])
    afficher_resultat(comparaison["bareme"])

    print(f"{'='*60}")
    print(f"  RECOMMANDATION : {comparaison['recommandation']}")
    print(f"  Économie       : {comparaison['economie']:,.2f} EUR")
    print(f"{'='*60}")
