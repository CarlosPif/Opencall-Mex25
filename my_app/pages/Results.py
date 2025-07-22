from pyairtable import Api
import pandas as pd
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
import plotly.express as px

# Configuracion de AirTable
api_key = st.secrets["airtable"]["api_key"]
base_id = st.secrets["airtable"]["base_id"]
table_id = st.secrets["airtable"]["table_id"]

api = Api(api_key)
table = api.table(base_id, table_id)

#sacamos los datos de All Applicants
records = table.all(view='PH1-PH2_All Applicants')
data = [record['fields'] for record in records]
df = pd.DataFrame(data)

#sacamos los datos para la vista de 1a evaluacion
records_1st = table.all(view='All applicants  by Phase')
data_1st = [record['fields'] for record in records_1st]
df_all = pd.DataFrame(data_1st)

#limpiamos un poco los datos
def fix_cell(val):
    if isinstance(val, dict) and "specialValue" in val:
        return float("nan")
    return val

df_all = df_all.map(fix_cell)
df_all = df_all.map(fix_cell)

#Comenzamos con el dashboard
st.set_page_config(
    page_title="Opencall Dashboard Decelera Mexico 2025",
    layout="wide"
)

st.markdown("**<h1 style='text-align: center;'>Open Call Decelera Mexico 2025</h1>**", unsafe_allow_html=True)

#================================Tablita con resultados generales=========================================
#Todos los que han sido evaluados POR EL team ya (los de Pending )
pending_judge = df_all[df_all['Status'] == 'PH4_Pending_Judge_Assignment'].shape[0]

#contamos cuantos han pasado a team evaluation
ph2 = df_all[
    (df_all['Status'] == 'PH4_Pending_Judge_Assignment') |
    (df_all['Status'] == 'PH4_Judge_Evaluation') | 
    (df_all['Status'] == 'PH3_Rejected') | 
    (df_all['Status'] == 'PH3_To_Be_Rejected') | 
    (df_all['Status'] == 'PH3_Internal_Evaluation')
    ].shape[0]

#porcentaje de exito en la team evaluation
succ_pct = round(pending_judge / ph2 * 100, 2)


st.markdown(f"""
<style>
.dashboard-row{{
  display:flex;
  gap:1rem;
  justify-content:center;
  margin-bottom:1rem;
  font-family:"Segoe UI",sans-serif;
}}
.big-card{{
  flex:1 1 0;
  background:#ffffff;
  border-radius:12px;
  padding:1rem;
  box-shadow:0 1px 6px rgba(0,0,0,.08);
  color:#000;
  text-align:center;
}}
.metric-main-num{{font-size:36px;margin:0;}}
.metric-main-label{{margin-top:2px;font-size:14px;font-weight:600;
                    border-bottom:2px solid #000;display:inline-block;padding-bottom:3px;}}
.sub-row{{display:flex;gap:0.6rem;justify-content:center;margin-top:0.8rem;}}
.metric-box{{
  background:#87CEEB;border-radius:8px;padding:10px 0 12px;
  box-shadow:0 1px 3px rgba(0,0,0,.05);border-bottom:2px solid #5aa5c8;
  color:#000;flex:1 1 0;
}}
.metric-value{{font-size:18px;font-weight:600;margin:0;}}
.metric-label{{margin-top:2px;font-size:14px;letter-spacing:.3px;}}
</style>

<!-- ───────── FILA ÚNICA CON UNA TARJETA ───────── -->
<div class="dashboard-row">

  <div class="big-card">
    <div class="metric-main-num">{pending_judge}</div>
    <div class="metric-main-label">Total number of companies currently in judge evaluations</div>
    <div class="sub-row">
      <div class="metric-box"><div class="metric-value">{ph2}</div>
                               <div class="metric-label">Number of companies that got to internal evaluation</div></div>
      <div class="metric-box"><div class="metric-value">{succ_pct}%</div>
                               <div class="metric-label">Percentage of success in Internal Evaluation</div></div>
    </div>
  </div>

</div>
""", unsafe_allow_html=True)

