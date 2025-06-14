import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ================================
# 🎯 Conectar ao banco de dados
# ================================
conn = sqlite3.connect('trading_logs.db')
df = pd.read_sql_query("SELECT * FROM logs ORDER BY id DESC", conn)

# ================================
# 🎨 Layout do Painel
# ================================
st.set_page_config(page_title="Painel de Trading Bot", layout="wide")

st.title("📊 Painel de Performance do Trading Bot")

# ================================
# 📈 Estatísticas Gerais
# ================================
col1, col2, col3, col4 = st.columns(4)

lucro_total = df['lucro'].sum() if not df.empty else 0
qtd_trades = len(df)
retorno_medio = df['retorno_percentual'].mean() if not df.empty else 0
win_rate = (len(df[df['lucro'] > 0]) / qtd_trades * 100) if qtd_trades > 0 else 0

col1.metric("💰 Lucro Total", f"${lucro_total:.2f}")
col2.metric("📊 Nº de Trades", f"{qtd_trades}")
col3.metric("📈 Retorno Médio", f"{retorno_medio:.2f}%")
col4.metric("✅ Win Rate", f"{win_rate:.2f}%")

st.divider()

# ================================
# 🔍 Visualização dos Trades
# ================================
st.subheader("📄 Histórico de Trades")

st.dataframe(df, use_container_width=True)

# ================================
# 📅 Filtros (opcional)
# ================================
st.sidebar.header("🔎 Filtros")

par_filtro = st.sidebar.selectbox("Escolher par", options=['Todos'] + list(df['par'].unique()))
if par_filtro != 'Todos':
    df = df[df['par'] == par_filtro]

# ================================
# 🗓️ Filtrar por data
# ================================
data_inicio = st.sidebar.date_input("Data Início", value=datetime.today())
data_fim = st.sidebar.date_input("Data Fim", value=datetime.today())

if not df.empty:
    df['hora_entrada_dt'] = pd.to_datetime(df['hora_entrada'])
    df_filtrado = df[
        (df['hora_entrada_dt'].dt.date >= data_inicio) &
        (df['hora_entrada_dt'].dt.date <= data_fim)
    ]
else:
    df_filtrado = df

st.subheader("📆 Histórico Filtrado")
st.dataframe(df_filtrado, use_container_width=True)

# ================================
# 📊 Gráfico de Lucro Acumulado
# ================================
st.subheader("📈 Lucro Acumulado")

if not df_filtrado.empty:
    df_filtrado['lucro_acumulado'] = df_filtrado['lucro'].cumsum()

    st.line_chart(
        data=df_filtrado,
        x='hora_entrada_dt',
        y='lucro_acumulado',
        use_container_width=True
    )
else:
    st.info("Nenhum dado disponível para o período selecionado.")

st.caption("🔗 Desenvolvido por Seu Trading Bot")

