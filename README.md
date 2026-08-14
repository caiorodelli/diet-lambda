# diet-lambda

Bot pessoal de Telegram rodando em **AWS Lambda** — saúde, treino, produtividade e prospecção de carreira em um único assistente. Toda a conversa passa por IA (Gemini, com fallback OpenAI), e o bot conversa, registra, agenda e age (publica no LinkedIn, liga a VM, envia e-mails) com a sua aprovação.

```
Telegram ⇄ Lambda Function URL ⇄ Gemini/OpenAI
                  │
                  ├─ DynamoDB (memória, refeições, treinos, tarefas, drafts)
                  ├─ EventBridge (12 regras cron — lembretes e eventos)
                  ├─ EC2 t3.nano (VM controlada pelo chat)
                  └─ Pipeline local C:\LangGraph (prospecção: vagas → e-mails/outreach)
```

---

## 1. O que o bot faz

### 🥗 Dieta
- **Lembretes de refeição** nos horários do plano (08:00, 11:30, 16:00, 20:00 — além de 09:00 Shema, 10:55 selênio e 22:01 Shema). Cada lembrete traz a composição da refeição com kcal e macros.
- **Registro automático**: quando o lembrete dispara, a refeição é gravada como *seguida*.
- **Substituição**: diga o que comeu fora do plano ("comi pizza", "troquei o almoço por lanche") e o bot registra a troca — a média calórica da semana e a última refeição "suja" entram no contexto de toda conversa.
- **Alvo diário**: 3.133 kcal (soma das refeições do plano) — o bot mostra a média da semana em cada resposta.

### 🏋️ Treinos
Quatro treinos com exercícios, séries, descanso e **progressão de carga por semana** (com correção de assimetria nos unilaterais):

| ID | Nome | Dia |
|---|---|---|
| `upper_a` | Upper A — Peito e Costas | Segunda |
| `lower_a` | Lower A — Quadríceps/Glúteos | Quarta |
| `upper_b` | Upper B — Ombros/Braços | Sexta |
| `lower_b` | Lower B — Posterior/Core | Sábado |

- **Exibir**: "treino upper a", "quero fazer lower b" → mostra o treino completo com os pesos da última sessão.
- **Salvar pesos**: "supino 80kg, remada 60kg" → registra (valor salvo exatamente como digitado).
- **Registro retroativo**: "atualiza o upper a do dia 25", "esqueci de salvar sexta: supino 80kg" → o bot calcula a data.
- **Consultar**: "meus pesos do último upper a".
- **Segunda 07:00** — mensagem de progressão da semana. **Domingo 20:00** — revisão semanal gerada por IA (parabéns se fez os 4, incentivo sem julgamento se faltou algum).

### ✅ Tarefas
- "lembra de pagar o boleto" → salva na lista.
- "concluí o boleto" → conclui (por aproximação de palavras).
- "minhas tarefas" / "o que tenho pendente?" → lista.
- **Lembretes automáticos às 10:00 e 14:00** com as pendências.

### 💼 LinkedIn — autopostagem
- **Contexto**: diga "registra que fiz X no projeto" (ou "anota no contexto do linkedin: …") — o bot acumula o contexto da semana no DynamoDB.
- **Rascunhos**: terça e quinta o EventBridge gera **3 rascunhos de post** a partir do contexto e manda no Telegram com botões de aprovação (também dá para pedir na hora: "gera um post pro linkedin").
- **Publicação**: no botão aprovado, o texto vai para o seu perfil via LinkedIn REST API (`/rest/posts`).
- Etapa pendente: OAuth do LinkedIn para o token de publicação (guia em `PASSO_A_PASSO.md`).

### 📧 Prospecção de clientes (pipeline local LangGraph)
O pipeline local em `C:\LangGraph` (fora deste repositório) monitora o histórico do Claude Code, busca vagas em 63 empresas (LinkedIn, Greenhouse, Lever, Ashby), calcula intent de contratação e invoca esta Lambda com três tipos de evento:

| Evento | O que chega no Telegram | Ação do botão |
|---|---|---|
| `outreach_aprovar` | Mensagem de outreach para empresa | Enviar (convite LinkedIn) / Pular |
| `email_aprovar` | E-mail frio completo (assunto + corpo) | **Enviar Email** (SMTP do Gmail) / Pular |
| `engajamento_dicas` | Empresas sem e-mail resolvido: link da vaga + comentário sugerido | Ação manual no LinkedIn |

