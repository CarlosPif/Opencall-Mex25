from pyairtable import Api
import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np
import datetime
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
    layout="centered"
)

df['Fecha'] = pd.to_datetime(df['Creation_date']).dt.date

# Agrupamos y calculamos acumulado
df_evolucion = df.groupby('Fecha').size().reset_index(name='Aplicaciones')
df_evolucion = df_evolucion.sort_values('Fecha')
df_evolucion['Acumulado'] = df_evolucion['Aplicaciones'].cumsum()

# Gráfico de línea acumulada en azul celeste
import plotly.graph_objects as go

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df_evolucion['Fecha'],
    y=df_evolucion['Acumulado'],
    mode='lines+markers',
    name='Acumulado',
    line=dict(color='#87CEEB', shape='spline', width=3)
))

# Línea horizontal de objetivo
fig.add_hline(y=1200, line_color='#FFA500', line_dash='dash', annotation_text='Target', annotation_position='top right')

# Diseño
fig.update_layout(
    title="Applications Time Evolution",
    xaxis_title='Date',
    yaxis_title='Applications',
    template='plotly_white',
    title_font=dict(size=24, color='black'),
    title_x=0.3
)

st.plotly_chart(fig)