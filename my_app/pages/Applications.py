from pyairtable import Api
import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np
import datetime
import plotly.graph_objects as go
from collections import Counter
import requests
import pytz

# Configuracion de AirTable

api_key_at = st.secrets["airtable"]["api_key"]
base_id = st.secrets["airtable"]["base_24_id"]
table_id = st.secrets["airtable"]["table_24_id"]

#tabla de dealflow
base_id_df = st.secrets["airtable"]["base_id"]
table_id_df = st.secrets["airtable"]["table_id"]

api_key_fl = st.secrets['fillout']['api_key']
form_id = st.secrets['fillout']['form_id']

api = Api(api_key_at)
table = api.table(base_id, table_id)
table_24 = api.table(base_id, table_id)
table_df = api.table(base_id_df, table_id_df)

# Obtenemos los datos
records = table.all(view='Applicants_MEX25', time_zone="Europe/Madrid")
data = [record['fields'] for record in records]
df = pd.DataFrame(data)

# y para mex24
records_24 = table_24.all(view='Applicants DEC MEXICO 2024', time_zone="Europe/Madrid")
data_24 = [record['fields'] for record in records_24]
df_24 = pd.DataFrame(data_24)

#y para el dealflow
records_df = table_df.all(view='Applicants_Phase', time_zone="Europe/Madrid")
data_df = [record['fields'] for record in records_df]
df_df = pd.DataFrame(data_df)

def fix_cell(val):
    if isinstance(val, dict) and "specialValue" in val:
        return float("nan")
    return val

df = df.applymap(fix_cell)
df_24 = df_24.applymap(fix_cell)

# Comenzamos con el dashboard
st.set_page_config(
    page_title="Opencall Dashboard Decelera Mexico 2025",
    layout="wide"
)

st.markdown("**<h1 style='text-align: center;'>Open Call Decelera Mexico 2025</h1>**", unsafe_allow_html=True)

# Un conteo general antes de nada=======================================================
# Sacamos los formularios en progreso
url = f"https://api.fillout.com/v1/api/forms/{form_id}/submissions"
headers = {
    "Authorization": f"Bearer {api_key_fl}"
}
params = {
    "status": "in_progress"
}

response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    data_ip = response.json()
    total_ip = data_ip.get("totalResponses", 0)

cols = st.columns([1, 1, 2, 2, 2, 1])
total = df.shape[0]
target = 1200
ratio = total / target * 100

cols[2].metric("Current number of applications", f"{total}")
cols[3].metric("In progress applications", f"{total_ip}")
cols[4].metric("Total number of applications", f"{total_ip + total}")

cols = st.columns([1, 1, 2, 2, 1])

cols[2].metric("Target number of applications", f"{target}")
cols[3].metric("Ratio", f"{ratio:.2f}%")

st.markdown("**<h2>Temporal Follow Up</h2>**", unsafe_allow_html=True)

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

#------------Vamos a sacar los clicks de Bitly---------------------
# === Funciones para Bitly ===
def get_group_guid():
    url = "https://api-ssl.bitly.com/v4/groups"
    headers = {"Authorization": f"Bearer {st.secrets['bitly']['access_token']}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data['groups'][0]['guid']  # Devuelve el primer grupo
    else:
        st.error(f"Error al obtener group_guid: {response.status_code} - {response.text}")
        return None

def get_all_bitlinks(group_guid):
    bitlinks = []
    url = f"https://api-ssl.bitly.com/v4/groups/{group_guid}/bitlinks"
    headers = {"Authorization": f"Bearer {st.secrets['bitly']['access_token']}"}
    params = {"size": 100, "page": 1}

    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            bitlinks.extend([link['id'] for link in data.get('links', [])])
            if 'pagination' in data and data['pagination'].get('next', None):
                params['page'] += 1
            else:
                break
        else:
            st.error(f"Error al obtener bitlinks: {response.status_code} - {response.text}")
            break

    return bitlinks


def get_clicks_by_day(bitlink, unit='day', units=30):
    url = f"https://api-ssl.bitly.com/v4/bitlinks/{bitlink}/clicks"
    params = {"unit": unit, "units": units, "size": 100}
    headers = {"Authorization": f"Bearer {st.secrets['bitly']['access_token']}"}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data.get('link_clicks', []))
        if not df.empty:
            df['date'] = pd.to_datetime(df['date']).dt.date
        return df
    else:
        return pd.DataFrame()
    
# === Obtener clics combinados de Bitly ===
click_data = pd.DataFrame()
with st.spinner("Cargando clics de Bitly..."):
    # Obtener group GUID y luego los enlaces
    group_guid = get_group_guid()
    if group_guid:
        bitlinks = get_all_bitlinks(group_guid)
    else:
        bitlinks = []

    clicks_list = []

    for bl in bitlinks:
        df_clicks = get_clicks_by_day(bl, units=60)
        if not df_clicks.empty:
            df_clicks['bitlink'] = bl
            clicks_list.append(df_clicks)

    if clicks_list:
        click_data = pd.concat(clicks_list)
        bitly_total = click_data.groupby('date')['clicks'].sum().reset_index()
    else:
        bitly_total = pd.DataFrame(columns=['date', 'clicks'])

