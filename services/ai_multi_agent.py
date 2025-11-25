"""
Serviço de IA com arquitetura Multi-Agente
Cada agente tem responsabilidade específica para reduzir alucinações
"""
import pandas as pd
from typing import Dict, List, Optional, Any
import json
from sqlalchemy.orm import Session

from config.ai_config import AIConfigManager


class AIMultiAgent:
    """
    Arquitetura Multi-Agente para processamento de dados
    Cada agente tem uma responsabilidade específica e bem definida
    """
    
    DATA_TYPES = {
        'transactions': 'Transações Financeiras',
        'bank_statements': 'Extratos Bancários',
        'contracts': 'Contratos/Eventos',
        'accounts_payable': 'Contas a Pagar',
        'accounts_receivable': 'Contas a Receber',
        'financial_investments': 'Extratos de Aplicações Financeiras',
        'credit_card_invoices': 'Faturas de Cartão de Crédito',
        'card_machine_statements': 'Extratos de Máquina de Cartão',
        'inventory': 'Controle de Estoque'
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.config = AIConfigManager.get_config_dict(db)
        self._client = None
    
    def _get_client(self):
        """Obtém cliente de IA"""
        if self._client:
            return self._client, None
        
        if not self.config:
            return None, "IA não configurada"
        
        provider = self.config.get('provider', 'openai')
        
        try:
            if provider == 'openai':
                from openai import OpenAI
                api_key = self.config.get('api_key')
                if not api_key:
                    return None, "API key não configurada"
                self._client = OpenAI(api_key=api_key)
                return self._client, None
            elif provider == 'gemini':
                import google.generativeai as genai
                api_key = self.config.get('api_key')
                if not api_key:
                    return None, "API key não configurada"
                genai.configure(api_key=api_key)
                self._client = genai.GenerativeModel('gemini-1.5-flash')
                return self._client, None
            else:
                return None, f"Provedor '{provider}' não suportado"
        except Exception as e:
            return None, f"Erro ao inicializar cliente: {str(e)}"
    
    def _call_ai(self, prompt: str, max_tokens: int = 4000) -> tuple:
        """Chama API de IA"""
        client, error = self._get_client()
        if error:
            return None, error
        
        provider = self.config.get('provider', 'openai')
        model = self.config.get('model', 'gpt-4o-mini')
        
        try:
            if provider == 'openai':
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,  # Baixa temperatura para reduzir alucinações
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content, None
            elif provider == 'gemini':
                response = client.generate_content(prompt)
                return response.text if response.text else None, None
            else:
                return None, f"Provedor '{provider}' não suportado"
        except Exception as e:
            return None, f"Erro ao chamar API: {str(e)}"
    
    # ==================== AGENTE 1: DETECÇÃO DE TIPO ====================
    
    def agent_detect_type(self, columns: List[str], data_sample: str) -> Dict[str, Any]:
        """
        Agente 1: Detecta o tipo de dado
        Responsabilidade: Apenas identificar o tipo, nada mais
        """
        prompt = f"""Você é um AGENTE ESPECIALIZADO em detectar tipos de dados financeiros.

SUA ÚNICA TAREFA: Identificar qual dos 9 tipos abaixo melhor descreve os dados.

**TIPOS DISPONÍVEIS:**
1. transactions - Movimentações financeiras gerais (sem saldo, sem cartão)
2. bank_statements - Extratos bancários (SEMPRE tem saldo após transação)
3. credit_card_invoices - Faturas de cartão (SEMPRE tem estabelecimento/bandeira/parcela)
4. contracts - Contratos/eventos (tem contratante, data evento, valor serviço)
5. accounts_payable - Contas a pagar (tem fornecedor, vencimento)
6. accounts_receivable - Contas a receber (tem cliente, vencimento)
7. financial_investments - Investimentos (tem tipo investimento, aplicação/resgate)
8. card_machine_statements - Máquina cartão (tem valor bruto, taxa, líquido)
9. inventory - Estoque (tem produto, quantidade, valor unitário)

**DADOS PARA ANÁLISE:**
Colunas: {', '.join(columns)}
Amostra (5 primeiras linhas): {data_sample[:500]}

**REGRAS CRÍTICAS:**
- Se tiver "saldo" → bank_statements
- Se tiver "estabelecimento" OU "bandeira" OU "parcela" → credit_card_invoices
- Se tiver "contratante" OU "evento" → contracts
- Se tiver "fornecedor" OU "credor" → accounts_payable
- Se tiver "cliente" OU "devedor" → accounts_receivable
- Se tiver "investimento" OU "aplicação" → financial_investments
- Se tiver "valor bruto" E "taxa" → card_machine_statements
- Se tiver "produto" E "quantidade" → inventory
- Caso contrário → transactions

**RESPONDA APENAS JSON (sem markdown, sem texto):**
{{
    "suggested_type": "tipo_identificado",
    "confidence": 0.0-1.0,
    "reasoning": "explicação curta (1-2 frases)",
    "key_indicators": ["indicador1", "indicador2"]
}}
"""
        response, error = self._call_ai(prompt, max_tokens=1000)
        if error:
            return {'success': False, 'error': error}
        
        try:
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            result = json.loads(response.strip())
            result['success'] = True
            return result
        except:
            return {'success': False, 'error': 'Erro ao parsear resposta', 'raw': response[:200]}
    
    # ==================== AGENTE 2: ANÁLISE ESTRUTURAL ====================
    
    def agent_analyze_structure(self, df: pd.DataFrame, import_type: str) -> Dict[str, Any]:
        """
        Agente 2: Analisa estrutura origem
        Responsabilidade: Apenas analisar colunas e tipos de dados origem
        """
        columns = list(df.columns)
        sample_data = df.head(5).to_dict('records')
        sample_json = json.dumps(sample_data, indent=2, default=str, ensure_ascii=False)
        
        target_columns = self._get_target_columns(import_type)
        
        prompt = f"""Você é um AGENTE ESPECIALIZADO em analisar estruturas de dados.

SUA ÚNICA TAREFA: Analisar as colunas origem e identificar tipos de dados.

**TIPO DE IMPORTAÇÃO:** {import_type}
**COLUNAS DESTINO ESPERADAS:** {', '.join(target_columns)}

**COLUNAS ORIGEM:**
{', '.join(columns)}

**AMOSTRA DE DADOS (5 linhas):**
{sample_json}

**TAREFA:**
Para cada coluna origem, identifique:
1. Tipo de dado (date, currency, text, number, boolean)
2. Formato (se aplicável)
3. Qual coluna destino corresponde (se houver correspondência clara)

**RESPONDA APENAS JSON (sem markdown, sem texto):**
{{
    "columns_analysis": {{
        "nome_coluna_origem": {{
            "type": "date|currency|text|number|boolean",
            "format": "formato se aplicável",
            "maps_to": "coluna_destino ou null",
            "sample_values": ["valor1", "valor2"]
        }}
    }},
    "detected_dates": ["colunas que são datas"],
    "detected_currencies": ["colunas que são valores monetários"],
    "detected_texts": ["colunas que são textos/descrições"]
}}
"""
        response, error = self._call_ai(prompt, max_tokens=2000)
        if error:
            return {'success': False, 'error': error}
        
        try:
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            result = json.loads(response.strip())
            result['success'] = True
            return result
        except:
            return {'success': False, 'error': 'Erro ao parsear resposta', 'raw': response[:200]}
    
    # ==================== AGENTE 3: MAPEAMENTO DE COLUNAS ====================
    
    def agent_map_columns(self, structure_analysis: Dict, import_type: str) -> Dict[str, str]:
        """
        Agente 3: Mapeia colunas origem → destino
        Responsabilidade: Apenas criar mapeamento, sem processar dados
        """
        target_columns = self._get_target_columns(import_type)
        columns_analysis = structure_analysis.get('columns_analysis', {})
        
        prompt = f"""Você é um AGENTE ESPECIALIZADO em mapear colunas.

SUA ÚNICA TAREFA: Criar mapeamento de colunas origem → destino.

**TIPO:** {import_type}
**COLUNAS DESTINO:** {', '.join(target_columns)}

**ANÁLISE DAS COLUNAS ORIGEM:**
{json.dumps(columns_analysis, indent=2, ensure_ascii=False)}

**TAREFA:**
Para cada coluna destino, identifique qual coluna origem corresponde.
Use a análise fornecida e correspondência por nome/conteúdo.

**RESPONDA APENAS JSON (sem markdown, sem texto):**
{{
    "mapping": {{
        "coluna_origem": "coluna_destino"
    }},
    "unmapped_destinations": ["colunas destino sem mapeamento"],
    "unmapped_sources": ["colunas origem sem mapeamento"]
}}
"""
        response, error = self._call_ai(prompt, max_tokens=1500)
        if error:
            return {}
        
        try:
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            result = json.loads(response.strip())
            return result.get('mapping', {})
        except:
            return {}
    
    # ==================== AGENTE 4: EXTRAÇÃO E FORMATAÇÃO ====================
    
    def agent_extract_and_format(self, records: List[Dict], import_type: str, mapping: Dict[str, str]) -> List[Dict]:
        """
        Agente 4: Extrai e formata valores
        Responsabilidade: Apenas extrair valores de strings complexas e formatar
        """
        target_columns = self._get_target_columns(import_type)
        column_specs = self._get_column_specifications(import_type)
        
        # Processa em lotes de 10 registros
        all_normalized = []
        batch_size = 10
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            batch_json = json.dumps(batch, indent=2, default=str, ensure_ascii=False)
            
            prompt = f"""Você é um AGENTE ESPECIALIZADO em extrair e formatar valores de dados financeiros.

SUA ÚNICA TAREFA: Extrair valores de strings complexas e formatar para o padrão correto.

**TIPO:** {import_type}
**COLUNAS DESTINO:**
{json.dumps(column_specs, indent=2, ensure_ascii=False)}

**MAPEAMENTO:**
{json.dumps(mapping, indent=2, ensure_ascii=False)}

**REGISTROS PARA PROCESSAR (lote de {len(batch)}):**
{batch_json}

**REGRAS CRÍTICAS DE EXTRAÇÃO:**

1. **VALORES MONETÁRIOS:**
   - Se valor está em string complexa (ex: "Pix enviado: R$ 200,00 R$ 6.901,09"):
     * Extraia APENAS o valor da TRANSAÇÃO (geralmente o primeiro valor após descrição)
     * IGNORE saldos ou valores secundários
     * Converta para número (float): "R$ 200,00" → 200.00
   - Remova símbolos: R$, $, BRL
   - Converta formato brasileiro: "1.234,56" → 1234.56
   - Se negativo: "-R$ 200,00" → -200.00

2. **DATAS:**
   - Converta QUALQUER formato para YYYY-MM-DD
   - Exemplos: "15/01/2024" → "2024-01-15", "01-15-2024" → "2024-01-15"

3. **DESCRIÇÕES:**
   - Remova valores monetários e datas da descrição
   - Mantenha apenas texto descritivo
   - Exemplo: "Pix enviado: R$ 200,00" → "Pix enviado"

4. **TIPO (entrada/saida):**
   - Se valor negativo OU descrição indica saída → "saida"
   - Se valor positivo OU descrição indica entrada → "entrada"

**RESPONDA APENAS JSON (sem markdown, sem texto):**
{{
    "normalized_records": [
        {{
            "date": "2024-01-15",
            "description": "texto limpo",
            "value": 200.00,
            ...
        }}
    ]
}}

**IMPORTANTE:**
- Cada registro DEVE ter TODAS as colunas destino
- Valores numéricos devem ser números (float/int), NUNCA strings
- Datas devem ser strings no formato YYYY-MM-DD
- Use null para campos opcionais não encontrados
"""
            response, error = self._call_ai(prompt, max_tokens=4000)
            if error:
                # Se falhar, mantém registros originais
                all_normalized.extend(batch)
                continue
            
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                elif '```' in response:
                    response = response.split('```')[1].split('```')[0]
                
                result = json.loads(response.strip())
                normalized = result.get('normalized_records', batch)
                all_normalized.extend(normalized)
            except:
                # Se falhar, mantém registros originais
                all_normalized.extend(batch)
        
        return all_normalized
    
    # ==================== AGENTE 5: VALIDAÇÃO ====================
    
    def agent_validate(self, records: List[Dict], import_type: str) -> Dict[str, Any]:
        """
        Agente 5: Valida dados finais
        Responsabilidade: Apenas validar estrutura e tipos, sem modificar
        """
        target_columns = self._get_target_columns(import_type)
        sample = records[:5] if len(records) > 5 else records
        sample_json = json.dumps(sample, indent=2, default=str, ensure_ascii=False)
        
        prompt = f"""Você é um AGENTE ESPECIALIZADO em validar dados.

SUA ÚNICA TAREFA: Validar se os dados estão corretamente estruturados.

**TIPO:** {import_type}
**COLUNAS ESPERADAS:** {', '.join(target_columns)}

**AMOSTRA DE DADOS (5 registros):**
{sample_json}

**TAREFA:**
1. Verifique se todos os registros têm todas as colunas esperadas
2. Verifique se tipos de dados estão corretos (datas como string YYYY-MM-DD, valores como números)
3. Identifique problemas ou inconsistências

**RESPONDA APENAS JSON (sem markdown, sem texto):**
{{
    "is_valid": true/false,
    "issues": ["problema1", "problema2"],
    "records_with_issues": [0, 2, 5],
    "missing_columns": ["coluna1", "coluna2"],
    "type_errors": ["campo X deveria ser número mas é string"]
}}
"""
        response, error = self._call_ai(prompt, max_tokens=1000)
        if error:
            return {'is_valid': True, 'issues': [f'Erro na validação: {error}']}
        
        try:
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            result = json.loads(response.strip())
            return result
        except:
            return {'is_valid': True, 'issues': ['Erro ao parsear validação']}
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def _get_target_columns(self, import_type: str) -> List[str]:
        """Retorna colunas destino para tipo de importação"""
        specs = self._get_column_specifications(import_type)
        return list(specs.keys())
    
    def _get_column_specifications(self, import_type: str) -> Dict[str, Dict[str, Any]]:
        """Retorna especificações de colunas"""
        specs = {
            'transactions': {
                'date': {'type': 'date', 'format': 'YYYY-MM-DD', 'required': True},
                'description': {'type': 'string', 'required': True},
                'value': {'type': 'float', 'required': True},
                'type': {'type': 'string', 'required': True, 'values': ['entrada', 'saida']},
                'category': {'type': 'string', 'required': False},
                'account': {'type': 'string', 'required': False},
                'group_id': {'type': 'integer', 'required': False},
                'subgroup_id': {'type': 'integer', 'required': False}
            },
            'bank_statements': {
                'date': {'type': 'date', 'format': 'YYYY-MM-DD', 'required': True},
                'description': {'type': 'string', 'required': True},
                'value': {'type': 'float', 'required': True},
                'balance': {'type': 'float', 'required': False},
                'account': {'type': 'string', 'required': False},
                'bank_name': {'type': 'string', 'required': False},
                'group_id': {'type': 'integer', 'required': False},
                'subgroup_id': {'type': 'integer', 'required': False}
            },
            'contracts': {
                'contract_start': {'type': 'date', 'format': 'YYYY-MM-DD', 'required': True},
                'event_date': {'type': 'date', 'format': 'YYYY-MM-DD', 'required': True},
                'service_value': {'type': 'float', 'required': True},
                'contractor_name': {'type': 'string', 'required': True},
                'displacement_value': {'type': 'float', 'required': False},
                'event_type': {'type': 'string', 'required': False},
                'service_sold': {'type': 'string', 'required': False},
                'guests_count': {'type': 'integer', 'required': False},
                'status': {'type': 'string', 'required': False},
                'group_id': {'type': 'integer', 'required': False},
                'subgroup_id': {'type': 'integer', 'required': False}
            },
            'accounts_payable': {
                'account_name': {'type': 'string', 'required': True},
                'due_date': {'type': 'date', 'format': 'YYYY-MM-DD', 'required': True},
                'value': {'type': 'float', 'required': True},
                'cpf_cnpj': {'type': 'string', 'required': False},
                'month_ref': {'type': 'string', 'required': False},
                'paid': {'type': 'boolean', 'required': False},
                'monthly_installments': {'type': 'integer', 'required': False},
                'total_monthly_outflow': {'type': 'float', 'required': False},
                'installment_number': {'type': 'integer', 'required': False},
                'group_id': {'type': 'integer', 'required': False},
                'subgroup_id': {'type': 'integer', 'required': False}
            },
            'accounts_receivable': {
                'account_name': {'type': 'string', 'required': True},
                'due_date': {'type': 'date', 'format': 'YYYY-MM-DD', 'required': True},
                'value': {'type': 'float', 'required': True},
                'cpf_cnpj': {'type': 'string', 'required': False},
                'month_ref': {'type': 'string', 'required': False},
                'received': {'type': 'boolean', 'required': False},
                'event_date': {'type': 'date', 'format': 'YYYY-MM-DD', 'required': False},
                'contract_value': {'type': 'float', 'required': False},
                'payment_method': {'type': 'string', 'required': False},
                'monthly_installments': {'type': 'integer', 'required': False},
                'total_expected_inflow': {'type': 'float', 'required': False},
                'installment_number': {'type': 'integer', 'required': False},
                'group_id': {'type': 'integer', 'required': False},
                'subgroup_id': {'type': 'integer', 'required': False}
            },
            'financial_investments': {
                'date': {'type': 'date', 'format': 'YYYY-MM-DD', 'required': True},
                'investment_type': {'type': 'string', 'required': False},
                'institution': {'type': 'string', 'required': False},
                'operation_type': {'type': 'string', 'required': False},
                'applied_value': {'type': 'float', 'required': False},
                'redeemed_value': {'type': 'float', 'required': False},
                'yield_value': {'type': 'float', 'required': False},
                'balance': {'type': 'float', 'required': False},
                'description': {'type': 'string', 'required': False},
                'group_id': {'type': 'integer', 'required': False},
                'subgroup_id': {'type': 'integer', 'required': False}
            },
            'credit_card_invoices': {
                'transaction_date': {'type': 'date', 'format': 'YYYY-MM-DD', 'required': True},
                'description': {'type': 'string', 'required': True},
                'value': {'type': 'float', 'required': True},
                'category': {'type': 'string', 'required': False},
                'establishment': {'type': 'string', 'required': False},
                'installment_number': {'type': 'integer', 'required': False},
                'total_installments': {'type': 'integer', 'required': False},
                'card_brand': {'type': 'string', 'required': False},
                'group_id': {'type': 'integer', 'required': False},
                'subgroup_id': {'type': 'integer', 'required': False}
            },
            'card_machine_statements': {
                'date': {'type': 'date', 'format': 'YYYY-MM-DD', 'required': True},
                'gross_value': {'type': 'float', 'required': True},
                'fee': {'type': 'float', 'required': False},
                'net_value': {'type': 'float', 'required': True},
                'card_brand': {'type': 'string', 'required': False},
                'transaction_type': {'type': 'string', 'required': False},
                'description': {'type': 'string', 'required': False},
                'group_id': {'type': 'integer', 'required': False},
                'subgroup_id': {'type': 'integer', 'required': False}
            },
            'inventory': {
                'product_name': {'type': 'string', 'required': True},
                'quantity': {'type': 'float', 'required': True},
                'unit_value': {'type': 'float', 'required': True},
                'movement_date': {'type': 'date', 'format': 'YYYY-MM-DD', 'required': False},
                'movement_type': {'type': 'string', 'required': False},
                'description': {'type': 'string', 'required': False},
                'group_id': {'type': 'integer', 'required': False},
                'subgroup_id': {'type': 'integer', 'required': False}
            }
        }
        return specs.get(import_type, {})
    
    def is_available(self) -> bool:
        """Verifica se IA está disponível"""
        return self.config is not None and self.config.get('api_key')

