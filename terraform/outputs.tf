# ════════════════════════════════════════════════════════════════════════════════
# Outputs — valores úteis após terraform apply
# ════════════════════════════════════════════════════════════════════════════════

output "function_url" {
  description = "URL pública do webhook (Telegram aponta pra cá)"
  value       = aws_lambda_function_url.dieta_telegram.function_url
}

output "function_arn" {
  description = "ARN da Lambda"
  value       = aws_lambda_function.dieta_telegram.arn
}

output "function_name" {
  description = "Nome da Lambda"
  value       = aws_lambda_function.dieta_telegram.function_name
}

output "dynamodb_table" {
  description = "Nome da tabela DynamoDB"
  value       = aws_dynamodb_table.dieta_historico.name
}

output "eventbridge_rules" {
  description = "Regras EventBridge criadas (nomes)"
  value = concat(
    [for k, _ in local.refeicoes : k],
    [for k, _ in local.eventos_com_input : k],
    ["dieta-1050"]
  )
}
