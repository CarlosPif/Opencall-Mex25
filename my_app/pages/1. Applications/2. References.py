from pyairtable import Api
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


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
records_df = table_df.all(view='PH1-PH2_All Applicants', time_zone="Europe/Madrid")
data_df = [record['fields'] for record in records_df]
df_df = pd.DataFrame(data_df)

def fix_cell(val):
    if isinstance(val, dict) and "specialValue" in val:
        return float("nan")
    return val

df = df.map(fix_cell)
df_24 = df_24.map(fix_cell)
df_ld = df_ld.map(fix_cell)

# Comenzamos con el dashboard
st.set_page_config(
    page_title="Opencall Dashboard Decelera Mexico 2025",
    layout="wide"
)

st.markdown("**<h1 style='text-align: center;'>Open Call Decelera Mexico 2025</h1>**", unsafe_allow_html=True)

#============================================================================
colors = ['#1FD0EF', '#FFB950', '#FAF3DC', '#1158E5', '#B9C1D4', '#F2F8FA']
inicio_2025 = pd.to_datetime("25-06-2025")
inicio_2024 = pd.to_datetime("20-06-2024")
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
        line=dict(color='#1FD0EF', width=2)
    )


# Punto (la piruleta)
fig.add_trace(go.Scatter(
    x=reference_count['PH1_reference_$startups'],
    y=reference_count['count'],
    mode='markers+text',
    marker=dict(color='#1FD0EF', size=20, line=dict(color='white', width=1)),
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
cols = st.columns(2)

with cols[0]:
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
        hole=0.35,
        color_discrete_sequence=colors           
    )

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

    st.plotly_chart(fig, use_container_width=True)

with cols[1]:
    df_ref = (
        df_df[df_df['PH1_reference_$startups'] == "Referral from within Decelera's community (who?, please specify)"]
        .assign(fecha=lambda d: pd.to_datetime(d['Created_str']))
        .assign(semana=lambda d: ((d['fecha'] - pd.Timestamp("2025-06-25")).dt.days // 7) + 1)
        .groupby('semana', as_index=False)
        .size()
        .rename(columns={'size': 'count'})
    )

    df_ref_ld = (
        df_ld[df_ld['Applied'] == False]
        .assign(fecha=lambda d: pd.to_datetime(d['Created_str']))
        .assign(semana=lambda d: ((d['fecha'] - pd.Timestamp("2025-06-25")).dt.days // 7) + 1)
        .groupby('semana', as_index=False)
        .size()
        .rename(columns={'size': 'count'})
    )

    df_total = pd.merge(df_ref, df_ref_ld, on='semana', how='outer').fillna(0)
    df_total['count'] = df_total['count_x'] + df_total['count_y']
    df_total = df_total[['semana', 'count']].sort_values('semana')

    objetivos_dict = {1: 25, 2: 50, 3: 50, 4: 50, 5: 35, 6: 20, 7: 7, 8: 6, 9: 5, 10: 2}
    df_obj = pd.DataFrame({'semana': list(objetivos_dict.keys()), 'objetivo': list(objetivos_dict.values())})

    df_total = pd.merge(df_obj, df_total, on='semana', how='left').fillna({'count': 0})
    df_total['count'] = df_total['count'].astype(int)
    total_ref = df_total['count'].sum()

    fig = go.Figure()

    # Barra de referrals reales
    fig.add_trace(go.Bar(
        x=df_total['semana'],
        y=df_total['count'],
        name="Referrals",
        text=df_total['count'],
        textposition='outside',
        textfont=dict(color='black'),
        marker=dict(
            color="#1FD0EF",
            line=dict(color="black", width=1.5),
        ),
        cliponaxis=False
    ))

    # Barra de objetivos
    fig.add_trace(go.Bar(
        x=df_total['semana'],
        y=df_total['objetivo'],
        name="Objetivo",
        text=df_total['objetivo'],
        textposition='outside',
        textfont=dict(color='black'),
        marker=dict(
            color='rgba(0,0,0,0)',
            line=dict(
                color='#AAAAAA',
                width=2
            )
        ),
        opacity=0.5,
        cliponaxis=False
    ))

    fig.update_layout(
        barmode='overlay',
        title=f"Referrals Mexico 2025 per week. Total: {total_ref}",
        xaxis=dict(
            range=[0.5,16],
            title='Week'
        ),
        legend=dict(
            x=0.99,            
            y=0.99,           
            xanchor="right",  
            yanchor="top",
            orientation="v",  
            bgcolor="rgba(255,255,255,0.5)",
            bordercolor="black",
            borderwidth=1
        ),
        bargap=0.15,
        yaxis_title="Number of Referrals",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig)


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
                    title="Mexico 2024 References", color_discrete_sequence=colors)
        
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
        textfont=dict(color='black'),
        marker=dict(
            color="#1FD0EF",
            line=dict(color="black", width=1.5),
        ),
        cliponaxis=False
    ))

    fig.update_layout(
        title=f"Referrals Mexico 2024 per week. Total: {total_referrals}",
        xaxis_title="Week",
        yaxis_title="Number of Referrals",
        bargap=0.15,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig, use_container_width=True)