- Os rascunhos ficam no DynamoDB vinculados à mensagem do Telegram.
- Envio de convite usa a Invitations API do LinkedIn — requer o product **Community Management API** aprovado na App (pendente; até lá o botão registra a aprovação e avisa o que falta).
- E-mails saem via SMTP do Gmail (`EMAIL_USER`/`EMAIL_PASSWORD` nas env vars).

### 🖥️ VM (EC2)
Comandos direto no chat — **restritos ao dono do bot** (comparação de `chat_id`):
- `vm on` / `vm off` — liga/desliga a instância 
- `vm status` — estado atual
- `vm ip` — IP público

### 🧠 Memória conversacional
Todas as trocas são persistidas na tabela `Dieta_Historico_Dev` (partição `chat#YYYY-MM-DD`). As últimas ~8 trocas entram no prompt da IA como `HISTÓRICO DA CONVERSA`, junto com o contexto de dieta e treino — o bot lembra de assuntos em aberto, preferências e pesos já combinados.

---

## 2. Agendamentos (EventBridge)

Horários em **Brasília (BRT = UTC−3)**:

| Hora (BRT) | Regra | O que faz |
|---|---|---|
| 07:00 seg | `treino-segunda-motivacao` | Mensagem de progressão da semana |
| 08:00 | refeição | Refeição 1 — O Despertar do Guerreiro |
| 09:00 | refeição | Shema Ysrael |
| 10:00 e 14:00 | `dieta-lembrete-tarefas-*` | Lista de tarefas pendentes |
| 10:55 | refeição | Hora do Selênio |
| 11:30 | refeição | Refeição 2 — O Combustível de Atenas |
| 16:00 | refeição | Refeição 3 — O Elixir do Olimpo |
| 20:00 | refeição | Refeição 4 — A Ceia dos Fortes |
| 20:00 dom | `treino-domingo-revisao` | Revisão semanal de treinos (IA) |
| 22:01 | refeição | Shema Ysrael |
| ter/qui 10:00 | `dieta-linkedin-cron` | Gera 3 rascunhos de post do LinkedIn |

---

## 3. Arquitetura e fluxo

```
1. Mensagem no Telegram → webhook → Lambda Function URL
2. lambda_handler valida TELEGRAM_SECRET_TOKEN (header X-Telegram-Bot-Api-Secret-Token)
3. processar_mensagem:
   a. Registra a mensagem no DynamoDB (sempre)
   b. Comandos de VM? → prioridade absoluta, sem IA, só o dono
   c. Monta o prompt com: dieta da semana + treinos + histórico da conversa
   d. IA responde JSON {"acao": ...} ou texto livre
   e. Ação executada (salvar/exibir/registrar/…) e resposta enviada
4. Callbacks de botão (callback_query) → aprovar/pular/publicar/enviar
```

O prompt instrui a IA a responder com ações estruturadas (JSON) para exibir treino, salvar pesos, registrar refeição/tarefa, gerar post etc. — e texto livre para qualquer outra conversa. **Gemini é o primário; qualquer falha cai para OpenAI (`gpt-4o-mini` por padrão).**

### DynamoDB — chaves usadas

| Partição | Conteúdo |
|---|---|
| `chat#YYYY-MM-DD` | Histórico da conversa (memória) |
| `YYYY-MM-DD` | Refeições (seguidas/substituídas) |
| `treino#*` | Sessões de treino e pesos |
| `tarefa#*` | Tarefas pendentes/concluídas |
| `linkedin#contexto#*` | Contexto acumulado para posts |
| `linkedin#draft#*` | Rascunhos de post (aprovados no Telegram) |
| `linkedin#outreach#*` / `linkedin#email#*` | Rascunhos de prospecção pendentes de aprovação |

---

## 4. Infraestrutura (Terraform)

Tudo em `terraform/` — kit de recuperação completo: `terraform apply` recria a infra do zero (perdeu a conta AWS? recria).

