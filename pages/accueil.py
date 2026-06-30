"""
pages/accueil.py - Page d'accueil
Les boutons hero utilisent store-nav pour la navigation (pas de Output url.pathname)
"""
from dash import html, dcc, callback, Input, Output


def _paquet(nom, couleur, tranche, branches, cotisation):
    return html.Div(className='paquet-card', style={'borderTopColor': couleur}, children=[
        html.Div(style={'display': 'flex', 'alignItems': 'center', 'gap': '0.6rem',
                        'marginBottom': '0.4rem'}, children=[
            html.Div(style={'width': '9px', 'height': '9px', 'borderRadius': '50%',
                            'background': couleur, 'flexShrink': '0'}),
            html.Div(f'Paquet {nom}', className='paquet-card-name', style={'color': couleur}),
        ]),
        html.Div(tranche, className='paquet-card-tranche'),
        html.Ul([html.Li(b) for b in branches], className='paquet-card-branches'),
        html.Div(className='paquet-badge',
                 style={'color': couleur, 'background': '#EEF4FC'},
                 children=[html.I(className='fa-solid fa-coins'), ' ', cotisation]),
    ])


def _pilier(ico, titre, texte):
    return html.Div(style={'background': '#fff', 'border': '1px solid #C5D8F0',
                            'borderRadius': '10px', 'padding': '1.3rem'}, children=[
        html.Div(style={'display': 'flex', 'alignItems': 'center', 'gap': '0.6rem',
                        'marginBottom': '0.7rem'}, children=[
            html.I(className=f'fa-solid {ico}',
                   style={'color': '#1565C0', 'fontSize': '1.1rem'}),
            html.Strong(titre, style={'fontFamily': 'Times New Roman,serif',
                                      'color': '#0D2B5E', 'fontSize': '1rem'}),
        ]),
        html.P(texte, style={'fontSize': '0.87rem', 'color': '#4A6080', 'lineHeight': '1.65'}),
    ])


