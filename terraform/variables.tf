# ─── Secrets (sensíveis — NUNCA commitados) ──────────────────────────────────

variable "telegram_bot_token" {
  description = "Token do bot do Telegram (@BotFather)"
  type        = string
  sensitive   = true
}

# Sem default de propósito: se faltar no terraform.tfvars, o `apply` FALHA em vez
# de subir a Lambda com a validação do webhook desligada. Falhar alto é o certo aqui.
variable "telegram_secret_token" {
  description = "secret_token do setWebhook, conferido no header X-Telegram-Bot-Api-Secret-Token"
  type        = string
  sensitive   = true
}

variable "telegram_chat_id" {
  description = "Chat ID do Telegram para envio de mensagens"
  type        = string
}

variable "gemini_api_key" {
  description = "Chave da API Gemini (Google AI Studio)"
  type        = string
  sensitive   = true
}

variable "linkedin_access_token" {
  description = "Token OAuth 2.0 do LinkedIn (60 dias, w_member_social + openid + profile)"
  type        = string
  sensitive   = true
}

variable "linkedin_author_urn" {
  description = "URN do autor no LinkedIn (ex: urn:li:person:XXXXX)"
  type        = string
}

# ─── Opcionais ──────────────────────────────────────────────────────────────────

variable "dynamodb_table_name" {
  description = "Nome da tabela DynamoDB"
  type        = string
  default     = "Dieta_Historico_Dev"
}

variable "openai_api_key" {
  description = "Chave da OpenAI (fallback — opcional)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openai_model" {
  description = "Modelo OpenAI para fallback"
  type        = string
  default     = "gpt-4o-mini"
}
