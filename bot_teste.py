import sqlite3
import datetime
import pytz
import time
import random
from config import (
    API_KEY, API_SECRET,
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
    EMAIL_DESTINO, EMAIL_ORIGEM, SMTP_SENHA
)
import requests


# === FUNÇÃO TELEGRAM ===
def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem}
    requests.post(url, json=payload)


# === CONEXÃO COM DB ===
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


# === FUNÇÃO SIMULAR TRADE ===
def simular_trade(par):
    entrada = round(random.uniform(100, 50000), 2)
    saida = entrada * random.uniform(1.005, 1.02)
    lucro = saida - entrada
    retorno_pct = ((saida / entrada) - 1) * 100 * 10  # simulando alavancagem 10x

    hora_entrada = datetime.datetime.now(pytz.UTC).isoformat()
    hora_saida = datetime.datetime.now(pytz.UTC).isoformat()

    mensagem = (
        f"🚀 Simulação de Trade em {par}\n"
        f"Entrada: {entrada:.2f}\nSaída: {saida:.2f}\n"
        f"Lucro: {lucro:.2f} USDT ({retorno_pct:.2f}%)"
    )
    enviar_telegram(mensagem)
    print(mensagem)

    c.execute('''INSERT INTO logs (par, entrada, saida, lucro, retorno_percentual, hora_entrada, hora_saida)
        VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (par, entrada, saida, lucro, retorno_pct, hora_entrada, hora_saida)
    )
    conn.commit()


# === LOOP DE TESTE ===
pares = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT']

print("🤖 Bot de Teste Iniciado!")
enviar_telegram("🤖 Bot de Teste Iniciado!")

try:
    while True:
        for par in pares:
            simular_trade(par)
            time.sleep(3)  # Espera 3 segundos entre trades

        print("✔️ Ciclo completo. Aguardando 1 minuto...")
        time.sleep(60)  # Aguarda 1 minuto antes de repetir
except KeyboardInterrupt:
    print("❌ Bot de Teste finalizado pelo usuário.")
    enviar_telegram("❌ Bot de Teste finalizado.")
