"""pages/dashboard.py - Tableau de bord"""
import re
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import html, dcc, callback, Input, Output
from simulation.moteur import simuler, INDICATEURS_BASE

PB = dict(
    font=dict(family='Arial,sans-serif', size=11, color='#1A2B4A'),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(240,246,255,0.5)',
    margin=dict(l=48, r=16, t=36, b=40),
    legend=dict(bgcolor='rgba(255,255,255,0.92)', bordercolor='#C5D8F0',
                borderwidth=1, font=dict(size=10)),
    xaxis=dict(showgrid=True, gridcolor='rgba(140,175,220,0.25)',
               linecolor='#C5D8F0', tickfont=dict(size=10)),
    yaxis=dict(showgrid=True, gridcolor='rgba(140,175,220,0.25)',
               linecolor='#C5D8F0', tickfont=dict(size=10)),
)

C = {
    'B': '#1565C0', 'A': '#2E9E5B', 'O': '#E8841A', 'Pl': '#8E44AD',
    'rec': '#1565C0', 'dep': '#C0392B',
}


def build_dashboard(df):
    d1, d40 = df.iloc[0], df.iloc[-1]
    viable   = df['Solde_cumule_M'].min() >= 0
    sol_fin  = df['Solde_cumule_M'].iloc[-1]
    n_star   = df.loc[df['Solde_cumule_M'] < 0, 'annee'].min() if not viable else None

    alerte = html.Div(
        className='alerte-ok' if viable else 'alerte-err',
        children=[
            html.I(className='fa-solid ' + ('fa-circle-check' if viable
                                             else 'fa-triangle-exclamation')),
            html.Span([
                html.Strong(
                    'Régime financièrement viable sur tout l\'horizon 2027-2066. '
                    if viable else f'Premier déficit cumulé en {n_star}. '
                ),
                f'Solde cumulé à 2066 : {sol_fin/1000:,.1f} Md FCFA.',
            ]),
        ],
    )

    kpis = html.Div(className='kpi-grid', children=[
        _kpi('Cotisants 2027',     f"{d1['CT_total']:,.0f}",     'fa-user-plus',    '#1565C0', '#E3F2FD'),
        _kpi('Cotisants 2066',     f"{d40['CT_total']:,.0f}",    'fa-users',        '#1976D2', '#E3F2FD'),
        _kpi('Pensionnaires 2066', f"{d40['NbPens_total']:,.0f}", 'fa-person-cane', '#0D47A1', '#E3F2FD'),
        _kpi('Solde cumulé 2066',  f"{sol_fin/1000:,.1f} Md",     'fa-scale-balanced',
             '#1B5E20' if viable else '#C62828',
             '#E8F5E9' if viable else '#FFEBEE'),
        _kpi('Couverture 2066',    f"{d40['Taux_couv']:.1f} %",  'fa-shield-halved', '#1976D2', '#E3F2FD'),
        _kpi('Recettes 2066',      f"{d40['Recettes_M']/1000:,.2f} Md", 'fa-coins',        '#1565C0', '#E3F2FD'),
    ])

    fgt_avant = [INDICATEURS_BASE['FGT0'], INDICATEURS_BASE['FGT1'], INDICATEURS_BASE['FGT2']]
    fgt_apres = [
        d40['FGT0_ap'],
        d40['FGT1_ap'],
        INDICATEURS_BASE['FGT2'] * (1 - d40['Taux_couv'] / 200),
    ]
    gini_av = INDICATEURS_BASE['Gini']
    gini_ap = d40['Gini_ap']

    return html.Div([
        html.Div(className='page-hdr', children=[
            html.Div(className='page-hdr-inner', children=[
                html.H1(className='page-hdr-title', children=[
                    html.I(className='fa-solid fa-chart-line'), ' Tableau de bord',
                ]),
                html.P('Résultats de la simulation'),
            ]),
        ]),
        html.Div(className='page-body', children=[
            alerte, kpis,
            # Ligne 1 : effectifs
            html.Div(className='g2', children=[
                _chart('Cotisants actifs et pensionnaires',
                       'Evolution du stock total de cotisants et du nombre de pensionnaires',
                       _fig1(df), '320px'),
                _chart('Répartition des cotisants par paquet',
                       'Structure des effectifs en 2027 et 2066',
                       _fig2_pie(df), '320px'),
            ]),
            # Ligne 2 : barres effectifs
            _chart("Effectifs de cotisants par paquet",
                   "Nombre de cotisants actifs par tranche de chiffre d'affaires",
                   _fig3_bars(df), '340px'),
            # Ligne 3 : finances
            _chart('Flux financiers annuels et viabilité du régime',
                   'Recettes, dépenses, solde annuel et solde cumulé sur 40 ans (2027-2066)',
                   _fig4_finances(df), '430px'),
            # Ligne 4 : depenses par branche (barres) + depenses catastrophiques
            html.Div(className='g2', children=[
                _chart('Dépenses par branche en 2066',
                       'Poids relatif de chaque branche en fin de période',
                       _fig6_bar_branches(df), '320px'),
                _chart('Évolution des dépenses catastrophiques de santé',
                       'Part des ménages exposés à des dépenses de santé ruineuses '
                       '(seuil de 10 % de la consommation totale)',
                       _fig_catastrophe(df), '320px'),
            ]),
            # Ligne 5 : cotisations + couverture
            html.Div(className='g2', children=[
                _chart('Cotisation mensuelle nominale par paquet',
                       'Montant nominal de la cotisation travailleur par paquet et par période',
                       _fig7_cotis_bar(df), '320px'),
                _chart('Taux de couverture de la population cible',
                       'Proportion des travailleurs informels assujettis à la CGU couverts',
                       _fig8_couv(df), '320px'),
            ]),
            # Ligne 6 : indicateurs redistributifs
            html.Div(className='g2', children=[
                _chart('Indices FGT de pauvreté (avant et après la réforme)',
                       "Comparaison de l'incidence, la profondeur et la sévérité de la pauvreté",
                       _fig9_fgt(fgt_avant, fgt_apres), '320px'),
                _chart('Inégalités et couverture (indice de Gini)',
                       "Coefficient de Gini avant et après introduction du régime",
                       _fig10_gini(gini_av, gini_ap, df), '320px'),
            ]),
        ]),
    ])


