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
    page_title="Opencall Dashboard Decelera Mexico 2025",
    layout="wide"
)

st.markdown("**<h1 style='text-align: center;'>Open Call Decelera Mexico 2025<br><br>Phase 5 (Team Calls)</h1>**", unsafe_allow_html=True)

#===========Vamos a hacer una buena distribucion================
df_j = df.dropna(subset=['HDD_avg', 'BDD_Average'])
df_j['PH5_Average'] = (df_j['HDD_avg'] + df_j['BDD_Average']) / 2

evaluation_ph5 = list(
    df_j[
        (df_j['PH5_Average'] != 0)
    ]['PH5_Average']
)

kde = gaussian_kde(evaluation_ph5)
x_j = np.linspace(min(evaluation_ph5), max(evaluation_ph5), 200)
y_j = kde(x_j) * len(evaluation_ph5)

fig = go.Figure()

fig.add_traces(go.Scatter(
    x=x_j,
    y=y_j,
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
    title='Team Calls Scoring Distribution',
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

#============================Calidad por reference========================
fig = go.Figure()

def add_source_trace(fig, df_src, name, color, legendonly=True):
    fig.add_trace(go.Scatter(
        x=df_src['Created_str'],
        y=df_src['average'],
        mode='lines+markers',
        name=name,
        visible=('legendonly' if legendonly else True),
        line_shape='spline',
        line=dict(color=color)
    ))

df_quality_int_agg = df_j.groupby('Created_str', as_index=False).agg(
    average=('PH5_Average','mean')
)
df_quality_int_agg = df_quality_int_agg.sort_values('Created_str')
mean_value = df_quality_int_agg['average'].mean()

add_source_trace(
    fig,
    df_quality_int_agg,
    'All',
    colors[0],
    legendonly=False
)

df_quality_int_agg = df_j[(df_j['PH1_reference_$startups'] == 'Referral') | (df_j['PH1_reference_$startups'] == "Referral from within Decelera's community (who?, please specify)")]

df_quality_int_agg = df_j.groupby('Created_str', as_index=False).agg(
    average=('PH3_Final_Score','mean')
)
df_quality_int_agg = df_quality_int_agg.sort_values('Created_str')

add_source_trace(
    fig,
    df_quality_int_agg,
    'Referral',
    colors[1]
)

df_quality_int_agg = df_j[df_j['PH1_reference_$startups'] == 'LinkedIn']

df_quality_int_agg = df_quality_int_agg.groupby('Created_str', as_index=False).agg(
    average=('PH3_Final_Score','mean')
)
df_quality_int_agg = df_quality_int_agg.sort_values('Created_str')

add_source_trace(
    fig,
    df_quality_int_agg,
    'LinkedIn',
    'blue'
)

df_quality_int_agg = df_j[df_j['PH1_reference_$startups'] == "Decelera's team reached out by email"]

df_quality_int_agg = df_quality_int_agg.groupby('Created_str', as_index=False).agg(
    average=('PH3_Final_Score','mean')
)
df_quality_int_agg = df_quality_int_agg.sort_values('Created_str')

add_source_trace(
    fig,
    df_quality_int_agg,
    "Decelera's team reached out by email",
    colors[3]
)

df_quality_int_agg = df_j[df_j['PH1_reference_$startups'] == "Decelera's newsletter"]

df_quality_int_agg = df_quality_int_agg.groupby('Created_str', as_index=False).agg(
    average=('PH3_Final_Score','mean')
)
df_quality_int_agg = df_quality_int_agg.sort_values('Created_str')

add_source_trace(
    fig,
    df_quality_int_agg,
    "Decelera's newsletter",
    colors[4]
)

df_quality_int_agg = df_j[df_j['PH1_reference_$startups'] == "Decelera's website"]

df_quality_int_agg = df_quality_int_agg.groupby('Created_str', as_index=False).agg(
    average=('PH3_Final_Score','mean')
)
df_quality_int_agg = df_quality_int_agg.sort_values('Created_str')

add_source_trace(
    fig,
    df_quality_int_agg,
    "Decelera's website",
    'black'
)

fig.add_hline(
    y=mean_value,
    line_color='black',
    line_dash='dash',
    annotation_text=f"mean: {mean_value:.2f}",
    annotation_position='top left'
)

fig.update_layout(
    title='Startups quality over time'
)

st.plotly_chart(fig)



#====================Tabla con los exceptional==========================

st.markdown("Below companies that are excepcional according to BDD")

exceptional = df[df['BDD_Excepcional'] == True]

exceptional = exceptional.rename(columns={
    'deck_URL': 'Deck (url)',
    'distancia': 'Distance to having the same score',
    'Judges_Average': 'Judge Evaluation Average'
})

exceptional['Deck (doc)'] = df['deck_$startup'].apply(
    lambda x: x[0]['url'] if isinstance(x, list) and len(x) > 0 and isinstance(x[0], dict) and 'url' in x[0] else None
)

exceptional['deck_icon'] = df['deck_$startup'].apply(
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
<th style="text-align: center; padding: 8px;">BDD Average</th>
<th style="text-align: center; padding: 8px;">HDD Average</th>
<th style="text-align: center; padding: 8px;">Tier Class</th>
</tr>
</thead>
<tbody>
"""

for _, row in exceptional.iterrows():
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
        f"<p>{row['BDD_Average']}</p>"
        if pd.notna(row['BDD_Average']) else ""
    )
    evaluators = (
        f"<p>{row['HDD_avg']}</p>"
        if pd.notna(row['HDD_avg']) else ""
    )
    tier = (
        f"<p>{row['Tier_Class']}</p>"
        if pd.notna(row['Tier_Class']) else ""
    )
    html_table += f"""
<tr>
<td style="padding: 8px;">{row['Startup name']}</td>
<td style="padding: 8px;">{website_link}</td>
<td style="padding: 8px;">{deck_link}</td>
<td style="padding: 8px;">{round(row['BDD_Average'], 2)}</td>
<td style="padding: 8px;">{round(row['HDD_avg'], 2)}</td>
<td style="padding: 8px;">{row['Tier_Class']}</td>
</tr>
"""

html_table += """
</tbody>
</table>
</div>
"""

st.markdown(html_table, unsafe_allow_html=True)