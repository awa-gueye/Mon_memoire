"""
pages/simulation.py - Simulation individuelle d'un cotisant

Deux sections :
  - Parametres  : sliders + bouton Simuler
  - Resultats   : KPIs + tableau + droits + 3 graphiques (tout en un)

Apres clic sur Simuler -> on passe directement sur Resultats.
"""

import plotly.graph_objects as go
from dash import html, dcc, callback, Input, Output, State, callback_context

from simulation.moteur import PARAMS_REF, DEMO

PB = dict(
    font=dict(family='Arial,sans-serif', size=11, color='#1A2B4A'),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(240,246,255,0.5)',
    margin=dict(l=48, r=16, t=40, b=40),
    legend=dict(bgcolor='rgba(255,255,255,0.92)', bordercolor='#C5D8F0',
                borderwidth=1, font=dict(size=10)),
    xaxis=dict(showgrid=True, gridcolor='rgba(140,175,220,0.25)',
               linecolor='#C5D8F0', tickfont=dict(size=10)),
    yaxis=dict(showgrid=True, gridcolor='rgba(140,175,220,0.25)',
               linecolor='#C5D8F0', tickfont=dict(size=10)),
)

PAQUETS_LABELS = {'B': 'Bronze', 'A': 'Argent', 'O': 'Or', 'Pl': 'Platine'}
PAQUETS_COLORS = {'B': '#1565C0', 'A': '#2E9E5B', 'O': '#E8841A', 'Pl': '#8E44AD'}
TRANCHES       = {'B': '0 - 5 M', 'A': '5 - 15 M', 'O': '15 - 30 M', 'Pl': '30 - 50 M'}

BRANCHES_LABEL = {
    'Sante_CMU':              'Santé (CMU)',
    'Accidents_du_travail':   'Accidents du travail',
    'Maternite':              'Maternité',
    'Prestations_familiales': 'Prestations familiales',
    'Invalidite_Deces':       'Invalidité/Décés',
    'Retraite':               'Retraite',
}
BRANCHES_PAR_PAQUET = {
    'B':  ['Sante_CMU', 'Accidents_du_travail'],
    'A':  ['Sante_CMU', 'Accidents_du_travail', 'Maternite', 'Prestations_familiales'],
    'O':  ['Sante_CMU', 'Accidents_du_travail', 'Maternite',
           'Prestations_familiales', 'Invalidite_Deces', 'Retraite'],
    'Pl': ['Sante_CMU', 'Accidents_du_travail', 'Maternite',
           'Prestations_familiales', 'Invalidite_Deces', 'Retraite'],
}
PROFIL_DEF = {'paquet': 'B', 'age': 35, 'conjointes': 0, 'enfants': 2}


# =============================================================================
#  CALCULS
# =============================================================================

