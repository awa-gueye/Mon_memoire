"""pages/cgu.py — Onglet CGU du tableau de bord.

Met en valeur la CGU (recettes projetées, taux de couverture) et mesure ce
que l'administration fiscale gagne à collaborer avec l'administration sociale.
Reproduit la logique de SenSim : chaque assujetti paie sa CGU selon son
secteur et son chiffre d'affaires, lus dans les microdonnées.
"""
import re
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc
from simulation.moteur import (simuler, cgu_par_paquet, cgu_individuelle,
                               cgu_moyenne, FORFAITS_CGU, CIBLE_CGU,
                               CIBLE_TOTALE, CIBLE_PAR_PAQUET,
                               fusionner_params, PAQUETS)

# Palette
PB = dict(
    font=dict(family='Arial,sans-serif', size=11, color='#1A2B4A'),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(240,246,255,0.5)',
    margin=dict(l=54, r=16, t=36, b=40),
    legend=dict(bgcolor='rgba(255,255,255,0.92)', bordercolor='#C5D8F0',
                borderwidth=1, font=dict(size=10)),
    xaxis=dict(showgrid=True, gridcolor='rgba(140,175,220,0.25)',
               linecolor='#C5D8F0', tickfont=dict(size=10)),
    yaxis=dict(showgrid=True, gridcolor='rgba(140,175,220,0.25)',
               linecolor='#C5D8F0', tickfont=dict(size=10)),
)
SEUL = '#94A3B8'   # gris : sans collaboration
COMB = '#1565C0'   # bleu : avec collaboration
GAIN = '#2E9E5B'   # vert : gain de la collaboration
OR   = '#E8841A'
NOMS_PAQUETS = {'B': 'Bronze', 'A': 'Argent', 'O': 'Or', 'Pl': 'Platine'}


# ══════════════════════════════════════════════════════════════════════════════
# PAGE
# ══════════════════════════════════════════════════════════════════════════════

def build_cgu(df, params=None):
    params = params or {}
    d1, dF = df.iloc[0], df.iloc[-1]
    gain_cum = dF['Gain_collab_actu_cum_M']

    # Indicateurs clés — six cartes
    kpis = html.Div(className='kpi-grid', children=[
        _kpi("Contribuables CGU en 2050 (sans collaboration)",
             f"{dF['N_cgu_seul']:,.0f}", 'fa-user', SEUL, '#F1F5F9'),
        _kpi("Contribuables CGU en 2050 (avec collaboration)",
             f"{dF['N_cgu_comb']:,.0f}", 'fa-user-plus', COMB, '#E3F2FD'),
        _kpi("Nouveaux contribuables attirés en 2050",
             f"{dF['Nouveaux_cgu']:,.0f}", 'fa-arrow-trend-up', GAIN, '#E8F5E9'),
        _kpi("Recettes CGU 2050 (avec collaboration)",
             f"{dF['R_cgu_comb_M']/1000:,.2f} Md", 'fa-coins', COMB, '#E3F2FD'),
        _kpi("Gain de recettes en 2050",
             f"+{dF['Gain_collab_M']/1000:,.2f} Md",
             'fa-hand-holding-dollar', GAIN, '#E8F5E9'),
        _kpi("Gain cumulé actualisé 2027–2050",
             f"{gain_cum/1000:,.1f} Md", 'fa-sack-dollar', GAIN, '#E8F5E9'),
    ])

    # Encart : message central
    encart = html.Div(className='chart-card', style={
        'background': 'linear-gradient(135deg,#E8F5E9 0%,#F1F8F4 100%)',
        'borderLeft': f'4px solid {GAIN}'}, children=[
        html.H3("L'intérêt de la collaboration entre administrations",
                className='chart-title'),
        html.P([
            "En adossant la protection sociale à la CGU, l'administration fiscale "
            f"attire {dF['Nouveaux_cgu']:,.0f} contribuables supplémentaires à "
            f"l'horizon 2050, portant le taux de couverture de la CGU de "
            f"{dF['Taux_cgu_seul']:.2f} % à {dF['Taux_cgu_comb']:.2f} % de la "
            "population éligible. ",
            html.Strong(f"Le gain de recettes cumulé, actualisé, s'élève à "
                        f"{gain_cum/1000:,.1f} milliards de FCFA sur la période "
                        "2027–2050."),
            " Ce gain mesure ce que la puissance publique recouvre en plus parce "
            "que la contrepartie sociale incite à la déclaration.",
        ], className='chart-sub', style={'fontSize': '0.95rem', 'lineHeight': '1.6'}),
    ])

    return html.Div([
        html.Div(className='page-hdr', children=[
            html.Div(className='page-hdr-inner', children=[
                html.H1(className='page-hdr-title', children=[
                    html.I(className='fa-solid fa-file-invoice-dollar'),
                    ' Contribution globale unique',
                ]),
                html.P("Modélisation des recettes de CGU et de l'effet "
                       "d'entraînement de la protection sociale sur l'enrôlement "
                       "fiscal", className='page-hdr-sub'),
            ]),
        ]),

        html.Div(className='page-body', children=[
            kpis,
            encart,

            html.Div(className='g2', children=[
                _chart("Enrôlement à la CGU",
                       "Nombre de contribuables, selon que la CGU est adossée "
                       "ou non à la protection sociale",
                       _fig_enrolement(df), '340px'),
                _chart("Taux de couverture de la CGU",
                       "Part de la population éligible effectivement enrôlée",
                       _fig_taux(df), '340px'),
            ]),

            _chart("Recettes de CGU projetées",
                   "Comparaison des deux scénarios ; l'aire verte matérialise "
                   "le gain attribuable à la collaboration",
                   _fig_recettes(df), '430px'),

            html.Div(className='g2', children=[
                _chart("Gain annuel de la collaboration",
                       "Recettes supplémentaires de CGU, par année",
                       _fig_gain(df), '320px'),
                _chart("Sensibilité à l'effet d'attraction",
                       "Gain cumulé actualisé selon la part des adhérents "
                       "sociaux qui n'étaient pas déjà contribuables",
                       _fig_sensibilite(params), '320px'),
            ]),

            html.Div(className='g2', style={'alignItems': 'start'}, children=[
                _tab_cgu_paquet(dF, params),
                _tab_bareme_actif(params),
            ]),
        ]),
    ])


