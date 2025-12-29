"""
Serviço de IA com arquitetura Multi-Agente usando MCP Tools
Cada agente tem responsabilidade específica para reduzir alucinações
Refatorado para usar MCP Tools ao invés de prompts longos
"""
import pandas as pd
from typing import Dict, List, Optional, Any
import json
import re
from datetime import datetime
from sqlalchemy.orm import Session

from config.ai_config import AIConfigManager
from utils.validators import parse_currency, parse_date
from services.mcp_tools import MCPTools
from services.mcp_schema_generator import MCPSchemaGenerator


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
        self.mcp_tools = MCPTools(db_session=db)
        self.schema_generator = MCPSchemaGenerator()
    
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
    
    # ==================== AGENTE 1: DETECÇÃO DE TIPO (MCP) ====================
    
    def agent_detect_type(self, columns: List[str], data_sample: str) -> Dict[str, Any]:
        """
        Agente 1: Detecta o tipo de dado usando MCP Tool
        Responsabilidade: Identificar o tipo e incluir informações sobre estrutura destino
        """
        sample_text = data_sample or "Nenhum dado disponível"
        
        # Usa MCP Tool para gerar prompt estruturado
        prompt = self.mcp_tools.get_tool_prompt(
            "detect_data_type",
            columns=columns,
            data_sample=sample_text
        )
        
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
            
            # Adiciona informações sobre estrutura destino após detecção
            if 'suggested_type' in result:
                suggested_type = result['suggested_type']
                try:
                    # Adiciona informações sobre a estrutura destino
                    target_columns = self._get_target_columns(suggested_type)
                    column_specs = self._get_column_specifications(suggested_type)
                    required_columns = [col for col, spec in column_specs.items() if spec.get('required', False)]
                    
                    result['target_structure'] = {
                        'table_name': suggested_type,
                        'total_columns': len(target_columns),
                        'required_columns': required_columns,
                        'optional_columns': [col for col in target_columns if col not in required_columns],
                        'column_specs': {col: spec for col, spec in list(column_specs.items())[:5]}  # Primeiras 5 para referência
                    }
                except:
                    pass  # Se houver erro, continua sem essas informações
            
            return result
        except:
            return {'success': False, 'error': 'Erro ao parsear resposta', 'raw': response[:200]}
    
    # ==================== AGENTE 2: MAPEAMENTO E NORMALIZAÇÃO (MCP) ====================
    
    def agent_analyze_structure(self, df: pd.DataFrame, import_type: str) -> Dict[str, Any]:
        """
        Agente 2: Analisa estrutura origem (mantido para compatibilidade)
        Agora usa MCP tools internamente e inclui informações sobre estrutura destino
        """
        # Filtra linhas em branco e saldos antes de analisar estrutura
        df = self._filter_invalid_rows(df, import_type)
        
        columns = list(df.columns)
        sample_data = df.head(10).to_dict('records')
        sample_json = json.dumps(sample_data, indent=2, default=str, ensure_ascii=False)
        
        # Adiciona informações sobre estrutura destino para ajudar no mapeamento
        target_columns = self._get_target_columns(import_type)
        column_specs = self._get_column_specifications(import_type)
        table_structure = self._get_table_structure_description(import_type)
        required_columns = [col for col, spec in column_specs.items() if spec.get('required', False)]
        
        # Retorna estrutura compatível com código existente + informações destino
        return {
            'success': True,
            'columns_analysis': {col: {'type': 'unknown'} for col in columns},
            'sample_json': sample_json,
            'target_structure': {
                'import_type': import_type,
                'target_columns': target_columns,
                'required_columns': required_columns,
                'table_structure': table_structure,
                'column_specs': column_specs
            },
            'df': df  # Inclui DataFrame para extrair colunas se necessário
        }
    
    def agent_map_columns(self, structure_analysis: Dict, import_type: str) -> Dict[str, str]:
        """
        Agente 2: Mapeia colunas origem → destino usando MCP Tool
        Responsabilidade: Criar mapeamento preciso baseado no schema da tabela destino
        Foca apenas nas colunas necessárias para a tabela final
        """
        source_columns = list(structure_analysis.get('columns_analysis', {}).keys())
        
        # Tenta extrair colunas do sample_json se não encontrou
        if not source_columns and 'sample_json' in structure_analysis:
            try:
                sample_data = json.loads(structure_analysis['sample_json'])
                if sample_data and isinstance(sample_data, list) and len(sample_data) > 0:
                    source_columns = list(sample_data[0].keys())
            except:
                pass
        
        # Tenta obter do DataFrame se disponível (prioridade)
        if 'df' in structure_analysis:
            df_columns = list(structure_analysis['df'].columns)
            if df_columns:
                # Usa colunas do DataFrame como fonte principal
                source_columns = df_columns
            elif not source_columns:
                source_columns = df_columns
        
        # Se ainda não tem colunas, retorna vazio (será tratado no código chamador)
        if not source_columns:
            return {}
        
        columns_analysis = json.dumps(structure_analysis.get('columns_analysis', {}), indent=2, ensure_ascii=False)
        
        # Obtém informações da estrutura destino para incluir no prompt
        target_columns = self._get_target_columns(import_type)
        column_specs = self._get_column_specifications(import_type)
        required_columns = [col for col, spec in column_specs.items() if spec.get('required', False)]
        
        # Usa MCP Tool para gerar prompt estruturado com foco na estrutura destino
        prompt = self.mcp_tools.get_tool_prompt(
            "map_columns",
            import_type=import_type,
            source_columns=source_columns,
            columns_analysis=columns_analysis if columns_analysis != '{}' else None
        )
        
        # Adiciona informação adicional sobre colunas obrigatórias
        prompt += f"""

**INFORMAÇÃO ADICIONAL:**
- Colunas destino obrigatórias que DEVEM ser mapeadas: {', '.join(required_columns)}
- Total de colunas destino disponíveis: {len(target_columns)}
- Foque em mapear as obrigatórias primeiro, depois as opcionais se houver correspondência clara.
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
            mapping = result.get('mapping', {})
            
            # Validação: remove mapeamentos para colunas que não existem na tabela destino
            valid_mapping = {}
            for source_col, target_col in mapping.items():
                if target_col in target_columns:
                    valid_mapping[source_col] = target_col
                # Se target_col não existe, ignora o mapeamento
            
            # Verifica se mapeou as colunas obrigatórias
            mapped_targets = set(valid_mapping.values())
            missing_required = set(required_columns) - mapped_targets
            if missing_required:
                print(f"⚠️  Aviso: Colunas obrigatórias não mapeadas: {', '.join(missing_required)}")
            
            return valid_mapping
        except Exception as e:
            print(f"Erro ao processar mapeamento: {e}")
            return {}
    
    # ==================== AGENTE 3: NORMALIZAÇÃO (MCP) ====================
    
    def agent_extract_and_format(self, records: List[Dict], import_type: str, mapping: Dict[str, str]) -> List[Dict]:
        """
        Agente 4: Extrai e formata valores
        Responsabilidade: Apenas extrair valores de strings complexas e formatar
        """
        target_columns = self._get_target_columns(import_type)
        column_specs = self._get_column_specifications(import_type)
        table_structure = self._get_table_structure_description(import_type)
        
        # Processa em lotes de 10 registros usando MCP Tool
        all_normalized = []
        batch_size = 10
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            
            # Converte batch para JSON para uso nos prompts
            batch_json = json.dumps(batch, indent=2, default=str, ensure_ascii=False)
            
            # Usa MCP Tool para normalização
            prompt = self.mcp_tools.get_tool_prompt(
                "normalize_data",
                import_type=import_type,
                mapping=mapping,
                records=batch
            )
            
            if import_type == 'bank_statements':
                type_specific_instructions = """
