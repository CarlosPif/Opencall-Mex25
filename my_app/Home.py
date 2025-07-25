import streamlit as st

#poner aqui titulo y fotillo decelera

st.set_page_config(
    page_title="Startup Program Feedback Dashboard",
    layout="centered"
)

st.markdown("""
    <style>
    div.stButton > button {
        background-color: #1FD0EF;
        color: white;
        border-radius: 10px;
        padding: 0.5em 1em;
        font-size: 16px;
    }
    div.stButton > button:hover {
        background-color: #D43F3F;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <style>
    .stApp {
        background-color: #00000;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("**<h1 style='text-align: center;'>Open Call</h1>**", unsafe_allow_html=True)
st.markdown("**<h1 style='text-align: center;'>Decelera Mexico 2025</h1>**", unsafe_allow_html=True)
#st.image("https://images.squarespace-cdn.com/content/v1/67811e8fe702fd5553c65249/749161ba-4abb-4514-9642-edc82c1c9c9d/Decelera-Logo.png?format=1500w", width=500)

cols = st.columns([1, 2, 1])

with cols[1]:
    if st.button("Application Metrics"):
        st.switch_page("pages/Applications.py")

    if st.button("Score Metrics"):
        st.switch_page("pages/Results.py")