"""pages/resultats.py - Tableau des résultats avec export Excel"""
import io
import pandas as pd
from dash import html, dcc, callback, Input, Output, State
from simulation.moteur import simuler, INDICATEURS_BASE


def _mini(val, lbl, sub, color, bg, icon):
    """Petite carte de synthèse (indicateur clé)."""
    return html.Div(className='kpi-card', style={'--kpi-color': color, '--kpi-bg': bg},
                    children=[
        html.Div(className='kpi-ico', children=[html.I(className='fa-solid ' + icon)]),
        html.Div(children=[
            html.Div(val, className='kpi-val'),
            html.Div(lbl, className='kpi-lbl'),
            html.Div(sub, style={'fontSize': '0.72rem', 'color': '#64748B',
                                 'marginTop': '0.15rem'}),
        ]),
    ])


def _synthese(df):
    """Bloc de synthèse : les résultats clés de l'étude, groupés par objectif."""
    d1, dF = df.iloc[0], df.iloc[-1]
    B = INDICATEURS_BASE

    BLEU, BLEUF = '#1565C0', '#E3F2FD'
    VERT, VERTF = '#2E9E5B', '#E8F5E9'
    OR,   ORF   = '#E8841A', '#FDF0E3'

    # Objectif 2 - Viabilité financière
    viab = html.Div([
        html.Div('Viabilité financière du régime', className='res-sec-ttl'),
        html.Div(className='kpi-grid', children=[
            _mini(f"{dF['Solde_cumule_M']/1000:,.2f} Md",
                  "Solde cumulé en 2050",
                  "Réserve constituée sur 24 ans", VERT, VERTF, 'fa-scale-balanced'),
            _mini(f"{dF['Recettes_M']/1000:,.2f} Md",
                  "Recettes annuelles en 2050",
                  f"contre {d1['Recettes_M']/1000:,.2f} Md en 2027", BLEU, BLEUF, 'fa-coins'),
            _mini(f"{dF['Depenses_M']/1000:,.2f} Md",
                  "Dépenses annuelles en 2050",
                  "prestations servies", BLEU, BLEUF, 'fa-money-bill-transfer'),
            _mini(f"{dF['CT_total']:,.0f}",
                  "Cotisants en 2050",
                  f"contre {d1['CT_total']:,.0f} en 2027", BLEU, BLEUF, 'fa-users'),
        ]),
    ])

    # Position budgétaire de l'État
    etat = html.Div([
        html.Div("Position budgétaire de l'État (cumul actualisé 2027 à 2050)",
                 className='res-sec-ttl'),
        html.Div(className='kpi-grid', children=[
            _mini(f"{dF['Sub_actu_cum_M']/1000:,.2f} Md",
                  "Subvention publique cumulée",
                  "coût pour l'État, actualisé", OR, ORF, 'fa-hand-holding-dollar'),
            _mini(f"{dF['R_cgu_comb_actu_cum_M']/1000:,.1f} Md",
                  "CGU sécurisée cumulée",
                  "recettes fiscales adossées au régime", VERT, VERTF, 'fa-file-invoice-dollar'),
            _mini(f"{dF['Gain_collab_actu_cum_M']/1000:,.1f} Md",
                  "Gain fiscal du régime social",
                  "contribuables ramenés dans le champ CGU", VERT, VERTF, 'fa-sack-dollar'),
            _mini(f"{dF['Taux_couv']:.2f} %",
                  "Taux de couverture en 2050",
                  "part de la population cible affiliée", BLEU, BLEUF, 'fa-shield-halved'),
        ]),
    ])

    # Objectif 3 - Impact redistributif (couverture universelle)
    fgt0_u = dF['FGT0_ap']   # potentiel = valeur à couverture ~100 %? non : interp au taux réel
    # Pour l'impact "plein", on affiche l'écart entre AVANT et le POTENTIEL (couverture universelle)
    from simulation.moteur import INDICATEURS_POTENTIEL as POT
    impact = html.Div([
        html.Div("Impact redistributif (potentiel, en couverture universelle)",
                 className='res-sec-ttl'),
        html.Div(className='kpi-grid', children=[
            _mini(f"{B['FGT0']*100:.2f} % → {POT['FGT0']*100:.2f} %",
                  "Incidence de la pauvreté",
                  "FGT(0), avant et après le régime", BLEU, BLEUF, 'fa-arrow-trend-down'),
            _mini(f"{B['CAT10']*100:.2f} % → {POT['CAT10']*100:.2f} %",
                  "Dépenses de santé catastrophiques",
                  "ménages exposés (seuil 10 %)", VERT, VERTF, 'fa-heart-pulse'),
            _mini(f"{B['FGT1']*100:.2f} % → {POT['FGT1']*100:.2f} %",
                  "Profondeur de la pauvreté",
                  "FGT(1)", BLEU, BLEUF, 'fa-ruler-vertical'),
            _mini(f"{B['Gini']:.4f} → {POT['Gini']:.4f}",
                  "Inégalité (coefficient de Gini)",
                  "quasi inchangé", BLEU, BLEUF, 'fa-chart-pie'),
        ]),
    ])

    return html.Div(style={'marginBottom': '2rem'}, children=[viab, etat, impact])