**INSTRUÇÕES ESPECÍFICAS PARA EXTRATOS BANCÁRIOS:**
- Você receberá texto extraído de um extrato bancário. Identifique TODAS as transações e devolva cada linha no formato da classe BankStatement:
  {{
    "client_id": <id>,
    "bank_name": "<nome do banco>",
    "account": "<número da conta>",
    "date": "YYYY-MM-DD",
    "description": "<texto original completo>",
    "value": <float (negativo saídas / positivo entradas)>,
    "balance": <float com saldo após a transação>,
    "imported_at": "<timestamp ISO do momento da importação>",
    "group_id": null,
    "subgroup_id": null
  }}
- Converta valores monetários para float (ex: "R$ 1.400,00" → 1400.00). Use número NEGATIVO para saídas (compra, débito, Pix enviado, pagamento) e POSITIVO para entradas (Pix recebido, depósito, resgate).
- O campo `description` deve manter o texto ORIGINAL da transação.
- O campo `balance` deve refletir o saldo informado após a transação (não invente saldos).
- `date` deve ser a data presente na linha; converta para YYYY-MM-DD.
- `bank_name` e `account` devem ser extraídos do cabeçalho do extrato (ou linhas específicas de identificação).
- `imported_at` deve receber a data/hora atual (ISO 8601) fornecida pelo sistema que chamou este prompt.
"""
            elif import_type == 'transactions':
                type_specific_instructions = """
**INSTRUÇÕES ESPECÍFICAS PARA TRANSAÇÕES FINANCEIRAS:**
- Estruture cada transação no formato da classe Transaction:
  {{
    "date": "YYYY-MM-DD",
    "description": "<texto original completo da transação>",
    "value": <float (negativo para saídas, positivo para entradas)>,
    "type": "entrada" ou "saida" (baseado no sinal do valor e descrição),
    "category": "<categoria inferida do estabelecimento/descrição quando possível>",
    "account": "<conta relacionada se disponível>",
    "group_id": null,
    "subgroup_id": null
  }}
- Converta valores monetários para float (ex: "R$ 200,00" → 200.0). Use NEGATIVO para saídas (compras, pagamentos, débitos) e POSITIVO para entradas (recebimentos, créditos).
- O campo `type` deve ser "entrada" se valor positivo ou descrição indica recebimento, "saida" se valor negativo ou descrição indica pagamento/gasto.
- O campo `description` deve manter o texto ORIGINAL completo da transação.
- O campo `category` pode ser inferido do estabelecimento/descrição (ex: "Supermercado" → "alimentação", "Uber" → "transporte").
- `date` deve ser convertida para YYYY-MM-DD quando presente.
"""
            elif import_type == 'credit_card_invoices':
                type_specific_instructions = """
**INSTRUÇÕES ESPECÍFICAS PARA FATURA DE CARTÃO DE CRÉDITO:**
- Você receberá texto extraído de uma fatura de cartão de crédito. Identifique TODAS as transações e estruture no formato da classe CreditCardInvoice:
  {{
    "client_id": <id>,
    "transaction_date": "YYYY-MM-DD",
    "description": "<descrição completa da transação>",
    "value": <float (negativo para compras/pagamentos, positivo para créditos)>,
    "category": "<categoria da transação (ex: supermercado, transporte, entretenimento)>",
    "establishment": "<nome do estabelecimento extraído da descrição>",
    "installment_number": <número da parcela se houver>,
    "total_installments": <total de parcelas se houver>,
    "card_brand": "<marca do cartão, ex: Mastercard, Visa, Nubank>",
    "group_id": null,
    "subgroup_id": null,
    "created_at": "<data/hora atual da importação>"
  }}
- Converta valores monetários para float (ex: "R$ 143,33" → 143.33).
- Se for compra ou pagamento, o valor deve ser negativo.
- Se for crédito ou estorno, o valor deve ser positivo.
- Extrair corretamente número da parcela e total de parcelas (ex: "Parcela 2/6" → installment_number=2, total_installments=6).
- O campo "establishment" deve conter apenas o nome do estabelecimento (ex: "Tom Motos").
- O campo "description" deve conter a descrição original completa da transação.
- O campo "category" deve ser inferido a partir do estabelecimento (ex: Netflix → "entretenimento", Uber → "transporte").
- O campo "card_brand" deve ser preenchido com a bandeira do cartão informada na fatura (ex: Nubank Mastercard).
- O campo "created_at" deve ser preenchido com a data/hora atual da importação.
"""
            elif import_type == 'contracts':
                type_specific_instructions = """
**INSTRUÇÕES ESPECÍFICAS PARA CONTRATOS/EVENTOS:**
- Estruture cada contrato/evento no formato da classe Contract:
  {{
    "contract_start": "YYYY-MM-DD",
    "event_date": "YYYY-MM-DD",
    "service_value": <float (valor do serviço)>,
    "contractor_name": "<nome do contratante>",
    "displacement_value": <float (valor de deslocamento, se houver)>,
    "event_type": "<tipo de evento, ex: casamento, aniversário>",
    "service_sold": "<serviço vendido/prestado>",
    "guests_count": <número de convidados, se disponível>,
    "status": "<status do contrato, ex: confirmado, pendente>",
    "group_id": null,
    "subgroup_id": null
  }}
- Converta valores monetários para float (ex: "R$ 5.000,00" → 5000.0).
- `contract_start` é a data de início do contrato.
- `event_date` é a data do evento.
- `service_value` é o valor principal do serviço.
- `displacement_value` é o valor de deslocamento (opcional).
- `contractor_name` deve ser extraído do nome do cliente/contratante.
- `guests_count` deve ser um número inteiro quando disponível.
"""
            elif import_type == 'accounts_payable':
                type_specific_instructions = """
**INSTRUÇÕES ESPECÍFICAS PARA CONTAS A PAGAR:**
- Estruture cada conta a pagar no formato da classe AccountPayable:
  {{
    "account_name": "<nome do fornecedor/credor>",
    "due_date": "YYYY-MM-DD",
    "value": <float (valor a pagar)>,
    "cpf_cnpj": "<CPF ou CNPJ do fornecedor, se disponível>",
    "month_ref": "<mês de referência, ex: 01/2024>",
    "paid": <boolean (true se pago, false se não pago, null se não informado)>,
    "monthly_installments": <número inteiro de parcelas mensais>,
    "total_monthly_outflow": <float (total de saídas mensais)>,
    "installment_number": <número da parcela atual, se houver>,
    "group_id": null,
    "subgroup_id": null
  }}
