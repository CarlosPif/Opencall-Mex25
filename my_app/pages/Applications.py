from pyairtable import Api
import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np
import datetime
import plotly.graph_objects as go
from collections import Counter
import requests

# Configuracion de AirTable

api_key_at = st.secrets["airtable"]["api_key"]
base_id = st.secrets["airtable"]["base_id"]
table_id = st.secrets["airtable"]["table_id"]

api_key_fl = st.secrets['fillout']['api_key']
form_id = st.secrets['fillout']['form_id']

api = Api(api_key_at)
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

#-----Aplicaciones por dia===========================================================

# Conversión de fechas
df['Created'] = pd.to_datetime(df['Created'], errors='coerce')
df = df.dropna(subset=['Created'])
df['Date'] = df['Created'].dt.date

# ===== Aplicaciones por Semana =========================================================

df['Date_dt'] = pd.to_datetime(df['Date'])
df['Week_start'] = (
    df['Date_dt']                           
    - pd.to_timedelta(df['Date_dt'].dt.weekday, unit='d')
).dt.normalize()                            

df['Week_start_date'] = df['Week_start'].dt.date      
df['Week_start_str']  = df['Week_start_date'].apply(
    lambda d: d.strftime("%d/%m/%Y"))                 

today_dt = datetime.date.today()
current_week_start = (today_dt - datetime.timedelta(days=today_dt.weekday()))  
current_week_str   = current_week_start.strftime("%d/%m/%Y")

available_weeks = sorted(df['Week_start_str'].unique())
default_week_idx = (available_weeks.index(current_week_str)
                    if current_week_str in available_weeks
                    else len(available_weeks)-1)
selected_week_str = st.selectbox("Select a week", available_weeks, index=default_week_idx)

selected_week_date = datetime.datetime.strptime(
    selected_week_str, "%d/%m/%Y").date()

df_week = df[df['Week_start_date'] == selected_week_date].copy()

df_week['Dia_semana'] = df_week['Date_dt'].dt.day_name().str.lower()

orden_dias = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
df_week['Dia_semana'] = pd.Categorical(df_week['Dia_semana'], categories=orden_dias, ordered=True)

conteo = df_week['Dia_semana'].value_counts().reindex(orden_dias, fill_value=0)

#Gráfico
df_plot = pd.DataFrame({"Día": conteo.index.str.capitalize(),
                        "Registros": conteo})

fig = px.bar(df_plot, x="Día", y="Registros", text='Registros',
             title=f"Below you can see the number of applications through the week - Week of the {selected_week_str}",
             labels={"Día": "Weekday", "Registros": "Applications"},
             template="plotly_white",
             height=600,
             color_discrete_sequence=["#87CEEB"])

total_apps = int(df_week.shape[0])

fig.add_annotation(
    text=f"<b>Total: {total_apps}<b>",
    xref="paper", yref="paper",
    x=0, y=1,          # posición a la derecha del título
    showarrow=False,
    font=dict(size=18, color='black')
)
fig.update_traces(textposition='outside')

fig.update_layout(yaxis=dict(dtick=1))

st.plotly_chart(fig, use_container_width=True)

#acumulado

df['Fecha'] = pd.to_datetime(df['Creation_date']).dt.date
df_evolucion = df.groupby('Fecha').size().reset_index(name='Aplicaciones')
df_evolucion = df_evolucion.sort_values('Fecha')
df_evolucion['Acumulado'] = df_evolucion['Aplicaciones'].cumsum()

# Gráfico de línea acumulada en azul celeste

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df_evolucion['Fecha'],
    y=df_evolucion['Acumulado'],
    mode='lines+markers',
    name='Acumulado',
    line=dict(color='#87CEEB', shape='spline', width=3)
))

# Línea horizontal de objetivo
#fig.add_hline(y=1200, line_color='#FFA500', line_dash='dash', annotation_text='Target', annotation_position='top right')

# Diseño
fig.update_layout(
    title="Applications Time Evolution",
    xaxis_title='Date',
    yaxis_title='Applications',
    template='plotly_white',
    title_font=dict(size=24, color='black'),
    title_x=0.4
)

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
    reference_data = df['PH1_reference_$startups']
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
    df_aprobados = df[(df['Phase1&2_result_mex25'] == "Passed Phase 2") | (df['Phase1&2_result_mex25'] == "Red Flagged at Phase 2")]

    # Contar las referencias entre los aprobados
    reference_data = df_aprobados['PH1_reference_$startups']
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
    ph_result = df['Phase1&2_result_mex25'].replace(
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

todos_motivos = []

for texto in df["Phase1&2_result_reason_mex25"]:
    if isinstance(texto, str):
        motivos = [m.strip() for m in texto.split(". ") if m.strip()]
        todos_motivos.extend(motivos)

# Contamos los motivos
conteo = Counter(todos_motivos)

# Convertimos a DataFrame para graficar
df_conteo = pd.DataFrame(conteo.items(), columns=["Motivo", "Cantidad"])

fig = px.bar(df_conteo, x='Motivo', y='Cantidad', title='Red Flag Reasons', text='Cantidad', color='Motivo',
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
    showlegend=False
)

fig.update_traces(textposition="outside", textfont_color='black',
                  cliponaxis=False)

st.plotly_chart(fig)

