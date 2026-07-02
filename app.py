"""
app.py - Instance Dash, layout, navigation centralisée
Architecture : UN SEUL callback écrit sur url.pathname
"""
import dash
from dash import dcc, html, callback, Input, Output, State

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    serve_locally=False,   # charge plotly.js et les libs depuis un CDN rapide
    external_stylesheets=[
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css',
    ],
    title='CGU Social - Sénégal',
)
server = app.server

# Compression gzip : reduit fortement le poids des donnees transferees
# (utile sur connexion lente). Sans effet si flask-compress n'est pas installe.
try:
    from flask_compress import Compress
    Compress(server)
except Exception:
    pass


def sn_stripe():
    return html.Div(className='sn-stripe', children=[
        html.Div(className='sn-stripe-vert'),
        html.Div(className='sn-stripe-jaune'),
        html.Div(className='sn-stripe-rouge'),
    ])


def navbar():
    items = [
        ('/', 'accueil',    'fa-house',        'Accueil'),
        ('/parametres',  'params',    'fa-sliders',      'Paramètres'),
        ('/dashboard',   'dashboard', 'fa-chart-line',   'Tableau de bord'),
        ('/resultats',   'resultats', 'fa-table',        'Résultats'),
        ('/simulation',  'simul',     'fa-user-check',   'Simulation individuelle'),
    ]
    return html.Div(className='nav-shell', children=[
        sn_stripe(),
        html.Nav(className='navbar', children=[
            html.Div(className='nav-brand', children=[
                html.Div(className='nav-brand-icon',
                         children=[html.I(className='fa-solid fa-shield-halved')]),
                html.Div(className='nav-brand-text', children=[
                    html.Div('CGU Social', className='nav-brand-title'),
                    html.Div('Microsimulation actuarielle',
                             className='nav-brand-sub'),
                ]),
            ]),
            html.Div(className='nav-links', children=[
                html.Button(
                    id=f'nav-{pid}',
                    className='nav-link',
                    n_clicks=0,
                    children=[
                        html.I(className=f'fa-solid {ico}'),
                        html.Span(lbl, className='nav-txt',
                                  style={'marginLeft': '0.35rem'}),
                    ],
                )
                for _, pid, ico, lbl in items
            ]),
        ]),
    ])


def footer():
    return html.Footer(className='footer', children=[
        html.Div(className='footer-main', children=[
            html.Div(className='footer-brand', children=[
                html.Div(className='footer-brand-ico',
                         children=[html.I(className='fa-solid fa-shield-halved')]),
                html.Div(children=[
                    html.Div('CGU Social', className='footer-brand-name'),
                    html.Div('République du Sénégal', className='footer-brand-tag'),
                ]),
            ]),
            html.Div(className='footer-info', children=[
                html.Div(className='footer-info-col', children=[
                    html.H5('Données'),
                    html.Ul([
                        html.Li('EHCVM 2021-2022 - ANSD'),
                        html.Li('Tables CIMA 2019'),
                        html.Li('Modèle OIT (2021)'),
                    ]),
                ]),
                html.Div(className='footer-info-col', children=[
                    html.H5('Institution'),
                    html.Ul([
                        html.Li('CEP - Ministère des Finances'),
                        html.Li('République du Sénégal'),
                    ]),
                ]),
            ]),
        ]),
        html.Div(className='footer-bottom', children=[
            html.Strong('CGU Social Sénégal'),
            html.Span('Simulation actuarielle 2027-2066'),
            html.Span('Données : EHCVM 2021-2022 - Tables CIMA 2019'),
        ]),
    ])


