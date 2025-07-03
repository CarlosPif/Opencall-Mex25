from pyairtable import Api
import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np
import datetime

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

st.title("Opencall Decelera Mexico 2025")

# Un conteo general antes de nada
cols = st.columns(3)
total = df.shape[0]
target = 1200
ratio = total / target * 100

cols[0].metric("Current number of applications", f"{total}")
cols[1].metric("Target number of applications", f"{target}")
cols[2].metric("Ratio", f"{ratio:.2f}%")

#-----Aplicaciones por dia-------

# Conversión de fechas
df['Creation_date'] = pd.to_datetime(df['Creation_date'], errors='coerce')
df = df.dropna(subset=['Creation_date'])
df['Date'] = df['Creation_date'].dt.date

# Columna para mostrar en el dropdown en formato "2 de diciembre"

df['Date_display'] = df['Creation_date'].dt.strftime("%B") + " " +  df['Creation_date'].dt.day.astype(str) + "th"
date_display_map = dict(zip(df['Date_display'], df['Date']))
available_dates_display = sorted(date_display_map.keys(), key=lambda x: date_display_map[x])

today      = datetime.date.today()
today_disp = None

# Localiza el string que corresponde a hoy
for disp, d in date_display_map.items():
    if d == today:
        today_disp = disp
        break

# Si está presente => usa su posición; si no, caída a 0
default_day_idx = (available_dates_display.index(today_disp)
                   if today_disp in available_dates_display
                   else 0)

selected_display = st.selectbox("Select the date", available_dates_display, index=default_day_idx)
selected_date = date_display_map[selected_display]

# Filtrar registros de ese día
df_day = df[df['Date'] == selected_date].copy()

# Crear columna de hora
df_day['Hora'] = df_day['Creation_date'].dt.hour

# Conteo por hora
hour_count = df_day['Hora'].value_counts().sort_index()
all_hours = np.arange(0, 24)
hour_count_full = pd.Series(0, index=all_hours)
hour_count_full.update(hour_count)
hour_count_full = hour_count_full.sort_index()

# Etiquetas tipo "0h", "1h", ..., "23h"
hora_labels = [f"{h}:00h" for h in hour_count_full.index]

# DataFrame para gráfica
df_plot = pd.DataFrame({
    "Hora": hora_labels,
    "Registros": hour_count_full.values
})

# Gráfico de barras
fig = px.bar(df_plot, x="Hora", y="Registros",
             title=f"Daily applications - {selected_display}",
             labels={"Hora": "Time", "Registros": "Applications"},
             template="plotly_white",
             height=600)

fig.update_layout(yaxis=dict(dtick=1))

total_apps_day = int(df_day.shape[0])

# Opción A – anotación sobre el gráfico
fig.add_annotation(
    text=f"<b>Total: {total_apps_day}<b>",
    xref="paper", yref="paper",
    x=0, y=1,            # Ajusta si quieres moverla
    showarrow=False,
    font=dict(size=18, color='black')
)

st.plotly_chart(fig, use_container_width=True)

# ===== Aplicaciones por Semana =====

# 1) Asegúrate de que 'Date' está como datetime pero SIN hora
df['Date_dt'] = pd.to_datetime(df['Date'])

# 2) Calcula el inicio de semana (lunes) y quítale la hora
df['Week_start'] = (
    df['Date_dt']                              # 2025-06-26 00:00:00
    - pd.to_timedelta(df['Date_dt'].dt.weekday, unit='d')
).dt.normalize()                               # 2025-06-23 00:00:00

# 3) Guarda una columna SOLO con la fecha para el menú y para comparar
df['Week_start_date'] = df['Week_start'].dt.date          # datetime.date(2025, 6, 23)
df['Week_start_str']  = df['Week_start_date'].apply(
    lambda d: d.strftime("%d/%m/%Y"))                      # "23/06/2025"

# 4) Menú de semanas — mostramos los strings bonitos
today_dt = datetime.date.today()
current_week_start = (today_dt - datetime.timedelta(days=today_dt.weekday()))  # lunes actual
current_week_str   = current_week_start.strftime("%d/%m/%Y")

available_weeks = sorted(df['Week_start_str'].unique())
default_week_idx = (available_weeks.index(current_week_str)
                    if current_week_str in available_weeks
                    else 0)
selected_week_str = st.selectbox("Select a week", available_weeks, index=default_week_idx)

# 5) Convertimos el string seleccionado a date
selected_week_date = datetime.datetime.strptime(
    selected_week_str, "%d/%m/%Y").date()

# 6) Filtramos registros de ESA semana (comparando date vs date)
df_week = df[df['Week_start_date'] == selected_week_date].copy()

# 7) Día de la semana
df_week['Dia_semana'] = df_week['Date_dt'].dt.day_name().str.lower()

orden_dias = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
df_week['Dia_semana'] = pd.Categorical(df_week['Dia_semana'], categories=orden_dias, ordered=True)

# Conteo por día
conteo = df_week['Dia_semana'].value_counts().reindex(orden_dias, fill_value=0)

# 8) Gráfico
df_plot = pd.DataFrame({"Día": conteo.index.str.capitalize(),
                        "Registros": conteo})

fig = px.bar(df_plot, x="Día", y="Registros",
             title=f"Weekly applications - Week of the {selected_week_str}",
             labels={"Día": "Weekday", "Registros": "Applications"},
             template="plotly_white",
             height=600)

total_apps = int(df_week.shape[0])

fig.add_annotation(
    text=f"<b>Total: {total_apps}<b>",
    xref="paper", yref="paper",
    x=0, y=1,          # posición a la derecha del título
    showarrow=False,
    font=dict(size=18, color='black')
)

fig.update_layout(yaxis=dict(dtick=1))

st.plotly_chart(fig, use_container_width=True)