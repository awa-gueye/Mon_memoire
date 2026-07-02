"""
pages/accueil.py - Page d'accueil (style inspire de sunu-souba.com, palette bleue)
Navigation via store-nav -> navigate() dans app.py (un seul Output sur store-nav).
"""
from dash import html, dcc, callback, Input, Output, callback_context
<<<<<<< HEAD
=======


# ---------------------------------------------------------------- composants --
def _stat(val, lbl):
    return html.Div(className='sn-stat', children=[
        html.Div(val, className='sn-stat-val'),
        html.Div(lbl, className='sn-stat-lbl'),
    ])


def _feature(num, ico, titre, texte, lien, btn_id):
    return html.Button(id=btn_id, n_clicks=0, className='sn-feature', children=[
        html.Div(num, className='sn-feature-num'),
        html.Div(className='sn-feature-ico', children=[html.I(className=f'fa-solid {ico}')]),
        html.Div(titre, className='sn-feature-title'),
        html.Div(texte, className='sn-feature-text'),
        html.Div(className='sn-feature-link', children=[lien, html.I(className='fa-solid fa-arrow-right')]),
    ])
>>>>>>> 81c332a929374abe8f37fcbe77945e644f78ca97


# ---------------------------------------------------------------- composants --
def _stat(val, lbl):
    return html.Div(className='sn-stat', children=[
        html.Div(val, className='sn-stat-val'),
        html.Div(lbl, className='sn-stat-lbl'),
    ])


def _feature(num, ico, titre, texte, lien, btn_id):
    return html.Button(id=btn_id, n_clicks=0, className='sn-feature', children=[
        html.Div(num, className='sn-feature-num'),
        html.Div(className='sn-feature-ico', children=[html.I(className=f'fa-solid {ico}')]),
        html.Div(titre, className='sn-feature-title'),
        html.Div(texte, className='sn-feature-text'),
        html.Div(className='sn-feature-link', children=[lien, html.I(className='fa-solid fa-arrow-right')]),
    ])


def _paquet(nom, couleur, imgnum, tranche, branches, cotisation):
    return html.Div(className='pkg',
                    style={'--c': couleur, '--bg': f"url('/assets/images/img{imgnum}.jpg')"},
                    children=[
        html.Div(className='pkg-ov'),
        html.Div(className='pkg-in', children=[
            html.Div(className='pkg-top', children=[
                html.Span(className='pkg-dot'),
                html.Span(f'Paquet {nom}', className='pkg-name'),
            ]),
            html.Div(tranche, className='pkg-tr'),
            html.Ul([html.Li(b) for b in branches], className='pkg-br'),
            html.Div(className='pkg-badge',
                     children=[html.I(className='fa-solid fa-coins'), ' ', cotisation]),
        ]),
<<<<<<< HEAD
=======
        html.Div(tranche, className='paquet-card-tranche'),
        html.Ul([html.Li(b) for b in branches], className='paquet-card-branches'),
        html.Div(className='paquet-badge', style={'color': couleur, 'background': '#EEF4FC'},
                 children=[html.I(className='fa-solid fa-coins'), ' ', cotisation]),
>>>>>>> 81c332a929374abe8f37fcbe77945e644f78ca97
    ])


def _pilier(ico, titre, texte):
    return html.Div(className='sn-pilier', children=[
        html.Div(style={'display': 'flex', 'alignItems': 'center', 'gap': '0.6rem',
                        'marginBottom': '0.7rem'}, children=[
            html.I(className=f'fa-solid {ico}', style={'color': '#1565C0', 'fontSize': '1.1rem'}),
            html.Strong(titre, style={'fontFamily': 'Times New Roman,serif',
                                      'color': '#0D2B5E', 'fontSize': '1rem'}),
        ]),
        html.P(texte, style={'fontSize': '0.87rem', 'color': '#4A6080', 'lineHeight': '1.65'}),
    ])