# ── Widget Assistant IA (bouton flottant + fenetre de chat) ──────────────────
def assistant_widget():
    return html.Div([
        # Bouton flottant
        html.Button(
            id='ia-fab', n_clicks=0, className='ia-fab',
            title="Assistant IA - poser une question sur les resultats",
            children=[html.I(className='fa-solid fa-robot')],
        ),
        # Fenetre de chat (masquee par defaut)
        html.Div(id='ia-panel', className='ia-panel ia-panel--hidden', children=[
            # En-tete
            html.Div(className='ia-header', children=[
                html.Div(className='ia-header-left', children=[
                    html.Div(className='ia-header-ico',
                             children=[html.I(className='fa-solid fa-robot')]),
                    html.Div([
                        html.Div('Assistant CGU', className='ia-header-title'),
                    ]),
                ]),
                html.Button(id='ia-close', n_clicks=0, className='ia-close',
                            children=[html.I(className='fa-solid fa-xmark')]),
            ]),

            # Fil de discussion
            html.Div(id='ia-messages', className='ia-messages', children=[
                html.Div(className='ia-msg ia-msg--bot', children=[
                    html.Div(className='ia-msg-ico',
                             children=[html.I(className='fa-solid fa-robot')]),
                    html.Div(
                        "Bonjour. Je suis votre assistant IA. Posez-moi une "
                        "question, ou choisissez une suggestion ci-dessous."
                        ,
                        className='ia-msg-txt'),
                ]),
            ]),

            # Suggestions rapides
            html.Div(className='ia-suggestions', children=[
                html.Button(s, id={'type': 'ia-suggest', 'index': i},
                            n_clicks=0, className='ia-suggest-btn')
                for i, s in enumerate([
                    "Le régime est-il viable ?",
                    "Quelle branche coute le plus cher ?",
                    "Compare Bronze et Platine",
                    "Explique l'évolution du solde cumulé",
                ])
            ]),

            # Zone de saisie
            html.Div(className='ia-input-zone', children=[
                dcc.Textarea(id='ia-input', className='ia-input',
                             placeholder="Posez votre question...",
                             rows=1),
                html.Button(id='ia-send', n_clicks=0, className='ia-send',
                            children=[html.I(className='fa-solid fa-paper-plane')]),
            ]),
        ]),

        # Stores : etat ouvert/ferme + historique de conversation
        dcc.Store(id='ia-open', data=False),
        dcc.Store(id='ia-history', data=[]),
    ])


# ── Layout principal ─────────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Store(id='store-params', storage_type='memory', data={}),
    dcc.Store(id='store-nav',    storage_type='memory', data='/'),
    dcc.Location(id='url', refresh=False),
    dcc.Download(id='dl-excel'),
    navbar(),
    html.Div(id='page-content', className='page-anim'),
    footer(),
    assistant_widget(),
])


# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION : UN SEUL callback écrit sur url.pathname
# ══════════════════════════════════════════════════════════════════════════════

NAV_BTNS = {
    'nav-accueil':   '/',
    'nav-params':    '/parametres',
    'nav-dashboard': '/dashboard',
    'nav-resultats': '/resultats',
    'nav-simul':     '/simulation',
}


@callback(
    Output('url', 'pathname'),
    [Input(bid, 'n_clicks') for bid in NAV_BTNS],
    Input('store-nav', 'data'),
    prevent_initial_call=True,
)
def navigate(*args):
    from dash import callback_context, no_update
    ctx = callback_context
    if not ctx.triggered:
        return no_update
    tid = ctx.triggered[0]['prop_id'].split('.')[0]
    if tid in NAV_BTNS:
        return NAV_BTNS[tid]
    if tid == 'store-nav':
        v = args[-1]
        if isinstance(v, dict):          # jeton {'p': chemin, 'k': compteur}
            return v.get('p', '/')
        return v or '/'
    return no_update


@callback(
    [Output(f'nav-{p}', 'className')
     for p in ['accueil', 'params', 'dashboard', 'resultats', 'simul']],
    Input('url', 'pathname'),
    prevent_initial_call=False,
)
def update_nav_active(pathname):
    pm = {
        'accueil':   '/',
        'params':    '/parametres',
        'dashboard': '/dashboard',
        'resultats': '/resultats',
        'simul':     '/simulation',
    }
    pathname = pathname or '/'
    return [
        'nav-link active' if pm[p] == pathname else 'nav-link'
        for p in ['accueil', 'params', 'dashboard', 'resultats', 'simul']
    ]


@callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    State('store-params', 'data'),
    prevent_initial_call=False,
)
def render_page(pathname, params_data):
    from pages.accueil      import layout as pg_acc
    from pages.parametres   import layout as pg_par
    from pages.dashboard    import build_dashboard
    from pages.resultats    import build_resultats
    from pages.simulation   import layout as pg_sim
    from simulation.moteur  import simuler

    pathname = pathname or '/'

    if pathname == '/':
        return pg_acc
    if pathname == '/parametres':
        return pg_par
    if pathname == '/dashboard':
        return build_dashboard(simuler(params_data or {}))
    if pathname == '/resultats':
        return build_resultats(simuler(params_data or {}))
    if pathname == '/simulation':
        return pg_sim
    return pg_acc