- Converta valores monetários para float (ex: "R$ 500,00" → 500.0).
- `due_date` é a data de vencimento da conta.
- `paid` deve ser true se houver indicação de pagamento (pago, quitado, pago em), false se não pago, null se não informado.
- `installment_number` e `total_installments` devem ser extraídos quando houver parcelas (ex: "Parcela 2/12").
- `cpf_cnpj` deve ser limpo de formatação (apenas números).
"""
            elif import_type == 'accounts_receivable':
                type_specific_instructions = """
**INSTRUÇÕES ESPECÍFICAS PARA CONTAS A RECEBER:**
- Estruture cada conta a receber no formato da classe AccountReceivable:
  {{
    "account_name": "<nome do cliente/devedor>",
    "due_date": "YYYY-MM-DD",
    "value": <float (valor a receber)>,
    "cpf_cnpj": "<CPF ou CNPJ do cliente, se disponível>",
    "month_ref": "<mês de referência, ex: 01/2024>",
    "received": <boolean (true se recebido, false se não recebido, null se não informado)>,
    "event_date": "YYYY-MM-DD (data do evento relacionado, se houver)",
    "contract_value": <float (valor do contrato relacionado, se houver)>,
    "payment_method": "<método de pagamento, ex: Pix, Boleto, Cartão>",
    "monthly_installments": <número inteiro de parcelas mensais>,
    "total_expected_inflow": <float (total esperado de entradas mensais)>,
    "installment_number": <número da parcela atual, se houver>,
    "group_id": null,
    "subgroup_id": null
  }}
- Converta valores monetários para float (ex: "R$ 1.000,00" → 1000.0).
- `due_date` é a data de vencimento da conta.
- `received` deve ser true se houver indicação de recebimento (recebido, pago, creditado), false se não recebido, null se não informado.
- `event_date` é a data do evento relacionado (opcional).
- `payment_method` deve ser extraído quando disponível.
- `installment_number` e `total_installments` devem ser extraídos quando houver parcelas.
"""
            elif import_type == 'financial_investments':
                type_specific_instructions = """
**INSTRUÇÕES ESPECÍFICAS PARA APLICAÇÕES FINANCEIRAS:**
- Estruture cada operação financeira no formato da classe FinancialInvestment:
  {{
    "date": "YYYY-MM-DD",
    "investment_type": "<tipo de investimento, ex: CDB, Tesouro Direto>",
    "institution": "<instituição financeira, ex: Banco Inter, Nubank>",
    "operation_type": "<tipo de operação: aplicação, resgate, rendimento>",
    "applied_value": <float (valor aplicado, se aplicação)>,
    "redeemed_value": <float (valor resgatado, se resgate)>,
    "yield_value": <float (valor de rendimento, se rendimento)>,
    "balance": <float (saldo após a operação)>,
    "description": "<descrição da operação>",
    "group_id": null,
    "subgroup_id": null
  }}
- Converta valores monetários para float (ex: "R$ 10.000,00" → 10000.0).
- `operation_type` deve ser "aplicação" quando há aplicação, "resgate" quando há resgate, "rendimento" quando há rendimento.
- Preencha apenas os valores relevantes para o tipo de operação:
  - Aplicação: preencher `applied_value`
  - Resgate: preencher `redeemed_value`
  - Rendimento: preencher `yield_value`
- `balance` deve refletir o saldo após a operação (não invente saldos).
- `institution` deve ser extraído do nome da instituição financeira.
"""
            elif import_type == 'card_machine_statements':
                type_specific_instructions = """
**INSTRUÇÕES ESPECÍFICAS PARA EXTRATOS DE MÁQUINA DE CARTÃO:**
- Estruture cada transação no formato da classe CardMachineStatement:
  {{
    "date": "YYYY-MM-DD",
    "gross_value": <float (valor bruto da transação)>,
    "fee": <float (taxa cobrada)>,
    "net_value": <float (valor líquido recebido)>,
    "card_brand": "<bandeira do cartão, ex: Visa, Mastercard, Elo>",
    "transaction_type": "<tipo: débito ou crédito>",
    "description": "<descrição da transação, se disponível>",
    "group_id": null,
    "subgroup_id": null
  }}
- Converta valores monetários para float (ex: "R$ 1.500,00" → 1500.0).
- `gross_value` é o valor bruto da transação (antes da taxa).
- `fee` é a taxa cobrada pela operadora.
- `net_value` é o valor líquido recebido (gross_value - fee).
- `card_brand` deve ser extraído da bandeira informada (Visa, Mastercard, Elo, etc).
- `transaction_type` deve ser "débito" ou "crédito" conforme o tipo da transação.
"""
            elif import_type == 'inventory':
                type_specific_instructions = """
**INSTRUÇÕES ESPECÍFICAS PARA CONTROLE DE ESTOQUE:**
- Estruture cada movimento de estoque no formato da classe Inventory:
  {{
    "product_name": "<nome do produto>",
    "quantity": <float (quantidade movimentada)>,
    "unit_value": <float (valor unitário do produto)>,
    "movement_date": "YYYY-MM-DD",
    "movement_type": "<tipo de movimento: entrada ou saída>",
    "description": "<descrição do movimento, se disponível>",
    "group_id": null,
    "subgroup_id": null
  }}
