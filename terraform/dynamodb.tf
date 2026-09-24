# ════════════════════════════════════════════════════════════════════════════════
# DynamoDB — Dieta_Historico_Dev
# ════════════════════════════════════════════════════════════════════════════════

resource "aws_dynamodb_table" "dieta_historico" {
  name = var.dynamodb_table_name

  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "data"
  range_key = "timestamp"

  attribute {
    name = "data"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  # Evita recriar a tabela em mudanças acidentais (dados são vivos)
  lifecycle {
    prevent_destroy = true
  }
}
