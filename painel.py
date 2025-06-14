import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from datetime import datetime
import numpy as np

# Configuração da página
st.set_page_config(page_title="Painel de Resultados do Bot", layout="wide")
st.title("📊 Painel de Resultados do Bot de Trading")

# Função para carregar dados do banco de dados
@st.cache_data
def carregar_dados():
    conexao = sqlite3.connect("trading_logs.db")
    df = pd.read_sql_query("SELECT * FROM trades", conexao)
    conexao.close()
    df["data"] = pd.to_datetime(df["data"])
    return df

# Carregar dados
try:
    df = carregar_dados()
except Exception as e:
    st.error("Erro ao carregar dados: " + str(e))
    st.stop()

# Filtros de data
col1, col2 = st.columns(2)
with col1:
    data_inicio = st.date_input("Data de início", value=df["data"].min().date())
with col2:
    data_fim = st.date_input("Data de fim", value=df["data"].max().date())

# Filtro por período
periodo = st.selectbox("Agrupar por:", ["Diário", "Semanal", "Mensal"])

# Aplicar filtros
df_filtrado = df[(df["data"] >= pd.to_datetime(data_inicio)) & (df["data"] <= pd.to_datetime(data_fim))]

# Mapeamento de agrupamento
if periodo == "Diário":
    df_filtrado["periodo"] = df_filtrado["data"].dt.date
elif periodo == "Semanal":
    df_filtrado["periodo"] = df_filtrado["data"].dt.to_period("W").apply(lambda r: r.start_time.date())
elif periodo == "Mensal":
    df_filtrado["periodo"] = df_filtrado["data"].dt.to_period("M").apply(lambda r: r.start_time.date())

# Cálculos de performance por período
resumo = df_filtrado.groupby("periodo")["lucro"].sum().reset_index()

# Exibir resumo
st.subheader("Lucro por Período")
col3, col4 = st.columns(2)
with col3:
    st.bar_chart(resumo.set_index("periodo"))
with col4:
    st.line_chart(resumo.set_index("periodo"))

# Exportação
csv = df_filtrado.to_csv(index=False).encode("utf-8")
st.download_button(
    label="🔽 Baixar CSV dos Trades Filtrados",
    data=csv,
    file_name="trades_filtrados.csv",
    mime="text/csv"
)

# Alertas de performance
st.subheader("🔔 Alertas de Performance")
lucro_total = df_filtrado["lucro"].sum()
meta_negativa = st.number_input("Definir alerta de prejuízo máximo", value=-100.0)
meta_positiva = st.number_input("Definir meta de lucro desejada", value=100.0)

if lucro_total <= meta_negativa:
    st.error(f"❌ Alerta: Lucro Total abaixo do limite! Lucro: ${lucro_total:.2f}")
elif lucro_total >= meta_positiva:
    st.success(f"🎉 Parabéns! Meta de lucro alcançada: ${lucro_total:.2f}")
else:
    st.info(f"⚠️ Lucro atual: ${lucro_total:.2f}")

# Análise de Trades
st.subheader("📊 Análise de Trades")
vencedores = df_filtrado[df_filtrado["lucro"] > 0]
perdedores = df_filtrado[df_filtrado["lucro"] <= 0]
total = len(df_filtrado)

percent_vencedores = len(vencedores) / total * 100 if total else 0
percent_perdedores = 100 - percent_vencedores
media_lucro = vencedores["lucro"].mean() if not vencedores.empty else 0
media_prejuizo = perdedores["lucro"].mean() if not perdedores.empty else 0

col5, col6 = st.columns(2)
with col5:
    st.metric("% Trades Vencedores", f"{percent_vencedores:.2f}%")
    st.metric("Média de Lucro", f"${media_lucro:.2f}")
with col6:
    st.metric("% Trades Perdidos", f"{percent_perdedores:.2f}%")
    st.metric("Média de Prejuízo", f"${media_prejuizo:.2f}")

# Gráficos
st.subheader("🌐 Visualizações de Performance")
fig1, ax1 = plt.subplots()
ax1.pie([percent_vencedores, percent_perdedores], labels=["Vencedores", "Perdedores"], autopct="%1.1f%%")
st.pyplot(fig1)

fig2, ax2 = plt.subplots()
sns.barplot(x=["Lucro Médio", "Prejuízo Médio"], y=[media_lucro, media_prejuizo], ax=ax2)
ax2.set_ylabel("Valor ($)")
st.pyplot(fig2)

# Estatísticas Avançadas
st.subheader("🔢 Estatísticas Avançadas")
desvio = df_filtrado["lucro"].std()
equity = df_filtrado["lucro"].cumsum()
drawdown = (equity.cummax() - equity).max()
volatilidade = df_filtrado["lucro"].pct_change().std() if len(df_filtrado) > 1 else 0

col7, col8, col9 = st.columns(3)
with col7:
    st.metric("Desvio Padrão", f"${desvio:.2f}")
with col8:
    st.metric("Drawdown Máximo", f"${drawdown:.2f}")
with col9:
    st.metric("Volatilidade", f"{volatilidade:.2%}")

# Curva de equity
st.subheader("📈 Curva de Equity")
fig3, ax3 = plt.subplots()
equity.plot(ax=ax3)
ax3.set_ylabel("Equity ($)")
st.pyplot(fig3)