def _chart(titre, sub, fig, height='300px'):
    return html.Div(className='chart-card', children=[
        html.H3(titre, className='chart-title'),
        html.P(sub, className='chart-sub'),
        dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': height}),
    ])


def _kpi(label, value, icon, color, bg):
    # Extrait la cible numerique du texte formate (US : virgule=milliers, point=decimal)
    # pour alimenter le compteur anime (assets/countup.js), sans changer l'affichage.
    data = {}
    m = re.search(r'-?\d[\d,]*(?:\.\d+)?', value)
    if m:
        num = m.group(0)
        data = {
            'data-count-to': str(float(num.replace(',', ''))),
            'data-decimals': str(len(num.split('.')[1]) if '.' in num else 0),
            'data-sep':      ',' if ',' in num else '',
            'data-suffix':   value[m.end():],
        }
    return html.Div(
        className='kpi-card',
        style={'--kpi-color': color, '--kpi-bg': bg},
        children=[
            html.Div(className='kpi-ico', children=[html.I(className='fa-solid ' + icon)]),
            html.Div(children=[
                html.Div(value, className='kpi-val', **data),
                html.Div(label, className='kpi-lbl'),
            ]),
        ],
    )


def _fig1(df):
    ann = df['annee'].values
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ann, y=df['CT_total'], name='Cotisants actifs',
        mode='lines', line=dict(color=C['rec'], width=2.5),
        fill='tozeroy', fillcolor='rgba(21,101,192,0.10)',
        hovertemplate='Cotisants : %{y:,.0f}<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=ann, y=df['NbPens_total'], name='Pensionnaires',
        mode='lines', line=dict(color='#2E7D32', width=2.5),
        fill='tozeroy', fillcolor='rgba(46,125,50,0.10)',
        hovertemplate='Pensionnaires : %{y:,.1f}<extra></extra>',
    ))
    n0 = df.loc[df['NbPens_total'] > 0, 'annee']
    if not n0.empty:
        fig.add_vline(
            x=n0.min(),
            line=dict(dash='dot', color='#888', width=1.2),
            annotation_text=f'Premiers retraités ({n0.min()})',
            annotation_font_size=9,
        )
    fig.update_layout(**PB, hovermode='x unified',
                      xaxis_title='Année', yaxis_title='Nombre')
    return fig


def _fig2_pie(df):
    d1, d40 = df.iloc[0], df.iloc[-1]
    labels = ['Bronze', 'Argent', 'Or', 'Platine']
    cols   = ['CT_B', 'CT_A', 'CT_O', 'CT_Pl']
    colors = [C['B'], C['A'], C['O'], C['Pl']]
    fig = make_subplots(rows=1, cols=2,
                        specs=[[{'type': 'pie'}, {'type': 'pie'}]],
                        subplot_titles=['2027', '2066'])
    for i, (d, r, c) in enumerate([(d1, 1, 1), (d40, 1, 2)]):
        fig.add_trace(
            go.Pie(labels=labels, values=[d[c2] for c2 in cols],
                   marker=dict(colors=colors), hole=0.38, textinfo='percent',
                   hovertemplate='%{label}: %{value:,.0f}<extra></extra>'),
            row=r, col=c,
        )
    fig.update_layout(
        **{k: v for k, v in PB.items() if k not in ['xaxis', 'yaxis']},
        showlegend=True,
    )
    return fig