- Converta valores monetários para float (ex: "R$ 25,50" → 25.5).
- `quantity` deve ser um número (float para permitir decimais, ex: 1.5 kg).
- `unit_value` é o valor unitário do produto.
- `movement_type` deve ser "entrada" quando há entrada de estoque, "saída" quando há saída de estoque.
- `movement_date` é a data do movimento (converta para YYYY-MM-DD).
- `product_name` deve ser o nome completo do produto.
"""
            
            # Inicializa prompt como None para garantir que sempre será definido
            prompt = None
            
            # Verifica se há prompt customizado
            custom_prompt = self._get_custom_prompt('agent4')
            if custom_prompt:
                # Substitui placeholders no prompt customizado
                try:
                    prompt = custom_prompt.format(
                        import_type=import_type,
                        table_structure=table_structure,
                        column_specs=json.dumps(column_specs, indent=2, ensure_ascii=False),
                        mapping=json.dumps(mapping, indent=2, ensure_ascii=False),
                        batch_size=len(batch),
                        batch_json=batch_json,
                        type_specific_instructions=type_specific_instructions
                    )
                except Exception as e:
                    # Se houver qualquer erro ao formatar, usa prompt padrão
                    prompt = None
            
            # Se não há prompt customizado ou houve erro, usa prompt padrão
            if prompt is None:
                prompt = self._get_default_prompt_template_agent4().format(
                    import_type=import_type,
                    table_structure=table_structure,
                    column_specs=json.dumps(column_specs, indent=2, ensure_ascii=False),
                    mapping=json.dumps(mapping, indent=2, ensure_ascii=False),
                    batch_size=len(batch),
                    batch_json=batch_json,
                    type_specific_instructions=type_specific_instructions
                )
            response, error = self._call_ai(prompt, max_tokens=4000)
            if error:
                # Se falhar, cria registros com todas as colunas destino (fallback)
                for record in batch:
                    normalized_record = {}
                    for col in target_columns:
                        # Tenta mapear do registro original
                        found = False
                        for orig_key, orig_value in record.items():
                            if orig_key in mapping and mapping[orig_key] == col:
                                normalized_record[col] = orig_value
                                found = True
                                break
                            # Tenta correspondência direta por nome
                            if orig_key.lower() == col.lower():
                                normalized_record[col] = orig_value
                                found = True
                                break
                        if not found:
                            normalized_record[col] = None
                    all_normalized.append(normalized_record)
                continue
            
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                elif '```' in response:
                    response = response.split('```')[1].split('```')[0]
                
                result = json.loads(response.strip())
                normalized = result.get('normalized_records', [])
                
                # GARANTE que todos os registros têm todas as colunas destino
                for idx, record in enumerate(normalized):
                    for col in target_columns:
                        if col not in record:
                            record[col] = None

                    # REGISTRO ORIGINAL PARA REFERÊNCIA
                    original = batch[idx] if idx < len(batch) else {}

                    # VALIDAÇÃO INTELIGENTE: Aceita transformações válidas
                    for col, value in record.items():
                        if value in [None, '', [], {}]:
                            continue
                        
                        # Verifica se há mapeamento para esta coluna
                        mapped_source = None
                        for orig_key, dest_key in mapping.items():
                            if dest_key == col:
                                mapped_source = orig_key
                                break
                        
                        # Se não há mapeamento, tenta correspondência por nome
                        if not mapped_source:
                            for orig_key in original.keys():
                                if orig_key.lower() == col.lower():
                                    mapped_source = orig_key
                                    break
                        
                        # Se encontrou mapeamento, valida o valor
                        if mapped_source and mapped_source in original:
                            orig_value = original[mapped_source]
                            
                            # Validação para datas (aceita formato YYYY-MM-DD mesmo que original seja diferente)
                            if col in ['date', 'transaction_date', 'due_date', 'event_date', 'contract_start', 'movement_date']:
                                if isinstance(value, str) and re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                                    # É uma data válida no formato YYYY-MM-DD
                                    # Verifica se há data no original (qualquer formato)
                                    if isinstance(orig_value, str):
                                        parsed_date = parse_date(orig_value)
                                        if parsed_date:
                                            # Data válida encontrada no original, aceita transformação
                                            continue
                                    # Se não encontrou data no original, mas o valor parece ser data válida, aceita
                                    continue
                            
                            # Validação para valores monetários (aceita float mesmo que original seja string formatada)
                            if col in ['value', 'balance', 'service_value', 'displacement_value', 'applied_value', 
                                      'redeemed_value', 'yield_value', 'gross_value', 'fee', 'net_value', 
                                      'unit_value', 'contract_value', 'total_monthly_outflow', 'total_expected_inflow']:
                                if isinstance(value, (int, float)):
                                    # É um número, verifica se corresponde ao valor monetário no original
                                    if isinstance(orig_value, str):
                                        parsed_currency = parse_currency(orig_value)
                                        if parsed_currency is not None:
                                            # Aceita se o valor extraído está próximo do original (tolerância de 0.01)
                                            if abs(value - parsed_currency) < 0.01 or abs(value) == abs(parsed_currency):
                                                continue
                                    elif isinstance(orig_value, (int, float)):
                                        # Aceita se valores são iguais ou próximos
                                        if abs(value - orig_value) < 0.01 or abs(value) == abs(orig_value):
                                            continue
                            
                            # Validação para descrições/textos (aceita se texto principal está presente)
                            if col in ['description', 'account_name', 'contractor_name', 'product_name', 
                                      'establishment', 'category', 'service_sold', 'event_type', 'status',
                                      'investment_type', 'institution', 'operation_type', 'card_brand',
                                      'transaction_type', 'payment_method', 'movement_type']:
                                if isinstance(value, str) and isinstance(orig_value, str):
                                    # Aceita se o texto principal (palavras significativas) está presente
                                    value_words = set(re.findall(r'\b\w{3,}\b', value.lower()))
                                    orig_words = set(re.findall(r'\b\w{3,}\b', orig_value.lower()))
                                    if value_words and len(value_words.intersection(orig_words)) >= min(2, len(value_words) * 0.5):
                                        continue
                            
                            # Validação para campos derivados (aceita se valor base existe)
                            if col == 'type' and import_type == 'transactions':
                                # Se há valor (value), aceita type derivado
                                if 'value' in record and record['value'] is not None:
                                    continue
                            
                            # Validação para booleanos (aceita se há indicação clara no original)
                            if col in ['paid', 'received']:
                                if isinstance(value, bool):
                                    orig_lower = str(orig_value).lower() if orig_value else ''
                                    if any(indicator in orig_lower for indicator in ['pago', 'quitado', 'recebido', 'creditado', 'sim', 'true', '1']):
                                        continue
                            
                            # Validação padrão: verifica correspondência literal ou parcial
                            if isinstance(orig_value, str) and isinstance(value, str):
                                cleaned_value = value.strip()
                                cleaned_orig = orig_value.strip()
                                if cleaned_value and (cleaned_value in cleaned_orig or cleaned_orig in cleaned_value):
                                    continue
                            elif orig_value == value:
                                continue
                        
                        # Se não passou em nenhuma validação, mas o valor não é None, mantém
                        # (pode ser um valor inferido válido que não está literalmente no original)
                        # Apenas remove se for claramente inválido
                        if isinstance(value, str) and len(value) > 1000:
                            # String muito longa, provavelmente erro
                            record[col] = None
                        elif isinstance(value, (int, float)) and abs(value) > 1e10:
                            # Número muito grande, provavelmente erro
                            record[col] = None
                
                all_normalized.extend(normalized)
            except:
                # Se falhar, cria registros com todas as colunas destino
                for record in batch:
                    normalized_record = {}
                    for col in target_columns:
                        # Tenta mapear do registro original
                        found = False
                        for orig_key, orig_value in record.items():
                            if orig_key in mapping and mapping[orig_key] == col:
                                normalized_record[col] = orig_value
                                found = True
                                break
                            # Tenta correspondência direta por nome
                            if orig_key.lower() == col.lower():
                                normalized_record[col] = orig_value
                                found = True
                                break
                        if not found:
                            normalized_record[col] = None
                    all_normalized.append(normalized_record)
        
        # VALIDAÇÃO FINAL: Garante que todos os registros têm todas as colunas destino
        for record in all_normalized:
            for col in target_columns:
                if col not in record:
                    record[col] = None
        
        return all_normalized
    
    # ==================== AGENTE 3: VALIDAÇÃO (MCP) ====================
    
    def agent_validate(self, records: List[Dict], import_type: str) -> Dict[str, Any]:
        """
        Agente 3: Valida dados finais usando MCP Tool
        Responsabilidade: Apenas validar estrutura e tipos, sem modificar
        """
        # Usa MCP Tool para validação
        prompt = self.mcp_tools.get_tool_prompt(
            "validate_data",
            import_type=import_type,
            normalized_records=records
        )
        
        response, error = self._call_ai(prompt, max_tokens=1000)
        if error:
            return {'success': True, 'is_valid': True, 'issues': [f'Erro na validação: {error}']}
        
        try:
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            result = json.loads(response.strip())
            # Garante que tem 'success' para compatibilidade
            if 'success' not in result:
                result['success'] = result.get('is_valid', True)
            return result
        except:
            return {'success': True, 'is_valid': True, 'issues': ['Erro ao parsear validação']}
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def _get_target_columns(self, import_type: str) -> List[str]:
        """Retorna colunas destino para tipo de importação usando schema generator"""
        try:
            return self.schema_generator.get_target_columns(import_type)
        except:
            # Fallback para método antigo
            specs = self._get_column_specifications(import_type)
            return list(specs.keys())
    
    def _get_column_specifications(self, import_type: str) -> Dict[str, Dict[str, Any]]:
        """Retorna especificações de colunas usando schema generator"""
        try:
            return self.schema_generator.get_column_specifications(import_type)
        except:
            # Fallback para especificações hardcoded (mantido para compatibilidade)
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
    
    def _get_table_structure_description(self, import_type: str) -> str:
        """Descrição textual resumida de cada tabela destino usando schema generator"""
        try:
            return self.schema_generator.get_table_structure_description(import_type)
        except:
            # Fallback para descrições hardcoded (mantido para compatibilidade)
            descriptions = {
            'transactions': (
                "Tabela transactions: (date, description, value, type, category, account, group_id, subgroup_id).\n"
                "- date: data da transação (YYYY-MM-DD)\n"
                "- value: número com sinal (entrada positivo, saída negativo)\n"
                "- type: \"entrada\" ou \"saida\"\n"
                "- description/category/account: textos"
            ),
            'bank_statements': (
                "Tabela bank_statements: (date, description, value, balance, account, bank_name, group_id, subgroup_id).\n"
                "Características: sempre tem saldo após cada linha."
            ),
            'contracts': (
                "Tabela contracts: (contract_start, event_date, service_value, displacement_value, event_type, "
                "service_sold, guests_count, contractor_name, payment_terms, status, group_id, subgroup_id)."
            ),
            'accounts_payable': (
                "Tabela accounts_payable: (account_name, due_date, value, cpf_cnpj, month_ref, paid, "
                "monthly_installments, total_monthly_outflow, installment_number, group_id, subgroup_id)."
            ),
            'accounts_receivable': (
                "Tabela accounts_receivable: (account_name, due_date, value, cpf_cnpj, month_ref, received, "
                "event_date, contract_value, payment_method, monthly_installments, installment_number, "
                "group_id, subgroup_id)."
            ),
            'financial_investments': (
                "Tabela financial_investments: (date, investment_type, institution, operation_type, applied_value, "
                "redeemed_value, yield_value, balance, description, group_id, subgroup_id)."
            ),
            'credit_card_invoices': (
                "Tabela credit_card_invoices: (transaction_date, description, value, category, establishment, "
                "installment_number, total_installments, card_brand, group_id, subgroup_id)."
            ),
            'card_machine_statements': (
                "Tabela card_machine_statements: (date, gross_value, fee, net_value, card_brand, transaction_type, "
                "description, group_id, subgroup_id)."
            ),
            'inventory': (
                "Tabela inventory: (product_name, quantity, unit_value, total_value, movement_date, movement_type, "
                "description, group_id, subgroup_id)."
            )
        }
        return descriptions.get(import_type, f"Tabela {import_type}: utilize colunas destino fornecidas no dicionário.")
    
    def _filter_invalid_rows(self, df: pd.DataFrame, import_type: str) -> pd.DataFrame:
        """
        Filtra linhas inválidas do DataFrame, removendo:
        - Linhas completamente em branco
        - Linhas que contêm saldo do dia (não são transações)
        """
        if df.empty:
            return df
        
        # Palavras-chave que indicam saldo (não transação)
        saldo_keywords = [
            'saldo', 'saldo do dia', 'saldo inicial', 'saldo final', 
            'saldo anterior', 'saldo atual', 'saldo anterior do dia',
            'saldo do período', 'saldo consolidado', 'balance'
        ]
        
        # Cria uma cópia para não modificar o original
        filtered_df = df.copy()
        rows_to_remove = []
        
        for idx, row in filtered_df.iterrows():
            should_remove = False
            
            # Verifica se a linha está completamente vazia
            is_empty = True
            for col in filtered_df.columns:
                value = row.get(col)
                if pd.notna(value) and value != '' and str(value).strip() != '':
                    is_empty = False
                    break
            
            if is_empty:
                rows_to_remove.append(idx)
                continue
            
            # Converte todos os valores da linha para string para busca
            row_text = ' '.join([
                str(row.get(col, '')).lower() 
                for col in filtered_df.columns 
                if pd.notna(row.get(col, ''))
            ])
            
            # Verifica se contém palavras-chave de saldo
            contains_saldo_keyword = any(
                keyword.lower() in row_text 
                for keyword in saldo_keywords
            )
            
            # Para bank_statements: verifica se tem apenas balance sem description ou value
            if import_type == 'bank_statements':
                has_balance = pd.notna(row.get('balance')) and str(row.get('balance', '')).strip() != ''
                has_description = pd.notna(row.get('description')) and str(row.get('description', '')).strip() != ''
                has_value = pd.notna(row.get('value')) and str(row.get('value', '')).strip() != ''
                
                if has_balance and not has_description and not has_value:
                    should_remove = True
            
            # Se contém palavra-chave de saldo e não parece ser uma transação válida
            if contains_saldo_keyword and not should_remove:
                has_transaction_fields = False
                if import_type == 'bank_statements':
                    has_transaction_fields = (
                        (pd.notna(row.get('description')) and str(row.get('description', '')).strip() != '') or
                        (pd.notna(row.get('value')) and str(row.get('value', '')).strip() != '')
                    )
                elif import_type == 'transactions':
                    has_transaction_fields = (
                        (pd.notna(row.get('description')) and str(row.get('description', '')).strip() != '') and
                        (pd.notna(row.get('value')) and str(row.get('value', '')).strip() != '')
                    )
                else:
                    has_transaction_fields = (
                        (pd.notna(row.get('description')) and str(row.get('description', '')).strip() != '') or
                        (pd.notna(row.get('value')) and str(row.get('value', '')).strip() != '')
                    )
                
                if not has_transaction_fields:
                    should_remove = True
            
            if should_remove:
                rows_to_remove.append(idx)
        
        # Remove linhas identificadas
        if rows_to_remove:
            filtered_df = filtered_df.drop(index=rows_to_remove).reset_index(drop=True)
        
        return filtered_df
    
    def is_available(self) -> bool:
        """Verifica se IA está disponível"""
        return self.config is not None and self.config.get('api_key')
    
    # ==================== MÉTODOS PARA GERENCIAR PROMPTS ====================
    
    def _get_custom_prompt(self, agent_name: str) -> Optional[str]:
        """Obtém prompt customizado do session_state se existir"""
        import streamlit as st
        prompts_key = 'ai_custom_prompts'
        if prompts_key in st.session_state:
            return st.session_state[prompts_key].get(agent_name)
        return None
    
    def _set_custom_prompt(self, agent_name: str, prompt: str):
        """Define prompt customizado no session_state"""
        import streamlit as st
        prompts_key = 'ai_custom_prompts'
        if prompts_key not in st.session_state:
            st.session_state[prompts_key] = {}
        st.session_state[prompts_key][agent_name] = prompt
    
    def _get_default_prompt_template_agent1(self) -> str:
        """Retorna o template completo do prompt padrão do Agente 1 (com placeholders)"""
        return """Você é um AGENTE ESPECIALIZADO em detectar tipos de dados financeiros.

