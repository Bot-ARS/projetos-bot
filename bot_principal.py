# === Crypto Trading Bot com Expansões (v2.0) ===

import ccxt
import time
import pandas as pd
import numpy as np
import requests
import talib
import sqlite3
import datetime
import pytz
import smtplib
from email.mime.text import MIMEText
from statistics import mean

# === IMPORTANDO CONFIGURAÇÕES ===
from config import (
    API_KEY,
    API_SECRET,
    TELEGRAM_TOKEN,
    TELEGRAM_CHAT_ID,
    EMAIL_DESTINO,
    EMAIL_ORIGEM,
    SMTP_SENHA
)

# === CONFIGURAÇÃO DA EXCHANGE ===
exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})
exchange.set_sandbox_mode(True)  # Modo de teste

# === CONEXÃO COM DB SQLITE ===
conn = sqlite3.connect('trading_logs.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    par TEXT,
    entrada REAL,
    saida REAL,
    lucro REAL,
    retorno_percentual REAL,
    hora_entrada TEXT,
    hora_saida TEXT
)''')
conn.commit()

# === FUNÇÃO TELEGRAM ===
def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro ao enviar mensagem no Telegram: {e}")

# === FUNÇÃO EMAIL RELATÓRIO DIÁRIO ===
def enviar_email_resumo():
    df = pd.read_sql_query("SELECT * FROM logs ORDER BY id DESC LIMIT 10", conn)
    lucro_total = df['lucro'].sum() if not df.empty else 0
    texto = f"Resumo do dia:\n\n{df}\n\nLucro total: {lucro_total:.2f} USDT"
    msg = MIMEText(texto)
    msg['Subject'] = 'Resumo Diário do Bot'
    msg['From'] = EMAIL_ORIGEM
    msg['To'] = EMAIL_DESTINO

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_ORIGEM, SMTP_SENHA)
            server.send_message(msg)
    except Exception as e:
        print(f"Erro ao enviar email: {e}")

# === CALENDÁRIO ECONÔMICO SIMPLES ===
def evitar_eventos():
    hora_atual = datetime.datetime.now(pytz.utc).hour
    return 12 <= hora_atual <= 15  # Evita operar nesse intervalo

# === INDICADORES ===
def calcular_indicadores(df):
    df['EMA20'] = talib.EMA(df['close'], timeperiod=20)
    df['EMA50'] = talib.EMA(df['close'], timeperiod=50)
    df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
    df['OBV'] = talib.OBV(df['close'], df['volume'])
    return df

# === TRAILING STOP ===
def aplicar_trailing_stop(preco_atual, preco_entrada, atr):
    distancia = atr * 1.2
    novo_sl = preco_atual - distancia
    return max(novo_sl, preco_entrada * 0.99)

# === EXECUTAR TRADE ===
def executar_trade(par):
    try:
        dados = exchange.fetch_ohlcv(par, timeframe='15m', limit=100)
        df = pd.DataFrame(dados, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = calcular_indicadores(df)

        ultimo = df.iloc[-1]
        penultimo = df.iloc[-2]

        condicao_entrada = (
            penultimo['EMA20'] < penultimo['EMA50'] and
            ultimo['EMA20'] > ultimo['EMA50'] and
            ultimo['close'] > ultimo['EMA20'] and
            ultimo['volume'] > mean(df['volume'][-10:])
        )

        if not condicao_entrada or evitar_eventos():
            print(f"Nenhuma entrada para {par} no momento.")
            return

        entrada = ultimo['close']
        alavancagem = 10
        tp = entrada * 1.015
        sl = aplicar_trailing_stop(entrada, entrada, ultimo['ATR'])
        quantidade = 10 / entrada

        enviar_telegram(f"🚀 Entrada em {par} a {entrada:.2f}\nTP: {tp:.2f} | SL: {sl:.2f}")
        print(f"Entrada em {par} a {entrada:.2f}")

        hora_entrada = datetime.datetime.now(pytz.utc).isoformat()

        # Simulação da saída no take profit
        preco_saida = tp
        hora_saida = datetime.datetime.now(pytz.utc).isoformat()
        lucro = (preco_saida - entrada) * quantidade
        retorno_pct = ((preco_saida / entrada) - 1) * 100 * alavancagem

        enviar_telegram(f"✅ Saída de {par} a {preco_saida:.2f}\nLucro: {lucro:.2f} USDT ({retorno_pct:.2f}%)")
        print(f"Saída de {par} a {preco_saida:.2f} | Lucro: {lucro:.2f}")

        c.execute('''INSERT INTO logs (par, entrada, saida, lucro, retorno_percentual, hora_entrada, hora_saida)
            VALUES (?, ?, ?, ?, ?, ?, ?)''', (par, entrada, preco_saida, lucro, retorno_pct, hora_entrada, hora_saida))
        conn.commit()

    except Exception as e:
        enviar_telegram(f"❌ Erro no trade de {par}: {e}")
        print(f"Erro no trade de {par}: {e}")

# === LOOP PRINCIPAL ===
pares = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT']
print("🤖 Bot iniciado em modo TESTNET")
enviar_telegram("🤖 Bot iniciado em modo TESTNET!")

while True:
    try:
        for par in pares:
            executar_trade(par)
            time.sleep(3)

        # Envia resumo diário às 23:59 UTC
        agora = datetime.datetime.now(pytz.utc)
        if agora.hour == 23 and agora.minute == 59:
            enviar_email_resumo()

        time.sleep(60)
    except Exception as e:
        enviar_telegram(f"❌ Erro no loop principal: {e}")
        print(f"Erro no loop principal: {e}")
        time.sleep(60)
