# 🏗 Terraform — Infraestrutura `diet-lambda`

IaC (Infrastructure as Code) do projeto **diet-lambda** — bot Telegram + dieta + treinos + LinkedIn autopost.

**⚠️ Este é o teu KIT DE RECUPERAÇÃO. Guarda no GitHub junto com o código.**

Se você perder a conta AWS, um `terraform apply` recria tudo.

---

## 📦 O que este Terraform CRIA

| Recurso | Nome | Detalhe |
|---|---|---|
| **Lambda** | `dieta-telegram` | Python 3.10, 128 MB, 30s, Function URL público |
| **IAM Role** | `dieta-lambda-role` | Trust: `lambda.amazonaws.com` |
| **IAM Policies** | 4 | EC2 full + Lambda logs + DynamoDB (`Dieta_Historico_Dev`, `Pontual_Tarefas_Dev`) |
| **DynamoDB** | `Dieta_Historico_Dev` | PK=`data` (S), SK=`timestamp` (S), PAY_PER_REQUEST |
| **EventBridge** | 12 regras | Refeições (6) + Tarefas (2) + LinkedIn (1) + Treinos (2) + Selênio (1) |
| **Lambda Permissions** | 14 | 1 por regra EventBridge + 2 do Function URL |
| **EC2** | `t3.nano` | 20 GB gp3, Ubuntu, SG com SSH/HTTP/HTTPS/WireGuard |
| **AMI** | `ami-02fdd9833f229beab` | Snapshot do disco (criado 2026-08-11) |

---

## ❌ O que este Terraform NÃO CRIA

| Recurso | Por quê |
|---|---|
| **Usuário `lambda-deploy`** | É o user do CI/CD (GitHub Actions), criado manualmente |
| **Lambda `dieta-thais`** | App separada — teria o próprio Terraform |
| **Código da Lambda** | Deploy via **GitHub Actions** (`.github/workflows/deploy.yml`) |
| **API Gateway** | O bot usa **Lambda Function URL**, não API Gateway |
| **Secrets Manager** | Tokens ficam em **env vars** da Lambda (e no `terraform.tfvars`) |

---

## 🚀 Como usar

### Pré-requisito

- [Terraform CLI](https://developer.hashicorp.com/terraform/downloads) ≥ 1.5 instalado
- AWS CLI configurado com credenciais (ou `aws configure`)
- **Conta AWS ativa** (sem recursos existentes com os mesmos nomes)

### 1. Preparar as variáveis

```bash
cd terraform

# Cria o arquivo de secrets (NUNCA commite isso!)
cp terraform.tfvars.example terraform.tfvars

# Edite terraform.tfvars com os valores REAIS dos tokens
# Os tokens atuais estão em ../KEY-IAM
```

### 2. Inicializar

```bash
terraform init
```

### 3. Verificar o que vai ser criado

```bash
terraform plan
```

### 4. Criar tudo

```bash
terraform apply
```

Confirme com `yes`. Em ~60 segundos tudo estará online.

### 5. Deployar o código

Após o Terraform criar a Lambda (vazia), faça o deploy do código:

```bash
# Push na main dispara o GitHub Actions automaticamente
git push origin main

# OU manualmente, se não tiver CI:
# pip install --target package -r requirements.txt
# zip -r function.zip main.py package/
# aws lambda update-function-code --function-name dieta-telegram --zip-file fileb://function.zip
```

### 6. Configurar o webhook do Telegram

Pegue a URL do output e configure no Telegram:

```bash
terraform output function_url
# → https://xxxxxxxxxxxx.lambda-url.us-east-1.on.aws/
```

```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<FUNCTION_URL>"
```

---

## 🔐 Segurança

| Arquivo | Commit? | Conteúdo |
|---|---|---|
| `terraform.tfvars` | ❌ NUNCA | Tokens reais (Telegram, Gemini, LinkedIn) |
| `terraform.tfvars.example` | ✅ SIM | Template sem valores |
| `.gitignore` | ✅ SIM | Bloqueia `.tfvars`, state, `.terraform/` |
| `KEY-IAM` (raiz) | ❌ NUNCA | Todos os segredos |

---

## 🔄 Fluxo de deploy

```
[Você escreve código] → git push → GitHub Actions → zip + update-function-code → Lambda
                                                              ↑
[Infra nova?] → cd terraform → terraform apply → Cria Lambda + DDB + EventBridge
```

O Terraform e o CI/CD não brigam:
- **Terraform**: gerencia a infra (Lambda, IAM, DynamoDB, EventBridge)
- **GitHub Actions**: gerencia o código (zip do `main.py` + dependências)
- O `lifecycle { ignore_changes = [source_code_hash] }` garante que `terraform apply` não sobrescreva o código

---

## 🧪 Testando após recriar

```bash
# 1. Invocar a Lambda diretamente
aws lambda invoke --function-name dieta-telegram --region us-east-1 \
  --cli-binary-format raw-in-base64-out \
  --payload '{"source":"aws.events","detail-type":"Linkedin-gerar-draft"}' \
  /tmp/out.json

# 2. Disparar uma regra EventBridge
aws events put-events --region us-east-1 \
  --entries '[{"Source":"aws.events","DetailType":"Linkedin-gerar-draft","Detail":"{}"}]'

# 3. Testar o webhook (simula mensagem do Telegram)
curl -X POST "<FUNCTION_URL>" \
  -H "Content-Type: application/json" \
  -d '{"message":{"text":"/start","chat":{"id":"SEU_CHAT_ID"}}}'
```

---

## 📅 Manutenção

| Quando | O que fazer |
|---|---|
| Token LinkedIn vencer (~60 dias) | Refazer OAuth (PASSO_A_PASSO.md) → atualizar `terraform.tfvars` → `terraform apply` |
| Adicionar nova regra EventBridge | Editar `eventbridge.tf` → `terraform apply` |
| Mudar tabela DynamoDB | Editar `dynamodb.tf` → ⚠️ `prevent_destroy = true` protege a tabela |
| Nova Lambda | Criar em outro `.tf` (não misturar com `dieta-telegram`) |
| **EC2: disco mudou muito** | Criar nova AMI: `aws ec2 create-image --instance-id <id> --name "dieta-ec2-backup-YYYY-MM-DD" --no-reboot` → atualizar `ami` no `ec2.tf` |

---

## 🗂 Estrutura

```
terraform/
├── main.tf                  # Provider AWS (us-east-1)
├── variables.tf             # Secrets (sensitive)
├── terraform.tfvars.example # Template — copie para terraform.tfvars
├── lambda.tf                # Lambda + IAM Role + Policies + Function URL
├── dynamodb.tf              # Tabela Dieta_Historico_Dev
├── ec2.tf                   # EC2 t3.nano + Security Group + AMI
├── eventbridge.tf           # 12 regras cron + targets + Lambda permissions
├── outputs.tf               # Function URL, ARNs
├── .gitignore               # Bloqueia secrets e state
└── README.md                # Este arquivo
```

---

## ⚠️ Avisos

1. **State local**: o arquivo `terraform.tfstate` fica na máquina local. Se perdê-lo, o Terraform perde o vínculo com os recursos. Para produção, coloque o state no S3 com DynamoDB lock.

2. **`prevent_destroy`**: a tabela DynamoDB não será apagada por `terraform destroy` (proteção dos dados).

3. **Não rode `terraform destroy` em produção** — ele apaga TUDO (Lambda, regras, permissões). Só use em ambiente de teste.