SUA ÚNICA TAREFA: Identificar qual dos 9 tipos abaixo melhor descreve os dados.

**TIPOS DISPONÍVEIS:**
1. transactions - Movimentações financeiras gerais
2. bank_statements - Extratos bancários com saldo
3. credit_card_invoices - Faturas de cartão de crédito
4. contracts - Contratos/eventos
5. accounts_payable - Contas a pagar (fornecedor + vencimento)
6. accounts_receivable - Contas a receber (cliente + vencimento)
7. financial_investments - Aplicações/Resgates financeiros
8. card_machine_statements - Extratos de máquina de cartão (valor bruto/taxa/líquido)
9. inventory - Controle de estoque (produto + quantidade)

**DADOS PARA ANÁLISE:**
Colunas: {columns}
Amostra completa (primeiras 20 linhas em JSON estruturado):
{data_sample}

**INDICADORES FORTES E FRACOS (avalie nesta ordem):**
- transactions:
  - Fortes: valores sem saldo acumulado, descrições genéricas, ausência total de bandeira/cartão/parcela.
  - Fracos: termos como "estabelecimento" dentro da descrição, porém sem colunas específicas de cartão.
  - Negativos: presença de coluna de saldo, bandeira, parcela ou campos de contrato.
- bank_statements:
  - Fortes: coluna de saldo, saldo acumulado após cada valor, informações de agência/conta/banco.
  - Fracos: palavras como "saldo" no texto, mas sem coluna dedicada.
  - Negativos: colunas de bandeira/parcela ou de produto.