# ---------------------------------------------------------------------- layout -
layout = html.Div([

    # ============ HERO ============
    html.Div(className='hero sn-hero', children=[
        html.Div(className='hero-slide slide-1'),
        html.Div(className='hero-slide slide-2'),
        html.Div(className='hero-slide slide-3'),
        html.Div(className='hero-slide slide-4'),
        html.Div(className='hero-overlay'),
        html.Div(className='hero-content sn-hero-content', children=[
            html.Div(className='hero-badge', children=[
                html.I(className='fa-solid fa-star'),
                " Cellule d'Etudes et de Planification - Ministère de l'Economie, des Finances et du Plan",
            ]),
            html.H1(className='sn-hero-title', children=[
                'Simulez l\'avenir de la ',
                html.Span('protection sociale', className='sn-accent'),
                ' au Sénégal',
            ]),
            html.P(
                "Un outil de microsimulation dynamique pour évaluer la viabilité financière "
                "et l'impact redistributif du régime de cotisations sociales adossé à la "
                "Contribution Globale Unique, destiné aux travailleurs informels.",
                className='sn-hero-sub',
            ),
            html.Div(className='hero-btns', children=[
                html.Button(id='hero-btn-dashboard', n_clicks=0, className='btn-hero-pri',
                            children=[html.I(className='fa-solid fa-play'), ' Voir le tableau de bord']),
                html.Button(id='hero-btn-params', n_clicks=0, className='btn-hero-sec',
                            children=[html.I(className='fa-solid fa-sliders'), ' Modifier les paramètres']),
            ]),
        ]),
    ]),

    # ============ BANDEAU DE STATISTIQUES (chevauche le hero) ============
    html.Div(className='sn-stats-wrap', children=[
        html.Div(className='sn-stats', children=[
            _stat('60 000',    'Cotisants en 2027'),
            _stat('4',         'Paquets de couverture'),
            _stat('6',         'Branches de protection'),
            _stat('40 ans',    'Horizon de projection'),
            _stat('2027-2066', 'Période simulée'),
        ]),
    ]),

    # ============ CARTES NUMEROTEES (les outils du dashboard) ============
    html.Div(className='section section-white', children=[
        html.Div(className='section-inner', children=[
            html.H2('Explorer l\'outil', className='section-heading'),
            html.Div(className='section-sep'),
            html.Div(className='sn-features', children=[
                _feature('01', 'fa-chart-line', 'Tableau de bord',
                         "Visualisez les projections de recettes, dépenses et soldes sur 40 ans.",
                         'Accéder', 'feat-dashboard'),
                _feature('02', 'fa-user-check', 'Simulation individuelle',
                         "Estimez la cotisation et les gains nets d'un adhérent type.",
                         'Simuler', 'feat-simul'),
                _feature('03', 'fa-table', 'Résultats',
                         "Consultez les indicateurs de viabilité et d'impact redistributif.",
                         'Consulter', 'feat-resultats'),
                _feature('04', 'fa-sliders', 'Paramètres',
                         "Ajustez les hypothèses du scénario et relancez le modèle.",
                         'Configurer', 'feat-params'),
            ]),
        ]),
    ]),

    # ============ SECTION SCINDEE IMAGE / TEXTE ============
    html.Div(className='section section-fond', children=[
        html.Div(className='section-inner sn-split', children=[
            html.Div(className='sn-split-media', children=[
                html.Div(className='sn-split-quote', children=[
                    "« La protection sociale, levier de formalisation du secteur informel. »"
                ]),
            ]),
            html.Div(className='sn-split-body', children=[
                html.Div('IMPACT NATIONAL', className='sn-split-kicker'),
                html.H2(className='sn-split-title', children=[
                    'Un régime ', html.Span('soutenable', className='sn-accent-b'), ' et redistributif',
                ]),
                html.P(
                    "Sur l'ensemble de la période, le régime dégage un solde cumulé positif de "
                    "11,5 milliards de FCFA, tout en réduisant la pauvreté et en protégeant les "
                    "ménages des dépenses de santé catastrophiques. La CGU sécurisée auprès des "
                    "cotisants dépasse largement la subvention publique.",
                    className='sn-split-text',
                ),
                html.Div(className='sn-split-pill', children=[
                    html.Div(className='sn-split-pill-ico',
                             children=[html.I(className='fa-solid fa-handshake-angle')]),
                    html.Span('Adossé à la Contribution Globale Unique'),
                ]),
            ]),
        ]),
    ]),

    # ============ PRESENTATION DU MODELE ============
    html.Div(className='section section-white', children=[
        html.Div(className='section-inner', children=[
            html.H2('Présentation du modèle', className='section-heading'),
            html.Div(className='section-sep'),
            html.Div(className='sn-cards3', children=[
                html.Div(className='card', children=[
                    html.Div(className='card-icon', children=[html.I(className='fa-solid fa-database')]),
                    html.H3('Données EHCVM 2021-2022', className='card-title'),
                    html.P("La simulation s'appuie sur la population cible CGU identifiée dans "
                           "l'Enquête Harmonisée sur les Conditions de Vie des Ménages, soit plus "
                           "d'un million de travailleurs informels au niveau national.",
                           className='card-text'),
                ]),
                html.Div(className='card', children=[
                    html.Div(className='card-icon', children=[html.I(className='fa-solid fa-calculator')]),
                    html.H3('Modèle actuariel récursif', className='card-title'),
                    html.P("Les effectifs sont projetés par récurrence sur le stock de cotisants. "
                           "Chaque branche est tarifée par espérance de sinistre. Le taux "
                           "d'accroissement alpha = 4 % et beta = 1 % modélisent l'adhésion progressive.",
                           className='card-text'),
                ]),
                html.Div(className='card', children=[
                    html.Div(className='card-icon', children=[html.I(className='fa-solid fa-scale-balanced')]),
                    html.H3('Viabilité et redistributivité', className='card-title'),
                    html.P("Le modèle projette recettes, dépenses et soldes sur 40 ans et mesure "
                           "l'impact via les indices FGT et le coefficient de Gini, avant et après "
                           "introduction du régime.",
                           className='card-text'),
                ]),
            ]),
        ]),
    ]),

    # ============ ARCHITECTURE DU REGIME ============
    html.Div(className='section section-bleu', children=[
        html.Div(className='section-inner', children=[
            html.H2('Architecture du régime', className='section-heading'),
            html.Div(className='section-sep'),
            html.Div(className='sn-cards4', children=[
<<<<<<< HEAD
                _paquet('Bronze',  '#2196F3', 1, '0 - 5 M FCFA',
                        ['Santé (CMU)', 'AT/MP'], '393 FCFA/mois'),
                _paquet('Argent',  '#2ECC71', 2, '5 - 15 M FCFA',
                        ['Santé (CMU)', 'AT/MP', 'Maternité', 'Prest. familiales'], '2 878 FCFA/mois'),
                _paquet('Or',      '#F39C12', 3, '15 - 30 M FCFA',
                        ['Santé', 'AT/MP', 'Maternité', 'Prest. fam.', 'Invalidité/Décès', 'Retraite'],
                        '8 208 FCFA/mois'),
                _paquet('Platine', '#B06BE0', 4, '30 - 50 M FCFA',
=======
                _paquet('Bronze',  '#1565C0', '0 - 5 M FCFA',
                        ['Santé (CMU)', 'AT/MP'], '393 FCFA/mois'),
                _paquet('Argent',  '#2E9E5B', '5 - 15 M FCFA',
                        ['Santé (CMU)', 'AT/MP', 'Maternité', 'Prest. familiales'], '2 878 FCFA/mois'),
                _paquet('Or',      '#E8841A', '15 - 30 M FCFA',
                        ['Santé', 'AT/MP', 'Maternité', 'Prest. fam.', 'Invalidité/Décès', 'Retraite'],
                        '8 208 FCFA/mois'),
                _paquet('Platine', '#8E44AD', '30 - 50 M FCFA',
>>>>>>> 81c332a929374abe8f37fcbe77945e644f78ca97
                        ['Santé', 'AT/MP', 'Maternité', 'Prest. familiales', 'Invalidité/Décès', 'Retraite'],
                        '11 053 FCFA/mois'),
            ]),
        ]),
    ]),

    # ============ HYPOTHESES CLES ============
    html.Div(className='section section-white', children=[
        html.Div(className='section-inner', children=[
            html.H2('Hypothèses clés du scénario de référence', className='section-heading'),
            html.Div(className='section-sep'),
            html.Div(className='sn-cards3', children=[
                _pilier('fa-chart-line', "Dynamique d'adhésion",
                        "Taux d'accroissement annuel alpha = 4 % - Amélioration beta = 1 % - "
                        "Aucun abandon (régime adossé à l'obligation CGU)"),
                _pilier('fa-shield-halved', 'Tables de mortalité',
                        'Tables CIMA 2019 (art. 338 du Code des Assurances CIMA), '
                        'obligatoires en zone UEMOA pour toute tarification actuarielle'),
                _pilier('fa-coins', "Subvention de l'Etat",
                        "Le taux de subvention par branche est calibré sur les données EHCVM "
                        "2021-2022, en tenant compte des sous-estimations de revenus des enquêtes."),
            ]),
        ]),
    ]),
])


# ---- Navigation : hero + cartes numerotees -> store-nav (Output unique) ------
@callback(
    Output('store-nav', 'data'),
    Input('hero-btn-dashboard', 'n_clicks'),
    Input('hero-btn-params',    'n_clicks'),
    Input('feat-dashboard',     'n_clicks'),
    Input('feat-simul',         'n_clicks'),
    Input('feat-resultats',     'n_clicks'),
    Input('feat-params',        'n_clicks'),
    prevent_initial_call=True,
)
def hero_navigate(*clicks):
    from dash import no_update
    ctx = callback_context
    if not ctx.triggered:
        return no_update
    tid = ctx.triggered[0]['prop_id'].split('.')[0]
    routes = {
        'hero-btn-dashboard': '/dashboard', 'hero-btn-params': '/parametres',
        'feat-dashboard': '/dashboard', 'feat-simul': '/simulation',
        'feat-resultats': '/resultats', 'feat-params': '/parametres',
    }
    # jeton dict : la cle 'k' change a chaque clic -> le callback se redeclenche
    # toujours, meme vers une destination deja visitee (plus de bouton "mort").
    return {'p': routes.get(tid, '/'), 'k': sum(c or 0 for c in clicks)}
