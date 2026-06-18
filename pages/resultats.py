"""pages/resultats.py - Tableau des résultats avec export Excel"""
import io
import pandas as pd
from dash import html, dcc, callback, Input, Output, State
from simulation.moteur import simuler


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
                    'Données annuelles complètes de la simulation sur 40 ans (2027-2066). '
                    'Montants exprimés en millions de FCFA.',
                    className='page-hdr-sub',
                ),
            ]),
        ]),
        html.Div(className='page-body', children=[
            html.Div(
                className='alerte-ok' if viable else 'alerte-err',
                style={'marginBottom': '1rem'},
                children=[
                    html.I(className='fa-solid ' + ('fa-circle-check' if viable
                                                     else 'fa-triangle-exclamation')),
                    html.Span([
                        html.Strong('Régime viable. ' if viable else 'Régime déficitaire. '),
                        f'Solde cumulé 2066 : {sol_fin:,.1f} M FCFA.',
                    ]),
                ],
            ),
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