# ══════════════════════════════════════════════════════════════════════════════
# FIGURES
# ══════════════════════════════════════════════════════════════════════════════

def _fig_enrolement(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['annee'], y=df['N_cgu_seul'],
                             name='CGU seule',
                             line=dict(color=SEUL, width=2.5, dash='dash')))
    fig.add_trace(go.Scatter(x=df['annee'], y=df['N_cgu_comb'],
                             name='CGU + protection sociale',
                             line=dict(color=COMB, width=3), fill='tonexty',
                             fillcolor='rgba(46,158,91,0.18)'))
    fig.update_layout(**PB, hovermode='x unified')
    fig.update_yaxes(title_text='Contribuables CGU')
    return fig


def _fig_taux(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['annee'], y=df['Taux_cgu_seul'],
                             name='CGU seule',
                             line=dict(color=SEUL, width=2.5, dash='dash')))
    fig.add_trace(go.Scatter(x=df['annee'], y=df['Taux_cgu_comb'],
                             name='CGU + protection sociale',
                             line=dict(color=COMB, width=3)))
    fig.update_layout(**PB, hovermode='x unified')
    fig.update_yaxes(title_text='Taux de couverture (%)', ticksuffix=' %')
    return fig


def _fig_recettes(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['annee'], y=df['R_cgu_seul_M']/1000,
                             name='Recettes, CGU seule',
                             line=dict(color=SEUL, width=2.5, dash='dash')))
    fig.add_trace(go.Scatter(x=df['annee'], y=df['R_cgu_comb_M']/1000,
                             name='Recettes, CGU + protection sociale',
                             line=dict(color=COMB, width=3), fill='tonexty',
                             fillcolor='rgba(46,158,91,0.22)'))
    fig.update_layout(**PB, hovermode='x unified')
    fig.update_yaxes(title_text='Milliards de FCFA', ticksuffix=' Md')
    return fig


def _fig_gain(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['annee'], y=df['Gain_collab_M']/1000,
                         name='Gain annuel',
                         marker_color=GAIN, opacity=0.85))
    fig.update_layout(**PB, showlegend=False)
    fig.update_yaxes(title_text='Milliards de FCFA', ticksuffix=' Md')
    return fig


def _fig_sensibilite(params):
    """Gain cumulé actualisé selon part_nouveaux : le graphe qui répond au
    coordonnateur. À 0 % d'effet d'attraction, le gain est nul ; plus l'effet
    est fort, plus la collaboration rapporte."""
    parts = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    gains = []
    for pn in parts:
        pp = dict(params or {}); pp['part_nouveaux'] = pn
        gains.append(simuler(pp).iloc[-1]['Gain_collab_actu_cum_M'] / 1000)
    ref = (params or {}).get('part_nouveaux', 0.60)
    cols = [GAIN if abs(p - ref) < 1e-6 else 'rgba(46,158,91,0.42)' for p in parts]
    fig = go.Figure(go.Bar(
        x=[f'{int(p*100)} %' for p in parts], y=gains, marker_color=cols,
        text=[f'{g:,.0f}' for g in gains], textposition='outside',
        textfont=dict(size=10)))
    fig.update_layout(**PB, showlegend=False)
    fig.update_xaxes(title_text="Part des adhérents non déjà contribuables")
    fig.update_yaxes(title_text='Gain cumulé (Md)', ticksuffix=' Md')
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# TABLEAUX
# ══════════════════════════════════════════════════════════════════════════════

