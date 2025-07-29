from pyairtable import Api
import pandas as pd
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
import plotly.express as px
import requests

# Configuracion de AirTable
api_key = st.secrets["airtable"]["api_key"]
base_id = st.secrets["airtable"]["base_id"]
table_id = st.secrets["airtable"]["table_id"]

api = Api(api_key)
table = api.table(base_id, table_id)

#fillout
api_key_fl = st.secrets['fillout']['api_key']
form_id = st.secrets['fillout']['form_id']

#sacamos los datos para la vista de 1a evaluacion
records = table.all(view='All applicants  by Phase')
data = [record['fields'] for record in records]
df = pd.DataFrame(data)

#limpiamos un poco los datos
def fix_cell(val):
    if isinstance(val, dict) and "specialValue" in val:
        return float("nan")
    return val

df = df.map(fix_cell)

#Llamada a Fillout
def get_in_progress_submissions_count(form_id, api_key):
    total_responses = 0
    after = None
    size = 150
    seen_cursors = set()

    while True:
        url = f"https://api.fillout.com/v1/api/forms/{form_id}/submissions"
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {
            "status": "in_progress",
            "limit": size
        }
        if after:
            params["after"] = after

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"Error Fillout API: {response.status_code} - {response.text}")

        data = response.json()
        responses = data.get("responses", [])
        total_responses += len(responses)

        print(f"Fetched: {len(responses)} | Total: {total_responses}")

        page_info = data.get("pageInfo", {})
        after = page_info.get("endCursor")

        # 🛑 Check for repeated cursor to avoid infinite loop
        if not after or after in seen_cursors:
            break
        seen_cursors.add(after)

    return total_responses


total_ip = get_in_progress_submissions_count(form_id, api_key_fl)

colors = ['#1FD0EF', '#FFB950', '#FAF3DC', '#1158E5', '#B9C1D4', '#F2F8FA']

#Comenzamos con el dashboard
st.set_page_config(
    page_title="Opencall Dashboard Decelera Mexico 2025",
    layout="wide"
)

st.markdown("**<h1 style='text-align: center;'>Open Call Decelera Mexico 2025</h1>**", unsafe_allow_html=True)

#================================Tablita con resultados generales=========================================
#Todos los que han sido evaluados POR EL team ya (los de Pending )
pending_judge = df[df['Status'] == 'PH4_Pending_Judge_Assignment'].shape[0]

#contamos cuantos han pasado a team evaluation
ph2 = df[
    (df['Status'] == 'PH4_Pending_Judge_Assignment') |
    (df['Status'] == 'PH4_Judge_Evaluation') | 
    (df['Status'] == 'PH3_Rejected') | 
    (df['Status'] == 'PH3_To_Be_Rejected') | 
    (df['Status'] == 'PH3_Internal_Evaluation') |
    (df['Status'] == 'PH3_Waiting_List')
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
  background:#1FD0EF;border-radius:8px;padding:10px 0 12px;
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
total = df.shape[0] 

funnel_count = (
    df.replace(
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
            'PH4_Judge_Evaluation': 'Phase 4 (Judge Evaluation)',
            'PH1_Pending_Send_Magic_Link': 'Phase 1',
            'PH1_To_Be_Rejected_Review': 'Phase 1',
            'PH3_Waiting_List': 'Phase 2 & 3 (Internal Evaluation)',
            'PH1_To_Be_Rejected_Reviewed': 'Phase 1'
        }
    )
)

funnel_count = (
    funnel_count.groupby('Status')['Status']
    .value_counts()
    .reset_index(name='count')
)

funnel_count['count'] = funnel_count['count'].iloc[::-1].cumsum().iloc[::-1]
funnel_count['pct_conv'] = funnel_count['count'].pct_change()
funnel_count['pct_conv'] = funnel_count['pct_conv'].apply(lambda x: f"{(1 + x)*100:.2f}%" if pd.notnull(x) else "")
funnel_count['label'] = funnel_count.apply(
    lambda row: f"{row['count']} ({row['pct_conv']})" if row['pct_conv'] else f"{row['count']}", axis=1
)