# Clics totales Bitly
if not bitly_total.empty:
    fig.add_trace(go.Scatter(
        x=bitly_total['date'],
        y=bitly_total['clicks'],
        mode='lines+markers',
        name='Bitly Total Clicks',
        line=dict(color='purple', shape='spline', width=3),
    ))

maximo = max(df_evolucion['Aplicaciones'].max(), df_24_evolucion['Aplicaciones'].max(), bitly_total['clicks'].max())
hoy = pd.Timestamp.today().date()

# Diseño
fig.update_layout(
    title="Applications received by day",
    xaxis_title='Date',
    yaxis_title='Applications',
    template='plotly_white',
    title_font=dict(size=20),
    title_x=0.4,
    xaxis_range = [df_evolucion['Created_date'].min(), hoy],
    yaxis_range=[-20, maximo + 10]
)

# Mostrar gráfico en Streamlit
st.plotly_chart(fig)

#====================grafica con los bilinks por separado====================
with st.spinner("Calculando clics totales por bitlink..."):
    group_guid = get_group_guid()
    if group_guid:
        bitlinks = get_all_bitlinks(group_guid)
    else:
        bitlinks = []

    all_clicks = []
    for bl in bitlinks:
        df_clicks = get_clicks_by_day(bl, units=60)
        if not df_clicks.empty:
            total = df_clicks['clicks'].sum()
            all_clicks.append({'bitlink': bl, 'total_clicks': total})

    df_click_totals = pd.DataFrame(all_clicks)

    #aplicamos etiquetas personalizadas
    etiquetas = {
        "bit.ly/4lE0725": "Power MBA",
        "bit.ly/4eG4mr1": "Partners Europa",
        "bit.ly/4l9zeCL": "TEC de Monterrey",
        "bit.ly/4kl3Pfg": "This Week in Fintech",
        "bit.ly/4lanY9j": "BBVA Spark",
        "bit.ly/3TRdKyp": "Collective",
        "bit.ly/3TPMHn5": "ICEX",
        "bit.ly/45Vv7Wh": "Podcast Andrés",
        "bit.ly/44aFUdP": "Pygma",
        "bit.ly/4km2EfL": "LinkedIn post Marcos",
        "bit.ly/44tP6Ji": "F6S",
        "bit.ly/4kfXv8Q": "GUST",
        "bit.ly/3IpanMz": "Team Link",
        "bit.ly/45PWD7u": "Experience Makers",
        "bit.ly/40AA6b9": "Partners",
        "bit.ly/4ev8F8A": "Alumni",
        "bit.ly/44oTh94": "Lead Contact",
        "bit.ly/40smjmT": "Squarespace Mail Communications",
        "bit.ly/4lsbWaU": "TikTok Profile",
        "bit.ly/44tUrAe": "Instagram Stories",
        "bit.ly/4ev8nP2": "Instagram Profile",
        "bit.ly/4eAlizk": "Decelera LinkedIn Job",
        "bit.ly/3ZX4aNY": "Decelera LinkedInd Post",
        "bit.ly/40wgbdm": "Decelera LinkedIn",
        "bit.ly/4lkunhy": "Decelera Form Press",
        "bit.ly/4k33Bt6": "Decelera_Mexico25_PH1",
        "bit.ly/4kOZYIH": "Waitinglinst post"
    }

    df_click_totals['labels'] = df_click_totals['bitlink'].map(etiquetas)

    if not df_click_totals.empty:
        df_sorted = df_click_totals.sort_values('total_clicks', ascending=False)
        fig = go.Figure()

        # Línea (el palito)
        fig.add_trace(go.Scatter(
            x=df_sorted['labels'],
            y=df_sorted['total_clicks'],
            mode='lines',
            line=dict(color='skyblue', width=2),
            showlegend=False,
            hoverinfo='skip'
        ))

        # Punto (la piruleta)
        fig.add_trace(go.Scatter(
            x=df_sorted['labels'],
            y=df_sorted['total_clicks'],
            mode='markers+text',
            marker=dict(color='skyblue', size=14, line=dict(color='white', width=1)),
            text=df_sorted['total_clicks'],
            textposition='top center',
            textfont=dict(color='black'),
            name='Total Clicks'
        ))

        fig.update_layout(
            title='Bitly Clicks per Link',
            xaxis_title='',
            xaxis=dict(
                tickfont=dict(color='black')
            ),
            yaxis_title='Total clicks',
            template='plotly_white',
            height=600
        )

        st.plotly_chart(fig)

    else:
        st.warning("No se encontraron clics para ningún enlace.")
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
semanas_disp_df['etiqueta'] = semanas_disp_df['week_start'].dt.strftime("Week of %Y-%m-%d")

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
#-----Vamos con un Pie Chart de las referencias-----
cols = st.columns(2)
colores_personalizados = [
    "#87CEEB",  # Azul celeste
    "#FFA500",  # Naranja
    "#90EE90",  # Verde suave
    "#FFD700",  # Amarillo dorado
    "#FFB6C1",  # Rosa claro
    "#00CED1"   # Azul turquesa
]