def _cotisation(paquet, n_conj, n_enf):
    p       = {**PARAMS_REF, **DEMO}
    g       = 1 + p['gamma']
    SMIG    = p['SMIG']
    n_conj  = int(n_conj)
    n_enf   = int(n_enf)
    n_benef = 1 + n_conj + min(n_enf, 6)

    pi_sa_tot = (p['CMU_an'] / 12) * n_benef * g
    lsa       = p['lambda_sa']
    t_sa, e_sa = pi_sa_tot*(1-lsa), pi_sa_tot*lsa

    pi_at_tot = p['taux_atmp'] * p['plaf_css'] * g
    lat       = p['lambda_at_B'] if paquet == 'B' else p.get('lambda_at_A', 0.0)
    t_at, e_at = pi_at_tot*(1-lat), pi_at_tot*lat

    t_ma=e_ma=t_pf=e_pf=t_id=e_id=t_re=e_re = 0.0

    if paquet in ('A','O','Pl'):
        K_ma    = (2/3)*(SMIG/30)*p['dur_conge'] + p['alloc_pre'] + p['alloc_mat']
        pi_ma_t = DEMO['f_rep'].get(paquet,0) * (p['ISF']/35) * K_ma / 12 * g
        lma     = p['lambda_ma']
        t_ma, e_ma = pi_ma_t*(1-lma), pi_ma_t*lma
        pi_pf_t = p['alloc_fam'] * max(min(n_enf,6),1) * g
        lpf     = p['lambda_pf']
        t_pf, e_pf = pi_pf_t*(1-lpf), pi_pf_t*lpf

    if paquet in ('O','Pl'):
        q_bar   = DEMO['q_bar'][paquet]
        pi_id_t = (q_bar*SMIG + 0.005*0.5*SMIG) * g
        lid     = p['lambda_id']
        t_id, e_id = pi_id_t*(1-lid), pi_id_t*lid
        lre     = p['lambda_re_O'] if paquet=='O' else p['lambda_re_Pl']
        pi_re_t = p['taux_ipres'] * SMIG * g
        t_re, e_re = pi_re_t*(1-lre), pi_re_t*lre

    det = {
        'Sante_CMU':              {'trav':t_sa, 'etat':e_sa},
        'Accidents_du_travail':   {'trav':t_at, 'etat':e_at},
        'Maternite':              {'trav':t_ma, 'etat':e_ma},
        'Prestations_familiales': {'trav':t_pf, 'etat':e_pf},
        'Invalidite_Deces':       {'trav':t_id, 'etat':e_id},
        'Retraite':               {'trav':t_re, 'etat':e_re},
    }
    tot_t = sum(v['trav'] for v in det.values())
    tot_e = sum(v['etat'] for v in det.values())
    return {'n_benef':n_benef,'detail':det,'total_trav':tot_t,'total_etat':tot_e,'total':tot_t+tot_e}


def _evolution(paquet, n_conj, n_enf, age, tau_inf=0.02, n_ans=40):
    c0 = _cotisation(paquet, n_conj, n_enf)
    t0 = c0['total_trav']
    ar = 2027 + max(0, 60 - int(age))
    annees, nom, reel = [], [], []
    for i in range(n_ans):
        an = 2027+i
        ok = an < ar
        annees.append(an)
        nom.append(t0*(1+tau_inf)**i if ok else 0.0)
        reel.append(t0 if ok else 0.0)
    return annees, nom, reel, ar


def _droits(paquet, age, n_conj, n_enf):
    SMIG=PARAMS_REF['SMIG']; plaf=PARAMS_REF['plaf_css']; af=PARAMS_REF['alloc_fam']
    n_conj=int(n_conj); n_enf=int(n_enf)
    n_tot=1+n_conj+min(n_enf,6); ne_eff=min(n_enf,6)
    res=[]; br=BRANCHES_PAR_PAQUET[paquet]
    if 'Sante_CMU' in br:
        res.append({'icon':'fa-heart-pulse','key':'Sante_CMU',
            'detail':f'Couverture maladie pour {n_tot} bénéficiaire(s) - Prise en charge à 80 % en structure publique'})
    if 'Accidents_du_travail' in br:
        ij1,ij2=round(plaf/22*0.5),round(plaf/22*2/3)
        res.append({'icon':'fa-bandage','key':'Accidents_du_travail',
            'detail':f'Indemnité journalière : {ij1:,} FCFA/jour (28 premiers jours), puis {ij2:,} FCFA/jour'})
    if 'Maternite' in br:
        IJ=round((2/3)*(SMIG/30))
        res.append({'icon':'fa-baby','key':'Maternite',
            'detail':f'Indemnité journalière : {IJ:,} FCFA/jour pendant 98 jours - Allocations prénatales (20 250 FCFA) et de maternité (54 000 FCFA)'})
    if 'Prestations_familiales' in br:
        res.append({'icon':'fa-children','key':'Prestations_familiales',
            'detail':f'{af:,} FCFA/mois par enfant - Total : {af*ne_eff:,} FCFA/mois pour {ne_eff} enfant(s)'})
    if 'Invalidite_Deces' in br:
        res.append({'icon':'fa-house-medical','key':'Invalidite_Deces',
            'detail':f"Rente mensuelle d'invalidité : {round(0.5*SMIG):,} FCFA - Capital décès : {12*SMIG:,} FCFA"})
    if 'Retraite' in br:
        pension=round(0.30*SMIG) if paquet=='O' else round(0.40*SMIG)
        el='Eligible' if int(age)<=50 else 'Non éligible (adhésion après 50 ans)'
        res.append({'icon':'fa-person-cane','key':'Retraite',
            'detail':f'{el} - Pension cible : {pension:,} FCFA/mois à 60 ans - Durée restante : {max(0,60-int(age))} an(s)'})
    return res


