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

st.markdown("**<h1 style='text-align: center;'>Open Call Decelera Mexico 2025</h1>**", unsafe_allow_html=True)

#===================Plantamos aqui tremendo funnel===============
total = df.shape[0] 

funnel_count = (
    df.replace(
        {
            'PH1_To_Be_Rejected': 'Phase 1',
            'PH1_Rejected': 'Phase 1',
            'PH1_Review': 'Phase 1',
            'PH1_Pending_Send_Magic_Link': 'Phase 2 & 3 (Internal Evaluation)',
            'PH1_Magic_Link_Sent': 'Phase 2 & 3 (Internal Evaluation)',
            'PH1_Rejected_Review': 'Phase 1',
            'PH3_Internal_Evaluation': 'Phase 2 & 3 (Internal Evaluation)',
            'PH3_To_Be_Rejected': 'Phase 2 & 3 (Internal Evaluation)',
            'PH3_Rejected': 'Phase 2 & 3 (Internal Evaluation)',
            'PH4_Pending_Judge_Assignment': 'Phase 4 (Judge Evaluation)',
            'PH4_Judge_Evaluation': 'Phase 4 (Judge Evaluation)',
            'PH3_Waiting_List': 'Phase 2 & 3 (Internal Evaluation)',
            'PH1_To_Be_Rejected_Reviewed': 'Phase 1',
            'PH4_Waiting_List': 'Phase 4 (Judge Evaluation)',
            'PH4_Rejected': 'Phase 4 (Judge Evaluation)',
            'PH5_Calls_Done': 'Phase 5 (Team Call)',
            'PH5_Pending_BDD': 'Phase 5 (Team Call)',
            'PH5_Pending_HDD': 'Phase 5 (Team Call)',
            'PH5_Pending_Team_Calls': 'Phase 5 (Team Call)'
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

st.plotly_chart(fig)