with cols[0]:
    reference_data = df['PH1_reference_$startups'].replace(
        {"Referral from within Decelera's community (who?, please specify)": "Referral"}
    )
    reference_count = reference_data.value_counts()

    ref_dict =dict(zip(reference_count.index, [int(reference_count[k]) for k in range(len(reference_count))]))
    df_ref = pd.DataFrame(list(ref_dict.items()), columns=['Reference', 'Applications'])

    fig = px.pie(df_ref, names='Reference', values='Applications', title=' Total Applications References',
                 color_discrete_sequence=colores_personalizados)

    fig.update_traces(textinfo="percent")

    fig.update_layout(
        legend=dict(
            x=0.8,  
            y=0.9,
            xanchor='left',
            yanchor='middle',
            font=dict(size=12),
            bgcolor="rgba(0,0,0,0)"
        ),
        title_x = 0.4
    )
    st.plotly_chart(fig)

with cols[1]:
    # Filtrar solo los aprobados
    df_aprobados = df_df[(df_df['Phase1&2_result_mex25'] == "Passed Phase 2") | (df_df['Phase1&2_result_mex25'] == "Red Flagged at Phase 2")]

    # Contar las referencias entre los aprobados
    reference_data = df_aprobados['PH1_reference_$startups'].replace(
        {"Referral from within Decelera's community (who?, please specify)": "Referral"}
    )
    reference_count = reference_data.value_counts()

    # Preparar DataFrame para el gráfico
    df_ref = pd.DataFrame({
        "Referencia": reference_count.index,
        "Aplicaciones": reference_count.values
    })

    # Generar el Pie Chart
    fig = px.pie(df_ref, names="Referencia", values="Aplicaciones",
                title="Phase 2 Applications References",
                color_discrete_sequence=colores_personalizados)
    
    fig.update_layout(
        legend=dict(
            x=0.8,  
            y=0.9,
            xanchor='left',
            yanchor='middle',
            font=dict(size=12),
            bgcolor="rgba(0,0,0,0)"
        ),
        title_x = 0.4
    )

    st.plotly_chart(fig)


#female founders

founders = 1
for founder in df['Second founder name']:
    if founder:
        founders += 1
for founder in df['Third founder name']:
    if founder:
        founders +=1

female_founders = df['Female'].sum()
male_founders = founders - female_founders
female_percentage = female_founders / founders * 100

cols = st.columns(2)

with cols[1]:
    data = {
        'Gender': ['Female founders', 'Male founders'],
        'Counts': [female_founders, male_founders]
    }

    fig = px.pie(
        data,
        names='Gender',
        values='Counts',
        title='Male and Female Founders',
        color_discrete_sequence=colores_personalizados
    )

    fig.update_layout(
        legend=dict(
            x=0.8,  
            y=0.9,
            xanchor='left',
            yanchor='middle',
            font=dict(size=12),
            bgcolor="rgba(0,0,0,0)"
        ),
        title_x = 0.4
    )

    st.plotly_chart(fig)

with cols[0]:
    ph_result = df_df['Phase1&2_result_mex25'].replace(
        {
            "Passed Phase 2": "Passed Phase 2",
            "Red Flagged at Phase 1": "Failed at Phase 1",
            "Red Flagged at Phase 2": "Passed Phase 2"
        }
    )

    resultado_count = ph_result.value_counts()

    # Crear DataFrame de conteo
    df_ph = pd.DataFrame({
        "Result": resultado_count.index,
        "Count": resultado_count.values
    })

    # Calcular porcentajes
    df_ph['Porcentaje'] = df_ph['Count'] / df_ph['Count'].sum() * 100
    df_ph['Texto'] = df_ph['Porcentaje'].round(2).astype(str) + "%"

    fig = px.bar(df_ph, x='Result', y='Count', title='Phase 1 and Phase 2 Results', color='Result',
                color_discrete_map={
                    "Passed Phase 2": "#87CEEB",
                    "Failed at Phase 1": "#FFA500"
                    },
                    category_orders={'Result': ['Passed Phase 2', 'Failed at Phase 1']},
                    text=df_ph['Texto']
                )

    fig.update_layout(
        xaxis_title="",
        xaxis=dict(
            tickfont=dict(
                color='black'
            )
        ),
        yaxis_title="Applications",
        title_x=0.4,
        showlegend=False,
        margin=dict(t=80)
    )

    fig.update_traces(textposition="outside", textfont_color='black')

    st.plotly_chart(fig)
    
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

    fig = px.bar(df_conteo, x='Motivo', y='Cantidad', title='Phase 1 Red Flag Reasons', text='Cantidad', color='Motivo',
                color_discrete_sequence=colores_personalizados)

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

    fig = px.bar(df_conteo, x='Motivo', y='Cantidad', title='Pahse 2 Red Flag Reasons', text='Cantidad', color='Motivo',
                color_discrete_sequence=colores_personalizados)

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