# ══════════════════════════════════════════════════════════════════════════════
# ASSISTANT IA : ouverture/fermeture + envoi de messages
# ══════════════════════════════════════════════════════════════════════════════

# Ouvrir / fermer le panneau
@callback(
    Output('ia-panel', 'className'),
    Output('ia-open',  'data'),
    Input('ia-fab',    'n_clicks'),
    Input('ia-close',  'n_clicks'),
    State('ia-open',   'data'),
    prevent_initial_call=True,
)
def toggle_assistant(n_fab, n_close, est_ouvert):
    from dash import callback_context
    ctx = callback_context
    if not ctx.triggered:
        return 'ia-panel ia-panel--hidden', False
    tid = ctx.triggered[0]['prop_id'].split('.')[0]
    if tid == 'ia-close':
        return 'ia-panel ia-panel--hidden', False
    # clic sur le bouton flottant : on inverse
    ouvrir = not est_ouvert
    cls = 'ia-panel' if ouvrir else 'ia-panel ia-panel--hidden'
    return cls, ouvrir


def _rendre_messages(historique):
    """Transforme l'historique en bulles de chat."""
    bulles = [
        html.Div(className='ia-msg ia-msg--bot', children=[
            html.Div(className='ia-msg-ico',
                     children=[html.I(className='fa-solid fa-robot')]),
            html.Div("Bonjour. Je peux analyser les résultats de la simulation "
                     "en cours. Posez-moi une question, ou choisissez une "
                     "suggestion ci-dessous.", className='ia-msg-txt'),
        ]),
    ]
    for m in historique:
        if m['role'] == 'user':
            bulles.append(html.Div(className='ia-msg ia-msg--user', children=[
                html.Div(m['content'], className='ia-msg-txt'),
                html.Div(className='ia-msg-ico',
                         children=[html.I(className='fa-solid fa-user')]),
            ]))
        else:
            bulles.append(html.Div(className='ia-msg ia-msg--bot', children=[
                html.Div(className='ia-msg-ico',
                         children=[html.I(className='fa-solid fa-robot')]),
                html.Div(m['content'], className='ia-msg-txt'),
            ]))
    return bulles


# Envoi d'un message (bouton Envoyer OU clic sur une suggestion)
@callback(
    Output('ia-messages', 'children'),
    Output('ia-history',  'data'),
    Output('ia-input',    'value'),
    Input('ia-send', 'n_clicks'),
    Input({'type': 'ia-suggest', 'index': dash.ALL}, 'n_clicks'),
    State('ia-input',    'value'),
    State('ia-history',  'data'),
    State('store-params','data'),
    prevent_initial_call=True,
)
def envoyer_message(n_send, n_suggests, texte, historique, params_data):
    from dash import callback_context
    from dash.exceptions import PreventUpdate
    from simulation.moteur    import simuler
    from simulation.assistant import construire_contexte, repondre

    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    historique = historique or []
    tid = ctx.triggered[0]['prop_id']

    # Determiner la question selon la source du declenchement
    question = None
    if 'ia-suggest' in tid:
        # Un seul des n_clicks change ; retrouver l'index
        import json
        try:
            comp = json.loads(tid.split('.')[0])
            idx = comp['index']
            suggestions = [
                "Le régime est-il viable ?",
                "Quelle branche coute le plus cher ?",
                "Compare Bronze et Platine",
                "Explique l'évolution du solde cumulé",
            ]
            # Ne reagir que si le clic est reel (n_clicks > 0)
            if not n_suggests or all(not c for c in n_suggests):
                raise PreventUpdate
            question = suggestions[idx]
        except (ValueError, KeyError, IndexError):
            raise PreventUpdate
    else:
        if not n_send or not (texte or '').strip():
            raise PreventUpdate
        question = texte.strip()

    if not question:
        raise PreventUpdate

    # Ajouter la question a l'historique
    historique.append({'role': 'user', 'content': question})

    # Construire le contexte factuel a partir de la simulation en cours
    df = simuler(params_data or {})
    contexte = construire_contexte(df)

    # Appel a l'IA
    ok, reponse = repondre(question, historique[:-1], contexte)
    historique.append({'role': 'assistant', 'content': reponse})

    return _rendre_messages(historique), historique, ''