# =============================================================================
#  HELPERS UI
# =============================================================================

def _kpi(titre, valeur, ico, coul, bg='#E3F2FD'):
    return html.Div(
        style={'background':bg,'border':'1px solid #C5D8F0','borderRadius':'10px',
               'padding':'1rem','display':'flex','alignItems':'center','gap':'0.8rem'},
        children=[
            html.Div(html.I(className=f'fa-solid {ico}'),
                     style={'width':'36px','height':'36px','borderRadius':'8px',
                            'background':coul,'color':'#fff','flexShrink':'0',
                            'display':'flex','alignItems':'center','justifyContent':'center'}),
            html.Div([html.Div(valeur,style={'fontWeight':'bold','fontSize':'1.1rem','color':'#0D2B5E'}),
                      html.Div(titre,style={'fontSize':'0.78rem','color':'#4A6080'})]),
        ])


def _droit_row(d, coul):
    lbl = BRANCHES_LABEL.get(d['key'], d['key'])
    return html.Div(
        style={'display':'flex','gap':'0.8rem','padding':'0.8rem','background':'#F5F8FC',
               'borderRadius':'8px','border':'1px solid #C5D8F0','marginBottom':'0.6rem'},
        children=[
            html.Div(html.I(className=f'fa-solid {d["icon"]}'),
                     style={'width':'32px','height':'32px','borderRadius':'7px',
                            'background':coul,'color':'#fff','flexShrink':'0',
                            'display':'flex','alignItems':'center','justifyContent':'center','fontSize':'0.9rem'}),
            html.Div([
                html.Strong(lbl,style={'color':'#0D2B5E','fontSize':'0.88rem','display':'block','marginBottom':'0.2rem'}),
                html.Span(d['detail'],style={'fontSize':'0.80rem','color':'#4A6080','lineHeight':'1.5'}),
            ]),
        ])