fig = go.Figure()

fig.add_traces(go.Funnel(
    x=funnel_count['count'],
    y=funnel_count['Status'],
    text=funnel_count['label'],
    textinfo="text",
    marker=dict(
        color = colors,
        line=dict(
            color='black',
            width=1.5
        )
    ),
    textfont=dict(color='black')
))

fig.update_layout(
    title='Selection process funnel with conversion rates',
    yaxis=dict(
        tickfont=dict(color='black')
    )
)

cols = st.columns(2)

with cols[0]:
    st.plotly_chart(fig)

#=======================================tabla percentiles=================================================
#vamos a dividir todo solo entre fases
ph1 = df['Status'].shape[0]
ph2 = df[
    (df['Status'] != 'PH1_To_Be_Rejected') &
    (df['Status'] != 'PH1_Rejected') &
    (df['Status'] != 'PH1_To_Be_Rejected_Reviewed') &
    (df['Status'] != 'PH1_Review')
    ].shape[0]
ph4 = df[
    (df['Status'] == 'PH4_Pending_Judge_Assignment') |
    (df['Status'] == 'PH4_Judge_Evaluation')
].shape[0]

#Ahora vamos a sacartodos los numeros de la tabla que vamos a hacer con lo de los percentiles. Excepto para phase 1

#separamos los de phase 1
ph1_in_progress = total_ip

ph1_rejection = df[
    (df['Status'] == 'PH1_Rejected') |
    (df['Status'] == 'PH1_To_Be_Rejected') |
    (df['Status'] == 'PH1_To_Be_Rejected_Reviewed')
].shape[0]

ph1_waiting_list = df[
    df['Status'] == 'PH1_Review'
].shape[0]

#separamos los de fase 2
ph2_in_progress = df[
    (df['Status'] == 'PH1_Pending_Send_Magic_Link') |
    (df['Status'] == 'PH1_Magic_Link_Sent')
].shape[0]

#separamos los de fase 3 (esta vez con percentiles)
ph3_in_progress = df[df['Status'] == 'PH3_Internal_Evaluation'].shape[0]

ph3_df = df[
    (df['Status'] != 'PH1_To_Be_Rejected') &
    (df['Status'] != 'PH1_Rejected') &
    (df['Status'] != 'PH1_To_Be_Rejected_Reviewed') &
    (df['Status'] != 'PH1_Review') &
    (df['PH3_Final_Score'] >= 1)
]

ph3_q1 = np.percentile(ph3_df['PH3_Final_Score'], 25)
ph3_q3 = np.percentile(ph3_df['PH3_Final_Score'], 75)

ph3_rejection    = ph3_df[ph3_df['PH3_Final_Score'] <= ph3_q1].shape[0]
ph3_waiting_list = ph3_df[(ph3_df['PH3_Final_Score'] < ph3_q3) & (ph3_df['PH3_Final_Score'] > ph3_q1)].shape[0]
ph3_passed       = ph3_df[ph3_df['PH3_Final_Score'] >= ph3_q3].shape[0]

#vamos con los de la fase 4


