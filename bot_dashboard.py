import streamlit as st
import sqlite3
import pandas as pd

conn = sqlite3.connect('trading_logs.db')
df = pd.read_sql_query("SELECT * FROM logs ORDER BY id DESC", conn)

st.title("📊 Painel de Performance do Bot")
st.dataframe(df)

lucro_total = df['lucro'].sum()
st.metric("Lucro Total", f"${lucro_total:.2f}")