- credit_card_invoices:
  - Fortes: colunas explícitas de estabelecimento/bandeira/cartão/parcela, número da fatura/cartão, termos Visa/Mastercard.
  - Fracos: nomes de estabelecimentos em descrições sem demais campos; isso sozinho NÃO basta.
  - Negativos: presença de saldo final, fornecedor/cliente + vencimento, ou termos de aplicação financeira.
- contracts:
  - Fortes: contratante, data do evento, valor de serviço, campos de status/serviço vendido.
  - Fracos: descrições com "evento" sem campos estruturados.
  - Negativos: colunas de saldo ou cartão.
- accounts_payable:
  - Fortes: fornecedor/credor, data de vencimento, indicador "pago/quitado", número de parcelas.
  - Fracos: termos "pagar" nas descrições, sem vencimento.
  - Negativos: referências a cliente/recebimento.
- accounts_receivable:
  - Fortes: cliente/devedor, data de vencimento, valor previsto de entrada, vínculo com contrato/evento.
  - Fracos: descrições com "receber" sem campos claros.
  - Negativos: menção a fornecedor/credor.
- financial_investments:
  - Fortes: colunas "aplicado", "resgatado", "rendimento", tipo de investimento, instituição financeira.
  - Fracos: palavras "investimento" no texto apenas.
  - Negativos: saldo bancário ou parcelas.
- card_machine_statements:
  - Fortes: valor bruto, taxa/fee, valor líquido, bandeira da transação e tipo (débito/crédito).
  - Fracos: apenas referência a POS sem valores separados.
  - Negativos: saldo acumulado ou parcelas do cartão do cliente.
- inventory:
  - Fortes: produto, quantidade, valor unitário/total, tipo de movimento (entrada/saída).
  - Fracos: descrições de itens sem quantidade/valor.
  - Negativos: presença de datas de vencimento ou campos financeiros.

**EXEMPLOS RÁPIDOS:**
- Transactions (positivo): colunas date/description/value/type; nenhuma menção a bandeira, saldo ou parcelas.
- Credit-card invoices (positivo): date, establishment, value, card_brand, installment_number, total_installments.
- Bank statements vs card machine (negativo): extrato tem saldo acumulado; extrato de máquina tem colunas gross_value, fee, net_value (sem saldo).

**IMPORTANTE:** Sempre retorne o tipo mais provável, mas lembre-se de que o usuário humano confirmará manualmente antes de continuar o fluxo.

**RESPONDA APENAS JSON (sem markdown, sem texto):**
{{
    "suggested_type": "tipo_identificado",
    "confidence": 0.0-1.0,
    "reasoning": "explicação curta (1-2 frases)",
    "key_indicators": ["indicador1", "indicador2"]
}}
"""
    
    def _get_default_prompt_agent1(self, columns: List[str], data_sample: str) -> str:
        """Retorna o prompt padrão do Agente 1"""
        sample_text = data_sample or "Nenhum dado disponível"
        return self._get_default_prompt_template_agent1().format(
            columns=', '.join(columns),
            data_sample=sample_text
        )
    
    def _get_default_prompt_template_agent2(self) -> str:
        """Retorna o template completo do prompt padrão do Agente 2 (com placeholders)"""
        return """Você é um AGENTE ESPECIALIZADO em analisar estruturas de dados financeiros.

SUA TAREFA: Analisar os dados extraídos do arquivo (PDF, CSV, Excel, etc) e entender como mapear para a tabela destino do banco de dados.

**TIPO DE IMPORTAÇÃO:** {import_type}
**TABELA DESTINO NO BANCO DE DADOS:**
{table_structure}

**COLUNAS DESTINO ESPERADAS (COM ESPECIFICAÇÕES):**
{column_specs}

**COLUNAS ORIGEM DO ARQUIVO:**
{columns}

**AMOSTRA DE DADOS EXTRAÍDOS (10 primeiras linhas):**
{sample_json}

**TAREFA DETALHADA:**
1. Para cada coluna origem, identifique:
   - Tipo de dado (date, currency, text, number, boolean)
   - Formato específico (ex: "DD/MM/YYYY", "R$ 1.234,56")
   - Exemplos de valores reais
   - Qual coluna destino corresponde (baseado no nome e conteúdo)
   
2. Identifique padrões nos dados:
   - Como datas estão formatadas
   - Como valores monetários estão formatados
   - Como descrições estão estruturadas
   - Se há informações misturadas em uma única coluna

3. Identifique campos que podem ser inferidos:
   - Tipo de transação (entrada/saida) baseado em valores ou descrições
   - Categorias baseadas em descrições
   - Informações que podem ser extraídas de strings complexas

**RESPONDA APENAS JSON (sem markdown, sem texto):**
{{
    "columns_analysis": {{
        "nome_coluna_origem": {{
            "type": "date|currency|text|number|boolean",
            "format": "formato específico detectado",
            "maps_to": "coluna_destino ou null",
            "sample_values": ["valor1", "valor2", "valor3"],
            "extraction_notes": "notas sobre como extrair/processar este campo"
        }}
    }},
    "detected_dates": ["colunas que são datas"],
    "detected_currencies": ["colunas que são valores monetários"],
    "detected_texts": ["colunas que são textos/descrições"],
    "complex_fields": ["colunas que contêm múltiplas informações misturadas"],
    "inference_opportunities": ["campos que podem ser inferidos dos dados"]
}}
"""
    
    def _get_default_prompt_template_agent3(self) -> str:
        """Retorna o template completo do prompt padrão do Agente 3 (com placeholders)"""
        return """Você é um AGENTE ESPECIALIZADO em mapear colunas de arquivos (PDF, CSV, Excel) para tabelas de banco de dados.