def _build_resultats_content(profil):
    """Construit tout le contenu de la section Resultats (tableaux + graphiques)."""
    paquet = profil.get('paquet','B')
    age    = int(profil.get('age',35))
    n_conj = int(profil.get('conjointes',0))
    n_enf  = int(profil.get('enfants',2))

    c      = _cotisation(paquet, n_conj, n_enf)
    droits = _droits(paquet, age, n_conj, n_enf)
    annees, nom, reel, anret = _evolution(paquet, n_conj, n_enf, age)
    coul   = PAQUETS_COLORS[paquet]
    label  = PAQUETS_LABELS[paquet]
    r,g,b  = int(coul[1:3],16), int(coul[3:5],16), int(coul[5:7],16)

    # KPIs
    kpis = html.Div(className='params-card', children=[
        html.Div(className='params-card-hdr', children=[
            html.Div(className='params-card-ico', children=[html.I(className='fa-solid fa-coins')]),
            html.H3('Cotisation mensuelle', className='params-card-ttl'),
        ]),
        html.Div(style={'display':'grid','gridTemplateColumns':'repeat(2,1fr)',
                        'gap':'0.8rem','marginTop':'0.5rem'}, children=[
            _kpi('Part cotisant',    f"{c['total_trav']:,.0f} FCFA/mois",'fa-person',coul),
            _kpi("Part de l'Etat",   f"{c['total_etat']:,.0f} FCFA/mois",'fa-building-columns','#1B5E20','#E8F5E9'),
            _kpi('Total prime',      f"{c['total']:,.0f} FCFA/mois",'fa-scale-balanced',coul),
            _kpi('Bénéficiaires CMU',f"{c['n_benef']} personne(s)",'fa-heart-pulse',coul),
        ]),
    ])

    # Resume profil
    lignes_p = [
        ('Paquet',                        f'{label} ({TRANCHES[paquet]} FCFA CA/an)'),
        ('Age',                           f'{age} ans'),
        ('Départ à la retraite',          f'{anret}' if anret<=2066 else '> 2066'),
        ('Conjointes a charge',           str(n_conj)),
        ('Enfants à charge',              str(min(n_enf,6))),
        ('Bénéficiaires CMU',             str(c['n_benef'])),
        ('Années de cotisation restantes',f'{max(0,min(60-age,40))} an(s)'),
    ]
    resume = html.Div(className='params-card', style={'background':'#EEF4FC'}, children=[
        html.Div(className='params-card-hdr', children=[
            html.Div(className='params-card-ico', children=[html.I(className='fa-solid fa-circle-info')]),
            html.H3('Résumé du profil simulé', className='params-card-ttl'),
        ]),
        html.Div([
            html.Div(style={'display':'flex','justifyContent':'space-between',
                            'fontSize':'0.83rem','padding':'0.3rem 0','borderBottom':'1px solid #DDE3EC'},
                     children=[html.Span(k,style={'color':'#4A6080'}),
                                html.Span(v,style={'fontWeight':'bold','color':'#1565C0'})])
            for k,v in lignes_p
        ]),
    ])

    # Tableau detail par branche
    lignes_tbl = [
        (BRANCHES_LABEL.get(br,br), v['trav'], v['etat'], v['trav']+v['etat'])
        for br,v in c['detail'].items()
        if br in BRANCHES_PAR_PAQUET[paquet]
    ]
    tableau = html.Div(className='params-card', children=[
        html.Div(className='params-card-hdr', children=[
            html.Div(className='params-card-ico', children=[html.I(className='fa-solid fa-list-check')]),
            html.H3('Détail des cotisations par branche', className='params-card-ttl'),
        ]),
        html.Div(className='tbl-wrap', children=[
            html.Table(className='data-tbl', children=[
                html.Thead(html.Tr([
                    html.Th('Branche',style={'textAlign':'left'}),
                    html.Th('Cotisant (FCFA/mois)'),
                    html.Th("Etat (FCFA/mois)"),
                    html.Th('Total (FCFA/mois)'),
                ])),
                html.Tbody([
                    html.Tr([
                        html.Td(br,style={'textAlign':'left','fontWeight':'bold','color':coul if t>0 else '#B0BEC5'}),
                        html.Td(f'{trav:,.0f}',style={'color':coul if trav>0 else '#B0BEC5'}),
                        html.Td(f'{etat:,.0f}',style={'color':'#1B5E20' if etat>0 else '#B0BEC5'}),
                        html.Td(f'{t:,.0f}',   style={'fontWeight':'bold','color':'#1A2B4A' if t>0 else '#B0BEC5'}),
                    ])
                    for br,trav,etat,t in lignes_tbl
                ]),
                html.Tfoot(html.Tr([
                    html.Td('TOTAL',style={'textAlign':'left','fontWeight':'bold','color':'#0D2B5E'}),
                    html.Td(f"{c['total_trav']:,.0f}",style={'fontWeight':'bold','color':coul}),
                    html.Td(f"{c['total_etat']:,.0f}",style={'fontWeight':'bold','color':'#1B5E20'}),
                    html.Td(f"{c['total']:,.0f}",     style={'fontWeight':'bold','color':'#0D2B5E'}),
                ])),
            ]),
        ]),
    ])

    # Droits ouverts
    bloc_droits = html.Div(className='params-card', children=[
        html.Div(className='params-card-hdr', children=[
            html.Div(className='params-card-ico', children=[html.I(className='fa-solid fa-shield-halved')]),
            html.H3(f'Droits ouverts - Paquet {label}', className='params-card-ttl'),
        ]),
        *[_droit_row(d,coul) for d in droits],
    ])

    # --- GRAPHIQUES ---

    # Fig 1 : evolution cotisation
    fig_evol = go.Figure()
    fig_evol.add_trace(go.Scatter(
        x=annees, y=nom, name='Cotisation nominale',
        mode='lines', line=dict(color=coul,width=2.5),
        fill='tozeroy', fillcolor=f'rgba({r},{g},{b},0.10)',
        hovertemplate='%{x} : %{y:,.0f} FCFA/mois<extra></extra>'))
    fig_evol.add_trace(go.Scatter(
        x=annees, y=reel, name='Cotisation réelle (valeur 2027)',
        mode='lines', line=dict(color='#1B5E20',width=2,dash='dot'),
        hovertemplate='Reel : %{y:,.0f} FCFA/mois<extra></extra>'))
    if anret <= 2066:
        fig_evol.add_vline(x=anret,
            line=dict(dash='dash',color='#C62828',width=1.5),
            annotation_text=f'Retraite ({anret})',
            annotation_font_size=9, annotation_font_color='#C62828')
    fig_evol.update_layout(**PB, hovermode='x unified',
        xaxis_title='Année', yaxis_title='FCFA/mois',
        title=dict(text=f'Evolution de la cotisation - Paquet {label}',
                   font=dict(size=13,color='#0D2B5E')))

    # Fig 2 : camembert cotisant / Etat
    fig_pie = go.Figure(go.Pie(
        labels=['Part cotisant',"Part de l'Etat"],
        values=[c['total_trav'],c['total_etat']],
        marker=dict(colors=[coul,'#2E9E5B']),
        hole=0.42, textinfo='label+percent',
        hovertemplate='%{label} : %{value:,.0f} FCFA/mois<extra></extra>'))
    fig_pie.update_layout(
        **{k:v for k,v in PB.items() if k not in ['xaxis','yaxis']},
        title=dict(text='Répartition cotisant / Etat',font=dict(size=13,color='#0D2B5E')),
        showlegend=True)

    graphiques = html.Div([
        # Titre de section
        html.Div(style={'display':'flex','alignItems':'center','gap':'0.6rem',
                        'margin':'1.8rem 0 1rem'},
                 children=[
                    html.Div(style={'width':'4px','height':'22px','background':'var(--bleu-vif)',
                                    'borderRadius':'2px'}),
                    html.H3('Graphiques', style={'fontFamily':"'Times New Roman',serif",
                                                  'color':'#0D2B5E','margin':'0','fontSize':'1.05rem'}),
                 ]),
        html.Div(className='chart-card', style={'marginBottom':'1.4rem'}, children=[
            dcc.Graph(figure=fig_evol, config={'displayModeBar':False}, style={'height':'380px'}),
        ]),
        html.Div(className='chart-card', children=[
            dcc.Graph(figure=fig_pie, config={'displayModeBar':False}, style={'height':'360px'}),
        ]),
    ])

    return html.Div([
        kpis,
        html.Div(className='g2', style={'marginTop':'1.2rem'}, children=[resume, tableau]),
        html.Div(style={'marginTop':'1.2rem'}, children=[bloc_droits]),
        graphiques,
    ])


