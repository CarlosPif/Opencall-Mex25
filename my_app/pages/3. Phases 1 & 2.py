from pyairtable import Api
import pandas as pd
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
import plotly.express as px
import requests
import io
from plotly.subplots import make_subplots
import plotly.io as pio
from PIL import Image

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

st.markdown("**<h1 style='text-align: center;'>Open Call Decelera Mexico 2025<br><br>Phases 1 & 2 (Form Algorithm)</h1>**", unsafe_allow_html=True)
# ====================Vamos con la distribucion de las notas=======================
evaluation = list(df[df['PH1&PH2_Sum_Mex25'] != 0].dropna(subset='PH1&PH2_Sum_Mex25')['PH1&PH2_Sum_Mex25'])

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
    title='Form Algorithm Scoring Distribution',
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

#====================================Calidad a lo largo del tiempo==========================
st.markdown("Below you can see the mean scored each day in order to check the quality of the applicants, divided by reference")
df_quality_int = df.copy().dropna(subset='PH1&PH2_Sum_Mex25')

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

df_quality_int_agg = df_quality_int.groupby('Created_str', as_index=False).agg(
    average=('PH3_Final_Score','mean')
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

df_quality_int_agg = df_quality_int[(df_quality_int['PH1_reference_$startups'] == 'Referral') | (df_quality_int['PH1_reference_$startups'] == "Referral from within Decelera's community (who?, please specify)")]

df_quality_int_agg = df_quality_int_agg.groupby('Created_str', as_index=False).agg(
    average=('PH3_Final_Score','mean')
)
df_quality_int_agg = df_quality_int_agg.sort_values('Created_str')

add_source_trace(
    fig,
    df_quality_int_agg,
    'Referral',
    colors[1]
)

df_quality_int_agg = df_quality_int[df_quality_int['PH1_reference_$startups'] == 'LinkedIn']

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

df_quality_int_agg = df_quality_int[df_quality_int['PH1_reference_$startups'] == "Decelera's team reached out by email"]

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

df_quality_int_agg = df_quality_int[df_quality_int['PH1_reference_$startups'] == "Decelera's newsletter"]

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

df_quality_int_agg = df_quality_int[df_quality_int['PH1_reference_$startups'] == "Decelera's website"]

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