def _fig3_bars(df):
    ann_sel = [2027, 2031, 2036, 2041, 2046, 2051, 2056, 2061, 2066]
    sub = df[df['annee'].isin(ann_sel)]
    fig = go.Figure()
    for col, nom, ch in [('CT_B', 'Bronze', C['B']), ('CT_A', 'Argent', C['A']),
                          ('CT_O', 'Or', C['O']), ('CT_Pl', 'Platine', C['Pl'])]:
        fig.add_trace(go.Bar(
            x=sub['annee'], y=sub[col], name=nom,
            marker_color=ch, opacity=0.88,
            hovertemplate=f'<b>{nom}</b> : %{{y:,.0f}}<extra></extra>',
        ))
    fig.update_layout(**PB, barmode='stack', hovermode='x unified',
                      xaxis_title='Année', yaxis_title='Cotisants')
    return fig


def _fig4_finances(df):
    ann = df['annee'].values
    fig = make_subplots(rows=2, cols=1, row_heights=[0.62, 0.38],
                        shared_xaxes=True, vertical_spacing=0.07,
                        subplot_titles=('Recettes et dépenses (M FCFA)',
                                        'Soldes annuel et cumulé (M FCFA)'))
    fig.add_trace(go.Scatter(
        x=ann, y=df['Recettes_M'], name='Recettes',
        line=dict(color=C['rec'], width=2.5), fill='tozeroy',
        fillcolor='rgba(21,101,192,0.10)',
        hovertemplate='Recettes : %{y:,.1f} M<extra></extra>',
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=ann, y=df['Depenses_M'], name='Dépenses',
        line=dict(color=C['dep'], width=2.5), fill='tozeroy',
        fillcolor='rgba(198,40,40,0.07)',
        hovertemplate='Dépenses : %{y:,.1f} M<extra></extra>',
    ), row=1, col=1)
    colors_bar = ['#1B5E20' if s >= 0 else '#C62828' for s in df['Solde_annuel_M']]
    fig.add_trace(go.Bar(
        x=ann, y=df['Solde_annuel_M'], name='Solde annuel',
        marker_color=colors_bar, opacity=0.82,
        hovertemplate='Solde annuel : %{y:,.1f} M<extra></extra>',
    ), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=ann, y=df['Solde_cumule_M'], name='Solde cumulé',
        line=dict(color='#1565C0', width=2.5, dash='dash'),
        hovertemplate='Solde cumulé : %{y:,.1f} M<extra></extra>',
    ), row=2, col=1)
    fig.update_layout(**PB, height=430, hovermode='x unified')
    return fig


def _fig_catastrophe(df):
    # Evolution de l'incidence des depenses catastrophiques de sante (seuil 10 %)
    # a mesure que la couverture du regime s'etend. La ligne pointillee rappelle
    # le niveau avant reforme.
    ann = df['annee'].values
    avant = INDICATEURS_BASE['CAT10'] * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ann, y=df['CAT10_ap'] * 100, name='Avec le régime',
        mode='lines+markers', line=dict(color='#1565C0', width=2.5),
        marker=dict(size=5, color='#1565C0'),
        fill='tozeroy', fillcolor='rgba(21,101,192,0.10)',
        hovertemplate='%{x} : %{y:.2f} %% des ménages<extra></extra>',
    ))
    fig.add_hline(
        y=avant, line=dict(dash='dash', color='#C0392B', width=1.5),
        annotation_text=f'Avant réforme : {avant:.2f} %',
        annotation_position='top left', annotation_font_size=9,
        annotation_font_color='#C0392B',
    )
    fig.update_layout(**PB, hovermode='x unified',
                      xaxis_title='Année', yaxis_title='Ménages exposés (%)',
                      yaxis_ticksuffix=' %')
    return fig


