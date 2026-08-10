import os
import json
import requests
import boto3
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key
import pytz

# ── Configurações da Máquina Virtual (EC2) ────────────────────────────────────
INSTANCE_ID = "i-0dd6c3397f1559061"
ec2_client = boto3.client("ec2", region_name="us-east-1")

def é_comando_vm(texto_mensagem):
    """Detecta se a mensagem é um comando de VM — sem executar nada."""
    txt = texto_mensagem.strip().lower()
    return (
        txt.startswith("/vm") or
        "vm" in txt.split() or
        "maquina" in txt or
        "máquina" in txt
    )


def processar_comando_vm(texto_mensagem):
    """Executa o comando de VM e sempre retorna uma string (nunca None)."""
    txt = texto_mensagem.strip().lower()

    if any(k in txt for k in ["on", "liga", "ligar", "start"]):
        try:
            ec2_client.start_instances(InstanceIds=[INSTANCE_ID])
            return "🚀 Comando enviado: *LIGANDO* a máquina virtual!"
        except Exception as e:
            return f"❌ Erro ao ligar a máquina: {e}"

    elif any(k in txt for k in ["off", "desliga", "desligar", "stop"]):
        try:
            ec2_client.stop_instances(InstanceIds=[INSTANCE_ID])
            return "🛑 Comando enviado: *DESLIGANDO* a máquina virtual!"
        except Exception as e:
            return f"❌ Erro ao desligar a máquina: {e}"

    elif any(k in txt for k in ["status", "estado", "situacao", "situação"]) or txt in ["/vm", "vm"]:
        try:
            resposta = ec2_client.describe_instances(InstanceIds=[INSTANCE_ID])
            status = resposta['Reservations'][0]['Instances'][0]['State']['Name']
            return f"📊 Status atual da máquina: *{status.upper()}*"
        except Exception as e:
            return f"❌ Erro ao consultar status: {e}"

    elif "ip" in txt:
        try:
            resposta = ec2_client.describe_instances(InstanceIds=[INSTANCE_ID])
            instancia = resposta['Reservations'][0]['Instances'][0]
            ip = instancia.get('PublicIpAddress', 'Máquina desligada ou sem IP público no momento.')
            return f"🌐 IP Público atual: `{ip}`"
        except Exception as e:
            return f"❌ Erro ao consultar IP: {e}"

    return "❓ Comando da VM não reconhecido. Use:\n- `vm status`\n- `vm on`\n- `vm off`\n- `vm ip`"


# ── Configurações de Dieta ─────────────────────────────────────────────────────
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

