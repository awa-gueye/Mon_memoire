"""pages/parametres.py — Paramètres du modèle, organisés en sous-onglets.

Quatre catégories : Démographie, Économique, Subventions, CGU. Seuls des
paramètres directement observables ou fixés par le décideur figurent ici :
les grandeurs de l'enquête (chiffre d'affaires individuel, composition
sectorielle) sont lues dans les microdonnées et ne sont pas exposées.
"""

from dash import html, dcc, callback, Input, Output, State
from simulation.moteur import PARAMS_REF


# ── Composants ────────────────────────────────────────────────────────────

def _sl(pid, label, default, mn, mx, step, note=None):
    return html.Div(className='param-group', children=[
        html.Div(className='param-lbl', children=[
            html.Span(label),
            html.Span(id=f'lbl-{pid}', className='param-lbl-val', children=str(default)),
        ]),
        dcc.Slider(id=f'sl-{pid}', min=mn, max=mx, step=step, value=default,
                   marks=None, tooltip={'placement': 'bottom', 'always_visible': False},
                   className='param-slider'),
        *([html.P(note, className='param-note')] if note else []),
    ])


def _sp(pid, label, default, mn, mx, step, note=None):
    return html.Div(className='param-group', children=[
        html.Div(className='param-lbl', children=[
            html.Span(label),
            html.Span(id=f'lbl-{pid}', className='param-lbl-val', children=f'{default} %'),
        ]),
        dcc.Slider(id=f'sl-{pid}', min=mn, max=mx, step=step, value=default,
                   marks=None, tooltip={'placement': 'bottom', 'always_visible': False},
                   className='param-slider'),
        *([html.P(note, className='param-note')] if note else []),
    ])


def _card(icone, titre, enfants):
    return html.Div(className='params-card', children=[
        html.Div(className='params-card-hdr', children=[
            html.Div(className='params-card-ico',
                     children=[html.I(className='fa-solid ' + icone)]),
            html.H3(titre, className='params-card-ttl'),
        ]),
        *enfants,
    ])


# ── Onglet 1 : Démographie et enrôlement ─────────────────────────────────

_onglet_demo = html.Div(className='g2', style={'alignItems': 'start'}, children=[
    html.Div([
        _card('fa-users', 'Effectifs initiaux N_p', [
            _sl('N0_B',  'Paquet Bronze  (N0_B)',  50000, 5000, 200000, 1000),
            _sl('N0_A',  'Paquet Argent  (N0_A)',   8000, 1000,  50000,  500),
            _sl('N0_O',  'Paquet Or      (N0_O)',   1500,  100,  10000,  100),
            _sl('N0_Pl', 'Paquet Platine (N0_Pl)',   500,   50,   5000,   50),
        ]),
    ]),
    html.Div([
        _card('fa-chart-line', "Dynamique d'adhésion", [
            _sp('alpha', "Taux d'accroissement annuel α (%)", 4, 1, 12, 0.5,
                note="δₙ = α × (1+β)ⁿ. Calibré en deçà des taux d'enrôlement observés "
                     "au Brésil (8 %), en Argentine (7 %) et au Maroc (5 %) : hypothèse "
                     "prudente."),
            _sp('beta', "Taux d'amélioration β (%)", 1, 0, 5, 0.5,
                note="Renforcement progressif de la notoriété du régime."),
        ]),
    ]),
])


# ── Onglet 2 : Économique ────────────────────────────────────────────────

_onglet_eco = html.Div(className='g2', style={'alignItems': 'start'}, children=[
    html.Div([
        _card('fa-money-bill-trend-up', 'Cadrage macroéconomique', [
            _sp('tau_inf', "Taux d'inflation (%)", 2, 0, 8, 0.5,
                note="Norme de convergence de la BCEAO pour l'UEMOA. "
                     "S'applique aux cotisations comme aux prestations."),
            _sp('a_actu', "Taux d'actualisation (%)", 5, 0, 12, 0.5,
                note="Actualisation du coût net de l'État et des gains de recettes."),
        ]),
    ]),
    html.Div([
        _card('fa-building-columns', 'Paramètres institutionnels', [
            _sl('SMIG',   'SMIG mensuel (FCFA)',        64223, 40000, 130000, 1000,
                note='Décret n°2023-1710 du 7 août 2023.'),
            _sl('CMU_an', 'Prime CMU annuelle (FCFA)',   7000,  3000,  15000,  500),
            _sp('gamma',  'Chargement administratif (%)', 10,    5,     25,     1,
                note="Bas de la fourchette usuelle des régimes de sécurité sociale, "
                     "justifié par l'adossement au réseau de la DGID."),
        ]),
    ]),
])


# ── Onglet 3 : Subventions ───────────────────────────────────────────────

