from pyairtable import Api
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import requests

# Configuracion de AirTable
api_key_at = st.secrets["airtable"]["api_key"]
base_id = st.secrets["airtable"]["base_24_id"]
table_id = st.secrets["airtable"]["table_24_id"]

#tabla de dealflow
base_id_df = st.secrets["airtable"]["base_id"]
table_id_df = st.secrets["airtable"]["table_id"]

#tabla de leads
base_id_ld = st.secrets["airtable"]["base_id_ld"]
table_id_ld = st.secrets["airtable"]["table_id_ld"]

#fillout
api_key_fl = st.secrets['fillout']['api_key']
form_id = st.secrets['fillout']['form_id']

api = Api(api_key_at)
table = api.table(base_id, table_id)
table_24 = api.table(base_id, table_id)
table_df = api.table(base_id_df, table_id_df)
table_ld = api.table(base_id_ld, table_id_ld)

# Obtenemos los datos
records = table.all(view='Applicants_MEX25', time_zone="Europe/Madrid")
data = [record['fields'] for record in records]
df = pd.DataFrame(data)

# y para mex24
records_24 = table_24.all(view='Applicants DEC MEXICO 2024', time_zone="Europe/Madrid")
data_24 = [record['fields'] for record in records_24]
df_24 = pd.DataFrame(data_24)

#y para leads
records_ld = table_ld.all(view='Referral Tracking')
data_ld = [record['fields'] for record in records_ld]
df_ld = pd.DataFrame(data_ld)

#y para el dealflow
records_df = table_df.all(view='All applicants  by Phase', time_zone="Europe/Madrid")
data_df = [record['fields'] for record in records_df]
df_df = pd.DataFrame(data_df)

def fix_cell(val):
    if isinstance(val, dict) and "specialValue" in val:
        return float("nan")
    return val

df = df.map(fix_cell)
df_24 = df_24.map(fix_cell)
df_ld = df_ld.map(fix_cell)
df_df = df_df.map(fix_cell)

colors = ['#1FD0EF', '#FFB950', '#FAF3DC', '#1158E5', '#B9C1D4', '#F2F8FA']

#Comenzamos con el dashboard
st.set_page_config(
    page_title="Opencall Dashboard Decelera Mexico 2025",
    layout="wide"
)

st.markdown("**<h1 style='text-align: center;'>Open Call Decelera Mexico 2025</h1>**", unsafe_allow_html=True)

#===================Plantamos aqui tremendo funnel===============
total = df.shape[0] 

map_status_to_phase = {
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

df2 = df_df.copy()
df2['Status'] = df2['Status'].replace(map_status_to_phase)

funnel_count = (df2.groupby('Status', as_index=False)
                  .size()
                  .rename(columns={'size': 'count'}))

order = [
    'Phase 1',
    'Phase 2 & 3 (Internal Evaluation)',
    'Phase 4 (Judge Evaluation)',
    'Phase 5 (Team Call)'
]
funnel_count = (funnel_count.set_index('Status')
                             .reindex(order, fill_value=0)
                             .reset_index())

funnel_count.loc[funnel_count['Status'] == 'Phase 1', 'count'] += 478

funnel_count['count_cum'] = funnel_count['count'].iloc[::-1].cumsum().iloc[::-1]
ratio = funnel_count['count_cum'] / funnel_count['count_cum'].shift(1)
funnel_count['pct_conv'] = ratio.apply(lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "")

funnel_count['label'] = funnel_count.apply(
    lambda r: f"{r['count_cum']} ({r['pct_conv']})" if r['pct_conv'] else f"{r['count_cum']}",
    axis=1
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
    title_x=0.5,
    yaxis=dict(
        tickfont=dict(color='black')
    )
)

st.plotly_chart(fig)

#============================Un conteo de las compañies en tiers============================
df_tier = df_df.dropna(subset='Tier_Class')
df_count = df_tier.groupby('Tier_Class').size().reset_index(name='count')
total_tier = df_count['count'].sum()

fig = go.Figure()

fig.add_trace(go.Bar(
    x = df_count['Tier_Class'],
    y = df_count['count'],
    name='Tier Clasification',
    text=df_count['count'],
    textposition='outside',
    textfont=dict(
        color='black'
    ),
    marker=dict(
            color="#1FD0EF",
            line=dict(color="black", width=1.5),
        ),
    cliponaxis=False
))

fig.update_layout(
        title=f'Companies per Tier. Total: {total_tier} companies'
)

st.plotly_chart(fig)

#grafica de aplicaciones a lo largo del tiempo
# Definir el inicio de campaña para cada dataset
inicio_2025 = pd.to_datetime("25-06-2025")
inicio_2024 = pd.to_datetime("20-06-2024")
time_delta = inicio_2025 - inicio_2024

df['Created'] = pd.to_datetime(df['Created_str'], errors='coerce').dt.tz_localize(None)
df_24['Created'] = pd.to_datetime(df_24['Created_str'], errors='coerce').dt.tz_localize(None)

# Filtrar solo datos de 2024 en df_24
df_24 = df_24[df_24['Created'] >= pd.to_datetime("2024-01-01")]

df['Created_date'] = df['Created'].dt.date
df_24['Created_date'] = df_24['Created'].dt.date + time_delta
df_evolucion = df.groupby('Created_date').size().reset_index(name='Aplicaciones')
df_evolucion = df_evolucion.sort_values('Created_date')
df_24_evolucion = df_24.groupby('Created_date').size().reset_index(name='Aplicaciones')
df_24_evolucion = df_24_evolucion.sort_values('Created_date')

# Gráfico de líneas con área rellena

hoy = pd.Timestamp.today().date()

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df_evolucion['Created_date'],
    y=df_evolucion['Aplicaciones'],
    mode='lines+markers',
    name='Applications per day (Mexico 2025)',
    line=dict(color='#1FD0EF', shape='spline', width=3),
    fill='tozeroy',
    fillcolor='rgba(31, 208, 239, 0.2)'
))