# ── Treinos ────────────────────────────────────────────────────────────────────
TREINOS = {
    "upper_a": {
        "nome": "Upper A — Peito e Costas (horizontal)",
        "dia": "Segunda",
        "emoji": "💪",
        "aquecimento": "Mobilidade de ombros + rotação torácica + 5 min esteira leve",
        "resfriamento": "Alongamento de peito + dorsais + mobilidade torácica (30s cada)",
        "exercicios": [
            {"id": "supino_reto", "nome": "Supino reto com barra", "fase": "Principal", "series": "4 × 8–10", "descanso": "90 seg", "progressao": "+2,5 kg/sem", "assimetrico": False},
            {"id": "remada_curvada", "nome": "Remada curvada com barra", "fase": "Principal", "series": "4 × 8–10", "descanso": "90 seg", "progressao": "+2,5 kg/sem", "assimetrico": False},
            {"id": "crucifixo_unilateral", "nome": "Crucifixo com halter — unilateral", "fase": "Assimetria", "series": "4E / 3D × 12–15", "descanso": "60 seg", "progressao": "+1 kg a cada 2 sem", "assimetrico": True, "obs": "Volume maior no lado esquerdo"},
            {"id": "remada_unilateral", "nome": "Remada unilateral com halter", "fase": "Auxiliar", "series": "3 × 12 cada", "descanso": "60 seg", "progressao": "+2 kg/sem", "assimetrico": False},
            {"id": "crossover_unilateral", "nome": "Crossover na polia — unilateral", "fase": "Assimetria", "series": "4E / 3D × 15", "descanso": "45 seg", "progressao": "+2,5 kg/sem", "assimetrico": True, "obs": "Volume maior no lado esquerdo"},
        ],
    },
    "lower_a": {
        "nome": "Lower A — Dominância de joelho (quadríceps e glúteos)",
        "dia": "Quarta",
        "emoji": "🦵",
        "aquecimento": "Mobilidade de quadril + ativação de glúteos com elástico + agachamento sem carga 2×15",
        "resfriamento": "Alongamento de quadríceps, panturrilha e flexores de quadril",
        "exercicios": [
            {"id": "agachamento_livre", "nome": "Agachamento livre com barra", "fase": "Principal", "series": "4 × 8", "descanso": "2 min", "progressao": "+5 kg/sem", "assimetrico": False},
            {"id": "leg_press", "nome": "Leg press 45°", "fase": "Principal", "series": "4 × 10–12", "descanso": "90 seg", "progressao": "+10 kg/sem", "assimetrico": False},
            {"id": "cadeira_extensora", "nome": "Cadeira extensora", "fase": "Auxiliar", "series": "3 × 15", "descanso": "60 seg", "progressao": "+5 kg/sem", "assimetrico": False},
            {"id": "afundo_caminhando", "nome": "Afundo (lunge) caminhando com halteres", "fase": "Auxiliar", "series": "3 × 12 cada", "descanso": "60 seg", "progressao": "+2 kg/sem", "assimetrico": False},
            {"id": "panturrilha_maquina", "nome": "Elevação de panturrilha em pé (máquina)", "fase": "Auxiliar", "series": "4 × 20", "descanso": "45 seg", "progressao": "+5 kg/sem", "assimetrico": False},
        ],
    },
    "upper_b": {
        "nome": "Upper B — Ombros, braços e volume adicional de peito",
        "dia": "Sexta",
        "emoji": "🏋️",
        "aquecimento": "Dislocação com elástico + rotação externa de ombro + face pull leve 2×12",
        "resfriamento": "Alongamento de ombros, bíceps e tríceps (30s cada)",
        "exercicios": [
            {"id": "desenvolvimento_halteres", "nome": "Desenvolvimento com halteres", "fase": "Principal", "series": "4 × 10–12", "descanso": "90 seg", "progressao": "+2 kg/sem", "assimetrico": False},
            {"id": "barra_fixa_supinada", "nome": "Barra fixa pegada supinada (pull-up)", "fase": "Principal", "series": "4 × 6–8", "descanso": "90 seg", "progressao": "+1 rep/sem", "assimetrico": False},
            {"id": "supino_inclinado_unilateral", "nome": "Supino inclinado com halter — unilateral", "fase": "Assimetria", "series": "4E / 3D × 10–12", "descanso": "75 seg", "progressao": "+1 kg/sem", "assimetrico": True, "obs": "Volume maior no lado esquerdo"},
            {"id": "elevacao_lateral", "nome": "Elevação lateral com halteres", "fase": "Auxiliar", "series": "3 × 15", "descanso": "60 seg", "progressao": "+1 kg a cada 2 sem", "assimetrico": False},
            {"id": "rosca_direta", "nome": "Rosca direta com barra", "fase": "Auxiliar", "series": "3 × 10–12", "descanso": "60 seg", "progressao": "+2,5 kg/sem", "assimetrico": False},
            {"id": "triceps_corda", "nome": "Tríceps corda na polia", "fase": "Auxiliar", "series": "3 × 12", "descanso": "60 seg", "progressao": "+2,5 kg/sem", "assimetrico": False},
            {"id": "prancha", "nome": "Prancha frontal + prancha lateral", "fase": "Core", "series": "3 × 40s", "descanso": "30 seg", "progressao": "+5s/sem", "assimetrico": False},
        ],
    },
    "lower_b": {
        "nome": "Lower B — Dominância de quadril (posterior, glúteos e mobilidade)",
        "dia": "Sábado",
        "emoji": "🔥",
        "aquecimento": "Hip hinge sem carga + mobilidade lombar + ativação de isquiotibiais com elástico 2×10",
        "resfriamento": "Hip flexor stretch + pigeon pose + mobilidade de tornozelo + rotação lombar (amplitude progressiva)",
        "exercicios": [
            {"id": "levantamento_terra", "nome": "Levantamento terra convencional", "fase": "Principal", "series": "4 × 6", "descanso": "2–3 min", "progressao": "+5 kg/sem", "assimetrico": False},
            {"id": "stiff_halteres", "nome": "Stiff com halteres", "fase": "Principal", "series": "4 × 10", "descanso": "90 seg", "progressao": "+2,5 kg/sem", "assimetrico": False},
            {"id": "mesa_flexora", "nome": "Mesa flexora", "fase": "Auxiliar", "series": "3 × 12", "descanso": "60 seg", "progressao": "+5 kg/sem", "assimetrico": False},
            {"id": "abducao_quadril_polia", "nome": "Abdução de quadril na polia — unilateral (glúteo médio)", "fase": "Auxiliar", "series": "3 × 15 cada", "descanso": "45 seg", "progressao": "+2,5 kg/sem", "assimetrico": False},
        ],
    },
}

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE_NAME", "Dieta_Historico_Dev")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
tabela = dynamodb.Table(DYNAMODB_TABLE)
tz = pytz.timezone("America/Sao_Paulo")