_onglet_sub = html.Div(className='g2', style={'alignItems': 'start'}, children=[
    html.Div([
        _card('fa-hand-holding-dollar', "Taux de subvention λ_b (%)", [
            _sp('lambda_sa',   'Santé — tous paquets',         50, 0, 80, 5,
                note="Reproduit le cofinancement public de la CMU."),
            _sp('lambda_at_B', 'AT/MP — Bronze',               40, 0, 80, 2),
            _sp('lambda_ma',   'Maternité — A, O, Platine',    70, 0, 90, 5,
                note="Traduit la politique de gratuité des soins obstétricaux."),
            _sp('lambda_pf',   'Prest. familiales — A, O, Pl', 60, 0, 80, 5),
        ]),
    ]),
    html.Div([
        _card('fa-piggy-bank', 'Branches longues', [
            _sp('lambda_id',    'Invalidité/Décès — O, Pl', 30, 0, 60, 5),
            _sp('lambda_re_O',  'Retraite — Or',            50, 0, 70, 5),
            _sp('lambda_re_Pl', 'Retraite — Platine',       40, 0, 70, 5),
            html.P("Les branches contributives de long terme reposent davantage "
                   "sur l'assuré, conformément à leur logique assurantielle.",
                   className='param-note'),
        ]),
    ]),
])


# ── Onglet 4 : CGU ───────────────────────────────────────────────────────
# Ne contient que ce que le décideur peut fixer : le régime tarifaire, les
# taux, les minimums de perception, les forfaits, le stock d'enrôlés et
# les hypothèses sur la collaboration. Le chiffre d'affaires de chaque
# assujetti et sa branche d'activité sont lus dans les microdonnées.

