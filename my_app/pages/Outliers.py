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

colors = ['#1FD0EF', '#FFB950', '#FAF3DC', '#1158E5', '#B9C1D4', '#F2F8FA']

#Comenzamos con el dashboard
st.set_page_config(
    page_title="Opencall Dashboard Decelera Mexico 2025<br><br>Outliers Detection",
    layout="wide"
)

st.markdown("**<h1 style='text-align: center;'>Open Call Decelera Mexico 2025</h1>**", unsafe_allow_html=True)

#=======================A ver un scatter plot para analizar las diferencias de puntuaciones==================

df['distancia'] = abs(df['PH3_Final_Score'] - df['Judges_Average']) / np.sqrt(2)
top_discrep = df.sort_values(by='distancia', ascending=False).head(10)

fig = go.Figure()

fig.add_traces(go.Scatter(
    x=df['PH3_Final_Score'],
    y=df['Judges_Average'],
    text=df['Startup name'],
    mode='markers',
    marker=dict(
        color=df['distancia'],
        colorscale='Viridis',
        colorbar=dict(title='distancia')
    )
))

fig.add_traces(go.Scatter(
    x=top_discrep['PH3_Final_Score'],
    y=top_discrep['Judges_Average'],
    text=top_discrep['Startup name'],
    mode='text',
    textposition='top right',
    name='Top 10 Discrepantes',
))

fig.add_traces(go.Scatter(
    x=[0,5],
    y=[0,5],
    mode='lines'
))

fig.update_layout(
    xaxis=dict(
        title='Team Evaluation',
        range=[2.5, 5]
    ),
    yaxis=dict(
        title='Judges Evaluation',
        range=[1, 5]
    ),
    title='Difference between Judge and Team Evaluations',
    showlegend=False
)

st.plotly_chart(fig)

top_distance = df.sort_values(by='distancia', ascending=False).head(20)
top_distance['distancia'] = top_distance['distancia'].apply(lambda x: round(x, 2))

top_distance = top_distance.rename(columns={
    'deck_URL': 'Deck (url)',
    'distancia': 'Distance to having the same score',
    'Judges_Average': 'Judge Evaluation Average'
})

top_distance['Deck (doc)'] = df['deck_$startup'].apply(
    lambda x: x[0]['url'] if isinstance(x, list) and len(x) > 0 and isinstance(x[0], dict) and 'url' in x[0] else None
)

top_distance['deck_icon'] = df['deck_$startup'].apply(
    lambda x: x[0].get('thumbnails', {}).get('small', {}).get('url') if isinstance(x, list) and x else None
)

html_table = """
<div style="overflow-x: auto; width: 100%;">
<table style="width: 100%; border-collapse: collapse;">
<thead>
<tr>
<th style="text-align: center; padding: 8px;">Startup</th>
<th style="text-align: center; padding: 8px;">Deck (doc)</th>
<th style="text-align: center; padding: 8px;">Deck (link)</th>
<th style="text-align: center; padding: 8px;">Judge Evaluation</th>
<th style="text-align: center; padding: 8px;">Judges</th>
<th style="text-align: center; padding: 8px;">Team Evaluation</th>
<th style="text-align: center; padding: 8px;">Evaluator</th>
<th style="text-align: center; padding: 8px;">Distance</th>
</tr>
</thead>
<tbody>
"""

for _, row in top_distance.iterrows():
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
    judges = (
        f"<p>{row['Judges_Evaluated']}</p>"
        if pd.notna(row['Judges_Evaluated']) else ""
    )
    evaluators = (
        f"<p>{row['PH3_Evaluator_1st']}, {row['PH3_Evaluator_2nd']}</p>"
        if pd.notna(row['PH3_Evaluator_1st']) and pd.notna(row['PH3_Evaluator_2nd']) else ""
    )
    distance = (
        f"<p>{row['Distance to having the same score']}</p>"
        if pd.notna(row['Distance to having the same score']) else ""
    )
    html_table += f"""
<tr>
<td style="padding: 8px;">{row['Startup name']}</td>
<td style="padding: 8px;">{website_link}</td>
<td style="padding: 8px;">{deck_link}</td>
<td style="padding: 8px;">{round(row['Judge Evaluation Average'], 2)}</td>
<td style="padding: 8px;">{judges}</td>
<td style="padding: 8px;">{round(row['PH3_Final_Score'], 2)}</td>
<td style="padding: 8px;">{evaluators}</td>
<td style="padding: 8px;">{distance}</td>
</tr>
"""

html_table += """
</tbody>
</table>
</div>
"""

st.markdown(html_table, unsafe_allow_html=True)