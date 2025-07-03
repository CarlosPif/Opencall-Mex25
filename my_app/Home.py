import streamlit as st

#poner aqui titulo y fotillo decelera

if st.button("See application stats"):
    st.switch_page("Applications.py")

if st.button("See scoring stats"):
    st.switch_page("Results.py")