# ── Gemini API ─────────────────────────────────────────────────────────────────
def chamar_gemini(prompt):
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=body, headers=headers, timeout=45)
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"Erro ao chamar Gemini: {e}")
        return "⚠️ A IA teve uma oscilação temporária. Envie sua mensagem novamente em instantes!"


def chamar_openai(prompt):
    """Fallback via OpenAI Chat Completions (modelo configurável por OPENAI_MODEL).
    Retorna o texto da resposta ou levanta exceção em falha."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"}
    body = {"model": OPENAI_MODEL, "messages": [{"role": "user", "content": prompt}]}
    response = requests.post(url, json=body, headers=headers, timeout=45)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def chamar_ia(prompt):
    """Tenta Gemini primeiro; em qualquer falha, cai pro ChatGPT (se OPENAI_API_KEY existir).
    Sem chave da OpenAI, mantém a mensagem amigável atual."""
    resposta = chamar_gemini(prompt)
    # A mensagem de erro amigável indica falha no Gemini → tenta fallback
    if resposta.startswith("⚠️"):
        if not OPENAI_API_KEY:
            return resposta
        try:
            print("Gemini indisponível → tentando OpenAI")
            return chamar_openai(prompt)
        except Exception as e:
            print(f"Erro ao chamar OpenAI: {e}")
            return "⚠️ As duas IAs estão com oscilações. Tente de novo em instantes!"
    return resposta


# ── Telegram ───────────────────────────────────────────────────────────────────
def enviar_telegram(mensagem, chat_id=None, guardar_conversa=True):
    """Envia ao Telegram e, se guardar_conversa, registra a RESPOSTA do bot no histórico.
    ⚠ Em processar_horario (agendados) SEMPRE passe guardar_conversa=False."""
    cid = chat_id or TELEGRAM_CHAT_ID
    if guardar_conversa and cid:
        salvar_conversa(mensagem, "bot", cid)   # grava ANTES de postar
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": cid, "text": mensagem, "parse_mode": "Markdown"})


# ── DynamoDB — Dieta ───────────────────────────────────────────────────────────
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
    return [r for r in registros if not r.get("data", "").startswith("treino#")]


def buscar_ultima_refeicao_suja():
    historico = buscar_historico_semana()
    sujas = [r for r in historico if not r.get("seguida", True)]
    if not sujas:
        return None
    return max(sujas, key=lambda r: r["timestamp"])


# ── DynamoDB — Treinos ─────────────────────────────────────────────────────────
def salvar_treino(treino_id, pesos: dict):
    agora = datetime.now(tz)
    tabela.put_item(Item={
        "data": f"treino#{agora.strftime('%Y-%m-%d')}",
        "timestamp": agora.isoformat(),
        "treino_id": treino_id,
        "semana": agora.strftime("%Y-W%W"),
        "pesos": pesos,
    })


def salvar_treino_com_data(treino_id, pesos, data_str):
    """Salva pesos de treino em data específica (retroativo).
    data_str no formato YYYY-MM-DD.
    """
    agora = datetime.now(tz)
    try:
        data_obj = datetime.strptime(data_str, "%Y-%m-%d")
        semana = data_obj.strftime("%Y-W%W")
    except ValueError:
        data_str = agora.strftime("%Y-%m-%d")
        semana = agora.strftime("%Y-W%W")

    tabela.put_item(Item={
        "data": f"treino#{data_str}",
        "timestamp": agora.isoformat(),   # timestamp atual → vira o registro mais recente desse dia
        "treino_id": treino_id,
        "semana": semana,
        "pesos": pesos,
    })


def buscar_ultimo_treino(treino_id):
    hoje = datetime.now(tz)
    for i in range(30):
        dia = (hoje - timedelta(days=i)).strftime("%Y-%m-%d")
        resp = tabela.query(KeyConditionExpression=Key("data").eq(f"treino#{dia}"))
        for item in resp.get("Items", []):
            if item.get("treino_id") == treino_id:
                return item
    return None


def buscar_resumo_ultimos_treinos():
    """Para cada treino, retorna o registro mais recente. Para quando achar todos os 4."""
    hoje = datetime.now(tz)
    resumo = {}
    for i in range(14):
        if len(resumo) == len(TREINOS):
            break
        dia = (hoje - timedelta(days=i)).strftime("%Y-%m-%d")
        resp = tabela.query(KeyConditionExpression=Key("data").eq(f"treino#{dia}"))
        for item in resp.get("Items", []):
            tid = item.get("treino_id")
            if tid and tid not in resumo:
                resumo[tid] = {"data": dia, "pesos": item.get("pesos", {})}
    return resumo


def buscar_treinos_semana_passada():
    """Retorna todos os treinos registrados nos últimos 7 dias (para revisão de domingo)."""
    hoje = datetime.now(tz)
    registros = []
    for i in range(7):
        dia = (hoje - timedelta(days=i)).strftime("%Y-%m-%d")
        resp = tabela.query(KeyConditionExpression=Key("data").eq(f"treino#{dia}"))
        registros.extend(resp.get("Items", []))
    return registros


# ── DynamoDB — Tarefas ─────────────────────────────────────────────────────────
def salvar_tarefa(descricao):
    agora = datetime.now(tz)
    tabela.put_item(Item={
        "data": f"tarefa#{agora.strftime('%Y-%m-%d')}",
        "timestamp": agora.isoformat(),
        "descricao": descricao,
        "status": "pendente",
    })


def buscar_tarefas_pendentes():
    hoje = datetime.now(tz)
    tarefas = []
    for i in range(30):  # 30 dias pois tarefas não expiram rapidamente
        dia = (hoje - timedelta(days=i)).strftime("%Y-%m-%d")
        resp = tabela.query(KeyConditionExpression=Key("data").eq(f"tarefa#{dia}"))
        tarefas.extend(resp.get("Items", []))
    return [t for t in tarefas if t.get("status") == "pendente"]


def concluir_tarefa(timestamp):
    """Marca uma tarefa como concluída pelo seu timestamp único."""
    hoje = datetime.now(tz)
    for i in range(30):
        dia = (hoje - timedelta(days=i)).strftime("%Y-%m-%d")
        chave = f"tarefa#{dia}"
        resp = tabela.query(KeyConditionExpression=Key("data").eq(chave))
        for item in resp.get("Items", []):
            if item.get("timestamp") == timestamp:
                tabela.update_item(
                    Key={"data": chave, "timestamp": timestamp},
                    UpdateExpression="SET #s = :s",
                    ExpressionAttributeNames={"#s": "status"},
                    ExpressionAttributeValues={":s": "concluida"},
                )
                return item.get("descricao", "")
    return None


# ── DynamoDB — Conversa ─────────────────────────────────────────────────────────
ULTIMAS_TROCAS_PROMPT = 16          # ≈ 8 trocas completas usuário+bot

def salvar_conversa(mensagem, remetente, chat_id=""):
    """Persiste UM lado da troca (remetente="usuario"|"bot") na partição chat#YYYY-MM-DD.
    Nunca lança exceção: falha de DDB não pode derrubar o envio do Telegram."""
    try:
        tabela.put_item(Item={
            "data": f"chat#{datetime.now(tz).strftime('%Y-%m-%d')}",
            "timestamp": datetime.now(tz).isoformat(),
            "remetente": remetente,
            "mensagem": mensagem,
            "chat_id": chat_id or "",
        })
    except Exception as e:
        print(f"[conversa] falha ao salvar: {e}")


def buscar_ultimas_trocas(n=ULTIMAS_TROCAS_PROMPT, dias_retroativos=5):
    """Últimas N mensagens EM ORDEM CRONOLÓGICA (loop de dias = padrão do código).
    Timestamp ISO ordena lexicograficamente = cronológico."""
    itens = []
    hoje = datetime.now(tz)
    for i in range(dias_retroativos):
        dia = (hoje - timedelta(days=i)).strftime("%Y-%m-%d")
        resp = tabela.query(KeyConditionExpression=Key("data").eq(f"chat#{dia}"))
        itens.extend(resp.get("Items", []))
    itens.sort(key=lambda x: x["timestamp"])
    return itens[-n:]


# ── Formatação de Treino ───────────────────────────────────────────────────────
def formatar_treino(treino_id, pesos_anteriores=None):
    t = TREINOS[treino_id]
    linhas = [
        f"{t['emoji']} *{t['nome']}*",
        f"📅 Dia sugerido: {t['dia']}",
        "",
        "🔥 *Aquecimento:*",
        f"_{t['aquecimento']}_",
        "",
        "─────────────────────",
    ]

    fase_atual = ""
    for ex in t["exercicios"]:
        if ex["fase"] != fase_atual:
            fase_atual = ex["fase"]
            linhas.append(f"\n*{fase_atual.upper()}*")

        peso_str = ""
        if pesos_anteriores and ex["id"] in pesos_anteriores:
            peso_str = f"  _(último: {pesos_anteriores[ex['id']]})_"

        linhas.append(f"• *{ex['nome']}*")
        linhas.append(f"  {ex['series']} | ⏱ {ex['descanso']} | 📈 {ex['progressao']}{peso_str}")

        if ex.get("obs"):
            linhas.append(f"  ⚠️ _{ex['obs']}_")

    linhas += [
        "",
        "─────────────────────",
        "❄️ *Resfriamento:*",
        f"_{t['resfriamento']}_",
        "",
        "─────────────────────",
        "📝 *Anote seus pesos após o treino!*",
        "Mande assim: `supino 80kg, remada 60kg, crucifixo 14kg`",
        "_Registrarei tudo e usarei pra calcular sua progressão na semana que vem._",
    ]

    return "\n".join(linhas)


# ── EventBridge — Automações agendadas ────────────────────────────────────────
def processar_horario(detail_type=""):
    agora = datetime.now(tz)
    dia_semana = agora.weekday()  # 0=segunda, 6=domingo

    # ── Lembrete de tarefas (10h e 14h) ──────────────────────────────────────
    if "lembrete_tarefas" in detail_type.lower():
        tarefas = buscar_tarefas_pendentes()
        if not tarefas:
            return {"statusCode": 200, "body": "Nenhuma tarefa pendente"}
        mensagem = "🔔 *Tarefas pendentes:*\n\n"
        for t in tarefas:
            data_curta = t["data"].replace("tarefa#", "")
            mensagem += f"• {t['descricao']} _(desde {data_curta})_\n"
        enviar_telegram(mensagem, guardar_conversa=False)
        return {"statusCode": 200, "body": "Lembrete de tarefas enviado"}

    # ── Segunda-feira: mensagem de progressão ─────────────────────────────────
    if dia_semana == 0 and "segunda" in detail_type.lower():
        msg = (
            "⚡ *Semana nova, guerreiro!*\n\n"
            "Esta semana teremos *progressão de carga* em todos os treinos. "
            "Seus pesos estão registrados — na hora do treino é só pedir e eu já trago tudo com as adições.\n\n"
            "Bora pra cima! 💪"
        )
        enviar_telegram(msg, guardar_conversa=False)
        return {"statusCode": 200, "body": "Mensagem de segunda enviada"}

    # ── Domingo: revisão semanal ───────────────────────────────────────────────
    if dia_semana == 6 and "domingo" in detail_type.lower():
        treinos_semana = buscar_treinos_semana_passada()
        ids_registrados = set(r.get("treino_id") for r in treinos_semana)
        faltantes = set(TREINOS.keys()) - ids_registrados

        if not faltantes:
            prompt_domingo = (
                "Você é um coach de academia entusiasta e empático. "
                "O usuário registrou TODOS os 4 treinos da semana (Upper A, Lower A, Upper B, Lower B). "
                "Escreva uma mensagem de parabéns em português, curta (máximo 5 linhas), "
                "com muito apoio moral, emoção genuína e incentivo à continuidade. "
                "Use emojis com moderação. Seja direto e humano."
            )
        else:
            nomes_faltantes = ", ".join(
                TREINOS[tid]["nome"].split("—")[0].strip() for tid in faltantes
            )
            prompt_domingo = (
                f"Você é um coach de academia empático. "
                f"O usuário NÃO registrou os seguintes treinos esta semana: {nomes_faltantes}. "
                f"Escreva uma mensagem de incentivo em português, curta (máximo 5 linhas), "
                f"sem julgamento, reconhecendo que imprevistos acontecem e motivando a retomar. "
                f"Use emojis com moderação. Seja humano e encorajador."
            )

        enviar_telegram(chamar_ia(prompt_domingo), guardar_conversa=False)
        return {"statusCode": 200, "body": "Revisão de domingo enviada"}

    # ── Lembretes de refeição ─────────────────────────────────────────────────
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

            enviar_telegram(msg, guardar_conversa=False)

            if dados["kcal"] > 0:
                salvar_refeicao(horario, dados["nome"], dados["descricao"], dados["kcal"], seguida=True)

            return {"statusCode": 200, "body": f"Enviado: {horario}"}

    return {"statusCode": 200, "body": "Nenhuma refeição no horário"}


# ── Webhook — Mensagens do usuário ────────────────────────────────────────────
def processar_mensagem(mensagem_usuario, chat_id):

    # 0. Registrar o lado do usuário SEMPRE — inclusive comandos de VM.
    salvar_conversa(mensagem_usuario, "usuario", chat_id)

    # 1. Comandos de VM têm prioridade absoluta (sem Gemini). A conversa é registrada acima;
    #    o enviar_telegram abaixo grava o lado do bot por padrão.
    if é_comando_vm(mensagem_usuario):
        enviar_telegram(processar_comando_vm(mensagem_usuario), chat_id)
        return

    # 2. Contexto de dieta
    historico_dieta = buscar_historico_semana()
    ultima_suja = buscar_ultima_refeicao_suja()

    linhas_historico = [
        f"- {r['data']} {r['horario']} | {r['nome']} | {'✅ seguida' if r.get('seguida', True) else '❌ substituída por: ' + r.get('substituicao', '?')}"
        for r in sorted(historico_dieta, key=lambda x: x["timestamp"])
    ]
    historico_formatado = "\n".join(linhas_historico) or "Nenhum registro esta semana."
    kcal_semana = sum(float(r.get("kcal", 0)) for r in historico_dieta if r.get("seguida"))
    dias = len(set(r["data"] for r in historico_dieta))
    media_kcal_dia = kcal_semana / dias if dias > 0 else 0
    ultima_suja_str = (
        f"{ultima_suja['data']} {ultima_suja['horario']} — {ultima_suja.get('substituicao', '?')}"
        if ultima_suja else "Nenhuma refeição fora do planejado esta semana."
    )

    # 3. Contexto de treino
    resumo_treinos = buscar_resumo_ultimos_treinos()
    todos_exercicios = {
        tid: [{"id": ex["id"], "nome": ex["nome"]} for ex in t["exercicios"]]
        for tid, t in TREINOS.items()
    }

    # 3.5. HISTÓRICO DA CONVERSA — últimas trocas, em ordem cronológica
    trocas = buscar_ultimas_trocas()
    linhas_conv = []
    for it in trocas:
        quem = "Usuário" if it.get("remetente") == "usuario" else "Bot"
        linhas_conv.append(f"{quem}: {it.get('mensagem', '')}")
    # Remove a mensagem atual (já aparece em MENSAGEM DO USUÁRIO no prompt)
    if linhas_conv and trocas[-1].get("remetente") == "usuario" and trocas[-1].get("mensagem") == mensagem_usuario:
        linhas_conv = linhas_conv[:-1]
    historico_conversa = "\n".join(linhas_conv) or "Sem histórico recente."

    prompt = f"""Você é um assistente pessoal de saúde, treino e produtividade. Responda em português, de forma direta.

