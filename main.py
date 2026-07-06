import os
import json
import requests
from datetime import datetime
import pytz

DIETA = {
    "08:00": "🍳 Refeição 1: O Despertar do Guerreiro — 3 ovos mexidos + 2 fatias de pão integral + 30g requeijão light + 1 banana + café preto. Total: 486 kcal | Prot: 28,9g | Carb: 49,7g | Gord: 19,3g",
    "09:00": "🕊️ SHEMA YSRAEL — \"Baruch Atá A-do-nai, rofê chol bassar umafli laassot\"",
    "10:55": "Hora do Selênio",
    "11:30": "🍗 Refeição 2: O Combustível de Atenas — 350g arroz branco + 150g frango grelhado + brócolis/cenoura + 12g azeite de oliva. Total: 834 kcal | Prot: 58g | Carb: 104g | Gord: 17g",
    "16:00": "⚡ Refeição 3: O Elixir do Olimpo — 140g farinha de arroz + 2 bananas + 40g castanhas/amendoim + creatina com água. Total: 939 kcal | Prot: 23,6g | Carb: 164,6g | Gord: 22g",
    "20:00": "🐟 Refeição 4: A Ceia dos Fortes — 350g arroz branco + 150g frango ou sardinha + 1 fruta + 12g azeite de oliva. Total: 874 kcal | Prot: 55,5g | Carb: 117g | Gord: 16,9g",
    "22:01": "🕊️ SHEMA YSRAEL — \"ganzu letova\""
}

def enviar_telegram(mensagem):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "Markdown"
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        print("Mensagem enviada com sucesso!")
    else:
        print(f"Erro ao enviar: {response.text}")

def lambda_handler(event, context):
    tz = pytz.timezone("America/Sao_Paulo")
    hora_brasilia = datetime.now(tz)

    for horario, refeicao in DIETA.items():
        horario_ref = datetime.strptime(horario, "%H:%M").replace(
            year=hora_brasilia.year,
            month=hora_brasilia.month,
            day=hora_brasilia.day,
            tzinfo=hora_brasilia.tzinfo
        )

        diferenca = abs((hora_brasilia - horario_ref).total_seconds())

        if diferenca <= 300:
            print(f"Enviando refeição das {horario}")
            enviar_telegram(refeicao)
            return {"statusCode": 200, "body": f"Enviado: {horario}"}

    print("Nenhuma refeição para este horário.")
    return {"statusCode": 200, "body": "Nenhuma refeição"}