# =============================================================================
#  LAYOUT
# =============================================================================

layout = html.Div([
    dcc.Store(id='store-profil', storage_type='memory', data=PROFIL_DEF),

    html.Div(className='page-hdr', children=[
        html.Div(className='page-hdr-inner', children=[
            html.H1(className='page-hdr-title', children=[
                html.I(className='fa-solid fa-user-check'),
                ' Simulation individuelle',
            ]),
            html.P("Renseignez le profil d'un cotisant et cliquez sur Simuler "
                   "pour obtenir la cotisation, les droits ouverts et les graphiques.",
                   className='page-hdr-sub'),
        ]),
    ]),

    html.Div(className='page-body', children=[

        # Navigation deux boutons
        html.Div(className='sim-nav', children=[
            html.Button(id='btn-nav-params', n_clicks=0,
                        className='sim-nav-btn sim-nav-btn--active',
                        children=[html.I(className='fa-solid fa-sliders',
                                         style={'marginRight':'0.4rem'}),
                                  'Paramètres']),
            html.Button(id='btn-nav-resultats', n_clicks=0,
                        className='sim-nav-btn',
                        children=[html.I(className='fa-solid fa-chart-bar',
                                         style={'marginRight':'0.4rem'}),
                                  'Resultats']),
        ]),

        # Section Parametres
        html.Div(id='sec-params', style={'display':'block'}, children=[
            html.Div(className='params-card', style={'marginTop':'1.5rem'}, children=[
                html.Div(className='params-card-hdr', children=[
                    html.Div(className='params-card-ico',
                             children=[html.I(className='fa-solid fa-id-card')]),
                    html.H3('Profil du cotisant', className='params-card-ttl'),
                ]),

                html.Div(className='param-group', children=[
                    html.Label('Paquet de couverture',
                               style={'fontSize':'0.84rem','fontWeight':'bold',
                                      'color':'#4A6080','marginBottom':'0.3rem','display':'block'}),
                    dcc.Dropdown(id='sp-paquet',
                        options=[
                            {'label':'Paquet Bronze  (CA <= 5 M FCFA)',  'value':'B'},
                            {'label':'Paquet Argent  (CA 5-15 M FCFA)',  'value':'A'},
                            {'label':'Paquet Or      (CA 15-30 M FCFA)', 'value':'O'},
                            {'label':'Paquet Platine (CA 30-50 M FCFA)', 'value':'Pl'},
                        ],
                        value='B', clearable=False, style={'fontSize':'0.88rem'}),
                ]),

                html.Div(className='param-group', children=[
                    html.Div(className='param-lbl', children=[
                        html.Span('Age du cotisant (années)'),
                        html.Span(id='lbl-sp-age', className='param-lbl-val', children='35 ans'),
                    ]),
                    dcc.Slider(id='sl-sp-age', min=15, max=59, step=1, value=35,
                               marks=None,
                               updatemode='drag'),
                ]),

                html.Div(className='param-group', children=[
                    html.Div(className='param-lbl', children=[
                        html.Span('Nombre de conjointes (0 a 4)'),
                        html.Span(id='lbl-sp-conj', className='param-lbl-val', children='0'),
                    ]),
                    dcc.Slider(id='sl-sp-conj', min=0, max=4, step=1, value=0,
                               marks={i:str(i) for i in range(5)},
                               ),
                    html.P("Chaque conjointe est couverte par la CMU. Dans les menages "
                           "", className='param-note'),
                ]),

                html.Div(className='param-group', children=[
                    html.Div(className='param-lbl', children=[
                        html.Span("Nombre d'enfants a charge (0 a 6)"),
                        html.Span(id='lbl-sp-enf', className='param-lbl-val', children='2'),
                    ]),
                    dcc.Slider(id='sl-sp-enf', min=0, max=6, step=1, value=2,
                               marks={i:str(i) for i in range(7)},
                               ),
                    html.P("Plafond : 6 enfants, conformément au bareme CSS (CLEISS, 2026). ",
                           className='param-note'),
                ]),

                html.P("Retraite : seuls les cotisants adhérant avant 50 ans sont éligibles "
                       "(durée minimale 10 ans, paramètre IPRES).",
                       className='param-note', style={'marginTop':'0.4rem'}),
            ]),

            html.Div(style={'marginTop':'1.5rem','display':'flex','gap':'1rem',
                            'alignItems':'center','flexWrap':'wrap'}, children=[
                html.Button(id='btn-simuler-profil', n_clicks=0, className='btn-simuler',
                            children=[html.I(className='fa-solid fa-play',
                                            style={'marginRight':'0.5rem'}),
                                      'Simuler ce profil']),
                html.Button(id='btn-reset-profil', n_clicks=0, className='btn-reset-inline',
                            children=[html.I(className='fa-solid fa-rotate-left',
                                            style={'marginRight':'0.4rem'}),
                                      'Reinitialiser']),
                html.Span(id='sp-confirm',
                          style={'fontSize':'0.82rem','color':'#1B5E20','fontStyle':'italic'}),
            ]),
        ]),

        # Section Resultats (vide au depart, remplie par callback)
        html.Div(id='sec-resultats', style={'display':'none'}, children=[
            html.Div(id='sp-resultats'),
        ]),
    ]),
])