═══════════════════════════════
CONTEXTO DE DIETA
═══════════════════════════════
ALVO DIÁRIO: {KCAL_DIARIA_ALVO} kcal | MÉDIA DA SEMANA: {media_kcal_dia:.0f} kcal
HISTÓRICO:
{historico_formatado}
ÚLTIMA REFEIÇÃO FORA DO PLANEJADO: {ultima_suja_str}

═══════════════════════════════
CONTEXTO DE TREINO
═══════════════════════════════
ÚLTIMOS PESOS: {json.dumps(resumo_treinos, ensure_ascii=False)}
EXERCÍCIOS: {json.dumps(todos_exercicios, ensure_ascii=False)}

═══════════════════════════════
HISTÓRICO DA CONVERSA
═══════════════════════════════
{historico_conversa}

═══════════════════════════════
MENSAGEM DO USUÁRIO: "{mensagem_usuario}"
═══════════════════════════════

INSTRUÇÕES — retorne APENAS um JSON ou texto direto:

1. EXIBIR TREINO (ex: "treino upper a", "quero fazer lower b"):
{{"acao":"exibir_treino","treino_id":"<upper_a|lower_a|upper_b|lower_b>"}}

2. SALVAR PESOS (ex: "supino 80kg, remada 60kg"):
{{"acao":"salvar_pesos","treino_id":"<id>","pesos":{{"<exercise_id>":"<valor>"}}}}

