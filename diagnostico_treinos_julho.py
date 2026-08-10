"""
diagnostico_treinos_julho.py
============================
Levantamento completo dos treinos de Julho/2026 no DynamoDB.
Rode localmente com suas credenciais AWS configuradas.

Uso:
    python diagnostico_treinos_julho.py

Pré-requisito:
    pip install boto3
"""

import boto3
from boto3.dynamodb.conditions import Key
from datetime import date, timedelta
from collections import defaultdict
import json

# ── Config ─────────────────────────────────────────────────────────────────────
TABLE_NAME  = "Dieta_Historico_Dev"
REGION      = "us-east-1"
ANO         = 2026
MES         = 7   # Julho

# IDs esperados dos treinos
TREINOS_ESPERADOS = {
    "upper_a": "Upper A — Peito e Costas",
    "lower_a": "Lower A — Joelho/Quadríceps",
    "upper_b": "Upper B — Ombros e Braços",
    "lower_b": "Lower B — Quadril/Posterior",
}

# ── Conexão ────────────────────────────────────────────────────────────────────
dynamodb = boto3.resource("dynamodb", region_name=REGION)
tabela   = dynamodb.Table(TABLE_NAME)

# ── Gera todos os dias de Julho ────────────────────────────────────────────────
inicio = date(ANO, MES, 1)
# Último dia do mês
if MES == 12:
    fim = date(ANO + 1, 1, 1) - timedelta(days=1)
else:
    fim = date(ANO, MES + 1, 1) - timedelta(days=1)

dias = []
d = inicio
while d <= fim:
    dias.append(d)
    d += timedelta(days=1)

# ── Query DynamoDB para cada dia ───────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  DIAGNÓSTICO DE TREINOS — JULHO {ANO}")
print(f"{'='*60}")
print(f"  Tabela : {TABLE_NAME}")
print(f"  Período: {inicio} → {fim}  ({len(dias)} dias)")
print(f"{'='*60}\n")

todos_registros = []

for dia in dias:
    chave = f"treino#{dia.strftime('%Y-%m-%d')}"
    resp  = tabela.query(KeyConditionExpression=Key("data").eq(chave))
    items = resp.get("Items", [])
    todos_registros.extend(items)

# ── Análise ────────────────────────────────────────────────────────────────────
if not todos_registros:
    print("⚠️  NENHUM registro de treino encontrado em Julho.")
    print("    Possíveis causas:")
    print("    1. Os registros ainda não existiam (bot não estava salvo)")
    print("    2. A chave 'treino#' nunca foi usada nesse período")
    print("    3. Os dados foram salvos com prefixo diferente")
    print()
else:
    print(f"📦 Total de registros encontrados: {len(todos_registros)}\n")

    # Agrupa por treino_id
    por_treino = defaultdict(list)
    sem_treino_id = []

    for r in todos_registros:
        tid = r.get("treino_id")
        if tid:
            por_treino[tid].append(r)
        else:
            sem_treino_id.append(r)

    # ── Resumo por treino ──────────────────────────────────────────────────────
    print("─" * 60)
    print("RESUMO POR TIPO DE TREINO")
    print("─" * 60)

    for tid, nome in TREINOS_ESPERADOS.items():
        registros = por_treino.get(tid, [])
        qtd = len(registros)
        if qtd == 0:
            status = "❌ Nenhum registro"
        else:
            datas = sorted(r["data"].replace("treino#", "") for r in registros)
            status = f"✅ {qtd}x → {', '.join(datas)}"
        print(f"  {nome:<40} {status}")

    if sem_treino_id:
        print(f"\n  ⚠️  Registros SEM treino_id: {len(sem_treino_id)}")

    # ── Detalhe cronológico ────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("DETALHE CRONOLÓGICO (ordem de data)")
    print("─" * 60)

    registros_ordenados = sorted(todos_registros, key=lambda r: r.get("timestamp", ""))

    for r in registros_ordenados:
        data_str = r.get("data", "?").replace("treino#", "")
        tid      = r.get("treino_id", "❓ sem treino_id")
        semana   = r.get("semana", "?")
        pesos    = r.get("pesos", {})
        ts       = r.get("timestamp", "?")

        print(f"\n  📅 {data_str}  |  Treino: {tid}  |  Semana: {semana}")
        print(f"     Timestamp: {ts}")

        if pesos:
            print(f"     Pesos registrados ({len(pesos)} exercício(s)):")
            for ex_id, valor in pesos.items():
                print(f"       • {ex_id}: {valor}")
        else:
            print(f"     ⚠️  Nenhum peso registrado (campo 'pesos' vazio ou ausente)")

    # ── Checagem de anomalias ──────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("CHECAGEM DE ANOMALIAS")
    print("─" * 60)

    anomalias = []

    # Duplicatas no mesmo dia+treino
    por_dia_tid = defaultdict(list)
    for r in todos_registros:
        chave_dup = (r.get("data"), r.get("treino_id"))
        por_dia_tid[chave_dup].append(r)

    for (data_k, tid_k), lista in por_dia_tid.items():
        if len(lista) > 1:
            anomalias.append(
                f"  ⚠️  DUPLICATA: {data_k} / {tid_k} → {len(lista)} registros no mesmo dia"
            )

    # Registros sem pesos
    for r in todos_registros:
        if not r.get("pesos"):
            anomalias.append(
                f"  ⚠️  SEM PESOS: {r.get('data')} / {r.get('treino_id', '?')} (timestamp: {r.get('timestamp')})"
            )

    # Registros sem treino_id
    for r in sem_treino_id:
        anomalias.append(
            f"  ⚠️  SEM treino_id: {r.get('data')} / ts: {r.get('timestamp')}"
        )

    if anomalias:
        for a in anomalias:
            print(a)
    else:
        print("  ✅ Nenhuma anomalia detectada.")

# ── Dump JSON completo (opcional) ──────────────────────────────────────────────
print(f"\n{'─'*60}")
print("DUMP JSON COMPLETO (para inspeção manual)")
print("─" * 60)
print(json.dumps(todos_registros, indent=2, ensure_ascii=False, default=str))
print(f"\n{'='*60}\n")