#=================Vamos a hacer un funnel================
total = df_all.shape[0] 

funnel_count = (
    df_all.replace(
        {
            'PH1_To_Be_Rejected': 'Phase 1',
            'PH1_Rejected': 'Phase 1',
            'PH1_Review': 'Phase 1',
            'PH1_Pending_Send_Magic_link': 'Phase 1',
            'PH1_Magic_Link_Sent': 'Phase 1',
            'PH1_To_Be_Rejected_Review': 'Phase 1',
            'PH1_Rejected_Review': 'Phase 1',
            'PH3_Internal_Evaluation': 'Phase 2 & 3 (Internal Evaluation)',
            'PH3_To_Be_Rejected': 'Phase 2 & 3 (Internal Evaluation)',
            'PH3_Rejected': 'Phase 2 & 3 (Internal Evaluation)',
            'PH4_Pending_Judge_Assignment': 'Phase 4 (Judge Evaluation)',
            'PH4_Judge_Evaluation': 'Phase 4 (Judge Evaluation)'
        }
    )
)

funnel_count = (
    funnel_count.groupby('Status')['Status']
    .value_counts()
    .reset_index(name='count')
)

funnel_count['count'] = funnel_count['count'].iloc[::-1].cumsum().iloc[::-1]
funnel_count['pct'] = round(funnel_count['count'] / total * 100, 2)
funnel_count['text'] = funnel_count['count'].astype(str) + " (" + funnel_count['pct'].astype(str) + "%)"


fig = go.Figure()

fig.add_traces(go.Funnel(
    x=funnel_count['count'],
    y=funnel_count['Status'],
    text=funnel_count['text'],
    textinfo="text",
    marker=dict(
        color='#87CEEB',
        line=dict(
            color='#5aa5c8',
            width=1.5
        )
    ),
    textfont=dict(color='black')
))

fig.update_layout(
    title='Selection process funnel chart',
    yaxis=dict(
        tickfont=dict(color='black')
    )
)

st.plotly_chart(fig)

#=====================Barras con cuantas aplicaciones hay en cada fase==============================
df_phase = (
    df_all.replace(
        {
            'PH1_To_Be_Rejected': 'Rejected in phase 1',
            'PH1_Review': 'Review for the phase 1',
            'PH1_Rejected': 'Rejected in phase 1',
            'PH1_Pending_Send_Magic_Link': 'Pending to send magic link',
            'PH1_Magic_Link_Sent': 'Magic link to phase 2 sent',
            'PH1_To_Be_Rejected_Review': 'Rejected in phase 1',
            'PH1_Rejected_Review': 'Rejected in phase 1',
            'PH3_Internal_Evaluation': 'Internal Evaluation (Phase 3)',
            'PH3_To_Be_Rejected': 'Rejected in phase 3',
            'PH3_Rejected': 'Rejected in phase 3',
            'PH4_Pending_Judge_Assignment': 'Pending judge assignment',
            'PH4_Judge_Evaluation': 'Judge Evaluation (Phase 4)'
        }
    )
)

df_phase = (
    df_phase.groupby('Status')['Status'].
    value_counts().
    reset_index(name='count')
)

df_phase['pct'] = round(df_phase['count'] / total * 100, 2)
df_phase['text'] = df_phase['count'].astype(str) + " (" + df_phase['pct'].astype(str) + "%)"

orden = [
    'Rejected in phase 1',
    'Review for the phase 1',
    'Internal Evaluation (Phase 3)',
    'Rejected in phase 3',
    'Pending judge assignment',
]
df_phase = df_phase.set_index('Status').loc[orden].reset_index()

fig = go.Figure()

fig.add_traces(go.Bar(
    x=df_phase['Status'],
    y=df_phase['count'],
    text=df_phase['text'],
    textposition='outside',
    textfont=dict(color='black'),
    marker=dict(
        color="#87CEEB",
        line=dict(color="#5aa5c8", width=1.5),
    ),
    cliponaxis=False
    ))

