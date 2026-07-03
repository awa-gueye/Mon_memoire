"""
pages/parametres.py - Paramètres de simulation
btn-simuler utilise store-nav pour naviguer (pas de Output url.pathname direct)
"""
from dash import html, dcc, callback, Input, Output, State
from simulation.moteur import PARAMS_REF


def _sl(pid, label, default, mn, mx, step, note=None):
    return html.Div(className='param-group', children=[
        html.Div(className='param-lbl', children=[
            html.Span(label),
            html.Span(id=f'lbl-{pid}', className='param-lbl-val', children=str(default)),
        ]),
        dcc.Slider(id=f'sl-{pid}', min=mn, max=mx, step=step, value=default,
                   marks=None,
                   updatemode='drag'),
        *([html.P(note, className='param-note')] if note else []),
    ])


def _sp(pid, label, default, mn, mx, step, note=None):
    return html.Div(className='param-group', children=[
        html.Div(className='param-lbl', children=[
            html.Span(label),
            html.Span(id=f'lbl-{pid}', className='param-lbl-val', children=f'{default} %'),
        ]),
        dcc.Slider(id=f'sl-{pid}', min=mn, max=mx, step=step, value=default,
                   marks=None,
                   updatemode='drag'),
        *([html.P(note, className='param-note')] if note else []),
    ])


layout = html.Div([
    html.Div(className='page-hdr', children=[
        html.Div(className='page-hdr-inner', children=[
            html.H1(className='page-hdr-title', children=[
                html.I(className='fa-solid fa-sliders'),
                ' Paramètres de simulation',
            ]),
            html.P('Modifiez les paramètres puis cliquez sur "Simuler" pour actualiser '
                   'les graphiques, les résultats et les indicateurs.',
                   className='page-hdr-sub'),
        ]),
    ]),
    html.Div(className='page-body', children=[
        # Boutons
        html.Div(style={'marginBottom': '1.5rem', 'display': 'flex',
                        'alignItems': 'center', 'gap': '1rem', 'flexWrap': 'wrap'}, children=[
            html.Button(id='btn-simuler', n_clicks=0, className='btn-simuler', children=[
                html.I(className='fa-solid fa-play', style={'marginRight': '0.5rem'}),
                'Simuler et voir le tableau de bord',
            ]),
            html.Button(id='btn-reset', n_clicks=0, className='btn-reset-inline', children=[
                html.I(className='fa-solid fa-rotate-left', style={'marginRight': '0.4rem'}),
                'Réinitialiser',
            ]),
        ]),

        html.Div(className='g2', style={'alignItems': 'start'}, children=[
            # Colonne gauche
            html.Div([
                html.Div(className='params-card', children=[
                    html.Div(className='params-card-hdr', children=[
                        html.Div(className='params-card-ico',
                                 children=[html.I(className='fa-solid fa-users')]),
                        html.H3('Effectifs initiaux N_p', className='params-card-ttl'),
                    ]),
                    _sl('N0_B',  'Paquet Bronze  (N0_B)',  50000, 5000, 200000, 1000),
                    _sl('N0_A',  'Paquet Argent  (N0_A)',   8000, 1000,  50000,  500),
                    _sl('N0_O',  'Paquet Or      (N0_O)',   1500,  100,  10000,  100),
                    _sl('N0_Pl', 'Paquet Platine (N0_Pl)',   500,   50,   5000,   50),
                ]),
                html.Div(className='params-card', children=[
                    html.Div(className='params-card-hdr', children=[
                        html.Div(className='params-card-ico',
                                 children=[html.I(className='fa-solid fa-chart-line')]),
                        html.H3('Dynamique de croissance', className='params-card-ttl'),
                    ]),
                    _sp('alpha',   "Taux d'accroissement annuel alpha (%)", 4, 1, 12, 0.5,
                        note='delta_n = alpha x (1+beta)^n - taux de croissance du stock de cotisants'),
                    _sp('beta',    "Taux d'amélioration beta (%)",           1, 0,  5, 0.5),
                    _sp('tau_inf', "Taux d'inflation (%)",                   2, 0,  8, 0.5),
                ]),
                html.Div(className='params-card', children=[
                    html.Div(className='params-card-hdr', children=[
                        html.Div(className='params-card-ico',
                                 children=[html.I(className='fa-solid fa-building-columns')]),
                        html.H3('Paramètres institutionnels', className='params-card-ttl'),
                    ]),
                    _sl('SMIG',   'SMIG mensuel (FCFA)',         64224, 40000, 130000, 1000),
                    _sl('CMU_an', 'Prime CMU annuelle (FCFA)',    7000,  3000,  15000,  500),
                    _sp('gamma',  'Chargement administratif (%)', 10,    5,     25,     1),
                ]),
            ]),

            # Colonne droite
            html.Div([
                html.Div(className='params-card', children=[
                    html.Div(className='params-card-hdr', children=[
                        html.Div(className='params-card-ico',
                                 children=[html.I(className='fa-solid fa-hand-holding-dollar')]),
                        html.H3("Taux de subvention de l'Etat lambda_b (%)",
                                className='params-card-ttl'),
                    ]),
                    _sp('lambda_sa',    'Santé - tous paquets',           50, 0, 80, 5),
                    _sp('lambda_at_B',  'AT/MP - Bronze',                 40, 0, 80, 2,
                        note="40 % - calibré sur données EHCVM en tenant compte de la "
                             "sous-estimation des revenus dans les enquêtes ménages"),
                    _sp('lambda_ma',    'Maternité - A, O, Platine',      70, 0, 90, 5),
                    _sp('lambda_pf',    'Prest. familiales - A, O, Pl',   60, 0, 80, 5),
                    _sp('lambda_id',    'Invalidité/Décès - O, Pl',       30, 0, 60, 5),
                    _sp('lambda_re_O',  'Retraite - Or',                  50, 0, 70, 5),
                    _sp('lambda_re_Pl', 'Retraite - Platine',             40, 0, 70, 5),
                ]),
            ]),
        ]),
    ]),
])


