# diet-lambda

Bot de Telegram (dieta, treinos e tarefas) rodando em AWS Lambda.

## Deploy

O deploy é **automatizado via GitHub Actions**: todo push na branch `main` monta o `function.zip`
(em runner Linux, com as deps de `requirements.txt`) e atualiza a função Lambda `dieta-telegram`.

### Pré-requisitos (uma vez)

1. Criar secrets no repositório (`Settings → Secrets and variables → Actions`):
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
2. A chave deve ter permissão apenas para o deploy (ex: `lambda:UpdateFunctionCode` + `lambda:GetFunction`
   no ARN da função `dieta-telegram`).

### Fluxo manual (legado)

O pipeline substituiu o processo manual. Os artefatos locais `package/` e `function.zip`
foram descartáveis. Caso precise deployar na mão:

```bash
python -m pip install -r requirements.txt --target package  # ambiente LINUX/Git Bash
rm -f function.zip
cd package && zip -r ../function.zip . && cd ..
zip -g function.zip main.py
aws lambda update-function-code --function-name dieta-telegram --zip-file fileb://function.zip
```

> ⚠️ O `package/` local desta máquina contém binários **Windows** (CPython 3.14 `.pyd`),
> incompatíveis com o runtime Lambda python3.10. Não o use como base do zip — sempre re-instale
> as deps em ambiente Linux (o CI faz isso corretamente).

## Memória conversacional

As trocas com o bot são persistidas na tabela `Dieta_Historico_Dev` (partições `chat#YYYY-MM-DD`).
As últimas ~8 trocas entram no prompt do Gemini como `HISTÓRICO DA CONVERSA`.