fig.update_layout(
    title=f"Current number of companies in each phase. Total: {total}",

)

st.plotly_chart(fig)
#=====================distribucion de notas de la internal evaluation==============================
st.markdown("**<h2>Internal evaluation (Phase 3)</h2>**", unsafe_allow_html=True)
st.markdown("Below a results analysis of the Internal Evaluation phase")

#y vamos con todos
evaluation = list(df_all[df_all['PH3_Final_Score'] != 0]['PH3_Final_Score'])

kde = gaussian_kde(evaluation)
x_t = np.linspace(min(evaluation), max(evaluation), 200)
y_t = kde(x_t) * len(evaluation)

fig = go.Figure()

fig.add_traces(go.Scatter(
    x=x_t,
    y=y_t,
    mode='lines',
    name='Final Score',
    line=dict(
        color='skyblue',
        width=2
    ),
    fill='tozeroy',
    fillcolor='rgba(135, 206, 235, 0.2)'
))

fig.update_layout(
    title='Internal Evaluation Scoring Distribution',
    bargap=0.1,
    xaxis=dict(
        title=dict(text='Score', font=dict(color='black')),
        tickfont=dict(color='black'),
        range=[1, 5]
    ),
    yaxis=dict(
        title=dict(text='Number of companies', font=dict(color='black')),
        tickfont=dict(color='black'),
    )
)

st.plotly_chart(fig)

#PRUEBA DE UN BOXPLOT
df_box = df_all[df_all['PH3_Final_Score'] != 0]

fig = px.box(df_box, y='PH3_Final_Score', points='all')
fig.update_traces(marker_color='skyblue', line_color='black')
st.plotly_chart(fig)

#vamos a poner una tabla interactiva con los 10 mejores
st.markdown("Top 10 Startups Internal Evaluation")

df_all['Deck (doc)'] = df_all['deck_$startup'].apply(
    lambda x: x[0]['url'] if isinstance(x, list) and len(x) > 0 and isinstance(x[0], dict) and 'url' in x[0] else None
)

df_all['deck_icon'] = df_all['deck_$startup'].apply(
    lambda x: x[0].get('thumbnails', {}).get('small', {}).get('url') if isinstance(x, list) and x else None
)

top_10 = df_all.sort_values(by='PH3_Final_Score', ascending=False).head(10)
top_10['PH3_Final_Score'] = top_10['PH3_Final_Score'].apply(lambda x: round(x, 2))

top_10 = top_10.rename(columns={
    'deck_URL': 'Deck (url)',
    'PH3_Final_Score': 'Internal Evaluation Score'
})

html_table = """
<div style="overflow-x: auto; width: 100%;">
<table style="width: 100%; border-collapse: collapse;">
<thead>
<tr>
<th style="text-align: left; padding: 8px;">Startup</th>
<th style="text-align: left; padding: 8px;">Deck (doc)</th>
<th style="text-align: left; padding: 8px;">Deck (link)</th>
<th style="text-align: left; padding: 8px;">Score</th>
</tr>
</thead>
<tbody>
"""

for _, row in top_10.iterrows():
    website_link = (
        f"<a href='{row['Deck (doc)']}' target='_blank'>"
        f"<img src='{row['deck_icon']}' alt='Website' width='40' style='vertical-align: middle;'/>"
        "</a>"
        if pd.notna(row['Deck (doc)']) and pd.notna(row['deck_icon']) else ""
    )
    deck_link = (
        f"<a href='{row['Deck (url)']}' target='_blank'>{row['Deck (url)']}</a>"
        if pd.notna(row['Deck (url)']) else ""
    )
    html_table += f"""
<tr>
<td style="padding: 8px;">{row['Startup name']}</td>
<td style="padding: 8px;">{website_link}</td>
<td style="padding: 8px;">{deck_link}</td>
<td style="padding: 8px;">{row['Internal Evaluation Score']}</td>
</tr>
"""

html_table += """
</tbody>
</table>
</div>
"""

st.markdown(html_table, unsafe_allow_html=True)
