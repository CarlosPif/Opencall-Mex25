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

st.markdown("**<h1 style='text-align: center;'>Open Call Decelera Mexico 2025</h1>**", unsafe_allow_html=True)

df_j = df.dropna(subset=['Judges_Average'])

evaluation_ph4 = list(
    df_j[
        (df_j['Judges_Average'] != 0)
    ]['Judges_Average']
)

kde = gaussian_kde(evaluation_ph4)
x_j = np.linspace(min(evaluation_ph4), max(evaluation_ph4), 200)
y_j = kde(x_j) * len(evaluation_ph4)

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
    title='Judge Evaluation Scoring Distribution',
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

#otra vez una de calidad a lo largo del tiempo
df_quality_judge = df[
    (df['Status'] == 'PH4_Judge_Evaluation') |
    (df['Status'] == 'PH4_Waiting_List') |
    (df['Status'] == 'PH5_Pending_Team_Calls') |
    (df['Status'] == 'PH5_Pending_BDD') |
    (df['Status'] == 'PH5_Pending_HDD') |
    (df['Status'] == 'PH5_Calls_Done')
].dropna(subset='Judges_Average')

df_quality_judge_agg = df_quality_judge.groupby('Created_str', as_index=False).agg(
    average=('Judges_Average', 'mean'),
    count=('Judges_Average', 'count'),
    acum=('Judges_Average', 'sum')
)

df_quality_judge_agg = df_quality_judge_agg.sort_values('Created_str')
df_quality_judge_agg['acum'] = df_quality_judge_agg['acum'].cumsum()
df_quality_judge_agg['derivative'] = df_quality_judge_agg['acum'].diff()

#y graficamos
fig = px.line(
    df_quality_judge_agg,
    x='Created_str',
    y='average',
    title='Startups quality over time (Judge Evaluation)',
    markers=True,
    line_shape='spline',
    hover_data={'count': True},
    color_discrete_sequence=['#1FD0EF']
)

mean_value = df_quality_judge_agg['average'].mean()

fig.add_hline(
    y=mean_value,
    line_color='#FFB950',
    line_dash='dash',
    annotation_text=f"mean: {mean_value:.2f}",
    annotation_position='top left'
)

st.plotly_chart(fig)

fig = px.line(
    df_quality_judge_agg,
    x='Created_str',
    y='derivative',
    title='Startups quality over time (Judge Evaluation) variation rate',
    markers=True,
    line_shape='spline',
    hover_data={'count': True},
    color_discrete_sequence=['#1FD0EF']
)

st.plotly_chart(fig)

#vamos a hacer una tabla de las mejores compañias en jueces
st.markdown("Top 10 Startups Judge Evaluation")

df['Deck (doc)'] = df['deck_$startup'].apply(
    lambda x: x[0]['url'] if isinstance(x, list) and len(x) > 0 and isinstance(x[0], dict) and 'url' in x[0] else None
)

df['deck_icon'] = df['deck_$startup'].apply(
    lambda x: x[0].get('thumbnails', {}).get('small', {}).get('url') if isinstance(x, list) and x else None
)

top_10 = df.sort_values(by='Judges_Average', ascending=False).head(10)
top_10['Judges_Average'] = top_10['Judges_Average'].apply(lambda x: round(x, 2))

top_10 = top_10.rename(columns={
    'deck_URL': 'Deck (url)',
    'Judges_Average': 'Judge Evaluation Average'
})

html_table = """
<div style="overflow-x: auto; width: 100%;">
<table style="width: 100%; border-collapse: collapse;">
<thead>
<tr>
<th style="text-align: center; padding: 8px;">Startup</th>
<th style="text-align: center; padding: 8px;">Deck (doc)</th>
<th style="text-align: center; padding: 8px;">Deck (link)</th>
<th style="text-align: center; padding: 8px;">Score</th>
<th style="text-align: center; padding: 8px;">Judges</th>
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
    judges = (
        f"<p>{row['Judges_Evaluated']}</p>"
        if pd.notna(row['Judges_Evaluated']) else ""
    )
    html_table += f"""
<tr>
<td style="padding: 8px;">{row['Startup name']}</td>
<td style="padding: 8px;">{website_link}</td>
<td style="padding: 8px;">{deck_link}</td>
<td style="padding: 8px;">{row['Judge Evaluation Average']}</td>
<td style="padding: 8px;">{judges}</td>
</tr>
"""

html_table += """
</tbody>
</table>
</div>
"""

st.markdown(html_table, unsafe_allow_html=True)