def _fig6_bar_branches(df):
    d40 = df.iloc[-1]
    data = [
        ('Santé',            'Dep_sante_M',     '#1565C0'),
        ('AT/MP',            'Dep_atmp_M',      '#C0392B'),
        ('Maternité',        'Dep_maternite_M', '#E8841A'),
        ('Prest. familiales','Dep_pf_M',        '#2E9E5B'),
        ('Invalidité/Décès', 'Dep_id_M',        '#8E44AD'),
        ('Retraite',         'Dep_retraite_M',  '#0D2B5E'),
    ]
    total = sum(max(0, d40[c]) for _, c, _ in data) or 1
    # tri par montant decroissant
    data = sorted(data, key=lambda x: d40[x[1]], reverse=True)
    noms   = [d[0] for d in data]
    vals   = [max(0, d40[d[1]]) for d in data]
    colors = [d[2] for d in data]
    txt    = [f'{v/total*100:.1f} %' for v in vals]
    fig = go.Figure(go.Bar(
        x=vals, y=noms, orientation='h', marker_color=colors, opacity=0.9,
        text=txt, textposition='auto',
        hovertemplate='<b>%{y}</b> : %{x:,.1f} M FCFA<extra></extra>',
    ))
    pb = {k: v for k, v in PB.items() if k != 'yaxis'}
    fig.update_layout(**pb, xaxis_title='Millions FCFA',
                      yaxis=dict(autorange='reversed'), showlegend=False)
    return fig


def _fig7_cotis_bar(df):
    paquets = ['Bronze', 'Argent', 'Or', 'Platine']
    cols    = ['S_trav_B', 'S_trav_A', 'S_trav_O', 'S_trav_Pl']
    # une couleur par annee (degrade de bleu, du clair au fonce = progression)
    annees  = [(2027, '#90CAF9'), (2046, '#1976D2'), (2066, '#0D2B5E')]
    fig = go.Figure()
    for ann_v, coul in annees:
        row = df.loc[df['annee'] == ann_v].iloc[0]
        tau  = (1.02) ** (row['n'] - 1)
        vals = [row[c] * tau for c in cols]
        fig.add_trace(go.Bar(
            name=str(ann_v), x=paquets, y=vals, opacity=0.9,
            marker_color=coul,
            hovertemplate='%{x} (%{fullData.name}) : %{y:,.0f} FCFA/mois<extra></extra>',
        ))
    fig.update_layout(
        **{k: v for k, v in PB.items() if k != 'legend'},
        barmode='group',
        xaxis_title='Paquet', yaxis_title='FCFA/mois',
        legend=dict(title='Année'),
    )
    return fig


def _fig8_couv(df):
    ann = df['annee'].values
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ann, y=df['Taux_couv'], mode='lines+markers',
        line=dict(color=C['rec'], width=2.5),
        marker=dict(size=5, color=C['rec']),
        fill='tozeroy', fillcolor='rgba(21,101,192,0.10)',
        hovertemplate='Couverture : %{y:.2f} %%<extra></extra>',
    ))
    fig.update_layout(**PB, xaxis_title='Année', yaxis_title='Couverture (%)',
                      yaxis_ticksuffix=' %')
    return fig


def _fig9_fgt(fgt_av, fgt_ap):
    labels = ['FGT(0) Incidence', 'FGT(1) Profondeur', 'FGT(2) Sévérité']
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Avant réforme', x=labels, y=fgt_av,
        marker_color='#1976D2', opacity=0.85,
        hovertemplate='Avant : %{y:.4f}<extra></extra>',
    ))
    fig.add_trace(go.Bar(
        name='Après réforme', x=labels, y=fgt_ap,
        marker_color='#1B5E20', opacity=0.85,
        hovertemplate='Après : %{y:.4f}<extra></extra>',
    ))
    for i, (av, ap) in enumerate(zip(fgt_av, fgt_ap)):
        var = (ap - av) * 100
        fig.add_annotation(
            x=labels[i], y=max(av, ap) * 1.05,
            text=f'{var:+.3f} pp', showarrow=False,
            font=dict(size=9.5, color='#C62828' if var > 0 else '#1B5E20'),
        )
    fig.update_layout(**PB, barmode='group',
                      xaxis_title='Indicateur', yaxis_title='Valeur')
    return fig


def _fig10_gini(gini_av, gini_ap, df):
    ann      = df['annee'].values
    gini_evol = df['Gini_ap'].values
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=['Gini avant / après', 'Evolution Gini'],
                        column_widths=[0.4, 0.6])
    fig.add_trace(go.Bar(
        x=['Avant', 'Après'], y=[gini_av, gini_ap],
        marker_color=['#1976D2', '#1B5E20'], opacity=0.85,
        hovertemplate='%{x} : %{y:.4f}<extra></extra>',
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=ann, y=gini_evol, mode='lines',
        line=dict(color='#1565C0', width=2.5),
        hovertemplate='Gini %{x} : %{y:.4f}<extra></extra>',
    ), row=1, col=2)
    fig.update_layout(
        **{k: v for k, v in PB.items() if k not in ['xaxis', 'yaxis']},
    )
    return fig


layout = build_dashboard(simuler())
