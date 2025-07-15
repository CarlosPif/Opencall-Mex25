from pyairtable import Api
import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np
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
records_df = table_df.all(view='PH1-PH2_All Applicant Mex25', time_zone="Europe/Madrid")
data_df = [record['fields'] for record in records_df]
df_df = pd.DataFrame(data_df)

def fix_cell(val):
    if isinstance(val, dict) and "specialValue" in val:
        return float("nan")
    return val

df = df.applymap(fix_cell)
df_24 = df_24.applymap(fix_cell)
df_ld = df_ld.applymap(fix_cell)

# Comenzamos con el dashboard
st.set_page_config(
    page_title="Opencall Dashboard Decelera Mexico 2025",
    layout="wide"
)

st.markdown("**<h1 style='text-align: center;'>Open Call Decelera Mexico 2025</h1>**", unsafe_allow_html=True)

# Un conteo general antes de nada=======================================================
# Sacamos los formularios en progreso

def get_in_progress_submissions_count(form_id, api_key):
    total_responses = 0
    after = None
    size = 100  # Fillout permite hasta 100

    while True:
        url = f"https://api.fillout.com/v1/api/forms/{form_id}/submissions"
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {
            "status": "in_progress",
            "limit": size
        }
        if after:
            params['after'] = after

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            responses = data.get("responses", [])
            total_responses += len(responses)

            after = data.get("pageInfo", {}).get("endCursor", None)
            if not after or not data.get("pageInfo", {}).get("hasNextPage", False):
                break
        else:
            st.error(f"Error Fillout API: {response.status_code} - {response.text}")
            break

    return total_responses

total_ip = get_in_progress_submissions_count(form_id, api_key_fl)

#totales
total = df.shape[0]
target = 1200
ratio = round(total / target * 100, 2)

#de los referral
df_df_ref = df_df[df_df['PH1_reference_$startups'] == "Referral from within Decelera's community (who?, please specify)"]
ref_app = df_df_ref['PH1_reference_$startups'].shape[0]

ref_ld_app = df_ld[df_ld['Applied'].fillna(False) == True].shape[0]

ref_ld = df_ld['Company'].shape[0] - ref_ld_app

total_ref = ref_app + ref_ld

#porcentaje de conversion
pct_conv = round(ref_app / total_ref *100, 2)

#porcentaje objetivo
pct_obj = round(ref_app / 250 * 100, 2)

#aplicaciones qu epasan a fase 2
phase2_clean = df_df[df_df['Phase1&2_result_mex25'] == 'Passed Phase 2'].shape[0]
phase2_flag = df_df[df_df['Phase1&2_result_mex25'] == "Red Flagged at Phase 2"].shape[0]
fase2_pct = round((phase2_clean + phase2_flag) / df_df.shape[0] * 100, 2)

#female founders
founders = df.shape[0]
for founder in df['Second founder name']:
    if founder:
        founders += 1
for founder in df['Third founder name']:
    if founder:
        founders +=1

female_founders = df['Female'].sum()
female_percentage = round(female_founders / founders * 100, 2)

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
.metric-label{{margin-top:2px;font-size:10px;letter-spacing:.3px;}}
</style>

<!-- ───────── PRIMER PISO (2 cajas) ───────── -->
<div class="dashboard-row">

  <!-- Caja 1: referrals -->
  <div class="big-card">
    <div class="metric-main-num">{total_ref}</div>
    <div class="metric-main-label">Total number of referrals</div>
    <div class="sub-row">
      <div class="metric-box"><div class="metric-value">{pct_conv}%</div>
                               <div class="metric-label">Percentage of referrals that applied</div></div>
      <div class="metric-box"><div class="metric-value">{pct_obj}%</div>
                               <div class="metric-label">Percentage of our target number of referrals covered</div></div>
    </div>
  </div>

  <!-- Caja 2: applications -->
  <div class="big-card">
    <div class="metric-main-num">{total + total_ip}</div>
    <div class="metric-main-label">Total number of applications</div>
    <div class="sub-row">
      <div class="metric-box"><div class="metric-value">{total_ip}</div>
                               <div class="metric-label">In progress applications</div></div>
      <div class="metric-box"><div class="metric-value">{ratio}%</div>
                               <div class="metric-label">Percentage of our target number of applications covered</div></div>
    </div>
  </div>

</div>

