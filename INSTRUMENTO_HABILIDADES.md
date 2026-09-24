# Instrumento de Habilidades e Experiências Práticas

**Engenheiro de IA / Software — baseado em evidências de código, infraestrutura e histórico de projetos (2026).**

---

## 1. Perfil

Engenheiro de IA e software que constrói produtos de ponta a ponta sozinho — do discovery de produto ao código, nuvem, LLM, CI/CD e operação. Autointitulado "arquiteto de sistemas de automação/IA que trabalha com startups de tecnologia" (prompt de persona do próprio bot). Atua em múltiplos domínios: fiscal/tributário, automação pessoal, prospecção B2B e análise de dados — sempre com IA aplicada como núcleo.

## 2. Projetos práticos (evidências)

| # | Projeto | O que é | Stack |
|---|---|---|---|
| 1 | **diet-lambda** (`Alerta-Dieta`) | Bot pessoal no Telegram rodando em AWS Lambda: dieta, treinos com progressão de carga, tarefas, autopostagem no LinkedIn, controle de EC2 pelo chat, aprovação de e-mails/outreach | Python 3.10, AWS Lambda + Function URL, DynamoDB, EventBridge (12 regras cron), EC2, Terraform, GitHub Actions, Gemini + OpenAI |
| 2 | **LangGraph eco** (`C:\LangGraph`) | Pipeline de prospecção: ingere histórico do Claude Code, monitora vagas em 63 empresas (LinkedIn, Greenhouse, Lever, Ashby), calcula intent de contratação e gera e-mails/outreach com aprovação humana no Telegram | Python, LangGraph, Postgres 5433 (cache de contatos + dedup) |
| 3 | **Bling Fiscal** (`C:\ZADI\MULTI\bling-fiscal`) | Produto de IA para contabilidades e empresas na Reforma Tributária (CBS/IBS/IS): diagnóstico de origem/NCM, classificação em grupos tributários, integração via API do ERP Bling | Python, API Bling, Postgres (jsonb) |
| 4 | **IRPF Dashboard** (`C:\SOLUTI\JANE`) | Comparativo de declarações IRPF entregues (.DEC) × pré-preenchidas (.DBK): parser de arquivos de largura fixa da Receita, banco e dashboard | Python, Streamlit, pandas, Plotly, Postgres |
| 5 | **NUTRICIONISTA** | Agente nutricionista clínico que gera planos alimentares em HTML | LLM + HTML |

## 3. Competências técnicas (com evidência)

### 🐍 Python / Engenharia de software
- `main.py` com ~1.490 linhas: funções nomeadas com docstrings, tratamento de exceção defensivo ("nunca derruba o fluxo"), fallback entre provedores de IA.
- Parsing de dados não estruturados: arquivos de largura fixa do Receitanet (registros 19–88/T9, campos monetários) — validado por cross-check entre fontes.
- Análise de dados e dashboards: pandas, Plotly, Streamlit (tabelas comparativas, gráficos, layout wide).
- Estruturação de repositórios: código, IaC, CI/CD e documentação convivendo organizados.

### ☁️ AWS (serverless)
- **Lambda** com Function URL público como webhook do Telegram.
- **DynamoDB** com design de tabela única por partição prefixada (`chat#`, `treino#`, `tarefa#`, `linkedin#contexto#`, `linkedin#draft#`, `linkedin#outreach#`, `linkedin#email#`) — padrão de modelagem real de NoSQL.
- **EventBridge**: 12 regras cron com timezone de Brasília (lembretes, revisão semanal com IA, geração de posts).
- **EC2** controlada por comando de chat, com trava de dono (`chat_id`).
- **IAM**: roles e policies para Lambda e usuário de deploy com privilégio mínimo.

### 🤖 IA aplicada (engenharia de LLM)
- Orquestração Gemini (2.5-flash) → fallback OpenAI (gpt-4o-mini) com degrade gracioso.
- Prompt engineering com **ações estruturadas em JSON** (exibir treino, salvar pesos, registrar refeição, tarefas, gerar posts) — function-calling manual.
- Composição de contexto: histórico conversacional (DynamoDB) + estado do domínio + preferências do usuário.
- Human-in-the-loop: nada é publicado/enviado sem aprovação por botão no Telegram.
- Geração de conteúdo com regras anti-clichê de IA (persona de produto).

