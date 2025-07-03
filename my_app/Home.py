import streamlit as st

#poner aqui titulo y fotillo decelera

if st.button("See application stats"):
    st.switch_page("pages/Applications.py")

if st.button("See scoring stats"):
    st.switch_page("pages/Results.py")