# Documentação dos Prompts de IA

Este documento explica como os prompts são construídos e usados para análise de arquivos.

## Estrutura dos Prompts

### 1. Prompt de Validação de Tipo de Dados

**Localização:** `services/ai_service.py` → `_create_prompt_for_validation()`

**Objetivo:** Validar se o tipo de dados escolhido pelo usuário faz sentido para o arquivo importado.

**Estrutura do Prompt:**
```
Você é um assistente especializado em análise de dados financeiros e contábeis.

Analise o arquivo fornecido e determine se o tipo de dados selecionado pelo usuário faz sentido.

**Tipo de dados selecionado:** [nome do tipo]
**Campos esperados para este tipo:** [lista de campos]

**Colunas do arquivo:**
[lista de colunas]

**Amostra dos dados (primeiras 5 linhas):**
[JSON com amostra dos dados]

**Tarefa:**
1. Analise se as colunas e dados do arquivo são compatíveis com o tipo
2. Identifique quais campos esperados estão presentes ou podem ser mapeados
3. Avalie a compatibilidade geral

**Responda em formato JSON:**
{
    "compatible": true/false,
    "confidence": 0.0-1.0,
    "reason": "explicação breve",
    "missing_fields": ["lista de campos faltantes"],
    "found_fields": ["lista de campos encontrados"],
    "suggestions": "sugestões de melhoria ou tipo alternativo"
}
```

**Resposta Esperada:**
- JSON válido com os campos especificados
- `compatible`: boolean indicando se o tipo faz sentido
- `confidence`: float entre 0.0 e 1.0 indicando confiança na análise
- `reason`: explicação textual breve
- `missing_fields`: lista de campos obrigatórios que não foram encontrados
- `found_fields`: lista de campos que foram identificados
- `suggestions`: sugestões de melhoria ou tipo alternativo

### 2. Prompt de Mapeamento de Colunas

**Localização:** `services/ai_service.py` → `_create_prompt_for_mapping()`

**Objetivo:** Sugerir o melhor mapeamento das colunas do arquivo para os campos do sistema.

**Estrutura do Prompt:**
```
Você é um assistente especializado em mapeamento de colunas de dados financeiros.

Analise o arquivo e sugira o melhor mapeamento das colunas do arquivo para os campos do sistema.

**Tipo de dados:** [nome do tipo]
**Campos esperados pelo sistema:** [lista de campos]

**Colunas do arquivo:**
[lista de colunas]

**Amostra dos dados (primeiras 5 linhas):**
[JSON com amostra dos dados]

**Tarefa:**
Para cada coluna do arquivo, sugira o campo do sistema mais apropriado.
Se uma coluna não se encaixa em nenhum campo, sugira "ignore".

**Responda em formato JSON:**
{
    "mapping": {
        "nome_coluna_arquivo": "campo_sistema",
        ...
    },
    "confidence": 0.0-1.0,
    "notes": "observações sobre o mapeamento"
}
```

**Resposta Esperada:**
- JSON válido com mapeamento de colunas
- `mapping`: dicionário onde chave é nome da coluna do arquivo e valor é campo do sistema ou "ignore"
- `confidence`: float entre 0.0 e 1.0 indicando confiança no mapeamento
- `notes`: observações sobre o mapeamento

## Preparação dos Dados

### Amostra de Dados

**Método:** `_prepare_data_sample()`

A amostra inclui:
- Lista de todas as colunas do arquivo
- Total de linhas
- Primeiras 5 linhas de dados em formato JSON

**Formato:**
```json
{
  "columns": ["coluna1", "coluna2", ...],
  "total_rows": 100,
  "sample_data": [
    {"coluna1": "valor1", "coluna2": "valor2", ...},
    ...
  ]
}
```

## System Message

Para provedores que suportam system message (OpenAI, Ollama, Groq):
```
Você é um assistente especializado em análise de dados financeiros e contábeis. 
Sempre responda APENAS em formato JSON válido, sem texto adicional antes ou depois do JSON.
```

Para Gemini (que não suporta system message separado):
O system message é incluído no início do prompt do usuário.

## Tratamento de Respostas

### Limpeza de Resposta

1. Remove blocos de código markdown (```json ... ```)
2. Remove espaços em branco no início e fim
3. Tenta parsear como JSON

### Tratamento de Erros

- Se a resposta não for JSON válido, retorna erro com a resposta bruta
- Se houver erro na API, retorna mensagem de erro específica
- Se biblioteca não estiver instalada, retorna instrução de instalação

## Tipos de Dados Suportados

### Transações Financeiras
- Campos esperados: `date`, `description`, `value`
- Campos opcionais: `type`, `category`, `account`

### Extratos Bancários
- Campos esperados: `date`, `description`, `value`
- Campos opcionais: `balance`, `account`

### Contratos/Eventos
- Campos esperados: `contract_start`, `event_date`, `service_value`, `contractor_name`
- Campos opcionais: `displacement_value`, `event_type`, `service_sold`, `guests_count`, `payment_terms`, `status`

### Contas a Pagar
- Campos esperados: `account_name`, `due_date`, `value`
- Campos opcionais: `cpf_cnpj`, `paid`

### Contas a Receber
- Campos esperados: `account_name`, `due_date`, `value`
- Campos opcionais: `cpf_cnpj`, `received`

## Exemplo de Uso

1. Usuário faz upload de arquivo CSV
2. Usuário seleciona tipo: "Transações Financeiras"
3. Sistema prepara amostra dos dados
4. Sistema cria prompt de validação
5. IA analisa e retorna JSON com validação
6. Sistema exibe resultado na interface
7. Se válido, sistema cria prompt de mapeamento
8. IA sugere mapeamento de colunas
9. Sistema exibe sugestões para o usuário revisar

## Troubleshooting

### Erro: "Biblioteca não instalada"
**Solução:** Instale a biblioteca necessária:
- OpenAI/Ollama: `pip install openai`
- Gemini: `pip install google-generativeai`
- Groq: `pip install groq`

### Erro: "Chave de API não configurada"
**Solução:** Configure a chave de API na página de Administração → Configuração de IA

### Erro: "Resposta não pôde ser parseada"
**Causa:** A IA retornou texto que não é JSON válido
**Solução:** Verifique a resposta bruta no expander de debug

### Erro: "Sem resposta da API"
**Causa:** A API não retornou resposta ou houve timeout
**Solução:** Verifique conexão com internet e configuração da API