# ── Identifiants ─────────────────────────────────────────────────────────────
SL_ABS = ['N0_B', 'N0_A', 'N0_O', 'N0_Pl', 'SMIG', 'CMU_an']
SL_PCT = ['alpha', 'beta', 'tau_inf', 'gamma',
          'lambda_sa', 'lambda_at_B', 'lambda_ma', 'lambda_pf',
          'lambda_id', 'lambda_re_O', 'lambda_re_Pl']
ALL_SL = SL_ABS + SL_PCT


# ── Simuler : sauvegarde les params ET demande la navigation via store-nav ───
@callback(
    Output('store-params', 'data'),
    Output('store-nav', 'data', allow_duplicate=True),
    Input('btn-simuler', 'n_clicks'),
    [State(f'sl-{s}', 'value') for s in ALL_SL],
    prevent_initial_call=True,
)
def lancer_simulation(nc, *vals):
    if not nc:
        from dash.exceptions import PreventUpdate
        raise PreventUpdate
    p = {}
    for sid, v in zip(ALL_SL, vals):
        if v is None:
            v = PARAMS_REF.get(sid, 0)
            if sid in SL_PCT:
                v *= 100
        p[sid] = v / 100 if sid in SL_PCT else v
    return p, '/dashboard'


# ── Labels dynamiques ────────────────────────────────────────────────────────
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


# ── Reset ────────────────────────────────────────────────────────────────────
@callback(
    [Output(f'sl-{s}', 'value') for s in ALL_SL],
    Input('btn-reset', 'n_clicks'),
    prevent_initial_call=True,
)
def reset(_):
    abs_vals = [PARAMS_REF.get(s, 0) for s in SL_ABS]
    pct_vals = [round(PARAMS_REF.get(s, 0) * 100, 2) for s in SL_PCT]
    return abs_vals + pct_vals