2B. ATUALIZAR TREINO RETROATIVO — usuário quer corrigir ou registrar pesos de um dia específico
    (ex: "atualiza o upper a do dia 25", "esqueci de salvar sexta, supino 80kg remada 60kg",
    "corrige o lower b de ontem", "registra o treino de segunda passada: agachamento 60kg"):
{{"acao":"atualizar_treino","treino_id":"<id>","data":"<YYYY-MM-DD>","pesos":{{"<exercise_id>":"<valor exato>"}}}}
Se o usuário disser "ontem", "sexta passada", etc., calcule a data correta.

IMPORTANTE: salve o valor do peso EXATAMENTE como o usuário digitou.
Pode conter letras, hífen, vírgula, barras, qualquer caractere.
Exemplos válidos: "80kg", "5-4-3", "5,5,4", "4 repetições", "falhou na 3ª", "bodyweight".
Nunca normalize, nunca converta, nunca remova caracteres.

3. CONSULTAR PESOS (ex: "meus pesos do último upper a"):
{{"acao":"consultar_pesos","treino_id":"<id>"}}

4. REGISTRAR SUBSTITUIÇÃO DE REFEIÇÃO (ex: "comi pizza"):
{{"acao":"registrar_refeicao","descricao":"<comida>","horario_referencia":"<HH:MM>"}}

