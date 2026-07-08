import os
import json
import requests
import boto3
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key
import pytz

# ── Configurações ──────────────────────────────────────────────────────────────
DIETA = {
    "08:00": {"nome": "Refeição 1 - O Despertar do Guerreiro", "descricao": "3 ovos mexidos + 2 fatias de pão integral + 30g requeijão light + 1 banana + café preto", "kcal": 486, "prot": 28.9, "carb": 49.7, "gord": 19.3},
    "09:00": {"nome": "Shema Ysrael", "descricao": "Baruch Atá A-do-nai, rofê chol bassar umafli laassot", "kcal": 0, "prot": 0, "carb": 0, "gord": 0},
    "10:55": {"nome": "Hora do Selênio", "descricao": "Suplemento de selênio", "kcal": 0, "prot": 0, "carb": 0, "gord": 0},
    "11:30": {"nome": "Refeição 2 - O Combustível de Atenas", "descricao": "350g arroz branco + 150g frango grelhado + brócolis/cenoura + 12g azeite de oliva", "kcal": 834, "prot": 58, "carb": 104, "gord": 17},
    "16:00": {"nome": "Refeição 3 - O Elixir do Olimpo", "descricao": "140g farinha de arroz + 2 bananas + 40g castanhas/amendoim + creatina com água", "kcal": 939, "prot": 23.6, "carb": 164.6, "gord": 22},
    "20:00": {"nome": "Refeição 4 - A Ceia dos Fortes", "descricao": "350g arroz branco + 150g frango ou sardinha + 1 fruta + 12g azeite de oliva", "kcal": 874, "prot": 55.5, "carb": 117, "gord": 16.9},
    "22:01": {"nome": "Shema Ysrael", "descricao": "ganzu letova", "kcal": 0, "prot": 0, "carb": 0, "gord": 0},
}

KCAL_DIARIA_ALVO = sum(r["kcal"] for r in DIETA.values())

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE_NAME", "Dieta_Historico_Dev")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
tabela = dynamodb.Table(DYNAMODB_TABLE)

tz = pytz.timezone("America/Sao_Paulo")