SUA TAREFA: Criar mapeamento preciso de colunas origem → destino baseado na estrutura real da tabela destino.

**TIPO DE IMPORTAÇÃO:** {import_type}
**ESTRUTURA DA TABELA DESTINO NO BANCO:**
{table_structure}

**COLUNAS DESTINO COM ESPECIFICAÇÕES:**
{column_specs}

**ANÁLISE DETALHADA DAS COLUNAS ORIGEM:**
{columns_analysis}

**TAREFA:**
1. Para cada coluna destino, identifique qual coluna origem corresponde
2. Use correspondência por:
   - Nome similar (ex: "Data" → "date", "Valor" → "value")
   - Conteúdo similar (ex: coluna com datas → "date")
   - Contexto (ex: coluna com descrições → "description")
   
3. Para colunas destino sem correspondência direta:
   - Identifique se pode ser inferida de outras colunas
   - Identifique se pode ser extraída de campos complexos
   - Marque como null se não houver correspondência

**RESPONDA APENAS JSON (sem markdown, sem texto):**
{{
    "mapping": {{
        "coluna_origem": "coluna_destino"
    }},
    "unmapped_destinations": ["colunas destino sem mapeamento direto"],
    "unmapped_sources": ["colunas origem que não mapeiam para nenhuma destino"],
    "inferred_mappings": {{
        "coluna_destino": "como será inferida (ex: 'from description field')"
    }}
}}
"""
    
    def _get_default_prompt_template_agent4(self) -> str:
        """Retorna o template completo do prompt padrão do Agente 4 (com placeholders)"""
        return """Você é um AGENTE ESPECIALIZADO em extrair dados de arquivos (PDF, CSV, Excel, etc) e estruturá-los para inserção em banco de dados.

SUA TAREFA: Extrair dados dos registros origem e formatá-los EXATAMENTE conforme a estrutura da tabela destino do banco de dados.

**TIPO DE IMPORTAÇÃO:** {import_type}
**ESTRUTURA DA TABELA DESTINO NO BANCO DE DADOS:**
{table_structure}

**COLUNAS DESTINO (ESPECIFICAÇÕES COMPLETAS):**
{column_specs}

**MAPEAMENTO ORIGEM → DESTINO:**
{mapping}

**REGISTROS EXTRAÍDOS DO ARQUIVO (lote de {batch_size}):**
{batch_json}

**COMO USAR O MAPEAMENTO (MUITO IMPORTANTE):**
1. Para cada coluna destino, consulte o mapeamento para encontrar a coluna origem correspondente.
   - Exemplo: Se o mapeamento indica "Data" → "date", busque o valor na coluna "Data" do registro original.
   - Exemplo: Se o mapeamento indica "Valor" → "value", busque o valor na coluna "Valor" do registro original.

2. Extraia o valor da coluna origem mapeada:
   - Se a coluna origem existe no registro, use seu valor.
   - Se a coluna origem não existe, use `null`.

3. Transforme o valor conforme necessário:
   - Datas: converta para YYYY-MM-DD (ex: "15/01/2024" → "2024-01-15")
   - Valores monetários: converta para float (ex: "R$ 200,00" → 200.0)
   - Textos: mantenha o texto original ou limpe apenas ruídos
   - Booleanos: converta para true/false quando houver indicação clara

4. Exemplo prático:
   - Registro original: {{"Data": "15/01/2024", "Descrição": "Compra no mercado", "Valor": "R$ 200,00"}}
   - Mapeamento: {{"Data": "date", "Descrição": "description", "Valor": "value"}}
   - Resultado: {{"date": "2024-01-15", "description": "Compra no mercado", "value": 200.0}}

{type_specific_instructions}
**REGRAS CRÍTICAS DE EXTRAÇÃO (VALE PARA TODAS AS COLUNAS):**

1. **NUNCA INVENTE DADOS:**
   - Cada campo destino deve ser preenchido APENAS com valores realmente presentes no registro origem.
   - Se o valor não existe ou não é identificável de forma objetiva, use `null`.
   - Não infira datas, valores ou textos baseados em suposições. Somente converta o que de fato está na linha.

2. **USE O MAPEAMENTO:**
   - Sempre consulte o mapeamento para saber qual coluna origem corresponde a cada coluna destino.
   - Se o mapeamento indica "coluna_origem" → "coluna_destino", busque o valor em "coluna_origem" do registro original.
   - Se a coluna origem não existe no registro, use `null`.

3. **VALORES MONETÁRIOS:**
   - Extrair apenas o valor da transação correspondente ao campo destino.
   - Nunca reutilizar saldo como valor da transação.
   - Converter formatos brasileiros (1.234,56) e remover símbolos mantendo o número original.
   - Exemplo: "Pix enviado: R$ 200,00 R$ 6.901,09" → extraia apenas 200.0 (valor da transação, não o saldo).

4. **DATAS:**
   - Apenas converter para formato YYYY-MM-DD quando houver uma data explícita.
   - Se não existir data na linha ou na coluna correspondente, deixe `null`.
   - Aceite qualquer formato de data comum (DD/MM/YYYY, DD-MM-YYYY, etc) e converta para YYYY-MM-DD.

5. **TEXTOS/DESCRIÇÕES:**
   - Remover apenas ruídos (datas/valores) mantendo o texto real.
   - Não criar descrições novas; use o texto verificado no registro.
   - Mantenha o texto original sempre que possível.

6. **TIPOS ESPECÍFICOS:**
   - `type` (transactions): derive apenas se o sinal do valor existir; caso contrário, deixe `null`.
   - Campos booleanos (paid/received): somente use true/false se houver indicação clara; senão `null`.
   - Bandeiras/cartões/parcelas: apenas quando o registro tiver essas informações.

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

**REGRAS FINAIS CRÍTICAS:**

1. **ESTRUTURA OBRIGATÓRIA:**
   - Cada registro DEVE ter todas as colunas destino (mesmo que `null`).
   - Use exatamente os nomes de coluna fornecidos.

2. **TIPOS DE DADOS:**
   - Valores numéricos: números (float/int).
   - Datas: strings no formato YYYY-MM-DD (apenas quando existem).
   - Textos: cópias limpas do texto original (sem inventar).
   - Booleanos/inteiros: somente quando presentes; caso contrário `null`.

3. **ORIGEM GARANTIDA:**
   - Antes de enviar o JSON, confirme que cada valor encontra correspondência direta no registro origem. Se houver dúvida, substitua por `null`.

4. **EXEMPLO DE ESTRUTURA CORRETA:**
   Retorne JSON contendo TODOS os campos destino (mesmo que `null`), com valores exatamente derivados do registro original.
"""
    
    def _get_default_prompt_template_agent5(self) -> str:
        """Retorna o template completo do prompt padrão do Agente 5 (com placeholders)"""
        return """Você é um AGENTE ESPECIALIZADO em validar dados.

SUA ÚNICA TAREFA: Validar se os dados estão corretamente estruturados.

