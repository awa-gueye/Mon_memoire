"""
simulation/assistant.py
=======================
Logique de l'assistant IA conversationnel du dashboard CGU.

- Construit un CONTEXTE FACTUEL a partir des resultats de la simulation
  (ancrage / grounding) pour que l'IA reponde sur les vrais chiffres.
- Appelle l'API Hugging Face (router compatible OpenAI).
- La cle API est lue depuis la variable d'environnement HF_TOKEN
  (jamais ecrite en dur dans le code).

Configuration :
    export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxxxxx"
    (ou creer un fichier .env a la racine du projet)
"""

import os

# Modele par defaut (modifiable). Modeles conversationnels solides sur HF router :
#   - "meta-llama/Llama-3.3-70B-Instruct"
#   - "Qwen/Qwen2.5-72B-Instruct"
#   - "mistralai/Mistral-7B-Instruct-v0.3"  (plus leger)
MODELE_DEFAUT = "meta-llama/Llama-3.3-70B-Instruct"
HF_BASE_URL   = "https://router.huggingface.co/v1"


# ── Chargement optionnel d'un fichier .env ───────────────────────────────────
def _charger_env():
    """Charge HF_TOKEN depuis un fichier .env a la racine, si present."""
    if os.environ.get('HF_TOKEN'):
        return
    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(racine, '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, encoding='utf-8') as f:
                for ligne in f:
                    ligne = ligne.strip()
                    if ligne and not ligne.startswith('#') and '=' in ligne:
                        cle, _, val = ligne.partition('=')
                        cle = cle.strip()
                        val = val.strip().strip('"').strip("'")
                        if cle and val:
                            os.environ.setdefault(cle, val)
        except OSError:
            pass


_charger_env()


# ── Construction du contexte factuel a partir de la simulation ───────────────
def construire_contexte(df):
    """
    Resume les resultats de la simulation en un bloc de texte structure
    que l'IA utilisera comme source de verite.
    """
    d1, d40 = df.iloc[0], df.iloc[-1]
    viable  = bool(df['Solde_cumule_M'].min() >= 0)
    sol_fin = df['Solde_cumule_M'].iloc[-1]

    # Annee de premier deficit cumule, le cas echeant
    deficit = df.loc[df['Solde_cumule_M'] < 0, 'annee']
    annee_deficit = int(deficit.min()) if not deficit.empty else None

    # Branche la plus couteuse en 2066
    branches = {
        'Sante':            d40['Dep_sante_M'],
        'AT/MP':            d40['Dep_atmp_M'],
        'Maternite':        d40['Dep_maternite_M'],
        'Prestations familiales': d40['Dep_pf_M'],
        'Invalidite/Deces': d40['Dep_id_M'],
        'Retraite':         d40['Dep_retraite_M'],
    }
    branche_max = max(branches, key=branches.get)

    lignes = [
        "DONNEES DE LA SIMULATION EN COURS (source de verite, horizon 2027-2066) :",
        "",
        f"- Cotisants actifs en 2027 : {d1['CT_total']:,.0f}",
        f"- Cotisants actifs en 2066 : {d40['CT_total']:,.0f}",
        f"- Pensionnaires en 2066 : {d40['NbPens_total']:,.0f}",
        f"- Recettes annuelles 2066 : {d40['Recettes_M']:,.1f} millions FCFA",
        f"- Depenses annuelles 2066 : {d40['Depenses_M']:,.1f} millions FCFA",
        f"- Solde cumule final (2066) : {sol_fin:,.1f} millions FCFA",
        f"- Regime financierement viable sur tout l'horizon : {'OUI' if viable else 'NON'}",
    ]
    if annee_deficit:
        lignes.append(f"- Premiere annee de deficit cumule : {annee_deficit}")
    lignes += [
        f"- Taux de couverture de la population cible en 2066 : {d40['Taux_couv']:.1f} %",
        f"- Branche la plus couteuse en 2066 : {branche_max} "
        f"({branches[branche_max]:,.1f} M FCFA)",
        "",
        "Depenses par branche en 2066 (millions FCFA) :",
    ]
    for nom, val in sorted(branches.items(), key=lambda x: -x[1]):
        lignes.append(f"    {nom} : {val:,.1f}")

    lignes += [
        "",
        "Indicateurs redistributifs (apres reforme, 2066) :",
        f"    FGT(0) incidence de pauvrete : {d40['FGT0_ap']:.4f} (avant reforme : 0,2421)",
        f"    FGT(1) profondeur : {d40['FGT1_ap']:.4f} (avant : 0,0531)",
        f"    FGT(2) severite : {d40['FGT2_ap']:.4f} (avant : 0,0181)",
        f"    Coefficient de Gini : {d40['Gini_ap']:.4f} (avant : 0,3092, quasi stable)",
        f"    Depenses de sante catastrophiques (seuil 10%) : {d40['CAT10_ap']*100:.2f} % "
        f"des menages (avant reforme : 6,48 % ; potentiel couverture universelle : 0,21 %)",
        "",
        "Population cible : 5 653 individus dans l'echantillon EHCVM 2021-2022, "
        "soit environ 1,66 million de travailleurs informels apres ponderation.",
        "",
        "Effectifs de cotisants par paquet en 2066 :",
        f"    Bronze : {d40['CT_B']:,.0f}",
        f"    Argent : {d40['CT_A']:,.0f}",
        f"    Or : {d40['CT_O']:,.0f}",
        f"    Platine : {d40['CT_Pl']:,.0f}",
    ]
    return "\n".join(lignes)


# ── System prompt : cadre le role et les garde-fous ──────────────────────────
SYSTEM_PROMPT = """Tu es l'assistant d'analyse d'un dashboard actuariel sur le \
regime de cotisations sociales integre a la Contribution Globale Unique (CGU) \
au Senegal. Ce regime couvre les travailleurs informels via 4 paquets (Bronze, \
Argent, Or, Platine) et 6 branches de protection sociale (sante/CMU, accidents \
du travail, maternite, prestations familiales, invalidite/deces, retraite).

REGLES IMPERATIVES :
1. Reponds UNIQUEMENT a partir des donnees de la simulation fournies dans le \
contexte. Ne devine jamais un chiffre.
2. Si une information n'est pas dans les donnees, dis-le clairement plutot que \
d'inventer. Exemple : "Cette donnee n'apparait pas dans la simulation actuelle."
3. Reste dans le domaine : protection sociale, actuariat, CGU, finances du \
regime. Si une question est hors sujet, recadre poliment.
4. Sois concis et precis. Cite les chiffres exacts du contexte.
5. Reponds en francais, dans un registre professionnel adapte a un cadre du \
Ministere des Finances.
6. Quand c'est pertinent, explique le raisonnement actuariel derriere un chiffre."""


# ── Appel a l'API ────────────────────────────────────────────────────────────
def repondre(question, historique, contexte_factuel, modele=None):
    """
    Envoie la question + l'historique + le contexte a l'API HF.

    Parametres
    ----------
    question : str
        La question de l'utilisateur.
    historique : list[dict]
        Liste de {'role': 'user'|'assistant', 'content': str} (echanges precedents).
    contexte_factuel : str
        Resume des donnees de simulation (issu de construire_contexte()).
    modele : str | None
        Identifiant du modele HF. Defaut : MODELE_DEFAUT.

    Retour
    ------
    (succes: bool, reponse: str)
    """
    token = os.environ.get('HF_TOKEN')
    if not token:
        return False, (
            "Cle API Hugging Face introuvable. Definissez la variable "
            "d'environnement HF_TOKEN ou creez un fichier .env a la racine du "
            "projet avec la ligne :  HF_TOKEN=hf_votre_cle"
        )

    try:
        from openai import OpenAI
    except ImportError:
        return False, ("Le paquet 'openai' n'est pas installe. "
                       "Lancez : pip install openai")

    client = OpenAI(base_url=HF_BASE_URL, api_key=token)

    # Construction des messages : system + contexte + historique + question
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": contexte_factuel},
    ]
    # Historique (limite aux 10 derniers echanges pour rester leger)
    for echange in (historique or [])[-10:]:
        messages.append({
            "role": echange.get('role', 'user'),
            "content": echange.get('content', ''),
        })
    messages.append({"role": "user", "content": question})

    try:
        completion = client.chat.completions.create(
            model=modele or MODELE_DEFAUT,
            messages=messages,
            max_tokens=700,
            temperature=0.3,
        )
        return True, completion.choices[0].message.content.strip()
    except Exception as e:  # noqa: BLE001
        return False, (f"Erreur lors de l'appel a l'API : {e}\n\n"
                       "Verifiez votre cle HF_TOKEN, votre connexion et que le "
                       "modele choisi est disponible sur le routeur Hugging Face.")