_onglet_cgu = html.Div([
    # Choix du régime tarifaire
    html.Div(className='params-card', style={
        'background': 'linear-gradient(135deg,#E3F2FD 0%,#F4F9FF 100%)',
        'borderLeft': '4px solid #1565C0', 'marginBottom': '1.2rem'}, children=[
        html.H3('Régime tarifaire appliqué', className='params-card-ttl',
                style={'marginBottom': '0.6rem'}),
        dcc.RadioItems(
            id='sl-regime_cgu',
            options=[
                {'label': "  Code général des impôts en vigueur (art. 134–141)", 'value': 0},
                {'label': "  Nouveau projet de code de l'administration fiscale", 'value': 1},
            ],
            value=0,
            labelStyle={'display': 'block', 'marginBottom': '0.35rem',
                        'fontSize': '0.9rem'},
        ),
        html.P("Le code en vigueur applique un taux proportionnel au chiffre "
               "d'affaires (5 % pour les services, 2 % pour les producteurs et "
               "revendeurs). Le nouveau projet de code ajoute des forfaits par "
               "catégorie (transport, commerce de détail, artisanat).",
               className='param-note'),
    ]),

    # Barème : taux et minimums (deux régimes)
    _card('fa-percent', 'Taux et minimums de perception', [
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr',
                        'gap': '1.2rem'}, children=[
            html.Div([
                _sp('taux_serv', 'Prestataires de services (%)', 5, 0, 10, 0.5),
                _sl('min_serv',  'Minimum services (FCFA/an)', 35000, 0, 100000, 5000),
                html.P("Régime RGU1 : divisions CITI ≥ 49 (services, réparation, "
                       "information, hôtellerie).", className='param-note'),
            ]),
            html.Div([
                _sp('taux_prod', 'Producteurs et revendeurs (%)', 2, 0, 10, 0.5),
                _sl('min_prod',  'Minimum producteurs (FCFA/an)', 25000, 0, 100000, 5000),
                html.P("Régime RGU3 : divisions CITI < 49 (industrie, "
                       "artisanat, commerce, transport).", className='param-note'),
            ]),
        ]),
    ]),

    # Forfaits du nouveau projet de code — modifiables
    _card('fa-file-invoice-dollar',
          "Forfaits du nouveau projet de code (FCFA/an)", [
        html.P("Ces montants sont appliqués aux assujettis relevant des "
               "catégories concernées lorsque le régime « Nouveau projet de code » "
               "est activé ci-dessus. Chaque palier est modifiable pour tester "
               "des réformes à venir.", className='param-note',
               style={'marginBottom': '0.8rem'}),

        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr',
                        'gap': '1.5rem'}, children=[
            html.Div([
                html.Div('Transport public de personnes', style={
                    'fontWeight': '700', 'color': '#1A2B4A',
                    'marginBottom': '0.6rem', 'fontSize': '0.88rem'}),
                _sl('fft_tp_16', '16 places ou moins',    130000, 50000, 500000, 5000),
                _sl('fft_tp_35', '17 à 35 places',        170000, 50000, 500000, 5000),
                _sl('fft_tp_45', '36 à 45 places',        225000, 50000, 500000, 5000),
                _sl('fft_tp_46', '46 places ou plus',     330000, 50000, 500000, 5000),
            ]),
            html.Div([
                html.Div('Transport public de marchandises', style={
                    'fontWeight': '700', 'color': '#1A2B4A',
                    'marginBottom': '0.6rem', 'fontSize': '0.88rem'}),
                _sl('fft_tm_10', '≤ 10 tonnes / 10 000 L', 190000, 50000, 600000, 5000),
                _sl('fft_tm_15', '10 à 15 tonnes',         245000, 50000, 600000, 5000),
                _sl('fft_tm_24', '15 à 24 tonnes',         320000, 50000, 600000, 5000),
                _sl('fft_tm_25', '> 24 tonnes / tracteurs', 415000, 50000, 600000, 5000),
            ]),
        ]),

        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr',
                        'gap': '1.5rem', 'marginTop': '1.2rem'}, children=[
            html.Div([
                html.Div('Commerce de détail', style={
                    'fontWeight': '700', 'color': '#1A2B4A',
                    'marginBottom': '0.6rem', 'fontSize': '0.88rem'}),
                _sl('fft_cd_mag', 'Magasins',              100000, 0, 200000, 5000),
                _sl('fft_cd_bou', 'Boutiques',              50000, 0, 200000, 2500),
                _sl('fft_cd_int', 'Catalogue / internet',   25000, 0, 200000, 2500),
                _sl('fft_cd_tab', 'Tabliers',               15000, 0, 200000, 1000),
                _sl('fft_cd_amb', 'Marchands ambulants',    10000, 0, 200000, 1000),
            ]),
            html.Div([
                html.Div('Artisanat', style={
                    'fontWeight': '700', 'color': '#1A2B4A',
                    'marginBottom': '0.6rem', 'fontSize': '0.88rem'}),
                _sl('fft_ar_fab', 'Fabrication (ébéniste, tailleur)',    100000, 0, 200000, 5000),
                _sl('fft_ar_ali', 'Alimentation (boulanger, pâtissier)', 100000, 0, 200000, 5000),
                _sl('fft_ar_bat', 'Bâtiment (plombier, électricien)',     50000, 0, 200000, 2500),
                _sl('fft_ar_ser', 'Service (coiffeur, mécanicien)',       50000, 0, 200000, 2500),
                _sl('fft_ar_aut', 'Autres (potier, horloger, boucher)',   25000, 0, 200000, 2500),
            ]),
        ]),
    ]),

    # Enrôlement et effet de la collaboration
    html.Div(className='g2', style={'alignItems': 'start',
                                     'marginTop': '1.2rem'}, children=[
        html.Div([
            _card('fa-user-check', "Enrôlement à la CGU (source DGID)", [
                _sl('stock_cgu_0', 'Contribuables CGU actuellement enrôlés',
                    60000, 0, 500000, 5000,
                    note="Stock effectif de contribuables CGU, tel qu'il figure "
                         "dans le fichier de la DGID. Distinct de la population "
                         "éligible (~1,89 million d'assujettis identifiés dans "
                         "l'EHCVM), qui est fixée par les données."),
                _sp('g_cgu_seul',
                    "Croissance annuelle propre à l'administration fiscale (%)",
                    3, 0, 15, 0.5,
                    note="Rythme d'enrôlement obtenu sans contrepartie sociale, "
                         "par l'effort de recouvrement de la DGID."),
            ]),
        ]),
        html.Div([
            _card('fa-handshake', "Effet de la collaboration avec le régime social", [
                _sp('part_nouveaux',
                    "Adhérents sociaux non déjà contribuables CGU (%)",
                    60, 0, 100, 5,
                    note="Paramètre central du module. Représente la part des "
                         "adhérents au régime social qui n'étaient pas contribuables "
                         "CGU auparavant : c'est l'effet d'attraction de la "
                         "protection sociale, et donc le rendement fiscal de la "
                         "collaboration entre administrations sociale et fiscale. "
                         "À 0 %, la collaboration ne rapporte rien."),
            ]),
        ]),
    ]),
])


# ── Layout global ────────────────────────────────────────────────────────

