"""
simulation/moteur.py - Moteur de microsimulation actuarielle CGU, Senegal
"""
import numpy as np
import pandas as pd

# Horizon de projection : aligne sur la Vision Senegal 2050 (2027-2050, soit 24 ans)
ANNEE_DEBUT = 2027
ANNEE_FIN   = 2050
N_ANNEES    = ANNEE_FIN - ANNEE_DEBUT + 1        # 24

# Indicateurs redistributifs AVANT reforme (EHCVM 2021-2022 ACTUALISEE en 2026,
# aging statique, taux ANSD). FGT recalcules sur la base 2026 ; Gini et depenses
# catastrophiques inchanges (l'actualisation preserve les ratios).
INDICATEURS_BASE = {
    "FGT0": 0.2332, "FGT1": 0.0505, "FGT2": 0.0172,
    "Gini": 0.3093, "CAT10": 0.0648, "CAT40": 0.0112,
}

# Indicateurs en cas de COUVERTURE UNIVERSELLE (potentiel), base 2026.
# Recalcules avec la methode du notebook 02 (fonction indices() : depense par
# tete + gain net = prestations attendues - cotisations), appliquee a 100 % de
# la population cible. L'effet monetaire sur la pauvrete est faible (les gains
# nets sont modestes) ; l'effet protecteur majeur porte sur les depenses
# catastrophiques de sante (CAT10 6,48 % -> 0,21 %). Les valeurs FGT ci-dessous
# remplacent l'ancienne calibration (FGT0 0,2065) qui etait incoherente avec la
# fonction indices() du notebook.
INDICATEURS_POTENTIEL = {
    "FGT0": 0.2318, "FGT1": 0.0502, "FGT2": 0.0171,
    "Gini": 0.3095, "CAT10": 0.0021, "CAT40": 0.0000,
}