def _tab_cgu_paquet(dF, params):
    """CGU annuelle moyenne due par paquet, calculée sur les microdonnées."""
    p = fusionner_params(params)
    cgu_pk = cgu_par_paquet(p)
    cgu_mo = cgu_moyenne(p)

    lignes = [
        html.Tr([
            html.Td(NOMS_PAQUETS[pk], style={'fontWeight': '600'}),
            html.Td(f"{CIBLE_PAR_PAQUET[pk]*100:.2f} %".replace('.', ','),
                    style={'textAlign': 'right', 'color': '#64748B'}),
            html.Td(f"{cgu_pk[pk]:,.0f}".replace(',', ' '),
                    style={'textAlign': 'right'}),
        ]) for pk in PAQUETS
    ]
    lignes.append(html.Tr([
        html.Td('Moyenne pondérée', style={'fontWeight': '700'}),
        html.Td('100,00 %', style={'textAlign': 'right', 'color': '#64748B',
                                    'fontWeight': '700'}),
        html.Td(f"{cgu_mo:,.0f}".replace(',', ' '),
                style={'textAlign': 'right', 'fontWeight': '700'}),
    ], style={'borderTop': '2px solid #C5D8F0'}))

    reforme = int(params.get('regime_cgu', 0)) == 1
    src = ("nouveau projet de code" if reforme
           else "code général des impôts en vigueur")

    return html.Div(className='chart-card', children=[
        html.H3('CGU annuelle due, par paquet', className='chart-title'),
        html.P(f"Moyenne pondérée par les poids de sondage EHCVM, régime : "
               f"{src}. Calcul individuel sur les 5 640 assujettis identifiés.",
               className='chart-sub'),
        html.Table(className='tbl', style={'width': '100%'}, children=[
            html.Thead(html.Tr([
                html.Th('Paquet'),
                html.Th('Part de la cible', style={'textAlign': 'right'}),
                html.Th('CGU due (FCFA/an)', style={'textAlign': 'right'})])),
            html.Tbody(lignes),
        ]),
    ])


def _tab_bareme_actif(params):
    """Barème effectivement appliqué (taux et minimums, ou forfaits selon
    le régime choisi). Reflète les paramètres du décideur."""
    p = fusionner_params(params)
    reforme = int(params.get('regime_cgu', 0)) == 1

    lignes = [
        html.Tr([html.Td('Régime tarifaire', style={'fontWeight': '600'}),
                 html.Td('Nouveau projet de code' if reforme
                         else 'Code en vigueur',
                         style={'textAlign': 'right', 'color': COMB,
                                'fontWeight': '700'})]),
        html.Tr([html.Td('Prestataires de services'),
                 html.Td(f"{p['taux_serv']*100:.1f} %".replace('.', ',')
                         + f" (min {p['min_serv']:,.0f})".replace(',', ' '),
                         style={'textAlign': 'right'})]),
        html.Tr([html.Td('Producteurs et revendeurs'),
                 html.Td(f"{p['taux_prod']*100:.1f} %".replace('.', ',')
                         + f" (min {p['min_prod']:,.0f})".replace(',', ' '),
                         style={'textAlign': 'right'})]),
    ]

    if reforme:
        lignes.append(html.Tr([
            html.Td('Forfaits appliqués (moyenne)', colSpan=2, style={
                'fontWeight': '700', 'background': '#F1F5F9',
                'fontSize': '0.82rem', 'padding': '0.45rem 0.6rem',
                'paddingTop': '0.8rem'}),
        ]))
        moyennes = [
            ('Transport public de personnes',
             (p['fft_tp_16']+p['fft_tp_35']+p['fft_tp_45']+p['fft_tp_46'])/4),
            ('Transport public de marchandises',
             (p['fft_tm_10']+p['fft_tm_15']+p['fft_tm_24']+p['fft_tm_25'])/4),
            ('Commerce de détail',
             (p['fft_cd_mag']+p['fft_cd_bou']+p['fft_cd_int']
              +p['fft_cd_tab']+p['fft_cd_amb'])/5),
            ('Artisanat',
             (p['fft_ar_fab']+p['fft_ar_ali']+p['fft_ar_bat']
              +p['fft_ar_ser']+p['fft_ar_aut'])/5),
        ]
        for lib, val in moyennes:
            lignes.append(html.Tr([
                html.Td(lib, style={'paddingLeft': '1.2rem'}),
                html.Td(f"{val:,.0f}".replace(',', ' ') + " FCFA/an",
                        style={'textAlign': 'right'}),
            ]))

    return html.Div(className='chart-card', children=[
        html.H3("Barème effectivement appliqué", className='chart-title'),
        html.P("Reflète les paramètres actuels ; les tarifs sont modifiables "
               "dans l'onglet CGU des paramètres.",
               className='chart-sub'),
        html.Table(className='tbl', style={'width': '100%'}, children=[
            html.Tbody(lignes),
        ]),
    ])


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _chart(titre, sub, fig, height='300px'):
    return html.Div(className='chart-card', children=[
        html.H3(titre, className='chart-title'),
        html.P(sub, className='chart-sub'),
        dcc.Graph(figure=fig, config={'displayModeBar': False},
                  style={'height': height}),
    ])


def _kpi(label, value, icon, color, bg):
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
            html.Div(className='kpi-ico',
                     children=[html.I(className='fa-solid ' + icon)]),
            html.Div(children=[
                html.Div(value, className='kpi-val', **data),
                html.Div(label, className='kpi-lbl'),
            ]),
        ],
    )