layout = html.Div([
    html.Div(className='page-hdr', children=[
        html.Div(className='page-hdr-inner', children=[
            html.H1(className='page-hdr-title', children=[
                html.I(className='fa-solid fa-sliders'),
                ' Paramètres du modèle',
            ]),
            html.P('Modifiez les paramètres puis cliquez sur « Simuler » pour '
                   'actualiser les résultats.', className='page-hdr-sub'),
        ]),
    ]),

    html.Div(className='page-body', children=[
        html.Div(style={'marginBottom': '1.5rem', 'display': 'flex',
                        'gap': '0.75rem', 'flexWrap': 'wrap'}, children=[
            html.Button(id='btn-simuler', n_clicks=0, className='btn-simuler', children=[
                html.I(className='fa-solid fa-play', style={'marginRight': '0.5rem'}),
                'Simuler',
            ]),
            html.Button(id='btn-reset', n_clicks=0, className='btn-reset-inline', children=[
                html.I(className='fa-solid fa-rotate-left', style={'marginRight': '0.4rem'}),
                'Réinitialiser',
            ]),
        ]),

        dcc.Tabs(id='tabs-params', value='t-demo', className='sub-tabs', children=[
            dcc.Tab(label='Démographie', value='t-demo', className='sub-tab',
                    selected_className='sub-tab--sel', children=[
                        html.Div(_onglet_demo, style={'paddingTop': '1.2rem'})]),
            dcc.Tab(label='Économique', value='t-eco', className='sub-tab',
                    selected_className='sub-tab--sel', children=[
                        html.Div(_onglet_eco, style={'paddingTop': '1.2rem'})]),
            dcc.Tab(label='Subventions', value='t-sub', className='sub-tab',
                    selected_className='sub-tab--sel', children=[
                        html.Div(_onglet_sub, style={'paddingTop': '1.2rem'})]),
            dcc.Tab(label='CGU', value='t-cgu', className='sub-tab',
                    selected_className='sub-tab--sel', children=[
                        html.Div(_onglet_cgu, style={'paddingTop': '1.2rem'})]),
        ]),
    ]),
])


# ── Identifiants ─────────────────────────────────────────────────────────

SL_ABS = ['N0_B', 'N0_A', 'N0_O', 'N0_Pl', 'SMIG', 'CMU_an',
          'min_serv', 'min_prod', 'stock_cgu_0',
          'fft_tp_16', 'fft_tp_35', 'fft_tp_45', 'fft_tp_46',
          'fft_tm_10', 'fft_tm_15', 'fft_tm_24', 'fft_tm_25',
          'fft_cd_mag', 'fft_cd_bou', 'fft_cd_int', 'fft_cd_tab', 'fft_cd_amb',
          'fft_ar_fab', 'fft_ar_ali', 'fft_ar_bat', 'fft_ar_ser', 'fft_ar_aut']

SL_PCT = ['alpha', 'beta', 'tau_inf', 'gamma', 'a_actu',
          'lambda_sa', 'lambda_at_B', 'lambda_ma', 'lambda_pf',
          'lambda_id', 'lambda_re_O', 'lambda_re_Pl',
          'taux_serv', 'taux_prod',
          'g_cgu_seul', 'part_nouveaux']

ALL_SL = SL_ABS + SL_PCT


# ── Simuler : sauvegarde les params et navigue vers /dashboard ───────────

@callback(
    Output('store-params', 'data'),
    Output('store-nav', 'data', allow_duplicate=True),
    Input('btn-simuler', 'n_clicks'),
    [State(f'sl-{s}', 'value') for s in ALL_SL],
    State('sl-regime_cgu', 'value'),
    prevent_initial_call=True,
)
def lancer_simulation(nc, *vals):
    if not nc:
        from dash.exceptions import PreventUpdate
        raise PreventUpdate
    slider_vals = vals[:-1]
    regime = vals[-1]
    p = {}
    for sid, v in zip(ALL_SL, slider_vals):
        if v is None:
            v = PARAMS_REF.get(sid, 0)
            if sid in SL_PCT:
                v *= 100
        p[sid] = v / 100 if sid in SL_PCT else v
    p['regime_cgu'] = regime if regime is not None else 0
    return p, '/dashboard'


# ── Labels dynamiques ────────────────────────────────────────────────────

for _sid in SL_ABS:
    @callback(
        Output(f'lbl-{_sid}', 'children'),
        Input(f'sl-{_sid}', 'value'),
        prevent_initial_call=False,
    )
    def _la(v, sid=_sid):
        if v is None:
            v = PARAMS_REF.get(sid, 0)
        return f'{int(v):,}'.replace(',', ' ')


for _sid in SL_PCT:
    @callback(
        Output(f'lbl-{_sid}', 'children'),
        Input(f'sl-{_sid}', 'value'),
        prevent_initial_call=False,
    )
    def _lp(v, sid=_sid):
        if v is None:
            v = PARAMS_REF.get(sid, 0) * 100
        return f'{v:.1f} %'


# ── Reset ────────────────────────────────────────────────────────────────

@callback(
    [Output(f'sl-{s}', 'value') for s in ALL_SL],
    Output('sl-regime_cgu', 'value'),
    Input('btn-reset', 'n_clicks'),
    prevent_initial_call=True,
)
def reset(_):
    abs_vals = [PARAMS_REF.get(s, 0) for s in SL_ABS]
    pct_vals = [round(PARAMS_REF.get(s, 0) * 100, 2) for s in SL_PCT]
    return abs_vals + pct_vals + [0]