with cols[1]:
    st.markdown("**<p style='text-align: center;'>Funnel situation based on percentiles (not real, just for research)</p>**", unsafe_allow_html=True)

    st.markdown(f"""
    <style>
    table {{
    border-collapse: collapse;
    width: 80%;
    margin: 30px auto;
    font-family: "Segoe UI", sans-serif;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
    text-align: center;
    }}

    th, td {{
    border: 1px solid #ddd;
    text-align: center;
    padding: 12px;
    }}

    th {{
    background-color: #f4f4f4;
    font-weight: 600;
    }}

    tr:nth-child(even) {{
    background-color: #f9f9f9;
    }}

    tr:hover {{
    background-color: #f1f1f1;
    }}

    .divider-row th {{
    background-color: #ffffff !important;
    border: none;
    padding: 12px 0;
    font-weight: 400;
    font-size: 14px;
    color: #999;
    text-align: center;
    }}
    .divider-row td {{
    display: none;
    }}

    </style>

    <table>
    <thead>
    <tr>
    <th></th>
    <th>In Progress</th>
    <th>Rejection</th>
    <th>Waiting List</th>
    <th>Passed to the Next Phase</th>
    </tr>
    </thead>
    <tbody>
    <tr>
    <th scope="row">Phase 1: {ph1}</th>
    <td>{ph1_in_progress}</td>
    <td>{ph1_rejection}</td>
    <td>{ph1_waiting_list}</td>
    <td>{ph2}</td>
    </tr>
    <tr>
    <th scope="row">Phase 2: {ph2}</th>
    <td>{ph2_in_progress}</td>
    <td>-</td>
    <td>-</td>
    <td>-</td>
    </tr>
    <tr>
    <th scope="row">Phase 3: {ph2}</th>
    <td>{ph3_in_progress}</td>
    <td>{ph3_rejection}</td>
    <td>{ph3_waiting_list}</td>
    <td>{ph3_passed}</td>
    </tr>
    <tr>
    <th scope="row">Phase 4: {ph3_passed}</th>
    <td>{ph3_passed}</td>
    <td></td>
    <td></td>
    <td></td>
    </tr>
    <tr class="divider-row">
    <th scope="row">Percentiles</th>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    </tr>
    <tr>
    <th scope="row">Phase 3: {ph2}</th>
    <td>-</td>
    <td>Less than {round(ph3_q1, 2)}</td>
    <td>Between {round(ph3_q1, 2)} and {round(ph3_q3, 2)}</td>
    <td>Greater than {round(ph3_q3, 2)}</td>
    </tr>
    <tr>
    <th scope="row">Phase 4: {ph3_passed}</th>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    </tr>
    </tbody>
    </table>
    """, unsafe_allow_html=True)

#=====================Barras con cuantas aplicaciones hay en cada fase==============================
df_phase = (
    df.replace(
        {
            'PH1_To_Be_Rejected': 'Rejected in phase 1',
            'PH1_Review': 'Review for the phase 1',
            'PH1_Rejected': 'Rejected in phase 1',
            'PH1_Pending_Send_Magic_Link': 'Magic link to phase 2',
            'PH1_Magic_Link_Sent': 'Magic link to phase 2',
            'PH1_To_Be_Rejected_Reviewed': 'Rejected in phase 1',
            'PH1_Rejected_Review': 'Rejected in phase 1',
            'PH3_Internal_Evaluation': 'Internal Evaluation (Phase 3)',
            'PH3_To_Be_Rejected': 'Rejected in phase 3',
            'PH3_Waiting_List': 'Rejected in phase 3',
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
    'Magic link to phase 2',
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
        color=colors,
        line=dict(color="black", width=1.5),
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
evaluation = list(df[df['PH3_Final_Score'] != 0]['PH3_Final_Score'])

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
        color='#1FD0EF',
        width=2
    ),
    fill='tozeroy',
    fillcolor='rgba(31, 208, 239, 0.2)'
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
df_box = df[df['PH3_Final_Score'] != 0]

fig = px.box(df_box, y='PH3_Final_Score', points='all')
fig.update_traces(marker_color='skyblue', line_color='black')
st.plotly_chart(fig)

#vamos a poner una tabla interactiva con los 10 mejores
st.markdown("Top 10 Startups Internal Evaluation")

df['Deck (doc)'] = df['deck_$startup'].apply(
    lambda x: x[0]['url'] if isinstance(x, list) and len(x) > 0 and isinstance(x[0], dict) and 'url' in x[0] else None
)

df['deck_icon'] = df['deck_$startup'].apply(
    lambda x: x[0].get('thumbnails', {}).get('small', {}).get('url') if isinstance(x, list) and x else None
)

top_10 = df.sort_values(by='PH3_Final_Score', ascending=False).head(10)
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

#==========================NUevo diseño que meto aqui tal cual==============================
#primero la columna con los cuadrados

