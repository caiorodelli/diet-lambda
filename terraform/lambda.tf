# ════════════════════════════════════════════════════════════════════════════════
# IAM Role + Lambda Function + Function URL
# ════════════════════════════════════════════════════════════════════════════════

# ── IAM Role ────────────────────────────────────────────────────────────────────

resource "aws_iam_role" "lambda_role" {
  name = "dieta-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

# Managed policies (AWS)
resource "aws_iam_role_policy_attachment" "lambda_basic_exec" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_ec2_full" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
}

# Inline: DynamoDB — Dieta_Historico_Dev
resource "aws_iam_role_policy" "dynamodb_dieta_dev" {
  name = "dieta-dev-dynamodb-policy"
  role = aws_iam_role.lambda_role.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ]
      Resource = "arn:aws:dynamodb:*:*:table/${var.dynamodb_table_name}"
    }]
  })
}

# Inline: DynamoDB — Pontual_Tarefas_Dev (comandos de VM + tarefas)
resource "aws_iam_role_policy" "dynamodb_pontual" {
  name = "botpontual-dynamodb"
  role = aws_iam_role.lambda_role.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:Query",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:GetItem"
      ]
      Resource = "arn:aws:dynamodb:us-east-1:*:table/Pontual_Tarefas_Dev"
    }]
  })
}

# ── Lambda Function ─────────────────────────────────────────────────────────────

resource "aws_lambda_function" "dieta_telegram" {
  function_name = "dieta-telegram"
  role          = aws_iam_role.lambda_role.arn
  runtime       = "python3.10"
  handler       = "main.lambda_handler"
  # 256 MB porque o copiloto manda imagem em base64 para o Gemini, e Python +
  # boto3 já ocupam ~70 MB dos 128 anteriores. 60 s porque download do arquivo +
  # chamada do modelo + upload não cabem em 30 — e um estouro de timeout no meio
  # do publish faz o Telegram reenviar o update e o post sair duas vezes.
  memory_size   = 256
  timeout       = 60
  architectures = ["x86_64"]

  # Placeholder: o código real é deployado via GitHub Actions (CI/CD).
  # O Terraform NÃO gerencia o código — apenas a infra.
  filename         = data.archive_file.placeholder.output_path
  source_code_hash = data.archive_file.placeholder.output_base64sha256

  environment {
    variables = {
      TELEGRAM_BOT_TOKEN      = var.telegram_bot_token
      TELEGRAM_CHAT_ID        = var.telegram_chat_id
      # Sem esta linha, um `apply` REMOVE a variável da Lambda — ela existe na
      # função mas não aqui. Com ela vazia, a checagem do secret_token do webhook
      # deixa de rodar e a Function URL fica aberta para qualquer um.
      TELEGRAM_SECRET_TOKEN   = var.telegram_secret_token
      DYNAMODB_TABLE_NAME     = var.dynamodb_table_name
      GEMINI_API_KEY          = var.gemini_api_key
      LINKEDIN_ACCESS_TOKEN   = var.linkedin_access_token
      LINKEDIN_AUTHOR_URN     = var.linkedin_author_urn
      OPENAI_API_KEY          = var.openai_api_key
      OPENAI_MODEL            = var.openai_model
    }
  }

  # Impede que 'terraform apply' futuro sobrescreva o código deployado pelo CI/CD
  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }
}

# Placeholder zip (1 linha de Python — o código real vem do CI/CD)
data "archive_file" "placeholder" {
  type        = "zip"
  output_path = "${path.module}/.placeholder.zip"

  source {
    content  = "# placeholder — deployed via GitHub Actions"
    filename = "main.py"
  }
}

# ── Function URL (webhook público do Telegram) ──────────────────────────────────

resource "aws_lambda_function_url" "dieta_telegram" {
  function_name      = aws_lambda_function.dieta_telegram.function_name
  authorization_type = "NONE"
  invoke_mode        = "BUFFERED"
}