PARAMS_REF = {
    "N0_B": 50000, "N0_A": 8000, "N0_O": 1500, "N0_Pl": 500,
    # alpha = taux d'accroissement annuel des cotisants (delta_n = alpha*(1+beta)^n)
    "alpha": 0.04, "beta": 0.01, "tau_abd": 0.0, "tau_inf": 0.02,
    "SMIG": 64223, "gamma": 0.10, "CMU_an": 7000,
    # taux_atmp = frequence annuelle d'accident (p_at) ; dur_at = duree moyenne d'ITT (jours)
    "plaf_css": 63000, "taux_atmp": 0.03, "dur_at": 30, "alloc_fam": 2600,
    "ISF": 4.0, "alloc_pre": 20250, "alloc_mat": 54000,

    # ══════════════════════════════════════════════════════════════════════
    # MODULE CGU - PARAMETRES DU DECIDEUR
    # Seuls figurent ici les parametres que l'administration fiscale detient
    # ou fixe : taux, minimums de perception, forfaits du projet de code,
    # statistiques d'enrolement (fichier DGID). Les grandeurs observees dans
    # l'enquete (chiffre d'affaires, composition sectorielle) sont des
    # constantes de donnees, definies plus bas (DONNEES_EHCVM).
    # Sources : CGI art. 134-141 ; SN_Sim_Tool VII 2025 (feuille "Impots
    # directs (2)") ; processus SenSim (02. Income Tax joint.do).
    # ══════════════════════════════════════════════════════════════════════

    # --- Regime tarifaire : 0 = code en vigueur, 1 = nouveau projet de code ---
    "regime_cgu": 0,

    # --- Taux proportionnels et minimums de perception (CGI art. 134-141) ---
    "taux_serv": 0.05,  "min_serv": 35000,   # prestataires de services
    "taux_prod": 0.02,  "min_prod": 25000,   # producteurs et revendeurs

    # --- Forfaits du projet de code (FCFA/an), tous modifiables -------------
    # Transport public de personnes
    "fft_tp_16":  130000,   # 16 places ou moins
    "fft_tp_35":  170000,   # 17 a 35 places
    "fft_tp_45":  225000,   # 36 a 45 places
    "fft_tp_46":  330000,   # 46 places ou plus
    # Transport public de marchandises
    "fft_tm_10":  190000,   # <= 10 t / 10 000 L
    "fft_tm_15":  245000,   # 10 a 15 t
    "fft_tm_24":  320000,   # 15 a 24 t
    "fft_tm_25":  415000,   # > 24 t, tracteurs
    # Commerce de detail
    "fft_cd_mag": 100000,   # magasins
    "fft_cd_bou":  50000,   # boutiques
    "fft_cd_int":  25000,   # catalogue / internet
    "fft_cd_tab":  15000,   # tabliers
    "fft_cd_amb":  10000,   # marchands ambulants
    # Artisanat
    "fft_ar_fab": 100000,   # fabrication (ebeniste, tailleur)
    "fft_ar_ali": 100000,   # alimentation (boulanger, patissier)
    "fft_ar_bat":  50000,   # batiment (plombier, electricien)
    "fft_ar_ser":  50000,   # service (coiffeur, mecanicien)
    "fft_ar_aut":  25000,   # autres (potier, horloger, boucher)

    # --- Repartition des contribuables forfaitaires par categorie -----------
    # Donnee que la DGID detient dans son fichier des contribuables.
    # Defaut : dominance du commerce de detail, coherente avec la composition
    # sectorielle de la population cible (EHCVM). Somme ramenee a 1.
    "part_fft_com": 0.65,   # commerce de detail
    "part_fft_art": 0.20,   # artisanat
    "part_fft_tp":  0.10,   # transport de personnes
    "part_fft_tm":  0.05,   # transport de marchandises

    # --- Enrolement a la CGU (statistiques DGID) ----------------------------
    "stock_cgu_0": 60000,   # contribuables CGU effectivement enroles au depart
    "g_cgu_seul":  0.03,    # croissance annuelle de l'enrolement, CGU seule
    # part des adherents au regime social non deja contribuables CGU :
    # l'effet d'attraction de la protection sociale (rendement de la
    # collaboration entre administrations sociale et fiscale)
    "part_nouveaux": 0.60,
    # taux d'actualisation du cout net de l'Etat et des gains de recettes
    "a_actu": 0.05,
    "dur_conge": 98, "taux_ipres": 0.14, "VPS0": 24.75,
    "lambda_sa": 0.50,
    "lambda_at_B": 0.40,  # 40% - calibre sur donnees EHCVM (sous-estimation revenus)
    "lambda_at_A": 0.0,
    "lambda_ma": 0.70, "lambda_pf": 0.60,
    "lambda_id": 0.30, "lambda_re_O": 0.50, "lambda_re_Pl": 0.40,
    # Profil type de l'adherent (pour simulation individuelle)
    "n_enfants": 2, "conjoint": 0,
    # Delais de carence par branche (en mois) - Convention OIT n.102 / IPRES
    # atmp:1 mois, sante:3 mois, pf:6 mois, maternite:10 mois, id:24 mois, retraite:120 mois
    "carence": {"sante": 3, "atmp": 1, "maternite": 10,
                "pf": 6, "id": 24, "retraite": 120},
}

DEMO = {
    "q_bar":  {"B": 0.003833, "A": 0.004789, "O": 0.006475, "Pl": 0.004758},
    "tau_ret":{"B": 0.028609, "A": 0.030327, "O": 0.062916, "Pl": 0.029559},
    "q_pens": {"B": 0.026,    "A": 0.024,    "O": 0.028,    "Pl": 0.025},
    "f_rep":  {"A": 0.22073,  "O": 0.13286,  "Pl": 0.07773},
}

PAQUETS = ["B", "A", "O", "Pl"]


# ══════════════════════════════════════════════════════════════════════════════
# MICRODONNEES DE LA POPULATION CIBLE CGU (EHCVM 2021-2022 actualisee 2026)
#
# Chaque ligne represente un assujetti, avec son chiffre d'affaires observe,
# son regime tarifaire deduit de sa branche d'activite (CITI, comme dans
# SenSim), la famille de forfait a laquelle il appartient dans le nouveau
# projet de code (transport, commerce de detail, artisanat), son paquet et
# son poids de sondage. C'est exactement la logique de SenSim : la CGU due
# est calculee individu par individu, jamais a partir d'une moyenne inconnue.
# ══════════════════════════════════════════════════════════════════════════════
import os
_CSV = os.path.join(os.path.dirname(__file__), "cible_cgu_2026.csv")
CIBLE_CGU = pd.read_csv(_CSV)
PAQUETS = ["B", "A", "O", "Pl"]