layout = html.Div([

    # HERO avec diaporama CSS
    html.Div(className='hero', children=[
        html.Div(className='hero-slide slide-1'),
        html.Div(className='hero-slide slide-2'),
        html.Div(className='hero-slide slide-3'),
        html.Div(className='hero-slide slide-4'),
        html.Div(className='hero-overlay'),
        html.Div(className='hero-content', children=[
            html.Div(className='hero-badge', children=[
                html.I(className='fa-solid fa-star'),
                ' Cellule d\'Etudes et de Planification - Ministère des Finances',
            ]),
            html.H1(className='hero-title', children=[
                'Simulation actuarielle du régime de ',
                html.Span('cotisations sociales', className='accent'),
                ' intégré à la CGU',
            ]),
            html.P(
                "Un outil de microsimulation dynamique pour évaluer la viabilité "
                "financière et l'impact redistributif du régime de protection sociale "
                "destiné aux travailleurs informels assujettis à la Contribution Globale "
                "Unique au Sénégal.",
                className='hero-sub',
            ),
            html.Div(className='hero-btns', children=[
                html.Button(
                    id='hero-btn-dashboard',
                    n_clicks=0,
                    className='btn-hero-pri',
                    children=[html.I(className='fa-solid fa-play'),
                               ' Voir le tableau de bord'],
                ),
                html.Button(
                    id='hero-btn-params',
                    n_clicks=0,
                    className='btn-hero-sec',
                    children=[html.I(className='fa-solid fa-sliders'),
                               ' Modifier les paramètres'],
                ),
            ]),
            html.Div(className='hero-kpis', children=[
                html.Div(className='hero-kpi', children=[
                    html.Div('60 000',           className='hero-kpi-val'),
                    html.Div('Cotisants en 2027', className='hero-kpi-lbl'),
                ]),
                html.Div(className='hero-kpi', children=[
                    html.Div('4',                     className='hero-kpi-val'),
                    html.Div('Paquets de couverture', className='hero-kpi-lbl'),
                ]),
                html.Div(className='hero-kpi', children=[
                    html.Div('6',                       className='hero-kpi-val'),
                    html.Div('Branches de protection', className='hero-kpi-lbl'),
                ]),
                html.Div(className='hero-kpi', children=[
                    html.Div('40 ans',              className='hero-kpi-val'),
                    html.Div('Horizon de projection', className='hero-kpi-lbl'),
                ]),
                html.Div(className='hero-kpi', children=[
                    html.Div('2027-2066',         className='hero-kpi-val'),
                    html.Div('Période simulée',   className='hero-kpi-lbl'),
                ]),
            ]),
        ]),
    ]),

    # Section présentation
    html.Div(className='section section-white', children=[
        html.Div(className='section-inner', children=[
            html.H2('Présentation du modèle', className='section-heading'),
            html.Div(className='section-sep'),
            html.Div(className='g3', children=[
                html.Div(className='card', children=[
                    html.Div(className='card-icon',
                             children=[html.I(className='fa-solid fa-database')]),
                    html.H3('Données EHCVM 2021-2022', className='card-title'),
                    html.P(
                        "La simulation s'appuie sur les individus de la population cible CGU "
                        "identifiés dans l'Enquête Harmonisée sur les Conditions de Vie des "
                        "Ménages, représentant plus d'un million de travailleurs informels "
                        "dans la population nationale.",
                        className='card-text',
                    ),
                ]),
                html.Div(className='card', children=[
                    html.Div(className='card-icon',
                             children=[html.I(className='fa-solid fa-calculator')]),
                    html.H3('Modèle actuariel récursif', className='card-title'),
                    html.P(
                        "Les effectifs sont projetés par une équation de récurrence sur le "
                        "stock absolu de cotisants. Les tables CIMA 2019 fournissent les "
                        "probabilités de survie. Le taux d'accroissement alpha = 4 % et "
                        "beta = 1 % modélisent la dynamique d'adhésion progressive.",
                        className='card-text',
                    ),
                ]),
                html.Div(className='card', children=[
                    html.Div(className='card-icon',
                             children=[html.I(className='fa-solid fa-scale-balanced')]),
                    html.H3('Viabilité et redistributivité', className='card-title'),
                    html.P(
                        "Le modèle projette les recettes, dépenses et soldes sur 40 ans et "
                        "mesure l'impact redistributif via les indices FGT et le coefficient "
                        "de Gini avant et après introduction du régime.",
                        className='card-text',
                    ),
                ]),
            ]),
        ]),
    ]),

    # Architecture du régime
    html.Div(className='section section-fond', children=[
        html.Div(className='section-inner', children=[
            html.H2('Architecture du régime', className='section-heading'),
            html.Div(className='section-sep'),
            html.Div(className='g4', children=[
                _paquet('Bronze',  '#1565C0', '0 - 5 M FCFA',
                        ['Santé (CMU)', 'AT/MP'],
                        '1 568 FCFA/mois'),
                _paquet('Argent',  '#2E9E5B', '5 - 15 M FCFA',
                        ['Santé (CMU)', 'AT/MP', 'Maternité', 'Prest. familiales'],
                        '4 836 FCFA/mois'),
                _paquet('Or',      '#E8841A', '15 - 30 M FCFA',
                        ['Santé', 'AT/MP', 'Maternité', 'Prest. fam.',
                         'Invalidité/Décès', 'Retraite'],
                        '10 166 FCFA/mois'),
                _paquet('Platine', '#8E44AD', '30 - 50 M FCFA',
                        ['Santé', 'AT/MP', 'Maternité', 'Prest. familiales',
                         'Invalidité/Décès', 'Retraite'],
                        '11 033 FCFA/mois'),
            ]),
        ]),
    ]),

    # Hypothèses clés
    html.Div(className='section section-bleu', children=[
        html.Div(className='section-inner', children=[
            html.H2('Hypothèses clés du scénario de référence', className='section-heading'),
            html.Div(className='section-sep'),
            html.Div(className='g3', children=[
                _pilier('fa-chart-line', "Dynamique d'adhésion",
                        "Taux d'accroissement annuel alpha = 4 % - Amélioration beta = 1 % - "
                        "Aucun abandon (régime adossé à l'obligation CGU)"),
                _pilier('fa-shield-halved', 'Tables de mortalité',
                        'Tables CIMA 2019 (art. 338 du Code des Assurances CIMA), '
                        'obligatoires en zone UEMOA pour toute tarification actuarielle'),
                _pilier('fa-coins', "Subvention de l'Etat",
                        "Le taux de subvention de l'Etat par branche est calibré sur les "
                        "données EHCVM 2021-2022, en tenant compte des sous-estimations de "
                        "revenus observées dans les enquêtes ménages."),
            ]),
        ]),
    ]),
])


# Callbacks des boutons hero -> store-nav -> navigate() dans app.py
@callback(
    Output('store-nav', 'data'),
    Input('hero-btn-dashboard', 'n_clicks'),
    Input('hero-btn-params',    'n_clicks'),
    prevent_initial_call=True,
)
def hero_navigate(n1, n2):
    from dash import callback_context
    ctx = callback_context
    if not ctx.triggered:
        return '/'
    tid = ctx.triggered[0]['prop_id'].split('.')[0]
    if tid == 'hero-btn-dashboard':
        return '/dashboard'
    if tid == 'hero-btn-params':
        return '/parametres'
    return '/'