def build_resultats(df):
    viable  = df['Solde_cumule_M'].min() >= 0
    sol_fin = df['Solde_cumule_M'].iloc[-1]
    cols = [
        ('annee',          'Année',           False),
        ('CT_B',           'Bronze',          False),
        ('CT_A',           'Argent',          False),
        ('CT_O',           'Or',              False),
        ('CT_Pl',          'Platine',         False),
        ('CT_total',       'Total cotisants', False),
        ('NbPens_total',   'Pensionnaires',   False),
        ('Recettes_M',     'Recettes (M)',    False),
        ('Depenses_M',     'Dépenses (M)',    False),
        ('Dep_sante_M',    'Santé (M)',       False),
        ('Dep_retraite_M', 'Retraite (M)',    False),
        ('Solde_annuel_M', 'Solde annuel (M)', True),
        ('Solde_cumule_M', 'Solde cumulé (M)', True),
        ('Taux_couv',      'Couverture %',    False),
        ('FGT0_ap',        'FGT(0) après',    False),
        ('Gini_ap',        'Gini après',      False),
    ]
    thead = html.Thead(html.Tr([
        html.Th(lbl, style={'whiteSpace': 'nowrap'}) for _, lbl, _ in cols
    ]))
    rows = []
    for _, row in df.iterrows():
        cells = []
        for col, _, is_sol in cols:
            v = row[col]
            if col == 'annee':
                cells.append(html.Td(int(v)))
            elif col in ('CT_B', 'CT_A', 'CT_O', 'CT_Pl', 'CT_total', 'NbPens_total'):
                cells.append(html.Td(f'{v:,.0f}'))
            elif col == 'Taux_couv':
                cells.append(html.Td(f'{v:.2f} %'))
            elif col in ('FGT0_ap', 'Gini_ap'):
                cells.append(html.Td(f'{v:.4f}'))
            elif is_sol:
                cells.append(html.Td(f'{v:,.1f}',
                                     className='td-pos' if v >= 0 else 'td-neg'))
            else:
                cells.append(html.Td(f'{v:,.1f}'))
        rows.append(html.Tr(cells))

    return html.Div([
        html.Div(className='page-hdr', children=[
            html.Div(className='page-hdr-inner', children=[
                html.H1(className='page-hdr-title', children=[
                    html.I(className='fa-solid fa-table'), ' Tableau des résultats',
                ]),
                html.P(
                    'Données annuelles complètes de la simulation sur 24 ans (2027-2050). '
                    'Montants exprimés en millions de FCFA.',
                    className='page-hdr-sub',
                ),
            ]),
        ]),
        html.Div(className='page-body', children=[
            html.Div(
                className='alerte-ok' if viable else 'alerte-err',
                style={'marginBottom': '1.5rem'},
                children=[
                    html.I(className='fa-solid ' + ('fa-circle-check' if viable
                                                     else 'fa-triangle-exclamation')),
                    html.Span([
                        html.Strong('Régime viable. ' if viable else 'Régime déficitaire. '),
                        f'Solde cumulé 2050 : {sol_fin:,.1f} M FCFA.',
                    ]),
                ],
            ),

            # Synthèse : résultats clés de l'étude
            _synthese(df),

            html.Div('Données annuelles détaillées', className='res-sec-ttl'),
            html.Div(style={'marginBottom': '1.2rem', 'display': 'flex', 'gap': '0.8rem'},
                     children=[
                html.Button(id='btn-export-excel', n_clicks=0, className='btn-export',
                            children=[
                    html.I(className='fa-solid fa-file-excel',
                           style={'marginRight': '0.4rem'}),
                    'Exporter en Excel (.xlsx)',
                ]),
                html.Button(id='btn-export-csv', n_clicks=0, className='btn-export',
                            children=[
                    html.I(className='fa-solid fa-file-csv',
                           style={'marginRight': '0.4rem'}),
                    'Exporter en CSV',
                ]),
            ]),
            html.Div(className='tbl-wrap', children=[
                html.Table(className='data-tbl', children=[thead, html.Tbody(rows)]),
            ]),
        ]),
    ])


layout = build_resultats(simuler())


@callback(
    Output('dl-excel', 'data'),
    Input('btn-export-excel', 'n_clicks'),
    State('store-params', 'data'),
    prevent_initial_call=True,
)
def export_excel(nc, params_data):
    if not nc:
        return None
    df = simuler(params_data or {})
    df_exp = df.rename(columns={
        'annee': 'Année', 'CT_B': 'Cotisants Bronze', 'CT_A': 'Cotisants Argent',
        'CT_O': 'Cotisants Or', 'CT_Pl': 'Cotisants Platine',
        'CT_total': 'Total cotisants', 'NbPens_total': 'Pensionnaires',
        'Recettes_M': 'Recettes (M FCFA)', 'Depenses_M': 'Dépenses (M FCFA)',
        'Dep_sante_M': 'Santé (M)', 'Dep_atmp_M': 'AT/MP (M)',
        'Dep_maternite_M': 'Maternité (M)', 'Dep_pf_M': 'Prest. fam. (M)',
        'Dep_id_M': 'Invalidité (M)', 'Dep_retraite_M': 'Retraite (M)',
        'Solde_annuel_M': 'Solde annuel (M)', 'Solde_cumule_M': 'Solde cumulé (M)',
        'Taux_couv': 'Couverture (%)', 'FGT0_ap': 'FGT(0) après',
        'FGT1_ap': 'FGT(1) après', 'Gini_ap': 'Gini après',
    })
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df_exp.to_excel(writer, sheet_name='Simulation CGU', index=False)
    buf.seek(0)
    return dcc.send_bytes(buf.read(), 'simulation_cgu.xlsx')


@callback(
    Output('dl-excel', 'data', allow_duplicate=True),
    Input('btn-export-csv', 'n_clicks'),
    State('store-params', 'data'),
    prevent_initial_call=True,
)
def export_csv(nc, params_data):
    if not nc:
        return None
    df = simuler(params_data or {})
    return dcc.send_data_frame(df.to_csv, 'simulation_cgu.csv', index=False)