# Repartition observee (ponderee, base 2026)
CIBLE_TOTALE  = float(CIBLE_CGU["poids"].sum())
CIBLE_PAR_PAQUET = (CIBLE_CGU.groupby("paquet")["poids"].sum() / CIBLE_TOTALE).to_dict()


def cgu_individuelle(p):
    """CGU annuelle due par chaque assujetti de la population cible.

    Reproduit exactement la logique de SenSim (02. Income Tax joint.do) :

    - Regime en vigueur : pour chaque individu, CGU = max(taux x CA, minimum),
      ou (taux, minimum) depend du regime tarifaire (services, ciment/denrees,
      autres producteurs et revendeurs).

    - Nouveau projet de code : les acteurs relevant du transport, du commerce
      de detail ou de l'artisanat basculent sur un forfait de leur categorie
      (moyenne des paliers officiels, chacun modifiable dans les parametres).
      Les autres restent au regime proportionnel. Les activites mixtes
      identifiees basculent au regime RGUMIX (4 %).

    Retourne un vecteur (Serie) alignee sur CIBLE_CGU, en FCFA par an.
    """
    df = CIBLE_CGU
    reforme = int(p.get("regime_cgu", 0)) == 1

    # Regime proportionnel : services (RGU1) et autres producteurs (RGU3).
    # Les revendeurs de ciment/denrees (regime 2) sont assimiles au regime des
    # producteurs et revendeurs, conformement au code en vigueur.
    du_serv = np.maximum(p["taux_serv"] * df["ca"], p["min_serv"])
    du_prod = np.maximum(p["taux_prod"] * df["ca"], p["min_prod"])
    du = np.where(df["regime"] == 1, du_serv, du_prod)

    if reforme:
        # Forfait moyen de chaque famille, tel que retenu par SenSim.
        f_tp = (p["fft_tp_16"] + p["fft_tp_35"] + p["fft_tp_45"] + p["fft_tp_46"]) / 4
        f_tm = (p["fft_tm_10"] + p["fft_tm_15"] + p["fft_tm_24"] + p["fft_tm_25"]) / 4
        f_cd = (p["fft_cd_mag"] + p["fft_cd_bou"] + p["fft_cd_int"]
                + p["fft_cd_tab"] + p["fft_cd_amb"]) / 5
        f_ar = (p["fft_ar_fab"] + p["fft_ar_ali"] + p["fft_ar_bat"]
                + p["fft_ar_ser"] + p["fft_ar_aut"]) / 5
        fam = df["famille"].values
        du = np.where(fam == "TR", f_tp,
             np.where(fam == "CO", f_cd,
             np.where(fam == "AR", f_ar, du)))
    return pd.Series(du, index=df.index)


def cgu_par_paquet(p):
    """CGU annuelle moyenne (ponderee) due par un assujetti, par paquet."""
    cgu = cgu_individuelle(p)
    df = CIBLE_CGU
    return {pk: float(np.average(cgu[df["paquet"] == pk],
                                 weights=df.loc[df["paquet"] == pk, "poids"]))
            for pk in PAQUETS}


def cgu_moyenne(p):
    """CGU annuelle moyenne ponderee sur toute la population cible."""
    cgu = cgu_individuelle(p)
    return float(np.average(cgu, weights=CIBLE_CGU["poids"]))


