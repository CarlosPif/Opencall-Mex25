from pyairtable import Api
import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np
import datetime
from scipy.stats import gaussian_kde
import plotly.graph_objects as go

# Configuracion de AirTable

api_key = st.secrets["airtable"]["api_key"]
base_id = st.secrets["airtable"]["base_id"]
table_id = st.secrets["airtable"]["table_id"]

api = Api(api_key)
table = api.table(base_id, table_id)

# Obtenemos los datos
records = table.all(view='Applicants Mex25')
data = [record['fields'] for record in records]
df = pd.DataFrame(data)

def fix_cell(val):
    if isinstance(val, dict) and "specialValue" in val:
        return float("nan")
    return val

df = df.applymap(fix_cell)

# Comenzamos con el dashboard
st.set_page_config(
    page_title="Opencall Dashboard Decelera Mexico 2025",
    layout="wide"
)

st.markdown("**<h1 style='text-align: center;'>Open Call Decelera Mexico 2025</h1>**", unsafe_allow_html=True)

# Tomamos las puntuaciones
scores = df['PH1&PH2_Average_Mex25']

#Algunas metricas generales
mean = np.mean(scores)
median = np.median(scores)
st_dev = np.std(scores)

# Curva de densidad kde
kde = gaussian_kde(scores)
x_vals = np.linspace(min(scores), max(scores), 1000)
y_vals = kde(x_vals)

fig = go.Figure()

fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', fill='tozeroy', name='Densidad', line_color='skyblue'))

fig.update_layout(title='Phase 1 & 2 Scoring Distribution',
                  xaxis_title='Score',
                  yaxis_title='Density')

#cuadro con metricas
texto_metricas = (
    f"<b>General Metrics:</b><br>"
    f"Mean: {mean:.2f}<br>"
    f"Median: {median:.2f}<br>"
    f"Std Dev: {st_dev:.2f}"
)

fig.add_annotation(
    text=texto_metricas,
    xref="paper", yref="paper",
    x=0.95, y=0.95,
    showarrow=False,
    bordercolor="black",
    borderwidth=1,
    bgcolor="white",
    opacity=0.8,
    align="left"
)

st.plotly_chart(fig)
