"""
simulation/moteur.py - Moteur de microsimulation actuarielle CGU, Senegal
"""
import numpy as np
import pandas as pd

# Indicateurs redistributifs AVANT reforme (microdonnees EHCVM 2021-2022)
INDICATEURS_BASE = {
    "FGT0": 0.2421, "FGT1": 0.0531, "FGT2": 0.0181,
    "Gini": 0.3092, "CAT10": 0.0648, "CAT40": 0.0112,
}

# Indicateurs en cas de COUVERTURE UNIVERSELLE (potentiel). Calibres a partir
# des notebooks (methode deterministe) : a la couverture de reference (6,77 %)
# on retrouve exactement FGT0 0,2397 ; FGT1 0,0524 ; FGT2 0,0178 ; Gini 0,3093 ;
# CAT10 6,48%->~6,05% ; CAT40 1,12%->~1,05%.
INDICATEURS_POTENTIEL = {
    "FGT0": 0.2065, "FGT1": 0.04276, "FGT2": 0.01366,
    "Gini": 0.31069, "CAT10": 0.0021, "CAT40": 0.0000,
}

PARAMS_REF = {
    "N0_B": 50000, "N0_A": 8000, "N0_O": 1500, "N0_Pl": 500,
    # alpha = taux d'accroissement annuel des cotisants (delta_n = alpha*(1+beta)^n)
    "alpha": 0.04, "beta": 0.01, "tau_abd": 0.0, "tau_inf": 0.02,
    "SMIG": 64224, "gamma": 0.10, "CMU_an": 7000,
    # taux_atmp = frequence annuelle d'accident (p_at) ; dur_at = duree moyenne d'ITT (jours)
    "plaf_css": 63000, "taux_atmp": 0.03, "dur_at": 30, "alloc_fam": 2600,
    "ISF": 4.0, "alloc_pre": 20250, "alloc_mat": 54000,
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
    # Historique des effectifs par paquet (pour calculer les eligibles par carence)
    hist = {pk: [] for pk in PAQUETS}     # hist[pk][k] = effectif du paquet pk a l'annee k+1

    for n in range(1, 41):
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

        # Impact redistributif : methode deterministe par interpolation.
        # Indicateur(c) = (1-c)*valeur_avant + c*valeur_potentielle, c = couverture.
        taux_couv = sum(N_curr.values()) / 1_663_513
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
            "S_trav_B": c["B"]["S_trav"], "S_trav_A": c["A"]["S_trav"],
            "S_trav_O": c["O"]["S_trav"], "S_trav_Pl": c["Pl"]["S_trav"],
            "FGT0_ap": fgt0_ap, "FGT1_ap": fgt1_ap, "FGT2_ap": fgt2_ap,
            "Gini_ap": gini_ap, "CAT10_ap": cat10_ap, "CAT40_ap": cat40_ap,
        })
        N = N_curr; NbPens = NbP

    return pd.DataFrame(rows)