# ── Gemini via HTTP puro (sem SDK) ─────────────────────────────────────────────
def chamar_gemini(prompt):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-2.5-flash:generateContent"
    )
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY,
    }
    body = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    response = requests.post(url, json=body, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


# ── Telegram ───────────────────────────────────────────────────────────────────
def enviar_telegram(mensagem, chat_id=None):
    cid = chat_id or TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": cid, "text": mensagem, "parse_mode": "Markdown"})


# ── DynamoDB ───────────────────────────────────────────────────────────────────
def salvar_refeicao(horario, nome, descricao, kcal, seguida=True, substituicao=None):
    agora = datetime.now(tz)
    tabela.put_item(Item={
        "data": agora.strftime("%Y-%m-%d"),
        "timestamp": agora.isoformat(),
        "horario": horario,
        "nome": nome,
        "descricao": descricao,
        "kcal": str(kcal),
        "seguida": seguida,
        "substituicao": substituicao or "",
    })


def buscar_historico_semana():
    hoje = datetime.now(tz)
    registros = []
    for i in range(7):
        dia = (hoje - timedelta(days=i)).strftime("%Y-%m-%d")
        resp = tabela.query(KeyConditionExpression=Key("data").eq(dia))
        registros.extend(resp.get("Items", []))
    return registros


def buscar_ultima_refeicao_suja():
    historico = buscar_historico_semana()
    sujas = [r for r in historico if not r.get("seguida", True)]
    if not sujas:
        return None
    return max(sujas, key=lambda r: r["timestamp"])


# ── Lógica de horário (EventBridge) ───────────────────────────────────────────
def processar_horario():
    agora = datetime.now(tz)

    for horario, dados in DIETA.items():
        horario_ref = datetime.strptime(horario, "%H:%M").replace(
            year=agora.year, month=agora.month, day=agora.day, tzinfo=agora.tzinfo
        )
        diferenca = abs((agora - horario_ref).total_seconds())

        if diferenca <= 300:
            emoji_map = {
                "08:00": "🍳", "11:30": "🍗", "16:00": "⚡",
                "20:00": "🐟", "09:00": "🕊️", "22:01": "🕊️", "10:55": "💊"
            }
            emoji = emoji_map.get(horario, "🔔")
            msg = f"{emoji} *{dados['nome']}*\n{dados['descricao']}"
            if dados["kcal"] > 0:
                msg += f"\n\n📊 {dados['kcal']} kcal | Prot: {dados['prot']}g | Carb: {dados['carb']}g | Gord: {dados['gord']}g"

            enviar_telegram(msg)

            if dados["kcal"] > 0:
                salvar_refeicao(horario, dados["nome"], dados["descricao"], dados["kcal"], seguida=True)

            return {"statusCode": 200, "body": f"Enviado: {horario}"}

    return {"statusCode": 200, "body": "Nenhuma refeição"}


# ── Lógica de webhook (mensagem do usuário) ────────────────────────────────────
def processar_mensagem(mensagem_usuario, chat_id):
    historico = buscar_historico_semana()
    ultima_suja = buscar_ultima_refeicao_suja()

    linhas_historico = []
    for r in sorted(historico, key=lambda x: x["timestamp"]):
        if r.get("seguida", True):
            status = "✅ seguida"
        else:
            status = f"❌ substituída por: {r.get('substituicao', 'não informado')}"
        linhas_historico.append(
            f"- {r['data']} {r['horario']} | {r['nome']} | {status}"
        )

    historico_formatado = "\n".join(linhas_historico) or "Nenhum registro esta semana."

    kcal_semana = sum(float(r.get("kcal", 0)) for r in historico if r.get("seguida"))
    dias_com_registro = len(set(r["data"] for r in historico))
    media_kcal_dia = kcal_semana / dias_com_registro if dias_com_registro > 0 else 0

    ultima_suja_str = (
        f"{ultima_suja['data']} {ultima_suja['horario']} — {ultima_suja.get('substituicao', 'não informado')}"
        if ultima_suja else "Nenhuma refeição fora do planejado esta semana."
    )

    prompt = f"""Você é um assistente de dieta direto e objetivo. Responda em português, de forma curta.

DIETA DIÁRIA ALVO: {KCAL_DIARIA_ALVO} kcal

HISTÓRICO DA SEMANA:
{historico_formatado}

ÚLTIMA REFEIÇÃO FORA DO PLANEJADO: {ultima_suja_str}

MÉDIA DE KCAL/DIA ESTA SEMANA: {media_kcal_dia:.0f} kcal

MENSAGEM DO USUÁRIO: "{mensagem_usuario}"

Instruções:
- Se o usuário perguntar sobre última refeição suja/livre, informe a data, horário e o que foi comido.
- Se o usuário perguntar se pode fazer uma refeição livre agora, analise o contexto calórico da semana e decida. Seja direto: sim ou não, e o motivo em 1-2 frases.
- Se o usuário estiver registrando uma substituição (ex: "comi pizza", "tomei sorvete"), confirme o registro e salve mentalmente — você vai retornar um JSON especial.
- Se for uma substituição, retorne EXATAMENTE neste formato JSON (sem markdown):
{{"acao":"registrar","descricao":"<o que foi comido>","horario_referencia":"<horário da dieta mais próximo>"}}
- Para qualquer outra resposta, retorne apenas o texto da resposta."""

    resposta = chamar_gemini(prompt)

    try:
        dados = json.loads(resposta)
        if dados.get("acao") == "registrar":
            agora = datetime.now(tz)
            horario_ref = dados.get("horario_referencia", agora.strftime("%H:%M"))
            nome_ref = DIETA.get(horario_ref, {}).get("nome", "Refeição")
            kcal_ref = DIETA.get(horario_ref, {}).get("kcal", 0)

            salvar_refeicao(
                horario=horario_ref,
                nome=nome_ref,
                descricao=dados["descricao"],
                kcal=kcal_ref,
                seguida=False,
                substituicao=dados["descricao"]
            )
            enviar_telegram(f"✅ Registrado: *{dados['descricao']}* no lugar de {nome_ref}.", chat_id)
            return
    except (json.JSONDecodeError, KeyError):
        pass

    enviar_telegram(resposta, chat_id)


# ── Handler principal ──────────────────────────────────────────────────────────
def lambda_handler(event, context):
    # Disparado pelo EventBridge (sem body)
    if "source" in event and event["source"] == "aws.events":
        return processar_horario()

    # Disparado pelo webhook do Telegram (Function URL)
    if "body" in event:
        try:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
            mensagem = body.get("message", {})
            texto = mensagem.get("text", "")
            chat_id = str(mensagem.get("chat", {}).get("id", ""))

            if texto and chat_id:
                processar_mensagem(texto, chat_id)

            return {"statusCode": 200, "body": "ok"}
        except Exception as e:
            print(f"Erro ao processar webhook: {e}")
            return {"statusCode": 200, "body": "ok"}

    # Fallback: tenta processar como horário
    return processar_horario()