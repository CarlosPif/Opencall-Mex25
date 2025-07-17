from pyairtable import Api
import pandas as pd
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

# Configuracion de AirTable
api_key = st.secrets["airtable"]["api_key"]
base_id = st.secrets["airtable"]["base_id"]
table_id = st.secrets["airtable"]["table_id"]

api = Api(api_key)
table = api.table(base_id, table_id)

#sacamos los datos de All Applicants
records = table.all(view='All applicants - MEX25')
data = [record['fields'] for record in records]
df = pd.DataFrame(data)

#sacamos los datos para la vista de 1a evaluacion
records_1st = table.all(view='PH3_Evaluation PH2 - 1st eval.')
data_1st = [record['fields'] for record in records_1st]
df_1st = pd.DataFrame(data_1st)

#limpiamos un poco los datos
def fix_cell(val):
    if isinstance(val, dict) and "specialValue" in val:
        return float("nan")
    return val

df_1st = df_1st.map(fix_cell)
df = df.map(fix_cell)

#Comenzamos con el dashboard
st.set_page_config(
    page_title="Opencall Dashboard Decelera Mexico 2025",
    layout="wide"
)

st.markdown("**<h1 style='text-align: center;'>Open Call Decelera Mexico 2025</h1>**", unsafe_allow_html=True)

#================================Tablita con resultados generales=========================================
#primero sacamos los datos, cuantos hay evaluados 1 vez, dos veces, el total etc

ph3_count = df[ df['Status'] == 'PH3_Internal_Evaluation'].shape[0]

ph3_1st = df[ df['PH3_Impact_1st'].notna() ].shape[0]
ph3_1st_pct = round(ph3_1st / ph3_count * 100, 2)

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
    <div class="metric-main-num">{ph3_count}</div>
    <div class="metric-main-label">Total number of companies in Internal Evaluation</div>
    <div class="sub-row">
      <div class="metric-box"><div class="metric-value">{ph3_1st}</div>
                               <div class="metric-label">Companies that have been through the first evaluation</div></div>
      <div class="metric-box"><div class="metric-value">{ph3_1st_pct}%</div>
                               <div class="metric-label">Percentage of those that have been through the first evaluation</div></div>
    </div>
  </div>

</div>
""", unsafe_allow_html=True)

#=====Vamos a hacer un funnel================

funnel_count = (
    df.groupby('Status')
    .size()
    .reset_index(name='count')
    .sort_values('count')
)

funnel_count['count'] = funnel_count['count'].iloc[::-1].cumsum().iloc[::-1]

fig = go.Figure()

fig.add_traces(go.Funnel(
    x=funnel_count['count'],
    y=funnel_count['Status'],
    marker=dict(
        color=['#87CEEB', '#87CEEB'],
        line=dict(
            color='#5aa5c8',
            width=1.5
        )
    )
))

fig.update_layout(
    title='Selection process funnel chart',
)

st.plotly_chart(fig)

#=====================distribucion de notas de la primera evaluacion==============================

#sacamos las notas de la primera evaluacion
evaluation_1st = list(df_1st[df_1st['PH3_First_Evaluation_Score'] != 0]['PH3_First_Evaluation_Score'])

kde = gaussian_kde(evaluation_1st)
x_vals = np.linspace(min(evaluation_1st), max(evaluation_1st), 200)
y_vals = kde(x_vals)*len(evaluation_1st)

fig = go.Figure()



fig.add_traces(go.Scatter(
    x=x_vals,
    y=y_vals,
    mode='lines',
    name='KDE',
    line=dict(
        color='#5aa5c8',
        width=2
    )
))

fig.update_layout(
    title='1st Evaluation Distribution',
    xaxis_title='Score',
    yaxis_title='Number of companies',
    bargap=0.1,
    xaxis_range=[0,5]
)

st.plotly_chart(fig)

#vamos a poner una tabla interactiva con los 10 mejores
st.markdown("Top 20 Startups in the First Evaluation")

top_20 = df_1st.sort_values(by='PH3_First_Evaluation_Score', ascending=False).head(20)
top_20 = top_20.rename(columns=
    {
        'deck_URL': 'Deck (url)',
        'deck_$startup': 'Deck',
        'PH3_First_Evaluation_Score': '1st Evaluation Score'
    }
)

st.dataframe(top_20[['Startup name', 'website', 'Deck (url)', 'Deck', '1st Evaluation Score']])

html_table = "<table>"
html_table += "<tr><th>Startup</th><th>Deck</th><th>Score</th></tr>"

for _, row in top_20.iterrows():
    html_table += (
    "<tr>"
    f"<td>{row['Startup name']}</td>"
    f"<td><a href='{row['Deck (url)']}' target='_blank'>{row['Deck']}</a></td>"
    f"<td>{row['1st Evaluation Score']}</td>"
    "</tr>"
    )
html_table += "</table>"

st.markdown(html_table, unsafe_allow_html=True)
