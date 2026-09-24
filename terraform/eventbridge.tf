# ════════════════════════════════════════════════════════════════════════════════
# EventBridge Rules + Targets + Lambda Invoke Permissions
# ════════════════════════════════════════════════════════════════════════════════
#
# 12 regras cron que disparam a Lambda dieta-telegram.
# Cada regra tem:
#   1. aws_cloudwatch_event_rule     → regra com cron expression
#   2. aws_cloudwatch_event_target    → target = Lambda
#   3. aws_lambda_permission           → permite EventBridge invocar a Lambda
#
# As refeições disparam sem Input (o detail-type padrão vazio cai no
# processar_horario, que checa o horário da refeição), as demais mandam
# um Input JSON com detail-type específico.

locals {
  lambda_arn = aws_lambda_function.dieta_telegram.arn

  # Refeições: disparam sem Input, o Lambda detecta pelo horário
  refeicoes = {
    "dieta-0800" = "cron(0 11 * * ? *)"   # 08:00 BRT
    "dieta-0900" = "cron(0 12 * * ? *)"   # 09:00 BRT
    "dieta-1130" = "cron(30 14 * * ? *)"  # 11:30 BRT
    "dieta-1600" = "cron(0 19 * * ? *)"   # 16:00 BRT
    "dieta-2000" = "cron(0 23 * * ? *)"   # 20:00 BRT
    "dieta-2201" = "cron(1 1 * * ? *)"    # 22:01 BRT
  }

  # Tarefas + LinkedIn + Treinos: disparam com Input JSON (detail-type)
  eventos_com_input = {
    "dieta-lembrete-tarefas-10h" = {
      cron   = "cron(0 13 * * ? *)"
      detail = "lembrete_tarefas"
      desc   = "Lembrete de tarefas às 10h (Brasília)"
    }
    "dieta-lembrete-tarefas-14h" = {
      cron   = "cron(0 17 * * ? *)"
      detail = "lembrete_tarefas"
      desc   = "Lembrete de tarefas às 14h (Brasília)"
    }
    "dieta-linkedin-cron" = {
      cron   = "cron(0 13 ? * TUE,THU *)"
      detail = "Linkedin-gerar-draft"
      desc   = "Gera 3 rascunhos de post do LinkedIn via bot (10h BRT = 13h UTC)"
    }
    "treino-segunda-motivacao" = {
      cron   = "cron(0 10 ? * MON *)"
      detail = "segunda-motivacao"
      desc   = null
    }
    "treino-domingo-revisao" = {
      cron   = "cron(0 23 ? * SUN *)"
      detail = "domingo-revisao"
      desc   = null
    }
  }
}

# ── Refeições (sem Input) ───────────────────────────────────────────────────────

resource "aws_cloudwatch_event_rule" "refeicao" {
  for_each = local.refeicoes

  name                = each.key
  schedule_expression = each.value
  state               = "ENABLED"
}

resource "aws_cloudwatch_event_target" "refeicao" {
  for_each = local.refeicoes

  rule = aws_cloudwatch_event_rule.refeicao[each.key].name
  arn  = local.lambda_arn
}

resource "aws_lambda_permission" "refeicao" {
  for_each = local.refeicoes

  statement_id  = each.key
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dieta_telegram.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.refeicao[each.key].arn
}

# ── Eventos com Input JSON ─────────────────────────────────────────────────────

resource "aws_cloudwatch_event_rule" "com_input" {
  for_each = local.eventos_com_input

  name                = each.key
  schedule_expression = each.value.cron
  description         = each.value.desc
  state               = "ENABLED"
}

resource "aws_cloudwatch_event_target" "com_input" {
  for_each = local.eventos_com_input

  rule = aws_cloudwatch_event_rule.com_input[each.key].name
  arn  = local.lambda_arn
  input = jsonencode({
    source     = "aws.events"
    "detail-type" = each.value.detail
    detail     = {}
  })
}

resource "aws_lambda_permission" "com_input" {
  for_each = local.eventos_com_input

  statement_id  = "eventbridge-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dieta_telegram.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.com_input[each.key].arn
}

# ── Regra dieta-1050 (selênio) — sem targets (mantida por integridade) ──────────

resource "aws_cloudwatch_event_rule" "dieta_1050" {
  name                = "dieta-1050"
  schedule_expression = "cron(50 13 * * ? *)"
  state               = "ENABLED"
}

# ── Lambda permission: Function URL público ─────────────────────────────────────

resource "aws_lambda_permission" "function_url_public" {
  statement_id  = "FunctionURLAllowPublicAccess"
  action        = "lambda:InvokeFunctionUrl"
  function_name = aws_lambda_function.dieta_telegram.function_name
  principal     = "*"
  condition {
    test     = "StringEquals"
    variable = "lambda:FunctionUrlAuthType"
    values   = ["NONE"]
  }
}

resource "aws_lambda_permission" "function_url_invoke" {
  statement_id  = "FunctionURLAllowInvokeAction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dieta_telegram.function_name
  principal     = "*"
  condition {
    test     = "Bool"
    variable = "lambda:InvokedViaFunctionUrl"
    values   = ["true"]
  }
}