# =============================================================================
#  CALLBACKS
# =============================================================================

# 1. Label age
@callback(Output('lbl-sp-age','children'), Input('sl-sp-age','value'),
          prevent_initial_call=False)
def lbl_age(v):
    return f'{int(v or 35)} ans'

# 2. Label conjointes
@callback(Output('lbl-sp-conj','children'), Input('sl-sp-conj','value'),
          prevent_initial_call=False)
def lbl_conj(v):
    return str(int(v or 0))

# 3. Label enfants
@callback(Output('lbl-sp-enf','children'), Input('sl-sp-enf','value'),
          prevent_initial_call=False)
def lbl_enf(v):
    return str(int(v or 0))

# 4. Reset
@callback(
    Output('sp-paquet','value'), Output('sl-sp-age','value'),
    Output('sl-sp-conj','value'), Output('sl-sp-enf','value'),
    Input('btn-reset-profil','n_clicks'), prevent_initial_call=True)
def reset_profil(_):
    return 'B', 35, 0, 2

# 5. Bouton Simuler -> store + aller sur Resultats
#    Boutons nav  -> changer section visible
#    Les deux ecrivent sur les memes sorties : un seul callback les gere tous
@callback(
    Output('store-profil',       'data'),
    Output('sp-confirm',         'children'),
    Output('sec-params',         'style'),
    Output('sec-resultats',      'style'),
    Output('btn-nav-params',     'className'),
    Output('btn-nav-resultats',  'className'),
    # Inputs
    Input('btn-simuler-profil',  'n_clicks'),
    Input('btn-nav-params',      'n_clicks'),
    Input('btn-nav-resultats',   'n_clicks'),
    # States lus uniquement quand Simuler est clique
    State('sp-paquet',  'value'),
    State('sl-sp-age',  'value'),
    State('sl-sp-conj', 'value'),
    State('sl-sp-enf',  'value'),
    State('store-profil','data'),
    prevent_initial_call=True,
)
def gerer_navigation(n_sim, n_par, n_res, paquet, age, conj, enf, profil_actuel):
    ctx = callback_context
    SHOW = {'display':'block'}
    HIDE = {'display':'none'}
    ACT  = 'sim-nav-btn sim-nav-btn--active'
    INA  = 'sim-nav-btn'

    if not ctx.triggered:
        return profil_actuel or PROFIL_DEF, '', SHOW, HIDE, ACT, INA

    tid = ctx.triggered[0]['prop_id'].split('.')[0]

    # Clic Simuler : calculer, stocker, aller sur Resultats
    if tid == 'btn-simuler-profil':
        profil = {
            'paquet':     paquet or 'B',
            'age':        int(age  or 35),
            'conjointes': int(conj or 0),
            'enfants':    int(enf  or 2),
        }
        lbl = PAQUETS_LABELS[profil['paquet']]
        msg = (f"Simulation effectuée - Paquet {lbl}, {profil['age']} ans, "
               f"{profil['conjointes']} conjointe(s), {profil['enfants']} enfant(s)")
        return profil, msg, HIDE, SHOW, INA, ACT

    # Clic nav Parametres
    if tid == 'btn-nav-params':
        return profil_actuel or PROFIL_DEF, '', SHOW, HIDE, ACT, INA

    # Clic nav Resultats
    if tid == 'btn-nav-resultats':
        return profil_actuel or PROFIL_DEF, '', HIDE, SHOW, INA, ACT

    return profil_actuel or PROFIL_DEF, '', SHOW, HIDE, ACT, INA


# 6. Mise a jour du contenu Resultats quand store-profil change
@callback(
    Output('sp-resultats','children'),
    Input('store-profil','data'),
    prevent_initial_call=False,
)
def build_resultats(profil):
    if not profil:
        profil = PROFIL_DEF
    return _build_resultats_content(profil)