**TIPO:** {import_type}
**COLUNAS ESPERADAS:** {target_columns}

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
    "type_errors": ["coluna1 deve ser date mas recebeu string", "coluna2 deve ser float mas recebeu string"]
}}
"""
    
    def get_prompts(self) -> Dict[str, Dict]:
        """Retorna todos os prompts (customizados ou padrão) dos agentes MCP"""
        import streamlit as st
        
        # Retorna estrutura com informações dos prompts alinhada com MCP Tools
        prompts = {
            'agent1': {
                'name': 'Agente 1: Detecção de Tipo',
                'description': 'Identifica o tipo de dado financeiro usando MCP Tool detect_data_type',
                'mcp_tool': 'detect_data_type',
                'custom': self._get_custom_prompt('agent1'),
                'has_placeholders': True,
                'placeholders': ['columns', 'data_sample'],
                'default_template': self._get_default_prompt_template_agent1(),
                'note': 'Este agente usa o MCP Tool detect_data_type. O prompt customizado será aplicado ao tool.'
            },
            'agent2': {
                'name': 'Agente 2: Mapeamento e Normalização',
                'description': 'Mapeia colunas e normaliza dados usando MCP Tools map_columns e normalize_data',
                'mcp_tools': ['map_columns', 'normalize_data'],
                'custom': self._get_custom_prompt('agent2'),
                'has_placeholders': True,
                'placeholders': ['import_type', 'table_structure', 'column_specs', 'source_columns', 'mapping', 'records'],
                'default_template': 'Usa MCP Tools internamente. Prompts são gerados automaticamente baseados nos schemas.',
                'note': 'Este agente combina map_columns (mapeamento) e normalize_data (normalização). Schemas são gerados automaticamente pelo MCPSchemaGenerator.'
            },
            'agent3': {
                'name': 'Agente 3: Validação',
                'description': 'Valida dados normalizados usando MCP Tool validate_data',
                'mcp_tool': 'validate_data',
                'custom': self._get_custom_prompt('agent3'),
                'has_placeholders': True,
                'placeholders': ['import_type', 'normalized_records'],
                'default_template': self._get_default_prompt_template_agent5(),
                'note': 'Este agente usa o MCP Tool validate_data. O prompt customizado será aplicado ao tool.'
            }
        }
        return prompts
    
    def get_mcp_tools_info(self) -> Dict[str, Dict]:
        """Retorna informações sobre os MCP Tools disponíveis"""
        tools_info = {}
        for tool_def in self.mcp_tools.get_all_tool_definitions():
            tool_name = tool_def.get('name')
            tools_info[tool_name] = {
                'name': tool_def.get('name'),
                'description': tool_def.get('description'),
                'input_schema': tool_def.get('inputSchema', {}),
                'required_params': tool_def.get('inputSchema', {}).get('required', [])
            }
        return tools_info
    
    def update_prompt(self, agent_name: str, new_prompt: str):
        """Atualiza prompt customizado de um agente"""
        self._set_custom_prompt(agent_name, new_prompt)
    
    def reset_prompt(self, agent_name: str):
        """Remove prompt customizado, voltando ao padrão"""
        import streamlit as st
        prompts_key = 'ai_custom_prompts'
        if prompts_key in st.session_state and agent_name in st.session_state[prompts_key]:
            del st.session_state[prompts_key][agent_name]
    
    def get_prompt_template(self, agent_name: str) -> str:
        """Retorna o template do prompt padrão de um agente (sem placeholders preenchidos)"""
        templates = {
            'agent1': """Você é um AGENTE ESPECIALIZADO em detectar tipos de dados financeiros.

SUA ÚNICA TAREFA: Identificar qual dos 9 tipos abaixo melhor descreve os dados.

**TIPOS DISPONÍVEIS:**
1. transactions - Movimentações financeiras gerais
2. bank_statements - Extratos bancários com saldo
3. credit_card_invoices - Faturas de cartão de crédito
4. contracts - Contratos/eventos
5. accounts_payable - Contas a pagar (fornecedor + vencimento)
6. accounts_receivable - Contas a receber (cliente + vencimento)
7. financial_investments - Aplicações/Resgates financeiros
8. card_machine_statements - Extratos de máquina de cartão (valor bruto/taxa/líquido)
9. inventory - Controle de estoque (produto + quantidade)

**DADOS PARA ANÁLISE:**
Colunas: {columns}
Amostra completa (primeiras 20 linhas em JSON estruturado):
{data_sample}

**INDICADORES FORTES E FRACOS (avalie nesta ordem):**
[...indicadores detalhados...]

**RESPONDA APENAS JSON (sem markdown, sem texto):**
{{
    "suggested_type": "tipo_identificado",
    "confidence": 0.0-1.0,
    "reasoning": "explicação curta (1-2 frases)",
    "key_indicators": ["indicador1", "indicador2"]
}}""",
            'agent2': """Você é um AGENTE ESPECIALIZADO em analisar estruturas de dados financeiros.

SUA TAREFA: Analisar os dados extraídos do arquivo (PDF, CSV, Excel, etc) e entender como mapear para a tabela destino do banco de dados.

**TIPO DE IMPORTAÇÃO:** {import_type}
**TABELA DESTINO NO BANCO DE DADOS:**
{table_structure}

**COLUNAS DESTINO ESPERADAS (COM ESPECIFICAÇÕES):**
{column_specs}

**COLUNAS ORIGEM DO ARQUIVO:**
{columns}

**AMOSTRA DE DADOS EXTRAÍDOS (10 primeiras linhas):**
{sample_json}

[...resto do prompt...]""",
            'agent3': """Você é um AGENTE ESPECIALIZADO em mapear colunas de arquivos (PDF, CSV, Excel) para tabelas de banco de dados.

SUA TAREFA: Criar mapeamento preciso de colunas origem → destino baseado na estrutura real da tabela destino.

**TIPO DE IMPORTAÇÃO:** {import_type}
**ESTRUTURA DA TABELA DESTINO NO BANCO:**
{table_structure}

**COLUNAS DESTINO COM ESPECIFICAÇÕES:**
{column_specs}

**ANÁLISE DETALHADA DAS COLUNAS ORIGEM:**
{columns_analysis}

[...resto do prompt...]""",
            'agent4': """Você é um AGENTE ESPECIALIZADO em extrair dados de arquivos (PDF, CSV, Excel, etc) e estruturá-los para inserção em banco de dados.

SUA TAREFA: Extrair dados dos registros origem e formatá-los EXATAMENTE conforme a estrutura da tabela destino do banco de dados.

**TIPO DE IMPORTAÇÃO:** {import_type}
**ESTRUTURA DA TABELA DESTINO NO BANCO DE DADOS:**
{table_structure}

**COLUNAS DESTINO (ESPECIFICAÇÕES COMPLETAS):**
{column_specs}

**MAPEAMENTO ORIGEM → DESTINO:**
{mapping}

**REGISTROS EXTRAÍDOS DO ARQUIVO (lote de {batch_size}):**
{batch_json}

{type_specific_instructions}

[...resto do prompt...]""",
            'agent5': """Você é um AGENTE ESPECIALIZADO em validar dados.

SUA ÚNICA TAREFA: Validar se os dados estão corretamente estruturados.

**TIPO:** {import_type}
**COLUNAS ESPERADAS:** {target_columns}

**AMOSTRA DE DADOS (5 registros):**
{sample_json}

[...resto do prompt...]"""
        }
        return templates.get(agent_name, "")