- **Lambda** `dieta-telegram` (Python 3.10, Function URL público)
- **DynamoDB** `Dieta_Historico_Dev` (PAY_PER_REQUEST, `prevent_destroy`)
- **EventBridge**: 12 regras cron (tabela acima)
- **EC2** `t3.nano` (VM controlada pelo chat) + Security Group
- **IAM**: role da Lambda + user de deploy (`lambda-deploy`, criado manualmente)

Detalhes completos em [`terraform/README.md`](terraform/README.md).

⚠️ **Segredos**: os tokens reais ficam nas env vars da Lambda e em `KEY-IAM` (NUNCA commitado — o `.gitignore` bloqueia). `terraform.tfvars` também nunca sobe.

### Env vars da Lambda

| Variável | Uso |
|---|---|
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Bot e dono (chat_id) |
| `TELEGRAM_SECRET_TOKEN` | Validação do webhook (anti-fraude) |
| `DYNAMODB_TABLE_NAME` | Tabela DynamoDB |
| `GEMINI_API_KEY` | IA primária |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | IA de fallback |
| `LINKEDIN_ACCESS_TOKEN` / `LINKEDIN_AUTHOR_URN` / `LINKEDIN_VERSION` | Publicação e convites no LinkedIn |
| `EMAIL_USER` / `EMAIL_PASSWORD` / `EMAIL_HOST` / `EMAIL_PORT` | SMTP (Gmail) dos e-mails de prospecção |

---

## 5. Deploy

**Automatizado via GitHub Actions** (`.github/workflows/deploy.yml`): todo push na `main` monta o `function.zip` em runner Linux (com as deps de `requirements.txt`) e atualiza a função `dieta-telegram`.

Pré-requisito (uma vez): secrets `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` no repositório (chave com permissão só de deploy).

Fluxo manual (legado):

```bash
python -m pip install -r requirements.txt --target package  # ambiente LINUX/Git Bash
rm -f function.zip
cd package && zip -r ../function.zip . && cd ..
zip -g function.zip main.py
aws lambda update-function-code --function-name dieta-telegram --zip-file fileb://function.zip
```

> ⚠️ O `package/` local desta máquina contém binários **Windows** (CPython 3.14 `.pyd`), incompatíveis com o runtime Lambda python3.10 — não o use como base do zip; o CI reinstala as deps em Linux.

**Webhook**: a URL do Function URL (`terraform output function_url`) é registrada no Telegram via `setWebhook` com o `secret_token`.

---

## 6. Segurança

- **Webhook**: toda atualização do Telegram precisa trazer `X-Telegram-Bot-Api-Secret-Token` correto; sem ele → 403.
- **VM**: comandos de EC2 conferem `chat_id` contra `TELEGRAM_CHAT_ID` — só o dono liga/desliga a máquina.
- **Segredos**: `KEY-IAM`, `terraform.tfvars`, `.env` nunca vão para o Git (`.gitignore` cobre).
- **Aprovação humana**: nada é publicado/enviado (LinkedIn, e-mail, convite) sem o clique no botão do Telegram.

---

## 7. Projetos relacionados (fora deste repositório)

| Projeto | Onde | Relação |
|---|---|---|
| **LangGraph eco** | `C:\LangGraph` | Pipeline local de prospecção: ingere o histórico do Claude Code, busca vagas, gera e-mails/outreach e invoca esta Lambda para as aprovações no Telegram. Cache de contatos e dedup de aprovações (7 dias) no Postgres 5433. |
| **Agente Nutricionista** | `..\NUTRICIONISTA\` | Persona e instruções de nutricionista clínico (agente à parte, gera planos alimentares em HTML). |
| **Bling Fiscal** | `C:\ZADI\MULTI\bling-fiscal` | Projeto separado de classificação fiscal do catálogo Bling (usa o mesmo Postgres portátil 5433). |

---

## 8. Estrutura do repositório

```
diet-lambda/
├── main.py                  # Todo o bot (dieta, treinos, tarefas, LinkedIn, outreach, email, VM)
├── requirements.txt         # Deps da Lambda (requests, boto3, pytz)
├── .github/workflows/       # CI/CD — deploy automático na main
├── terraform/               # Infra as code (Lambda, DDB, EventBridge, EC2, IAM)
│   └── README.md            # Manual do Terraform (recuperação de desastre)
├── diagnostico_treinos_julho.py  # Script avulso de diagnóstico dos treinos
└── README.md                # Este arquivo
```