### 🔌 Integrações / APIs
- Telegram Bot API: webhook com `secret_token`, inline keyboards, callbacks, parse_mode HTML/Markdown com fallback.
- LinkedIn: OAuth 2.0 (fluxo completo), REST API `/rest/posts` e `/rest/invitations`, `X-Restli-Protocol-Version`.
- SMTP Gmail (e-mails de prospecção).
- API Bling (ERP) para classificação fiscal.

### 🗄️ Banco de dados
- DynamoDB (queries por partição, `update_item` com expression names).
- PostgreSQL (5433): bancos `soluti`, `langgraph_eco`, `bling_fiscal`; SQL com jsonb, modelagem relacional, upserts.

### 🔐 Segurança (proativo — não reativo)
- Validação de `X-Telegram-Bot-Api-Secret-Token` no webhook (403 para forjados).
- Comandos de VM restritos ao dono por comparação de `chat_id`.
- Aprovação humana obrigatória antes de qualquer ação externa.
- Segredos fora do Git: env vars, `terraform.tfvars` no `.gitignore`, `KEY-IAM` local.

### 🛠️ DevOps / IaC
- **Terraform** completo como "kit de recuperação de desastre": Lambda, IAM, DynamoDB, EventBridge, EC2, AMI — `terraform apply` recria tudo.
- **GitHub Actions**: build do zip em Linux (removendo deps duplicadas do runtime), sanity check do pacote, deploy automático na main.
- Git com commits semânticos (`feat:`, `fix:`, `security:`).

### 📋 Produto / discovery
- Trabalho de discovery registrado no histórico: para um cliente com milhares de produtos, definiu que o MVP não é "calcular CBS/IBS" (o ERP já faz), mas **corrigir e classificar cadastros em massa** (origem importada incorreta, grupos tributários) — problema que existe hoje e escala para milhares de empresas.
- Validou a arquitetura diretamente com o fornecedor do ERP (Grupo Tributário → Natureza de Operação → regras por UF) antes de construir — de-risking de produto.

## 4. Domínios de atuação

- **Fiscal/tributário como produto**: Reforma Tributária (CBS/IBS/IS), NCM, CEST, origem de mercadorias, Grupos Tributários, Naturezas de Operação, regras interestaduais — nível suficiente para construir e vender produto para contabilidades.
- **Automação pessoal / agentes**: bot multi-domínio com memória, agendamentos e ações reais.
- **Prospecção B2B**: funil de vagas → intent → outreach/e-mail com aprovação.
- **Análise fiscal de PF**: arquivos da Receita Federal (DEC/DBK).

## 5. Pontos fortes observáveis

1. **Autonomia total**: concebe, codifica, sobe infra, faz deploy e documenta sozinho.
2. **Documentação excepcional**: READMEs com arquitetura, tabelas de recursos, avisos e manutenção.
3. **Pragmatismo de MVP**: prioriza o gargalo operacional real em vez do sistema grandioso.
4. **Segurança como hábito**: travas, validações e aprovação humana sem ninguém pedir.
5. **Velocidade de aprendizado**: em poucos meses evoluiu de bot de dieta para pipelines de prospecção com LLM, Terraform e CI/CD.

## 6. Áreas em desenvolvimento (oportunidades)

- Testes automatizados (não há suite de testes nos projetos analisados).
- Observabilidade (logs/métricas centralizados na AWS).
- Remote state do Terraform (S3 + DynamoDB lock) — já reconhecido no próprio README.

---

*Documento gerado a partir da leitura do código e histórico dos projetos. Evidências: `main.py`, `README.md`, `terraform/README.md`, `.github/workflows/deploy.yml`, `chat.txt`, `diagnostico_treinos_julho.py` e configurações de ambiente.*