# Table decorative des forfaits officiels, affichee dans l'onglet CGU.
FORFAITS_CGU = {
    "Transport public de personnes": {
        "16 places ou moins": ("fft_tp_16", 130000),
        "17 a 35 places":     ("fft_tp_35", 170000),
        "36 a 45 places":     ("fft_tp_45", 225000),
        "46 places ou plus":  ("fft_tp_46", 330000),
    },
    "Transport public de marchandises": {
        "10 tonnes / 10 000 L ou moins": ("fft_tm_10", 190000),
        "10 a 15 tonnes / 15 000 L":     ("fft_tm_15", 245000),
        "15 a 24 tonnes / 24 000 L":     ("fft_tm_24", 320000),
        "Plus de 24 tonnes, tracteurs":  ("fft_tm_25", 415000),
    },
    "Commerce de detail": {
        "Magasins":                    ("fft_cd_mag", 100000),
        "Boutiques":                   ("fft_cd_bou",  50000),
        "Catalogue ou site internet":  ("fft_cd_int",  25000),
        "Tabliers":                    ("fft_cd_tab",  15000),
        "Marchands ambulants":         ("fft_cd_amb",  10000),
    },
    "Artisanat": {
        "Fabrication (ebeniste, tailleur)":    ("fft_ar_fab", 100000),
        "Alimentation (boulanger, patissier)": ("fft_ar_ali", 100000),
        "Batiment (plombier, electricien)":    ("fft_ar_bat",  50000),
        "Service (coiffeur, mecanicien)":      ("fft_ar_ser",  50000),
        "Autres (potier, horloger, boucher)":  ("fft_ar_aut",  25000),
    },
}


def fusionner_params(pu):
    p = {**PARAMS_REF, **DEMO}
    if pu:
        for k, v in pu.items():
            if k in p and not isinstance(p.get(k), dict):
                p[k] = v
    return p


def calculer_cotisations(p):
    g = 1 + p["gamma"]
    pi_sa = p["CMU_an"] / 12
    n_conj = max(0, min(int(p.get("conjoint", 0)), 4))   # 0 a 4 conjoints (polygame)
    pi_sa = pi_sa * (1 + n_conj)                         # prime sante proportionnelle
    # AT/MP tarifee par esperance de sinistre : frequence x severite (barometre CSS/CIPRES)
    w_j  = p["plaf_css"] / 22                       # salaire journalier de reference
    D_at = p.get("dur_at", 30)                      # duree moyenne d'incapacite (jours)
    K_at = 0.5*w_j*min(D_at, 28) + (2/3)*w_j*max(D_at - 28, 0)   # cout moyen d'un sinistre
    pi_at = p["taux_atmp"] * K_at / 12              # prime mensuelle = p_at x K_at / 12
    n_e = min(int(p.get("n_enfants", 2)), 6)
    K_ma = (2/3)*(p["SMIG"]/30)*p["dur_conge"] + p["alloc_pre"] + p["alloc_mat"]
    pi_ma_f = (p["ISF"]/35) * K_ma / 12
    pi_pf = p["alloc_fam"] * max(n_e, 1)  # selon nombre d'enfants reel
    pi_re = p["taux_ipres"] * p["SMIG"]

    lam_at = {"B": p["lambda_at_B"], "A": p["lambda_at_A"],
               "O": p["lambda_at_A"], "Pl": p["lambda_at_A"]}
    cotis = {}
    for pk in PAQUETS:
        sa  = pi_sa * g * (1 - p["lambda_sa"])
        at  = pi_at * g * (1 - lam_at[pk])
        esa = pi_sa * g * p["lambda_sa"]
        eat = pi_at * g * lam_at[pk]
        if pk == "B":
            cotis[pk] = {"S_trav": sa+at, "S_etat": esa+eat,
                         "pi_b": pi_sa+pi_at}
            continue
        f   = p["f_rep"].get(pk, 0)
        ma  = f * pi_ma_f * g * (1 - p["lambda_ma"])
        pf  = pi_pf * g * (1 - p["lambda_pf"])
        ema = f * pi_ma_f * g * p["lambda_ma"]
        epf = pi_pf * g * p["lambda_pf"]
        if pk == "A":
            cotis[pk] = {"S_trav": sa+at+ma+pf, "S_etat": esa+eat+ema+epf,
                         "pi_b": pi_sa+pi_at+f*pi_ma_f+pi_pf}
            continue
        q    = p["q_bar"][pk]
        pi_id = q * p["SMIG"] + 0.005 * 0.5 * p["SMIG"]
        idd  = pi_id * g * (1 - p["lambda_id"])
        eid  = pi_id * g * p["lambda_id"]
        lr   = p["lambda_re_O"] if pk == "O" else p["lambda_re_Pl"]
        # Cotisation retraite proportionnelle a la cible : Platine vise 40/30, Or 30/30
        pi_re_pk = pi_re if pk == "O" else pi_re * (40/30)
        re   = pi_re_pk * g * (1 - lr)
        ere  = pi_re_pk * g * lr
        cotis[pk] = {"S_trav": sa+at+ma+pf+idd+re,
                     "S_etat": esa+eat+ema+epf+eid+ere,
                     "pi_b": pi_sa+pi_at+f*pi_ma_f+pi_pf+pi_id+pi_re_pk,
                     "pi_id": pi_id, "pi_re": pi_re_pk}
    return cotis