5. SALVAR TAREFA (ex: "lembra de pagar o boleto", "anota: ligar pro médico"):
{{"acao":"salvar_tarefa","descricao":"<tarefa>"}}

6. CONCLUIR TAREFA (ex: "concluí o boleto", "pode tirar o lembrete do médico"):
{{"acao":"concluir_tarefa","descricao_aproximada":"<descrição aproximada>"}}

7. LISTAR TAREFAS (ex: "minhas tarefas", "o que tenho pendente?"):
{{"acao":"listar_tarefas"}}

8. QUALQUER OUTRA PERGUNTA: responda em texto direto, sem JSON.

REGRAS:
- Retorne SOMENTE o JSON ou SOMENTE o texto. Nunca misture.
- Não use markdown no JSON. Sem texto antes ou depois do JSON.
- Para salvar_pesos, deduza o treino_id pelos exercícios mencionados.
- Use o HISTÓRICO DA CONVERSA para manter continuidade: assuntos em aberto, preferências já ditas, pesos já combinados. Não repita o que você mesmo já falou."""

    resposta = chamar_ia(prompt)

    try:
        texto_limpo = resposta.strip().strip("```json").strip("```").strip()
        dados = json.loads(texto_limpo)
        acao = dados.get("acao")

        # ── Exibir treino ──────────────────────────────────────────────────────
        if acao == "exibir_treino":
            treino_id = dados.get("treino_id")
            if treino_id not in TREINOS:
                enviar_telegram("❌ Treino não encontrado. Tente: upper_a, lower_a, upper_b ou lower_b.", chat_id)
                return
            ultimo = buscar_ultimo_treino(treino_id)
            pesos_anteriores = ultimo.get("pesos", {}) if ultimo else {}
            enviar_telegram(formatar_treino(treino_id, pesos_anteriores), chat_id)
            return

        # ── Salvar pesos ───────────────────────────────────────────────────────
        if acao == "salvar_pesos":
            treino_id = dados.get("treino_id")
            pesos = dados.get("pesos", {})
            if not treino_id or not pesos:
                enviar_telegram("❌ Não consegui identificar o treino ou os pesos. Pode repetir?", chat_id)
                return
            salvar_treino(treino_id, pesos)
            t = TREINOS.get(treino_id, {})
            linhas = [f"✅ *{t.get('nome', treino_id)}* registrado!\n"]
            for ex in t.get("exercicios", []):
                if ex["id"] in pesos:
                    linhas.append(f"• {ex['nome']}: *{pesos[ex['id']]}*")
            linhas.append("\n_Na semana que vem já trago com as progressões calculadas. 💪_")
            enviar_telegram("\n".join(linhas), chat_id)
            return

        # ── Atualizar treino retroativo ────────────────────────────────────────
        if acao == "atualizar_treino":
            treino_id = dados.get("treino_id")
            pesos = dados.get("pesos", {})
            data_str = dados.get("data", "")
            if not treino_id or not pesos:
                enviar_telegram("❌ Não consegui identificar o treino ou os pesos. Pode repetir?", chat_id)
                return

            salvar_treino_com_data(treino_id, pesos, data_str)

            t = TREINOS.get(treino_id, {})
            linhas = [f"✅ *{t.get('nome', treino_id)}* atualizado para {data_str}!\n"]
            for ex in t.get("exercicios", []):
                eid = ex["id"]
                if eid in pesos:
                    linhas.append(f"• {ex['nome']}: *{pesos[eid]}*")
            linhas.append("\n_Registro retroativo salvo. 📅_")
            enviar_telegram("\n".join(linhas), chat_id)
            return

        # ── Consultar pesos ────────────────────────────────────────────────────
        if acao == "consultar_pesos":
            treino_id = dados.get("treino_id")
            ultimo = buscar_ultimo_treino(treino_id)
            if not ultimo:
                enviar_telegram(f"📭 Nenhum registro encontrado para *{TREINOS.get(treino_id, {}).get('nome', treino_id)}*.", chat_id)
                return
            t = TREINOS.get(treino_id, {})
            data_str = ultimo["data"].replace("treino#", "")
            pesos = ultimo.get("pesos", {})
            linhas = [f"📋 *{t.get('nome', treino_id)}*", f"_Último registro: {data_str}_\n"]
            for ex in t.get("exercicios", []):
                if ex["id"] in pesos:
                    linhas.append(f"• {ex['nome']}: *{pesos[ex['id']]}*  _(próximo: {ex['progressao']})_")
            enviar_telegram("\n".join(linhas), chat_id)
            return

        # ── Registrar substituição de refeição ─────────────────────────────────
        if acao == "registrar_refeicao":
            horario_ref = dados.get("horario_referencia", datetime.now(tz).strftime("%H:%M"))
            nome_ref = DIETA.get(horario_ref, {}).get("nome", "Refeição")
            kcal_ref = DIETA.get(horario_ref, {}).get("kcal", 0)
            descricao = dados.get("descricao", "")
            salvar_refeicao(
                horario=horario_ref,
                nome=nome_ref,
                descricao=descricao,
                kcal=kcal_ref,
                seguida=False,
                substituicao=descricao,
            )
            enviar_telegram(f"✅ Registrado: *{descricao}* no lugar de {nome_ref}.", chat_id)
            return

        # ── Salvar tarefa ──────────────────────────────────────────────────────
        if acao == "salvar_tarefa":
            descricao = dados.get("descricao", "").strip()
            if not descricao:
                enviar_telegram("❌ Não entendi a tarefa. Pode repetir?", chat_id)
                return
            salvar_tarefa(descricao)
            enviar_telegram(f"📝 Anotado na sua lista: *{descricao}*", chat_id)
            return

        # ── Concluir tarefa ────────────────────────────────────────────────────
        if acao == "concluir_tarefa":
            descricao_aproximada = dados.get("descricao_aproximada", "").lower()
            tarefas = buscar_tarefas_pendentes()
            encontrada = None
            for t in tarefas:
                if any(palavra in t["descricao"].lower() for palavra in descricao_aproximada.split()):
                    encontrada = t
                    break
            if not encontrada and tarefas:
                encontrada = tarefas[-1]  # fallback: última tarefa pendente
            if not encontrada:
                enviar_telegram("📭 Não encontrei nenhuma tarefa pendente para concluir.", chat_id)
                return
            concluir_tarefa(encontrada["timestamp"])
            enviar_telegram(f"✅ Tarefa concluída: *{encontrada['descricao']}*", chat_id)
            return

        # ── Listar tarefas ─────────────────────────────────────────────────────
        if acao == "listar_tarefas":
            tarefas = buscar_tarefas_pendentes()
            if not tarefas:
                enviar_telegram("✅ Nenhuma tarefa pendente. Você está em dia!", chat_id)
                return
            linhas = ["📋 *Suas tarefas pendentes:*\n"]
            for t in tarefas:
                data_curta = t["data"].replace("tarefa#", "")
                linhas.append(f"• {t['descricao']} _(desde {data_curta})_")
            enviar_telegram("\n".join(linhas), chat_id)
            return

    except (json.JSONDecodeError, KeyError):
        pass

    # ── Resposta de texto livre ────────────────────────────────────────────────
    enviar_telegram(resposta, chat_id)


# ── Handler principal ──────────────────────────────────────────────────────────
def lambda_handler(event, context):
    # EventBridge
    if event.get("source") == "aws.events":
        detail_type = event.get("detail-type", "")
        return processar_horario(detail_type)

    # Webhook do Telegram
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
            print(f"Erro no webhook: {e}")
            return {"statusCode": 200, "body": "ok"}

    # Fallback
    return processar_horario()