fig.add_trace(go.Scatter(
    x=df_24_evolucion['Created_date'],
    y=df_24_evolucion['Aplicaciones'],
    mode='lines+markers',
    name='Applications per day (Mexico 2024)',
    line=dict(color='#FFB950', shape='spline', width=3),
))

fig.update_layout(
    title="Applications received by day",
    xaxis_title='Date',
    yaxis_title='Applications',
    template='plotly_white',
    title_font=dict(size=20),
    title_x=0.4,
    legend=dict(
        x=0.95,
        y=0.95,
        xanchor='right',
        yanchor='top',
        bgcolor='rgba(255,255,255,0.5)',
        bordercolor='gray',
        borderwidth=1,
        font=dict(color='black')
    ),
    xaxis_range = [df_evolucion['Created_date'].min(), hoy],
    yaxis_range=[0, 151]
)

st.plotly_chart(fig)

#acumulado-------------------------------------------------------------------------

inicio_2025 = pd.to_datetime("2025-06-25")
inicio_2024 = pd.to_datetime("2024-06-20")

# Preparamos los datos de 2025
df['Fecha'] = pd.to_datetime(df['Created']).dt.date
df_evolucion_25 = df.groupby('Fecha').size().reset_index(name='Aplicaciones')
df_evolucion_25 = df_evolucion_25.sort_values('Fecha')
df_evolucion_25['Acumulado'] = df_evolucion_25['Aplicaciones'].cumsum()

# Preparamos los datos de 2024
df_24['Fecha_real'] = pd.to_datetime(df_24['Created']).dt.date
df_24['Fecha'] = df_24['Fecha_real'] + (inicio_2025.date() - inicio_2024.date())

df_evolucion_24 = df_24.groupby('Fecha').size().reset_index(name='Aplicaciones')
df_evolucion_24 = df_evolucion_24.sort_values('Fecha')
df_evolucion_24['Acumulado'] = df_evolucion_24['Aplicaciones'].cumsum()

hoy = pd.Timestamp.today().date()

# Filtrar acumulado de 2025 solo hasta hoy
df_evolucion_25_filtrado = df_evolucion_25[df_evolucion_25['Fecha'] <= hoy]

# Obtener valor máximo
max_acumulado_hoy = df_evolucion_25_filtrado['Acumulado'].max()
limite_superior_y = max_acumulado_hoy + 50
# Gráfico combinado
fig = go.Figure()

# Línea azul celeste - 2025
fig.add_trace(go.Scatter(
    x=df_evolucion_25['Fecha'],
    y=df_evolucion_25['Acumulado'],
    mode='lines+markers',
    name='2025 Accumulated',
    line=dict(color='#1FD0EF', shape='spline', width=3),
    fill='tozeroy',
    fillcolor='rgba(31, 208, 239, 0.2)'
))

# Línea naranja - 2024
fig.add_trace(go.Scatter(
    x=df_evolucion_24['Fecha'],
    y=df_evolucion_24['Acumulado'],
    mode='lines+markers',
    name='2024 Accumulated',
    line=dict(color='#FFB950', shape='spline', width=3)
))

# Diseño
fig.update_layout(
    title="Applications Time Evolution - 2025 vs 2024",
    xaxis_title='Date',
    yaxis_title='Applications',
    template='plotly_white',
    title_font=dict(size=24, color='black'),
    title_x=0.3,
    xaxis_range=[df_evolucion_25['Fecha'].min(), hoy],
     yaxis_range=[0, limite_superior_y]
)

# Mostrar gráfico
st.plotly_chart(fig)