def simuler(params_utilisateur=None):
    p  = fusionner_params(params_utilisateur or {})
    c  = calculer_cotisations(p)
    N0 = {pk: p[f"N0_{pk}"] for pk in PAQUETS}

    rows, N, NbPens, sol_cum = [], {pk: float(N0[pk]) for pk in PAQUETS}, {"O":0.,"Pl":0.}, 0.

    # ── Module CGU : tarifs et cumuls actualises ─────────────────────────────
    CGU_PK  = cgu_par_paquet(p)                       # CGU due par paquet
    # CGU annuelle moyenne sur toute la population cible (moyenne ponderee
    # des CGU individuelles issues des microdonnees EHCVM).
    CGU_MOY = cgu_moyenne(p)
    sub_actu_cum = rcgu_seul_actu = rcgu_comb_actu = 0.0
    # Historique des effectifs par paquet (pour calculer les eligibles par carence)
    hist = {pk: [] for pk in PAQUETS}     # hist[pk][k] = effectif du paquet pk a l'annee k+1

    for n in range(1, N_ANNEES + 1):
        annee = 2026 + n
        inf   = (1 + p["tau_inf"]) ** (n - 1)
        N_prev = dict(N)

        N_curr = {}
        for pk in PAQUETS:
            if n == 1:
                N_curr[pk] = float(N0[pk])
            else:
                # delta_n = alpha * (1+beta)^n : taux d'accroissement annuel
                d = p["alpha"] * (1 + p["beta"]) ** n
                f = 1 + d - p["q_bar"][pk] - p["tau_ret"][pk] - p["tau_abd"]
                N_curr[pk] = max(0., N_prev[pk] * f)
            hist[pk].append(N_curr[pk])

        # Effectif eligible a la branche b = cotisants ayant depasse le delai de
        # carence delta_b. En annuel : un cotisant present il y a >= ceil(delta_b/12)
        # annees est eligible. On approxime par l'effectif de l'annee (n - annees_carence).
        def eligibles(pk, branche):
            mois = p["carence"].get(branche, 0)
            a = int(-(-mois // 12))          # ceil(mois/12) = nb d'annees de carence
            idx = n - 1 - a                  # indice dans hist (0-based) de l'annee eligible
            if idx < 0:
                return 0.0                   # personne n'a encore atteint la carence
            return hist[pk][idx]             # effectif present il y a 'a' annees, toujours la

        NbP = {}
        for pk in ["O","Pl"]:
            # Retraite : carence 120 mois = 10 ans
            nouv = N_prev[pk] * p["tau_ret"][pk] if n >= 10 else 0.
            NbP[pk] = max(0., NbPens[pk] * (1 - p["q_pens"][pk]) + nouv)

        rec = dep = 0.
        dep_br = {b:0. for b in ["sante","atmp","maternite","pf","id","retraite"]}
        pi_sa = p["CMU_an"]/12
        _nc = max(0, min(int(p.get("conjoint",0)), 4))
        pi_sa *= (1 + _nc)
        _wj = p["plaf_css"]/22; _Dat = p.get("dur_at", 30)
        _Kat = 0.5*_wj*min(_Dat,28) + (2/3)*_wj*max(_Dat-28,0)
        pi_at = p["taux_atmp"]*_Kat/12
        n_e   = min(int(p.get("n_enfants",2)),6)
        pi_pf = p["alloc_fam"]*max(n_e,1)

        for pk in PAQUETS:
            # Recettes : TOUS les cotisants actifs cotisent des l'adhesion
            rec += N_curr[pk]*(c[pk]["S_trav"]+c[pk]["S_etat"])*12*inf
            f = p["f_rep"].get(pk,0)
            pi_ma_f = (p["ISF"]/35)*((2/3)*(p["SMIG"]/30)*p["dur_conge"]+p["alloc_pre"]+p["alloc_mat"])/12
            # Depenses : seuls les ELIGIBLES (carence depassee) generent des prestations
            dsa = eligibles(pk,"sante")*pi_sa*inf*12;  dep+=dsa; dep_br["sante"]+=dsa
            dat = eligibles(pk,"atmp")*pi_at*inf*12;   dep+=dat; dep_br["atmp"]+=dat
            if pk!="B":
                dma = eligibles(pk,"maternite")*f*pi_ma_f*inf*12; dep+=dma; dep_br["maternite"]+=dma
                dpf = eligibles(pk,"pf")*pi_pf*inf*12;            dep+=dpf; dep_br["pf"]+=dpf
            if pk in ("O","Pl"):
                did = eligibles(pk,"id")*c[pk].get("pi_id",0)*inf*12; dep+=did; dep_br["id"]+=did
        for pk in ["O","Pl"]:
            pen = (0.30 if pk=="O" else 0.40)*p["SMIG"]
            dre = NbP[pk]*pen*(1+p["tau_inf"])**(n-1)*12; dep+=dre; dep_br["retraite"]+=dre

        sol_ann = rec - dep; sol_cum += sol_ann

        # ══════════════════════════════════════════════════════════════════
        # MODULE CGU : enrolement et recettes fiscales
        #
        # Deux trajectoires d'enrolement a la CGU sont comparees :
        #
        #  1. SANS le regime social : le nombre de contribuables progresse au
        #     seul rythme de recouvrement de l'administration fiscale
        #     (g_cgu_seul), a partir du stock de depart.
        #
        #  2. AVEC le regime social : pour cotiser au regime, il faut etre en
        #     regle de CGU. Les cotisants du regime social qui ne figuraient
        #     pas encore dans le fichier fiscal entrent donc dans le champ de
        #     la CGU. La trajectoire combinee = enrolement fiscal de base
        #     + cotisants sociaux venus s'ajouter (part non deja enrolee).
        #
        # Cette construction lie directement l'enrolement combine a la
        # dynamique reelle du regime social (le meme effectif que le reste de
        # l'application), et non a un parametre exogene. La divergence entre
        # les deux courbes est donc l'effet propre du regime social.
        # ══════════════════════════════════════════════════════════════════
        cible_cgu = CIBLE_TOTALE

        # --- Trajectoire 1 : enrolement fiscal SANS regime social ----------
        n_cgu_seul = min(p["stock_cgu_0"] * (1 + p["g_cgu_seul"]) ** (n - 1),
                         cible_cgu)

        # --- Trajectoire 2 : enrolement AVEC regime social -----------------
        # Les cotisants du regime social (sum N_curr) sont tous en regle de
        # CGU. Le supplement d'enrolement apporte par le regime est la part de
        # ces cotisants qui depasse le stock deja enrole au fil de la montee
        # en charge fiscale. On l'estime par l'ecart entre l'effectif social
        # et le stock initial deja compte dans la trajectoire fiscale.
        n_social      = sum(N_curr.values())
        apport_social = max(0.0, n_social - p["stock_cgu_0"])
        n_cgu_comb    = min(n_cgu_seul + apport_social, cible_cgu)

        # --- Recettes de CGU ------------------------------------------------
        r_cgu_seul  = n_cgu_seul * CGU_MOY * inf
        r_cgu_comb  = n_cgu_comb * CGU_MOY * inf
        gain_collab = r_cgu_comb - r_cgu_seul          # gain du a l'effet social
        nouveaux    = n_cgu_comb - n_cgu_seul          # contribuables supplementaires

        # CGU securisee aupres des seuls cotisants du regime social
        # (structure reelle du regime, non celle de la population cible)
        r_cgu_social = sum(N_curr[pk] * CGU_PK[pk] for pk in PAQUETS) * inf

        # --- Position budgetaire de l'Etat ----------------------------------
        sub  = sum(N_curr[pk] * c[pk]["S_etat"] * 12 * inf for pk in PAQUETS)
        cnet = sub - r_cgu_social                      # negatif = favorable
        disc = (1 + p["a_actu"]) ** (n - 1)
        sub_actu_cum   += sub        / disc
        rcgu_seul_actu += r_cgu_seul / disc
        rcgu_comb_actu += r_cgu_comb / disc

        # Impact redistributif : methode deterministe par interpolation.
        # Indicateur(c) = (1-c)*valeur_avant + c*valeur_potentielle, c = couverture.
        taux_couv = sum(N_curr.values()) / 1_889_085
        cc = min(max(taux_couv, 0.0), 1.0)
        def interp(cle):
            return (1 - cc) * INDICATEURS_BASE[cle] + cc * INDICATEURS_POTENTIEL[cle]
        fgt0_ap = interp("FGT0"); fgt1_ap = interp("FGT1"); fgt2_ap = interp("FGT2")
        gini_ap = interp("Gini"); cat10_ap = interp("CAT10"); cat40_ap = interp("CAT40")

        rows.append({
            "n": n, "annee": annee,
            "CT_B": N_curr["B"], "CT_A": N_curr["A"],
            "CT_O": N_curr["O"], "CT_Pl": N_curr["Pl"],
            "CT_total": sum(N_curr.values()),
            "NbPens_O": NbP["O"], "NbPens_Pl": NbP["Pl"],
            "NbPens_total": NbP["O"]+NbP["Pl"],
            "Recettes_M": rec/1e6, "Depenses_M": dep/1e6,
            "Dep_sante_M": dep_br["sante"]/1e6,
            "Dep_atmp_M": dep_br["atmp"]/1e6,
            "Dep_maternite_M": dep_br["maternite"]/1e6,
            "Dep_pf_M": dep_br["pf"]/1e6,
            "Dep_id_M": dep_br["id"]/1e6,
            "Dep_retraite_M": dep_br["retraite"]/1e6,
            "Solde_annuel_M": sol_ann/1e6,
            "Solde_cumule_M": sol_cum/1e6,
            "Taux_couv": taux_couv*100,
            # ── Module CGU ──
            "CGU_moy": CGU_MOY,
            "CGU_B_du": CGU_PK["B"], "CGU_A_du": CGU_PK["A"],
            "CGU_O_du": CGU_PK["O"], "CGU_Pl_du": CGU_PK["Pl"],
            "N_cgu_seul": n_cgu_seul,
            "N_cgu_comb": n_cgu_comb,
            "Nouveaux_cgu": nouveaux,
            "Taux_cgu_seul": n_cgu_seul / cible_cgu * 100,
            "Taux_cgu_comb": n_cgu_comb / cible_cgu * 100,
            "R_cgu_seul_M": r_cgu_seul/1e6,
            "R_cgu_comb_M": r_cgu_comb/1e6,
            "Gain_collab_M": gain_collab/1e6,
            "R_cgu_seul_actu_cum_M": rcgu_seul_actu/1e6,
            "R_cgu_comb_actu_cum_M": rcgu_comb_actu/1e6,
            "Gain_collab_actu_cum_M": (rcgu_comb_actu - rcgu_seul_actu)/1e6,
            # ── Position budgetaire de l'Etat ──
            "Sub_M": sub/1e6, "R_cgu_M": r_cgu_social/1e6, "Cnet_M": cnet/1e6,
            "Sub_actu_cum_M": sub_actu_cum/1e6,
            "S_trav_B": c["B"]["S_trav"], "S_trav_A": c["A"]["S_trav"],
            "S_trav_O": c["O"]["S_trav"], "S_trav_Pl": c["Pl"]["S_trav"],
            "FGT0_ap": fgt0_ap, "FGT1_ap": fgt1_ap, "FGT2_ap": fgt2_ap,
            "Gini_ap": gini_ap, "CAT10_ap": cat10_ap, "CAT40_ap": cat40_ap,
        })
        N = N_curr; NbPens = NbP

    return pd.DataFrame(rows)