<!-- ───────── SEGUNDO PISO (1 caja) ───────── -->
<div class="dashboard-row">

  <!-- Caja 3: female + phase-2 -->
  <div class="big-card" style="max-width:600px;margin:auto;">
    <div class="sub-row">
      <div class="metric-box"><div class="metric-value">{female_percentage}%</div>
                               <div class="metric-label">Female founder percentage</div></div>
      <div class="metric-box"><div class="metric-value">{fase2_pct}%</div>
                               <div class="metric-label">Percentage of applications that passed phase 2</div></div>
    </div>
  </div>

</div>
""", unsafe_allow_html=True)

st.markdown("**<h2>Temporal Follow Up</h2>**", unsafe_allow_html=True)
st.markdown("Below a temporal analysis of the number of applications submitted and times a bitly link has been clicked")

#======Aplicaciones por dia===========================
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
    line=dict(color='skyblue', shape='spline', width=3),
    fill='tozeroy',
    fillcolor='rgba(135, 206, 235, 0.2)'
))

fig.add_trace(go.Scatter(
    x=df_24_evolucion['Created_date'],
    y=df_24_evolucion['Aplicaciones'],
    mode='lines+markers',
    name='Applications per day (Mexico 2024)',
    line=dict(color='orange', shape='spline', width=3),
))

fig.update_layout(
    title="Applications received by day",
    xaxis_title='Date',
    yaxis_title='Applications',
    template='plotly_white',
    title_font=dict(size=20),
    title_x=0.4,
    legend=dict(
        x=0.95,         # Posición horizontal (0=izq, 1=der)
        y=0.95,         # Posición vertical (0=abajo, 1=arriba)
        xanchor='right',  # El punto de anclaje (left, center, right)
        yanchor='top',    # El punto de anclaje (top, middle, bottom)
        bgcolor='rgba(255,255,255,0.5)',  # Fondo blanco semitransparente
        bordercolor='gray',
        borderwidth=1,
        font=dict(color='black')
    ),
    xaxis_range = [df_evolucion['Created_date'].min(), hoy],
    yaxis_range=[0, df_evolucion['Aplicaciones'].max() + 10]
)

st.plotly_chart(fig)
#Referencias de las aplicaciones=============================================

reference_data = df['PH1_reference_$startups'].replace(
{"Referral from within Decelera's community (who?, please specify)": "Referral"}
)
reference_count = reference_data.value_counts().reset_index(name='count')

total = reference_count['count'].sum()
reference_count['pct'] = (reference_count['count'] / total * 100).round(1)
reference_count['text'] = reference_count['count'].astype(str) + "(" + reference_count['pct'].astype(str) + "%)"

fig = go.Figure()

for i, row in reference_count.iterrows():
    fig.add_shape(
        type="line",
        x0=row['PH1_reference_$startups'], x1=row['PH1_reference_$startups'],
        y0=0, y1=row['count'],
        xref='x', yref='y',
        line=dict(color='skyblue', width=2)
    )


# Punto (la piruleta)
fig.add_trace(go.Scatter(
    x=reference_count['PH1_reference_$startups'],
    y=reference_count['count'],
    mode='markers+text',
    marker=dict(color='skyblue', size=20, line=dict(color='white', width=1)),
    text=reference_count['text'],
    textposition='top center',
    textfont=dict(color='black'),
    name='Total Clicks'
))

fig.update_layout(
    title='Application references',
    xaxis_title='',
    xaxis=dict(
        tickfont=dict(color='black')
    ),
    title_x=0.4,
    yaxis_title='Amount of applications',
    template='plotly_white',
    height=600,
    showlegend=False
)

st.plotly_chart(fig)

#==================Desglose de references y referrals=======================
# ── Conteo de cada valor en Source_leads ─────────────────────────
source_count = (
    df_df['Source_leads']             
        .fillna('Sin fuente')            
        .value_counts()
        .reset_index(name='count')
)

source_count = source_count[~source_count['Source_leads'].isin(['Sin fuente', "Didn't specify"])]

fig = px.pie(
    source_count,
    names='Source_leads',
    values='count',
    title='Referrals Source Mexico 2025',
    hole=0.35              
)

fig.update_layout(
    legend=dict(
        orientation='v',  
        y=0.5,           
        x=1.05,          
        xanchor='left',
        font=dict(size=12)
    ),
    margin=dict(l=20, r=120, t=80, b=20)
)

st.plotly_chart(fig, use_container_width=True)


cols = st.columns(2)

with cols[0]:
    conteo_refs = df_24.groupby('PH1_reference_$startups').size().reset_index(name='count')

    total_global = conteo_refs['count'].sum()
    conteo_refs['pct'] = conteo_refs['count'] / total_global * 100

    conteo_refs['PH1_reference_$startups'] = conteo_refs.apply(
        lambda row: 'Others' if row['pct'] < 2 else row['PH1_reference_$startups'],
        axis=1
    )

    referral_pct = conteo_refs.loc[
        conteo_refs['PH1_reference_$startups'] == 'Referral', 'pct'
        ].iloc[0]

    conteo_refs = (
        conteo_refs
        .groupby('PH1_reference_$startups', as_index=False)['count']
        .sum()
    )

    fig = px.pie(conteo_refs, names="PH1_reference_$startups", values="count",
                    title="Mexico 2024 References")
        
    fig.update_layout(
        legend=dict(
        orientation='h',
        y=-0.20,
        x=0.5,
        xanchor='center',
        font=dict(size=11)
        ),
        margin=dict(t=90, b=120),
        title_x = 0.35
    )

    st.plotly_chart(fig)

with cols[1]:
    # DataFrame con columnas 'semana' (1-N) y 'count'
    semana_referrals = (
        df_24[df_24['PH1_reference_$startups'] == 'Referral']
        .assign(fecha=lambda d: pd.to_datetime(d['Created_str']))
        .assign(semana=lambda d: ((d['fecha'] - inicio_2024).dt.days // 7) + 1)
        .groupby('semana', as_index=False)['fecha']
        .size()
        .rename(columns={'size': 'count'})
        .sort_values('semana')
    )

    total_referrals = semana_referrals['count'].sum()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=semana_referrals['semana'],
        y=semana_referrals['count'],
        text=semana_referrals['count'],
        textposition='outside',
        marker=dict(
            color="#87CEEB",
            line=dict(color="#5aa5c8", width=1.5),
        ),
    ))

    fig.update_layout(
        title=f"Total referrals Mexico 2024: {total_referrals}",
        xaxis_title="Week",
        yaxis_title="Number of Referrals",
        bargap=0.15,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig, use_container_width=True)

#------------Vamos a sacar los clicks de Bitly---------------------
# === Funciones para Bitly ===


#====================grafica con los bilinks por separado====================


#============================Barras=========================
# Filtrar solo datos de 2024 en df_24
df['year'] = 2025
df_24 = df_24[df_24['Created'] >= pd.to_datetime("2024-01-01")]
df_24['year'] = 2024

# Aplicar desfase temporal a df_24 para alinear campañas
df_24['Created_aligned'] = df_24['Created'] + time_delta
df['Created_aligned'] = df['Created']  # Para mantener misma columna

# Extraer semana y día de la semana alineados
df['week_start'] = df['Created_aligned'] - pd.to_timedelta(df['Created_aligned'].dt.dayofweek, unit='D')
df['weekday'] = df['Created_aligned'].dt.day_name()

df_24['week_start'] = df_24['Created_aligned'] - pd.to_timedelta(df_24['Created_aligned'].dt.dayofweek, unit='D')
df_24['weekday'] = df_24['Created_aligned'].dt.day_name()

# Combinar ambos datasets
df_comparado = pd.concat([df, df_24], ignore_index=True)

# === Crear lista de semanas disponibles ===
semanas_disp_df = df_comparado[['week_start']].drop_duplicates().sort_values('week_start')
semanas_disp_df['etiqueta'] = semanas_disp_df['week_start'].dt.strftime(f"Week of %Y-%m-%d")

# Crear diccionario para dropdown
diccionario_semanas = dict(zip(semanas_disp_df['etiqueta'], semanas_disp_df['week_start']))

# Calcular semana actual alineada
hoy = pd.Timestamp.today().normalize()
hoy_alineado = hoy - pd.to_timedelta(hoy.dayofweek, unit='D')
etiqueta_actual = None
for etiqueta, fecha in diccionario_semanas.items():
    if fecha == hoy_alineado:
        etiqueta_actual = etiqueta
        break

default_index = list(diccionario_semanas.keys()).index(etiqueta_actual) if etiqueta_actual else len(diccionario_semanas) - 1

# === Dropdown de semana ===
semana_etiqueta_seleccionada = st.selectbox('Select campaign week', list(diccionario_semanas.keys()), index=default_index)
fecha_inicio_seleccionada = diccionario_semanas[semana_etiqueta_seleccionada]

# === Filtrar y agrupar datos ===
fecha_fin_seleccionada = fecha_inicio_seleccionada + pd.Timedelta(days=6)
df_filtrado = df_comparado[(df_comparado['Created_aligned'] >= fecha_inicio_seleccionada) & 
                           (df_comparado['Created_aligned'] <= fecha_fin_seleccionada)]

total_aplicaciones = df_filtrado[df_filtrado['year'] == 2025].shape[0]
total_aplicaciones_24 = df_filtrado[df_filtrado['year'] == 2024].shape[0]

# Agrupar por día de la semana
conteo_dias = df_filtrado.groupby(['weekday', 'year']).size().reset_index(name='count')

# Orden correcto de días
dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
conteo_dias['weekday'] = pd.Categorical(conteo_dias['weekday'], categories=dias_orden, ordered=True)
conteo_dias = conteo_dias.sort_values('weekday')

# Asegurar que 'year' sea string
conteo_dias['year'] = conteo_dias['year'].astype(str)

# === Gráfico de barras agrupadas ===
fig = px.bar(
    conteo_dias,
    x="weekday",
    y="count",
    color='year',
    barmode='group',
    text='count',
    title=f"Applications by Day - Week of {fecha_inicio_seleccionada.strftime('%Y-%m-%d')} Comparison",
    template="plotly_white",
    color_discrete_sequence=["#FFA500", "#87CEEB"],
    height=600
)

fig.add_annotation(
    text=f"<b>Total 2025: {total_aplicaciones}</b><br><b>Total 2024: {total_aplicaciones_24}",
    xref="paper", yref="paper",
    x=0, y=1.1,
    showarrow=False,
    font=dict(size=16, color="black"),
    bgcolor="white",
)

fig.update_traces(textposition='outside', textfont=dict(color='black'))
fig.update_layout(yaxis=dict(dtick=1))

st.plotly_chart(fig, key="grafica_barras_semana_alineada")

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
    line=dict(color='#87CEEB', shape='spline', width=3),
    fill='tozeroy',
    fillcolor='rgba(135, 206, 235, 0.2)'
))

# Línea naranja - 2024
fig.add_trace(go.Scatter(
    x=df_evolucion_24['Fecha'],
    y=df_evolucion_24['Acumulado'],
    mode='lines+markers',
    name='2024 Accumulated',
    line=dict(color='#FFA500', shape='spline', width=3)
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


st.markdown("**<h2>General Metrics</h2>**", unsafe_allow_html=True)
    
# Vamos a hablar de los red flags

cols = st.columns(2)

with cols[0]:
    todos_motivos = []

    for texto in df_df["Phase1_result_reason_mex25"]:
        if isinstance(texto, str):
            motivos = [m.strip() for m in texto.split(". ") if m.strip()]
            todos_motivos.extend(motivos)

    # Contamos los motivos
    conteo = Counter(todos_motivos)

    # Convertimos a DataFrame para graficar
    df_conteo = pd.DataFrame(conteo.items(), columns=["Motivo", "Cantidad"])

    fig = px.bar(df_conteo, x='Motivo', y='Cantidad', title='Phase 1 Red Flag Reasons', text='Cantidad', color='Motivo')

    fig.update_layout(
        xaxis_title="",
        xaxis=dict(
            tickfont=dict(
                color='black'
            )
        ),
        xaxis_tickangle=45,
        yaxis_title="Companies",
        title_x=0.4,
        showlegend=False
    )

    fig.update_traces(textposition="outside", textfont_color='black',
                    cliponaxis=False)

    st.plotly_chart(fig)

with cols[1]:
    todos_motivos = []

    for texto in df_df["Phase2_result_reason_mex25"]:
        if isinstance(texto, str):
            motivos = [m.strip() for m in texto.split(". ") if m.strip()]
            todos_motivos.extend(motivos)

    # Contamos los motivos
    conteo = Counter(todos_motivos)

    # Convertimos a DataFrame para graficar
    df_conteo = pd.DataFrame(conteo.items(), columns=["Motivo", "Cantidad"])

    fig = px.bar(df_conteo, x='Motivo', y='Cantidad', title='Pahse 2 Red Flag Reasons', text='Cantidad', color='Motivo')

    fig.update_layout(
        xaxis_title="",
        xaxis=dict(
            tickfont=dict(
                color='black'
            )
        ),
        yaxis_title="Companies",
        title_x=0.4,
        xaxis_tickangle=45,
        showlegend=False
    )

    fig.update_traces(textposition="outside", textfont_color='black',
                    cliponaxis=False)

    st.plotly_chart(fig)