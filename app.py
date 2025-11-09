import pandas as pd
import streamlit as st

st.title("📊 Tableau de bord - Production durable")

uploaded_file = st.file_uploader("Téléverser le fichier de production durable", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.subheader("Aperçu des données :")
    st.dataframe(df)
