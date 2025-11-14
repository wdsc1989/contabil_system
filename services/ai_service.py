"""
Serviço de IA para análise inteligente de arquivos
"""
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import json
import os
import re
from sqlalchemy.orm import Session

from config.ai_config import AIConfigManager


class AIService:
    """
    Serviço para análise de arquivos usando IA
    """
    
    # Tipos de dados suportados
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
    
    # Campos esperados por tipo
    EXPECTED_FIELDS = {
        'transactions': ['date', 'description', 'value'],
        'bank_statements': ['date', 'description', 'value'],
        'contracts': ['contract_start', 'event_date', 'service_value', 'contractor_name'],
        'accounts_payable': ['account_name', 'due_date', 'value'],
        'accounts_receivable': ['account_name', 'due_date', 'value'],
        'financial_investments': ['date', 'investment_type', 'applied_value', 'redeemed_value'],
        'credit_card_invoices': ['transaction_date', 'description', 'value'],
        'card_machine_statements': ['date', 'gross_value', 'net_value', 'transaction_type'],
        'inventory': ['product_name', 'quantity', 'unit_value', 'movement_date', 'movement_type']
    }

    def __init__(self, db: Session):
        """
        Inicializa o serviço de IA com configuração do banco
        """
        self.db = db
        self.config = AIConfigManager.get_config_dict(db)
        self._client = None

    def _reload_config(self):
        """
        Recarrega configuração do banco de dados
        """
        self.config = AIConfigManager.get_config_dict(self.db)
        self._client = None  # Reseta cliente para recarregar com nova config

    def is_available(self) -> bool:
        """
        Verifica se o serviço de IA está disponível e configurado
        """
        return AIConfigManager.is_configured(self.db) and self.config is not None

    def _get_client(self):
        """
        Obtém cliente da API de IA baseado no provedor configurado
        Retorna (client, error_message) onde error_message é None se sucesso
        """
        if not self.config:
            return None, "Configuração de IA não encontrada"
        
        if self._client is not None:
            return self._client, None
        
        provider = self.config['provider']
        api_key = self.config.get('api_key', '').strip()
        
        # Valida chave de API (exceto Ollama)
        if provider != 'ollama' and not api_key:
            return None, f"Chave de API não configurada para {provider}"
        
        try:
            if provider == 'openai':
                try:
                    from openai import OpenAI
                except ImportError:
                    return None, "Biblioteca 'openai' não instalada. Execute: pip install openai"
                self._client = OpenAI(api_key=api_key)
                return self._client, None
                
            elif provider == 'gemini':
                try:
                    import google.generativeai as genai
                except ImportError:
                    return None, "Biblioteca 'google-generativeai' não instalada. Execute: pip install google-generativeai"
                genai.configure(api_key=api_key)
                model_name = self.config.get('model', 'gemini-1.5-flash')
                self._client = genai.GenerativeModel(model_name)
                return self._client, None
                
            elif provider == 'ollama':
                try:
                    from openai import OpenAI
                except ImportError:
                    return None, "Biblioteca 'openai' não instalada. Execute: pip install openai"
                base_url = self.config.get('base_url', 'http://localhost:11434/v1')
                self._client = OpenAI(
                    api_key='ollama',  # Ollama não requer chave real
                    base_url=base_url
                )
                return self._client, None
                
            elif provider == 'groq':
                try:
                    from groq import Groq
                except ImportError:
                    return None, "Biblioteca 'groq' não instalada. Execute: pip install groq"
                self._client = Groq(api_key=api_key)
                return self._client, None
            else:
                return None, f"Provedor '{provider}' não suportado"
                
        except Exception as e:
            error_msg = f"Erro ao inicializar cliente de IA ({provider}): {str(e)}"
            print(error_msg)
            return None, error_msg

    def _prepare_pdf_context(self, pdf_data: Dict[str, Any], import_type: str) -> str:
        """
        Prepara contexto adicional de PDF para incluir nos prompts da IA
        """
        context_parts = []
        
        # Metadados do PDF
        metadata = pdf_data.get('metadata', {})
        if metadata.get('title'):
            context_parts.append(f"- Título do PDF: {metadata['title']}")
        if metadata.get('num_pages'):
            context_parts.append(f"- Número de páginas: {metadata['num_pages']}")
        
        # Cabeçalhos e rodapés
        headers_footers = pdf_data.get('headers_footers', {})
        if headers_footers.get('header_text'):
            header_preview = headers_footers['header_text'][:500]  # Limita tamanho
            context_parts.append(f"- Cabeçalho do documento:\n{header_preview}")
        
        if headers_footers.get('bank_name'):
            context_parts.append(f"- Nome do banco detectado: {headers_footers['bank_name']}")
        
        if headers_footers.get('account_info'):
            context_parts.append(f"- Informações de conta: {headers_footers['account_info']}")
        
        # Texto completo (amostra das primeiras 2000 caracteres)
        full_text = pdf_data.get('full_text', '')
        if full_text:
            text_preview = full_text[:2000]  # Primeiros 2000 caracteres
            context_parts.append(f"- Texto do documento (amostra):\n{text_preview}")
            if len(full_text) > 2000:
                context_parts.append(f"- ... (texto completo tem {len(full_text)} caracteres)")
        
        return "\n".join(context_parts)
    
    def _text_to_dataframe(self, text: str) -> pd.DataFrame:
        """
        Tenta criar um DataFrame básico a partir do texto do PDF
        Usa regex para identificar padrões de dados estruturados
        """
        lines = text.split('\n')
        records = []
        
        # Padrões comuns para identificar linhas de dados
        date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
        currency_pattern = r'R?\$?\s*-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?'
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Verifica se a linha parece ter dados estruturados
            has_date = bool(re.search(date_pattern, line))
            has_currency = bool(re.search(currency_pattern, line))
            
            if has_date or has_currency:
                # Tenta extrair campos
                date_match = re.search(date_pattern, line)
                currency_matches = re.findall(currency_pattern, line)
                
                record = {
                    'raw_text': line,
                    'date': date_match.group(0) if date_match else '',
                    'value': currency_matches[0] if currency_matches else '',
                    'description': line
                }
                records.append(record)
        
        if records:
            return pd.DataFrame(records)
        
        # Se não encontrou padrões, cria DataFrame simples com o texto
        return pd.DataFrame({'text': lines[:100]})  # Limita a 100 linhas
    
    def _repair_json(self, json_str: str, error: json.JSONDecodeError) -> str:
        """
        Tenta reparar JSON malformado corrigindo problemas comuns
        """
        repaired = json_str
        
        # Obtém posição do erro
        error_pos = getattr(error, 'pos', None)
        error_msg = str(error)
        
        # Se o erro menciona vírgula faltante, tenta adicionar
        if "Expecting ','" in error_msg or "delimiter" in error_msg:
            if error_pos and error_pos < len(repaired):
                # Analisa o contexto ao redor do erro (mais amplo para capturar o padrão)
                start = max(0, error_pos - 200)
                end = min(len(repaired), error_pos + 50)
                context = repaired[start:end]
                
                # Procura padrões comuns que indicam vírgula faltante
                # Padrão: "valor" } ou "valor" ] ou número } ou número ]
                # Mas não se já houver vírgula antes
                before_error = repaired[:error_pos]
                after_error = repaired[error_pos:]
                
                # Verifica se precisa adicionar vírgula antes de } ou ]
                # Procura por: valor seguido de } ou ] sem vírgula
                # Procura de trás para frente a partir do erro
                search_start = max(0, error_pos - 200)
                search_end = error_pos + 10
                search_area = repaired[search_start:search_end]
                
                # Padrões mais específicos para detectar vírgula faltante
                patterns_to_fix = [
                    # String seguida de } ou ] sem vírgula
                    (r'("(?:[^"\\]|\\.)+")\s*([}\]])', r'\1, \2'),
                    # Número seguido de } ou ] sem vírgula
                    (r'(\d+\.?\d*)\s*([}\]])', r'\1, \2'),
                    # Boolean/null seguido de } ou ] sem vírgula
                    (r'\b(true|false|null)\b\s*([}\]])', r'\1, \2'),
                ]
                
                # Aplica os padrões na área de busca
                fixed_area = search_area
                for pattern, replacement in patterns_to_fix:
                    # Aplica globalmente na área, mas apenas se não houver vírgula antes
                    fixed_area = re.sub(pattern, replacement, fixed_area)
                
                if fixed_area != search_area:
                    repaired = repaired[:search_start] + fixed_area + repaired[search_end:]
        
        # Aplica correções globais de vírgulas (mais agressivo)
        # Remove vírgulas extras antes de } ou ]
        repaired = re.sub(r',\s*}', r'}', repaired)
        repaired = re.sub(r',\s*]', r']', repaired)
        
        # Remove vírgulas duplicadas
        repaired = re.sub(r',\s*,', r',', repaired)
        
        # Tenta adicionar vírgulas faltantes globalmente (mais conservador)
        # Apenas se não houver vírgula antes e não for o primeiro item
        # Padrão: valor } ou valor ] onde valor não é seguido de vírgula
        # Mas evita adicionar se já houver vírgula antes
        repaired = re.sub(r'("(?:[^"\\]|\\.)+")\s+([}\]])', r'\1, \2', repaired)
        repaired = re.sub(r'(\d+\.?\d*)\s+([}\]])', r'\1, \2', repaired)
        repaired = re.sub(r'\b(true|false|null)\b\s+([}\]])', r'\1, \2', repaired)
        
        # Corrige strings não terminadas
        if error_pos and error_pos < len(repaired):
            before_error = repaired[:error_pos]
            # Conta aspas não escapadas
            quote_count = 0
            escape_next = False
            for char in before_error:
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"':
                    quote_count += 1
            
            if quote_count % 2 != 0:
                # String não terminada, tenta fechar
                after_error = repaired[error_pos:]
                next_quote = after_error.find('"')
                next_brace = after_error.find('}')
                next_bracket = after_error.find(']')
                
                if next_quote != -1 and (next_brace == -1 or next_quote < next_brace) and (next_bracket == -1 or next_quote < next_bracket):
                    repaired = repaired[:error_pos] + '"' + repaired[error_pos:]
                elif next_brace != -1:
                    repaired = repaired[:error_pos] + '"' + repaired[error_pos:]
        
        # Remove caracteres de controle
        repaired = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', repaired)
        
        return repaired
    
    def _extract_partial_json(self, json_str: str) -> Optional[Dict[str, Any]]:
        """
        Tenta extrair dados parciais de JSON malformado
        """
        try:
            # Tenta encontrar e extrair apenas o processed_data
            # Usa padrão mais flexível para encontrar o array
            processed_data_match = re.search(r'"processed_data"\s*:\s*\[', json_str)
            if not processed_data_match:
                return None
            
            # Encontra o início do array
            array_start = processed_data_match.end()
            
            # Procura por objetos { ... } dentro do array
            objects = []
            depth = 0
            array_depth = 1  # Profundidade do array
            current_obj = ""
            in_string = False
            escape_next = False
            obj_start = -1
            
            for i in range(array_start, len(json_str)):
                char = json_str[i]
                
                if escape_next:
                    if obj_start >= 0:
                        current_obj += char
                    escape_next = False
                    continue
                
                if char == '\\':
                    if obj_start >= 0:
                        current_obj += char
                    escape_next = True
                    continue
                
                if char == '"':
                    in_string = not in_string
                    if obj_start >= 0:
                        current_obj += char
                elif not in_string:
                    if char == '[':
                        array_depth += 1
                        if obj_start >= 0:
                            current_obj += char
                    elif char == ']':
                        array_depth -= 1
                        if array_depth == 0:
                            # Fim do array, tenta salvar último objeto se houver
                            if obj_start >= 0 and depth == 0 and current_obj:
                                try:
                                    obj = json.loads(current_obj)
                                    objects.append(obj)
                                except:
                                    pass
                            break
                        elif obj_start >= 0:
                            current_obj += char
                    elif char == '{':
                        if depth == 0:
                            obj_start = i
                            current_obj = "{"
                        else:
                            current_obj += char
                        depth += 1
                    elif char == '}':
                        if obj_start >= 0:
                            current_obj += char
                        depth -= 1
                        if depth == 0 and obj_start >= 0:
                            # Objeto completo encontrado
                            try:
                                obj = json.loads(current_obj)
                                objects.append(obj)
                            except json.JSONDecodeError:
                                # Tenta reparar o objeto antes de parsear
                                try:
                                    repaired_obj = self._repair_json(current_obj, json.JSONDecodeError("", current_obj, 0))
                                    obj = json.loads(repaired_obj)
                                    objects.append(obj)
                                except:
                                    pass
                            current_obj = ""
                            obj_start = -1
                    else:
                        if obj_start >= 0:
                            current_obj += char
                else:
                    if obj_start >= 0:
                        current_obj += char
            
            # Constrói resultado parcial
            if objects:
                result = {
                    'processed_data': objects,
                    'summary': {},
                    'issues': []
                }
                
                # Tenta extrair summary
                summary_match = re.search(r'"summary"\s*:\s*\{([^}]*)\}', json_str)
                if summary_match:
                    try:
                        summary_str = "{" + summary_match.group(1) + "}"
                        summary = json.loads(summary_str)
                        result['summary'] = summary
                    except:
                        # Tenta criar summary básico
                        result['summary'] = {
                            'total_rows': len(objects),
                            'processed': len(objects),
                            'errors': 0
                        }
                
                # Tenta extrair issues
                issues_match = re.search(r'"issues"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
                if issues_match:
                    try:
                        issues_str = "[" + issues_match.group(1) + "]"
                        issues = json.loads(issues_str)
                        result['issues'] = issues
                    except:
                        result['issues'] = ["Alguns dados podem ter sido perdidos devido a erro de parsing"]
                
                return result
        except Exception as e:
            print(f"Erro ao extrair JSON parcial: {e}")
        
        return None
    
    def _prepare_data_sample(self, df: pd.DataFrame, max_rows: int = 5) -> str:
        """
        Prepara amostra dos dados para análise
        """
        sample = df.head(max_rows)
        
        # Converte para formato legível
        data_info = {
            'columns': list(df.columns),
            'total_rows': len(df),
            'sample_data': sample.to_dict('records')
        }
        
        return json.dumps(data_info, indent=2, default=str, ensure_ascii=False)

    def _create_prompt_for_validation(
        self,
        columns: List[str],
        data_sample: str,
        selected_type: str
    ) -> str:
        """
        Cria prompt para validação do tipo de dados escolhido
        """
        expected_fields = self.EXPECTED_FIELDS.get(selected_type, [])
        type_name = self.DATA_TYPES.get(selected_type, selected_type)
        
        prompt = f"""Você é um assistente especializado em análise de dados financeiros e contábeis.

Analise o arquivo fornecido e determine se o tipo de dados selecionado pelo usuário faz sentido.

**Tipo de dados selecionado:** {type_name}
**Campos esperados para este tipo:** {', '.join(expected_fields)}

**Colunas do arquivo:**
{', '.join(columns)}

**Amostra dos dados (primeiras 5 linhas):**
{data_sample}

**Tarefa:**
1. Analise se as colunas e dados do arquivo são compatíveis com o tipo "{type_name}"
2. Identifique quais campos esperados estão presentes ou podem ser mapeados
3. Avalie a compatibilidade geral

**Responda em formato JSON:**
{{
    "compatible": true/false,
    "confidence": 0.0-1.0,
    "reason": "explicação breve",
    "missing_fields": ["lista de campos faltantes"],
    "found_fields": ["lista de campos encontrados"],
    "suggestions": "sugestões de melhoria ou tipo alternativo"
}}
"""
        return prompt

    def _create_prompt_for_mapping(
        self,
        columns: List[str],
        data_sample: str,
        import_type: str
    ) -> str:
        """
        Cria prompt para sugestão de mapeamento de colunas
        """
        expected_fields = self.EXPECTED_FIELDS.get(import_type, [])
        type_name = self.DATA_TYPES.get(import_type, import_type)
        
        prompt = f"""Você é um assistente especializado em mapeamento de colunas de dados financeiros.

Analise o arquivo e sugira o melhor mapeamento das colunas do arquivo para os campos do sistema.

**Tipo de dados:** {type_name}
**Campos esperados pelo sistema:** {', '.join(expected_fields)}

**Colunas do arquivo:**
{', '.join(columns)}

**Amostra dos dados (primeiras 5 linhas):**
{data_sample}

**Tarefa:**
Para cada coluna do arquivo, sugira o campo do sistema mais apropriado.
Se uma coluna não se encaixa em nenhum campo, sugira "ignore".

**Responda em formato JSON:**
{{
    "mapping": {{
        "nome_coluna_arquivo": "campo_sistema",
        ...
    }},
    "confidence": 0.0-1.0,
    "notes": "observações sobre o mapeamento"
}}
"""
        return prompt

    def _call_ai(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        status_callback: Optional[callable] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Chama a API de IA e retorna (resposta, erro)
        Se erro for None, resposta contém o texto retornado
        
        Args:
            prompt: Prompt para enviar à IA
            model: Nome do modelo (opcional)
            status_callback: Função callback(status_message) para atualizar status em tempo real
        """
        if status_callback:
            status_callback("Conectando à API de IA...")
        
        client, error = self._get_client()
        if error:
            return None, error
        
        if not client:
            return None, "Cliente de IA não inicializado"
        
        provider = self.config['provider']
        model_name = model or self.config.get('model')
        
        if not model_name:
            return None, "Nome do modelo não configurado"
        
        try:
            if status_callback:
                status_callback(f"Enviando requisição para {provider} (modelo: {model_name})...")
            
            if provider == 'openai' or provider == 'ollama' or provider == 'groq':
                system_message = "Você é um assistente especializado em análise de dados financeiros e contábeis. Sempre responda APENAS em formato JSON válido, sem texto adicional antes ou depois do JSON."
                user_message = prompt
                
                if status_callback:
                    status_callback("Processando com IA...")
                
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.2,  # Reduzido para respostas mais rápidas e consistentes
                    max_tokens=6000,  # Otimizado: reduzido de 8000 para melhor performance
                    response_format={"type": "json_object"} if provider == 'openai' else None
                )
                
                if status_callback:
                    status_callback("Recebendo resposta da IA...")
                
                if response and response.choices and len(response.choices) > 0:
                    return response.choices[0].message.content, None
                else:
                    return None, "Resposta vazia da API"
            
            elif provider == 'gemini':
                if status_callback:
                    status_callback("Processando com Gemini...")
                
                # Gemini precisa do system message no prompt
                full_prompt = f"""Você é um assistente especializado em análise de dados financeiros e contábeis. Sempre responda APENAS em formato JSON válido, sem texto adicional antes ou depois do JSON.

{prompt}"""
                
                response = client.generate_content(full_prompt)
                
                if status_callback:
                    status_callback("Recebendo resposta da IA...")
                
                if response and response.text:
                    return response.text, None
                else:
                    return None, "Resposta vazia da API"
            
            else:
                return None, f"Provedor '{provider}' não suportado"
            
        except Exception as e:
            error_msg = f"Erro ao chamar API de IA ({provider}): {str(e)}"
            print(error_msg)
            return None, error_msg

    def validate_data_type(
        self,
        df: pd.DataFrame,
        selected_type: str
    ) -> Dict[str, Any]:
        """
        Valida se o tipo de dados escolhido faz sentido para o arquivo
        
        Retorna:
        {
            'compatible': bool,
            'confidence': float (0-1),
            'reason': str,
            'missing_fields': List[str],
            'found_fields': List[str],
            'suggestions': str
        }
        """
        if not self.is_available():
            return {
                'compatible': True,  # Assume compatível se IA não disponível
                'confidence': 0.0,
                'reason': 'IA não configurada',
                'missing_fields': [],
                'found_fields': [],
                'suggestions': ''
            }
        
        try:
            columns = list(df.columns)
            data_sample = self._prepare_data_sample(df)
            prompt = self._create_prompt_for_validation(columns, data_sample, selected_type)
            
            response, error = self._call_ai(prompt)
            
            if error:
                # Retorna erro específico
                return {
                    'compatible': True,
                    'confidence': 0.0,
                    'reason': f'Erro na IA: {error}',
                    'missing_fields': [],
                    'found_fields': columns,
                    'suggestions': '',
                    'error': error
                }
            
            if response:
                # Tenta extrair JSON da resposta
                try:
                    # Remove markdown code blocks se existirem
                    response_clean = response
                    if '```json' in response_clean:
                        response_clean = response_clean.split('```json')[1].split('```')[0]
                    elif '```' in response_clean:
                        response_clean = response_clean.split('```')[1].split('```')[0]
                    
                    result = json.loads(response_clean.strip())
                    return result
                except json.JSONDecodeError as e:
                    # Se não conseguir parsear, retorna erro
                    return {
                        'compatible': True,
                        'confidence': 0.5,
                        'reason': f'Resposta da IA não pôde ser parseada como JSON: {str(e)}',
                        'missing_fields': [],
                        'found_fields': columns,
                        'suggestions': response[:200] if response else '',
                        'error': f'Erro ao parsear JSON: {str(e)}',
                        'raw_response': response[:500] if response else ''
                    }
            else:
                return {
                    'compatible': True,
                    'confidence': 0.0,
                    'reason': 'Sem resposta da IA',
                    'missing_fields': [],
                    'found_fields': columns,
                    'suggestions': '',
                    'error': 'Sem resposta da API'
                }
        except Exception as e:
            error_msg = f"Erro ao validar tipo de dados: {str(e)}"
            print(error_msg)
            return {
                'compatible': True,
                'confidence': 0.0,
                'reason': error_msg,
                'missing_fields': [],
                'found_fields': list(df.columns),
                'suggestions': '',
                'error': error_msg
            }

    def suggest_column_mapping(
        self,
        df: pd.DataFrame,
        import_type: str,
        target_columns: List[str]
    ) -> Dict[str, str]:
        """
        Sugere mapeamento de colunas usando IA
        
        Retorna dicionário: {coluna_arquivo: campo_sistema}
        """
        if not self.is_available():
            return {}
        
        try:
            columns = list(df.columns)
            data_sample = self._prepare_data_sample(df)
            prompt = self._create_prompt_for_mapping(columns, data_sample, import_type)
            
            response, error = self._call_ai(prompt)
            
            if error:
                print(f"Erro ao obter mapeamento da IA: {error}")
                return {}
            
            if response:
                try:
                    # Remove markdown code blocks se existirem
                    response_clean = response
                    if '```json' in response_clean:
                        response_clean = response_clean.split('```json')[1].split('```')[0]
                    elif '```' in response_clean:
                        response_clean = response_clean.split('```')[1].split('```')[0]
                    
                    result = json.loads(response_clean.strip())
                    mapping = result.get('mapping', {})
                    
                    # Valida que os campos mapeados existem em target_columns
                    validated_mapping = {}
                    for source_col, target_col in mapping.items():
                        if source_col in columns:
                            if target_col in target_columns or target_col == 'ignore':
                                validated_mapping[source_col] = target_col
                            else:
                                validated_mapping[source_col] = 'ignore'
                    
                    return validated_mapping
                except json.JSONDecodeError as e:
                    print(f"Erro ao parsear JSON do mapeamento: {e}")
                    print(f"Resposta recebida: {response[:500]}")
                    return {}
            else:
                print("Sem resposta da IA para mapeamento")
                return {}
        except Exception as e:
            print(f"Erro ao sugerir mapeamento: {e}")
            return {}

    def test_connection(self) -> Tuple[bool, str]:
        """
        Testa conexão com a API de IA
        
        Retorna: (sucesso, mensagem)
        """
        if not self.config:
            return False, "IA não configurada"
        
        try:
            # Recarrega cliente para garantir que está atualizado
            self._client = None
            client, error = self._get_client()
            
            if error:
                return False, error
            
            if not client:
                return False, "Erro ao inicializar cliente de IA"
            
            # Teste simples
            test_prompt = "Responda apenas: OK"
            response, error = self._call_ai(test_prompt)
            
            if error:
                return False, error
            
            if response:
                return True, f"Conexão bem-sucedida! Resposta: {response[:50]}"
            else:
                return False, "Sem resposta da API"
        except Exception as e:
            return False, f"Erro: {str(e)}"

    def _create_prompt_structural_analysis(
        self,
        columns: List[str],
        data_sample: str,
        import_type: str
    ) -> str:
        """
        Cria prompt para análise estrutural completa do arquivo
        """
        expected_fields = self.EXPECTED_FIELDS.get(import_type, [])
        optional_fields = self.get_target_columns(import_type)
        optional_fields = [f for f in optional_fields if f not in expected_fields]
        type_name = self.DATA_TYPES.get(import_type, import_type)
        
        prompt = f"""Você é um especialista em análise de dados financeiros e contábeis.

Analise o arquivo fornecido e forneça uma análise estrutural completa.

**Colunas do arquivo:**
{', '.join(columns)}

**Amostra dos dados (primeiras 10 linhas):**
{data_sample}

**Tipo de dados esperado:** {type_name}
**Campos obrigatórios:** {', '.join(expected_fields)}
**Campos opcionais:** {', '.join(optional_fields) if optional_fields else 'Nenhum'}

**Tarefa:**
1. Identifique o tipo real de dados no arquivo
2. Analise cada coluna: tipo de dado, formato, padrões, valores únicos
3. Identifique campos de data e seus formatos
4. Identifique campos monetários e seus formatos (R$, BRL, etc)
5. Identifique campos de descrição/histórico
6. Detecte campos que podem ser inferidos ou calculados
7. Identifique inconsistências ou problemas nos dados
8. Sugira transformações necessárias

**Responda em formato JSON:**
{{
    "file_type": "tipo identificado",
    "columns_analysis": {{
        "nome_coluna": {{
            "type": "date|currency|text|numeric|boolean",
            "format": "formato específico se aplicável",
            "sample_values": ["valor1", "valor2"],
            "patterns": "padrões identificados",
            "issues": ["problemas encontrados"],
            "suggested_mapping": "campo_sistema_sugerido"
        }}
    }},
    "data_quality": {{
        "completeness": 0.0-1.0,
        "consistency": 0.0-1.0,
        "issues": ["lista de problemas"]
    }},
    "transformations_needed": [
        {{
            "column": "nome_coluna",
            "transformation": "normalize_date|normalize_currency|extract_text|etc",
            "from_format": "formato atual",
            "to_format": "formato desejado"
        }}
    ],
    "inferred_fields": {{
        "campo_sistema": {{
            "source": "coluna_origem ou calculado",
            "method": "como foi inferido",
            "confidence": 0.0-1.0
        }}
    }}
}}
"""
        return prompt

    def _create_prompt_detect_type(
        self,
        columns: List[str],
        data_sample: str
    ) -> str:
        """
        Cria prompt para detecção automática do tipo de dado
        """
        prompt = f"""Você é um especialista em análise de dados financeiros e contábeis.

Analise o arquivo fornecido e identifique automaticamente qual tipo de dado ele contém.

**Tipos de dados suportados e suas características:**

1. **💳 Transações Financeiras (transactions):**
   - Campos típicos: data, descrição, valor, tipo (entrada/saida), categoria
   - Valores podem ser positivos ou negativos
   - Geralmente tem coluna de tipo ou sinal
   - Pode ter categoria, conta, grupo

2. **🏦 Extratos Bancários (bank_statements):**
   - Campos típicos: data, histórico/descrição, valor, saldo, banco, conta
   - Valores podem ser positivos (crédito) ou negativos (débito)
   - Geralmente tem saldo acumulado
   - Pode ter informações de banco e conta
   - Padrões: "TED", "DOC", "PIX", "SALDO", "EXTRATO"

3. **📝 Contratos/Eventos (contracts):**
   - Campos típicos: data_inicio, data_evento, valor_servico, contratante, tipo_evento
   - Geralmente tem datas de início e evento
   - Tem valor de serviço e possível valor de deslocamento
   - Tem nome do contratante/cliente

4. **💸 Contas a Pagar (accounts_payable):**
   - Campos típicos: conta, vencimento, valor, cpf_cnpj, mes_referencia
   - Tem data de vencimento
   - Geralmente tem nome da conta/fornecedor
   - Pode ter status de pagamento

5. **💰 Contas a Receber (accounts_receivable):**
   - Campos típicos: conta, vencimento, valor, cpf_cnpj, mes_referencia
   - Tem data de vencimento
   - Geralmente tem nome do devedor/cliente
   - Pode ter status de recebimento

**Colunas encontradas no arquivo:**
{', '.join(columns)}

**Amostra dos dados (primeiras 15 linhas):**
{data_sample}

**Tarefa:**
Analise as colunas e a amostra de dados para identificar qual tipo de dado o arquivo contém.
Compare os padrões encontrados com as características de cada tipo.
Retorne o tipo mais provável com nível de confiança e justificativa.

**Responda em formato JSON:**
{{
    "suggested_type": "transactions" | "bank_statements" | "contracts" | "accounts_payable" | "accounts_receivable",
    "confidence": 0.0-1.0,
    "reasoning": "explicação detalhada do motivo",
    "alternative_types": [
        {{
            "type": "bank_statements",
            "confidence": 0.3,
            "reason": "motivo da alternativa"
        }}
    ],
    "detected_fields": {{
        "date": "nome_coluna_encontrada",
        "value": "nome_coluna_encontrada",
        "description": "nome_coluna_encontrada"
    }},
    "key_indicators": [
        "indicador 1 que levou à conclusão",
        "indicador 2 que levou à conclusão"
    ]
}}
"""
        return prompt

    def detect_data_type(
        self,
        df: pd.DataFrame,
        columns: List[str],
        data_sample: str
    ) -> Dict[str, Any]:
        """
        Detecta automaticamente o tipo de dado do arquivo usando IA
        
        Retorna:
        {
            'success': bool,
            'suggested_type': str,
            'confidence': float,
            'reasoning': str,
            'alternative_types': List[Dict],
            'detected_fields': Dict,
            'error': str
        }
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'IA não configurada ou não disponível',
                'suggested_type': None,
                'confidence': 0.0,
                'reasoning': '',
                'alternative_types': [],
                'detected_fields': {}
            }
        
        try:
            prompt = self._create_prompt_detect_type(columns, data_sample)
            response, error = self._call_ai(prompt)
            
            if error:
                return {
                    'success': False,
                    'error': error,
                    'suggested_type': None,
                    'confidence': 0.0,
                    'reasoning': '',
                    'alternative_types': [],
                    'detected_fields': {}
                }
            
            if not response:
                return {
                    'success': False,
                    'error': 'Sem resposta da IA',
                    'suggested_type': None,
                    'confidence': 0.0,
                    'reasoning': '',
                    'alternative_types': [],
                    'detected_fields': {}
                }
            
            # Parse da resposta
            try:
                # Remove markdown code blocks se existirem
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                elif '```' in response:
                    response = response.split('```')[1].split('```')[0]
                
                # Limpa a resposta
                response_clean = response.strip()
                
                # Tenta encontrar o JSON válido na resposta
                start_idx = response_clean.find('{')
                if start_idx == -1:
                    raise json.JSONDecodeError("JSON não encontrado", response_clean, 0)
                
                end_idx = response_clean.rfind('}')
                if end_idx == -1 or end_idx <= start_idx:
                    raise json.JSONDecodeError("JSON incompleto", response_clean, start_idx)
                
                json_str = response_clean[start_idx:end_idx + 1]
                result = json.loads(json_str)
                
                return {
                    'success': True,
                    'suggested_type': result.get('suggested_type'),
                    'confidence': float(result.get('confidence', 0.0)),
                    'reasoning': result.get('reasoning', ''),
                    'alternative_types': result.get('alternative_types', []),
                    'detected_fields': result.get('detected_fields', {}),
                    'key_indicators': result.get('key_indicators', []),
                    'error': None
                }
                
            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'error': f'Erro ao parsear resposta da IA: {str(e)}',
                    'suggested_type': None,
                    'confidence': 0.0,
                    'reasoning': '',
                    'alternative_types': [],
                    'detected_fields': {},
                    'raw_response': response[:500]
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro ao detectar tipo de dado: {str(e)}',
                'suggested_type': None,
                'confidence': 0.0,
                'reasoning': '',
                'alternative_types': [],
                'detected_fields': {}
            }

    def _create_prompt_normalization(
        self,
        file_data: str,
        import_type: str,
        structural_analysis: str,
        mapping: Dict[str, str]
    ) -> str:
        """
        Cria prompt para normalização e estruturação de dados
        """
        type_name = self.DATA_TYPES.get(import_type, import_type)
        expected_fields = self.EXPECTED_FIELDS.get(import_type, [])
        all_fields = self.get_target_columns(import_type)
        
        expected_structure = {
            field: "tipo e formato esperado" for field in all_fields
        }
        
        prompt = f"""Você é um especialista em normalização e estruturação de dados financeiros.

Normalize e estruture os dados do arquivo para o formato esperado pelo sistema.

**Tipo de dados:** {type_name}
**Estrutura esperada:**
{json.dumps(expected_structure, indent=2, ensure_ascii=False)}

**Mapeamento de colunas:**
{json.dumps(mapping, indent=2, ensure_ascii=False)}

**Dados do arquivo (primeiras 20 linhas):**
{file_data}

**Análise estrutural prévia:**
{structural_analysis}

**Tarefa:**
Para cada linha de dados:
1. Normalize datas para formato YYYY-MM-DD
2. Normalize valores monetários para número decimal (sem símbolos)
3. Identifique tipo de transação (entrada/saída) baseado em valores ou descrições
4. Extraia informações relevantes de campos de texto
5. Preencha campos faltantes com valores inferidos quando possível
6. Valide e corrija dados inconsistentes
7. Estruture no formato JSON esperado

**Regras de normalização:**
- Datas: Converter qualquer formato para YYYY-MM-DD
- Valores: Remover símbolos (R$, BRL, etc), pontos de milhar, manter apenas vírgula ou ponto decimal
- Descrições: Limpar espaços extras, normalizar caracteres
- Tipos: Identificar automaticamente entrada/saída baseado em sinais ou palavras-chave

**Responda em formato JSON com array de objetos normalizados:**
{{
    "normalized_data": [
        {{
            "date": "YYYY-MM-DD",
            "description": "descrição normalizada",
            "value": 1234.56,
            "type": "entrada|saida",
            "category": "categoria se identificada",
            "account": "conta se identificada",
            "original_row": 1,
            "transformations_applied": ["lista de transformações"],
            "confidence": 0.0-1.0
        }}
    ],
    "summary": {{
        "total_rows": 100,
        "successfully_normalized": 95,
        "rows_with_issues": 5,
        "common_issues": ["lista de problemas comuns"]
    }}
}}
"""
        return prompt

    def _create_prompt_validation(
        self,
        normalized_data: str,
        import_type: str
    ) -> str:
        """
        Cria prompt para validação e correção inteligente
        """
        type_name = self.DATA_TYPES.get(import_type, import_type)
        required_fields = self.EXPECTED_FIELDS.get(import_type, [])
        
        validation_rules = {
            "required_fields": required_fields,
            "date_format": "YYYY-MM-DD",
            "value_format": "número decimal",
            "type_values": ["entrada", "saida"]
        }
        
        prompt = f"""Você é um especialista em validação e correção de dados financeiros.

Valide e corrija os dados normalizados, garantindo consistência e completude.

**Tipo de dados:** {type_name}
**Dados normalizados:**
{normalized_data}

**Regras de validação:**
{json.dumps(validation_rules, indent=2, ensure_ascii=False)}

**Tarefa:**
1. Valide cada registro:
   - Datas estão no formato correto e são válidas?
   - Valores são numéricos válidos?
   - Descrições não estão vazias?
   - Campos obrigatórios estão preenchidos?
2. Identifique inconsistências:
   - Valores muito altos ou muito baixos (outliers)
   - Datas fora de período esperado
   - Descrições duplicadas suspeitas
   - Padrões anômalos
3. Corrija problemas quando possível:
   - Corrija formatos de data
   - Corrija valores monetários
   - Complete campos faltantes com valores inferidos
   - Sugira correções para dados inválidos
4. Classifique registros:
   - Válido e pronto para importação
   - Válido com avisos
   - Inválido mas corrigível
   - Inválido e não corrigível

**Responda em formato JSON:**
{{
    "validated_data": [
        {{
            "row": 1,
            "data": {{dados validados}},
            "status": "valid|warning|error",
            "issues": ["problemas encontrados"],
            "corrections": ["correções aplicadas"],
            "confidence": 0.0-1.0
        }}
    ],
    "validation_summary": {{
        "total": 100,
        "valid": 90,
        "with_warnings": 5,
        "with_errors": 5,
        "corrected": 3
    }},
    "recommendations": [
        "recomendações para melhorar qualidade dos dados"
    ]
}}
"""
        return prompt

    def _create_prompt_inference(
        self,
        available_data: str,
        import_type: str,
        missing_fields: List[str],
        context: Optional[str] = None
    ) -> str:
        """
        Cria prompt para inferência de campos faltantes
        """
        type_name = self.DATA_TYPES.get(import_type, import_type)
        
        prompt = f"""Você é um especialista em inferência de dados financeiros.

Analise os dados e infira campos faltantes baseado em padrões, contexto e regras de negócio.

**Tipo de dados:** {type_name}
**Dados disponíveis:**
{available_data}

**Campos faltantes que precisam ser inferidos:**
{', '.join(missing_fields)}

**Contexto adicional:**
{context or 'Nenhum contexto adicional fornecido'}

**Tarefa:**
Para cada campo faltante:
1. Analise se pode ser inferido dos dados existentes
2. Identifique padrões que permitam inferência
3. Aplique regras de negócio conhecidas
4. Calcule valores quando possível
5. Classifique por tipo de transação/descrição quando aplicável
6. Atribua valores padrão quando necessário

**Exemplos de inferências:**
- Tipo (entrada/saída): baseado em sinal do valor ou palavras-chave na descrição
- Categoria: baseado em palavras-chave na descrição
- Conta: baseado em padrões de descrição ou valores
- Data: inferir de outros campos de data se disponível

**Responda em formato JSON:**
{{
    "inferred_fields": {{
        "campo1": {{
            "method": "como foi inferido",
            "source": "fonte dos dados",
            "value": "valor inferido",
            "confidence": 0.0-1.0,
            "rules_applied": ["regras aplicadas"]
        }}
    }},
    "inference_summary": {{
        "fields_inferred": ["lista de campos"],
        "average_confidence": 0.0-1.0,
        "methods_used": ["métodos utilizados"]
    }}
}}
"""
        return prompt

    def _create_prompt_intelligent_mapping(
        self,
        columns: List[str],
        data_sample: str,
        import_type: str,
        structural_analysis: Optional[str] = None
    ) -> str:
        """
        Cria prompt para mapeamento inteligente com contexto
        """
        expected_fields = self.EXPECTED_FIELDS.get(import_type, [])
        all_fields = self.get_target_columns(import_type)
        type_name = self.DATA_TYPES.get(import_type, import_type)
        
        prompt = f"""Você é um especialista em mapeamento inteligente de dados financeiros.

Mapeie as colunas do arquivo para os campos do sistema considerando nomes, conteúdo, formato e contexto.

**Colunas do arquivo:**
{', '.join(columns)}

**Amostra de dados (primeiras 15 linhas):**
{data_sample}

**Tipo de dados:** {type_name}
**Campos esperados pelo sistema:**
{', '.join(all_fields)}
**Campos obrigatórios:** {', '.join(expected_fields)}

**Análise estrutural:**
{structural_analysis or 'Não disponível'}

**Tarefa:**
1. Para cada campo esperado, identifique a melhor coluna correspondente considerando:
   - Nome da coluna (similaridade semântica)
   - Tipo e formato dos dados
   - Padrões nos valores
   - Contexto e posição na estrutura
2. Para colunas que não mapeiam diretamente:
   - Identifique se podem ser combinadas
   - Identifique se precisam de transformação
   - Identifique se devem ser ignoradas
3. Crie regras de transformação quando necessário
4. Valide o mapeamento proposto

**Responda em formato JSON:**
{{
    "mapping": {{
        "coluna_arquivo": {{
            "target_field": "campo_sistema",
            "transformation": "nenhuma|normalize_date|normalize_currency|extract_text|combine|etc",
            "confidence": 0.0-1.0,
            "reason": "por que este mapeamento foi escolhido"
        }}
    }},
    "transformation_rules": [
        {{
            "column": "coluna",
            "rule": "regra de transformação",
            "example": "exemplo de transformação"
        }}
    ],
    "missing_fields": {{
        "campo": {{
            "can_infer": true/false,
            "method": "como inferir",
            "confidence": 0.0-1.0
        }}
    }},
    "mapping_confidence": 0.0-1.0
}}
"""
        return prompt

    def get_target_columns(self, import_type: str) -> List[str]:
        """
        Retorna todas as colunas alvo (obrigatórias + opcionais) para um tipo de importação
        """
        from services.import_service import ImportService
        return ImportService.get_target_columns(import_type)
    
    def _create_prompt_process_transactions(
        self,
        file_data: str,
        columns: List[str],
        data_sample: str,
        is_pdf_source: bool = False,
        groups_subgroups: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Cria prompt específico para processar transações financeiras
        Baseado na estrutura real da tabela Transaction
        """
        pdf_note = ""
        if is_pdf_source:
            pdf_note = """
**NOTA IMPORTANTE - Arquivo PDF:**
- Os dados podem incluir texto completo do PDF, cabeçalhos, rodapés e metadados
- Use TODAS as informações disponíveis (não apenas tabelas) para identificar campos
- Se houver texto não estruturado, analise-o cuidadosamente para encontrar dados relevantes
- Datas podem estar em diferentes formatos no texto - identifique e converta corretamente
"""
        
        groups_info = ""
        if groups_subgroups:
            groups_info = "\n**GRUPOS E SUBGRUPOS DISPONÍVEIS PARA CLASSIFICAÇÃO:**\n"
            for group in groups_subgroups:
                group_name = group.get('name', '')
                group_id = group.get('id', '')
                subgroups = group.get('subgroups', [])
                groups_info += f"- Grupo ID {group_id}: {group_name}\n"
                if subgroups:
                    for sg in subgroups:
                        sg_name = sg.get('name', '')
                        sg_id = sg.get('id', '')
                        groups_info += f"  - Subgrupo ID {sg_id}: {sg_name}\n"
            groups_info += "\n**IMPORTANTE - Classificação Automática:**\n"
            groups_info += "- Para CADA linha processada, analise a descrição, categoria e valor\n"
            groups_info += "- Identifique o grupo e subgrupo mais apropriado baseado no contexto da transação\n"
            groups_info += "- Use group_id e subgroup_id nos dados processados\n"
            groups_info += "- Se não conseguir identificar com certeza, deixe null\n"
        
        prompt = f"""Você é um especialista em processamento de transações financeiras e contábeis.

Analise o arquivo de transações financeiras e estruture os dados para importação no sistema.

**Estrutura da Tabela de Transações:**
- date (Date, obrigatório): Data da transação no formato YYYY-MM-DD
- description (Text, obrigatório): Descrição/histórico da transação
- value (Float, obrigatório): Valor da transação (número decimal, sem símbolos)
- type (String, obrigatório): Tipo da transação - DEVE SER "entrada" ou "saida"
- category (String, opcional): Categoria da transação
- account (String, opcional): Conta/banco relacionado
- group_id (Integer, opcional): ID do grupo de classificação
- subgroup_id (Integer, opcional): ID do subgrupo de classificação

{groups_info}

{pdf_note}

**Colunas encontradas no arquivo:**
{', '.join(columns) if columns else 'Dados extraídos do texto'}

**Amostra dos dados (primeiras 20 linhas):**
{data_sample}

**Dados completos (pode incluir texto, tabelas, metadados):**
{file_data}

**Regras de Processamento CRÍTICAS:**
1. DATAS: 
   - Use EXATAMENTE a data do arquivo original, linha por linha
   - Converta QUALQUER formato para YYYY-MM-DD
   - NÃO invente datas, use apenas as que estão no arquivo
   - Se houver múltiplas colunas de data, identifique qual é a data da transação
   - Preserve a correspondência: original_row deve corresponder à linha real do arquivo
   - Exemplos de conversão: "01/01/2024" → "2024-01-01", "2024-01-01 10:30" → "2024-01-01", "15-JAN-2024" → "2024-01-15"

2. VALORES: Normalize valores monetários para número decimal
   - Remova símbolos: R$, BRL, $, etc
   - Remova pontos de milhar: 1.234,56 → 1234.56
   - Mantenha vírgula ou ponto como separador decimal: 1234,56 ou 1234.56
   - Valores negativos indicam SAÍDA, positivos indicam ENTRADA (se não houver campo tipo explícito)

3. TIPO (entrada/saida): Identifique automaticamente
   - Se houver coluna explícita de tipo: use "entrada" ou "saida"
   - Se valor for negativo: "saida"
   - Se valor for positivo: "entrada"
   - Palavras-chave para saída: "débito", "saída", "pagamento", "retirada", "transferência enviada"
   - Palavras-chave para entrada: "crédito", "entrada", "recebimento", "depósito", "transferência recebida"

4. DESCRIÇÃO: Limpe e normalize
   - Remova espaços extras
   - Mantenha informações relevantes
   - Se houver múltiplas colunas de descrição, combine-as

5. GRUPO E SUBGRUPO (CLASSIFICAÇÃO PRINCIPAL - OBRIGATÓRIO):
   - **PRIORIDADE MÁXIMA:** Você DEVE analisar CADA linha e classificar por grupo e subgrupo PRIMEIRO
   - Analise a descrição e valor de CADA transação
   - Compare com a lista de grupos e subgrupos fornecida acima
   - Identifique o grupo e subgrupo mais apropriado baseado no contexto
   - Use palavras-chave na descrição para fazer a classificação:
     * "fornecedor", "compra", "pagamento" → geralmente despesas/fornecedores
     * "salário", "folha", "funcionário" → geralmente despesas/pessoal
     * "aluguel", "energia", "água", "telefone", "internet" → geralmente despesas/operação
     * "venda", "recebimento", "cliente" → geralmente receitas
     * "transferência", "TED", "PIX" → analise o contexto (entrada ou saída)
   - **SEMPRE retorne group_id e subgroup_id** - mesmo que seja null se não conseguir identificar
   - Retorne os IDs numéricos (group_id e subgroup_id) nos dados processados
   - Se a descrição não for clara, use o valor e tipo (entrada/saida) para ajudar na classificação
   - **IMPORTANTE:** Grupo e subgrupo são a classificação PRINCIPAL para relatórios contábeis (DRE/DFC)

6. CATEGORIA (CLASSIFICAÇÃO SECUNDÁRIA - OPCIONAL):
   - Use APENAS como classificação adicional/descritiva
   - Pode ser útil para análises complementares ou filtros
   - Se não conseguir identificar grupo/subgrupo, pode usar categoria como classificação genérica
   - Exemplos: "alimentação", "transporte", "salário", "fornecedor", etc
   - **NOTA:** Categoria é complementar, não substitui grupo/subgrupo

7. CONTA: Identifique se houver informação de banco/conta

**Tarefa:**
Processe TODAS as linhas do arquivo e retorne dados estruturados prontos para importação, incluindo classificação automática por grupo e subgrupo.

**CRÍTICO - Correspondência de Linhas:**
- O campo "original_row" DEVE corresponder EXATAMENTE ao número da linha no arquivo original
- Se o arquivo tem 10 linhas, original_row deve ir de 1 a 10
- Use o índice da linha no array de dados fornecido + 1 (primeira linha = 1, segunda = 2, etc)
- Isso é ESSENCIAL para garantir que as datas correspondam corretamente

**IMPORTANTE - Regras para JSON válido:**
- Retorne APENAS JSON válido, sem texto adicional antes ou depois
- Escape corretamente caracteres especiais em strings:
  * Aspas duplas dentro de strings: use \"
  * Quebras de linha: use \\n (não use quebras reais de linha)
  * Barras invertidas: use \\\\
- Limite descrições a 500 caracteres (trunque se necessário)
- Garanta que todas as strings estejam entre aspas duplas
- Não use aspas simples para strings
- Se uma descrição contiver caracteres especiais, escape-os corretamente

**Responda em formato JSON válido:**
{{
    "processed_data": [
        {{
            "date": "2024-01-15",
            "description": "Pagamento fornecedor ABC",
            "value": 1500.00,
            "type": "saida",
            "category": "fornecedor",
            "account": "Banco do Brasil",
            "group_id": 1,
            "subgroup_id": 3,
            "original_row": 1,
            "confidence": 0.95
        }}
    ],
    "summary": {{
        "total_rows": 100,
        "processed": 98,
        "errors": 2,
        "entradas": 45,
        "saidas": 53
    }},
    "issues": [
        "Linha 5: Data inválida, usando data atual",
        "Linha 12: Valor não numérico, ignorado"
    ]
}}
"""
        return prompt
    
    def _create_prompt_process_bank_statements(
        self,
        file_data: str,
        columns: List[str],
        data_sample: str,
        is_pdf_source: bool = False,
        groups_subgroups: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Cria prompt específico para processar extratos bancários
        Baseado na estrutura real da tabela BankStatement
        """
        pdf_note = ""
        if is_pdf_source:
            pdf_note = """
**NOTA IMPORTANTE - Arquivo PDF:**
- Os dados podem incluir texto completo do PDF, cabeçalhos, rodapés e metadados
- Use TODAS as informações disponíveis (não apenas tabelas) para identificar campos
- Extraia nome do banco, número de conta e outras informações dos cabeçalhos/rodapés
- Se houver texto não estruturado, analise-o cuidadosamente para encontrar dados relevantes
- Datas podem estar em diferentes formatos no texto - identifique e converta corretamente
"""
        
        groups_info = ""
        if groups_subgroups:
            groups_info = "\n**GRUPOS E SUBGRUPOS DISPONÍVEIS PARA CLASSIFICAÇÃO:**\n"
            for group in groups_subgroups:
                group_name = group.get('name', '')
                group_id = group.get('id', '')
                subgroups = group.get('subgroups', [])
                groups_info += f"- Grupo ID {group_id}: {group_name}\n"
                if subgroups:
                    for sg in subgroups:
                        sg_name = sg.get('name', '')
                        sg_id = sg.get('id', '')
                        groups_info += f"  - Subgrupo ID {sg_id}: {sg_name}\n"
            groups_info += "\n**IMPORTANTE - Classificação Automática:**\n"
            groups_info += "- Para CADA linha processada, analise a descrição/histórico e valor\n"
            groups_info += "- Identifique o grupo e subgrupo mais apropriado baseado no contexto da transação\n"
            groups_info += "- Use group_id e subgroup_id nos dados processados\n"
            groups_info += "- Se não conseguir identificar com certeza, deixe null\n"
        
        prompt = f"""Você é um especialista em processamento de extratos bancários.

Analise o arquivo de extrato bancário e estruture os dados para importação no sistema.

**Estrutura da Tabela de Extratos Bancários:**
- date (Date, obrigatório): Data da transação no formato YYYY-MM-DD - DEVE SER EXATAMENTE A DATA DO ARQUIVO ORIGINAL
- description (Text, obrigatório): Descrição/histórico da transação
- value (Float, obrigatório): Valor da transação (número decimal, negativo para débitos, positivo para créditos)
- bank_name (String, opcional): Nome do banco - EXTRAIA DO ARQUIVO (cabeçalho, rodapé, ou padrões nas descrições)
- account (String, opcional): Número da conta
- balance (Float, opcional): Saldo após a transação
- group_id (Integer, opcional): ID do grupo de classificação
- subgroup_id (Integer, opcional): ID do subgrupo de classificação

{groups_info}

{pdf_note}

**Colunas encontradas no arquivo:**
{', '.join(columns) if columns else 'Dados extraídos do texto'}

**Amostra dos dados (primeiras 20 linhas):**
{data_sample}

**Dados completos (pode incluir texto, tabelas, metadados):**
{file_data}

**Regras de Processamento CRÍTICAS:**
1. DATAS: 
   - Use EXATAMENTE a data do arquivo original, linha por linha
   - Converta QUALQUER formato para YYYY-MM-DD
   - NÃO invente datas, use apenas as que estão no arquivo
   - Se houver múltiplas colunas de data, use a coluna de data da transação
   - Preserve a correspondência: original_row deve corresponder à linha real do arquivo

2. VALORES: Normalize para número decimal (negativo = débito, positivo = crédito)
   - Mantenha o sinal original do arquivo

3. DESCRIÇÃO: Limpe e normalize histórico, mas mantenha informações importantes

4. NOME DO BANCO: 
   - EXTRAIA automaticamente do arquivo
   - Procure em: cabeçalhos, rodapés, nomes de colunas, descrições, ou padrões conhecidos
   - Exemplos: "Banco do Brasil", "Itaú", "Bradesco", "Caixa", "Santander", "Nubank", etc
   - Se encontrar, use o mesmo nome para todas as linhas
   - Se não encontrar, deixe vazio

5. GRUPO E SUBGRUPO (CLASSIFICAÇÃO PRINCIPAL - OBRIGATÓRIO):
   - **PRIORIDADE MÁXIMA:** Você DEVE analisar CADA linha e classificar por grupo e subgrupo PRIMEIRO
   - Analise a descrição/histórico e valor de CADA transação
   - Compare com a lista de grupos e subgrupos fornecida acima
   - Identifique o grupo e subgrupo mais apropriado baseado no contexto
   - Use palavras-chave no histórico para fazer a classificação:
     * "TED", "PIX", "DOC", "TRANSFERÊNCIA" → analise se é entrada ou saída
     * "FORNECEDOR", "PAGAMENTO", "COMPRA" → geralmente despesas/fornecedores
     * "SALÁRIO", "FOLHA", "FUNCIONÁRIO" → geralmente despesas/pessoal
     * "ALUGUEL", "ENERGIA", "ÁGUA", "TELEFONE" → geralmente despesas/operação
     * "RECEBIMENTO", "CLIENTE", "VENDA" → geralmente receitas
   - **SEMPRE retorne group_id e subgroup_id** - mesmo que seja null se não conseguir identificar
   - Retorne os IDs numéricos (group_id e subgroup_id) nos dados processados
   - Se o histórico não for claro, use o valor e sinal (positivo/negativo) para ajudar na classificação
   - **IMPORTANTE:** Grupo e subgrupo são a classificação PRINCIPAL para relatórios contábeis (DRE/DFC)

6. CONTA: Identifique número da conta se houver

7. SALDO: Identifique se houver coluna de saldo

**CRÍTICO - Correspondência de Linhas:**
- O campo "original_row" DEVE corresponder EXATAMENTE ao número da linha no arquivo original
- Se o arquivo tem 10 linhas, original_row deve ir de 1 a 10
- Use o índice da linha no array de dados fornecido + 1 (primeira linha = 1, segunda = 2, etc)
- Isso é ESSENCIAL para garantir que as datas correspondam corretamente

**IMPORTANTE - Regras para JSON válido:**
- Retorne APENAS JSON válido, sem texto adicional
- Escape corretamente caracteres especiais em strings
- Limite descrições a 500 caracteres

**Responda em formato JSON:**
{{
    "processed_data": [
        {{
            "date": "2024-01-15",
            "description": "TED RECEBIDA",
            "value": 5000.00,
            "bank_name": "Banco do Brasil",
            "account": "12345-6",
            "balance": 15000.00,
            "group_id": 1,
            "subgroup_id": 3,
            "original_row": 1
        }}
    ],
    "summary": {{
        "total_rows": 50,
        "processed": 50,
        "bank_name": "Banco do Brasil"
    }}
}}
"""
        return prompt
    
    def _create_prompt_process_accounts_payable(
        self,
        file_data: str,
        columns: List[str],
        data_sample: str,
        is_pdf_source: bool = False
    ) -> str:
        """
        Cria prompt específico para processar contas a pagar
        """
        prompt = f"""Você é um especialista em processamento de contas a pagar.

**Estrutura da Tabela:**
- account_name (String, obrigatório): Nome do credor/fornecedor
- due_date (Date, obrigatório): Data de vencimento YYYY-MM-DD
- value (Float, obrigatório): Valor a pagar
- cpf_cnpj (String, opcional): CPF/CNPJ
- month_ref (String, opcional): Mês de referência YYYY-MM
- paid (Boolean, opcional): Se já foi pago

**Colunas do arquivo:** {', '.join(columns)}
**Amostra:** {data_sample}
**Dados completos:** {file_data}

Processe e retorne em JSON com array "processed_data".
"""
        return prompt
    
    def _create_prompt_process_accounts_receivable(
        self,
        file_data: str,
        columns: List[str],
        data_sample: str,
        is_pdf_source: bool = False
    ) -> str:
        """
        Cria prompt específico para processar contas a receber
        """
        prompt = f"""Você é um especialista em processamento de contas a receber.

**Estrutura da Tabela:**
- account_name (String, obrigatório): Nome do devedor/cliente
- due_date (Date, obrigatório): Data de vencimento YYYY-MM-DD
- value (Float, obrigatório): Valor a receber
- cpf_cnpj (String, opcional): CPF/CNPJ
- month_ref (String, opcional): Mês de referência YYYY-MM
- received (Boolean, opcional): Se já foi recebido

**Colunas do arquivo:** {', '.join(columns)}
**Amostra:** {data_sample}
**Dados completos:** {file_data}

Processe e retorne em JSON com array "processed_data".
"""
        return prompt
    
    def _create_prompt_process_contracts(
        self,
        file_data: str,
        columns: List[str],
        data_sample: str,
        is_pdf_source: bool = False
    ) -> str:
        """
        Cria prompt específico para processar contratos
        """
        pdf_note = ""
        if is_pdf_source:
            pdf_note = """
**NOTA IMPORTANTE - Arquivo PDF:**
- Os dados podem incluir texto completo do PDF, cabeçalhos, rodapés e metadados
- Use TODAS as informações disponíveis para identificar campos
"""
        
        prompt = f"""Você é um especialista em processamento de contratos e eventos.

Analise o arquivo e estruture os dados para importação.

**Estrutura esperada:**
- contract_start (Date): Data de início do contrato
- event_date (Date): Data do evento
- service_value (Float): Valor do serviço
- displacement_value (Float): Valor do deslocamento
- event_type (String): Tipo de evento
- service_sold (String): Serviço vendido
- guests_count (Integer): Número de convidados
- contractor_name (String): Nome do contratante

{pdf_note}

**Colunas encontradas:** {', '.join(columns) if columns else 'Dados extraídos do texto'}
**Amostra:** {data_sample}
**Dados completos:** {file_data}

Processe e retorne em JSON com array "processed_data".
"""
        return prompt
    
    def _create_prompt_process_financial_investments(
        self,
        file_data: str,
        columns: List[str],
        data_sample: str,
        is_pdf_source: bool = False
    ) -> str:
        """
        Cria prompt específico para processar extratos de aplicações financeiras
        """
        pdf_note = ""
        if is_pdf_source:
            pdf_note = """
**NOTA IMPORTANTE - Arquivo PDF:**
- Os dados podem incluir texto completo do PDF, cabeçalhos, rodapés e metadados
- Use TODAS as informações disponíveis para identificar campos
"""
        
        prompt = f"""Você é um especialista em processamento de extratos de aplicações financeiras.

Analise o arquivo e estruture os dados para importação.

**Estrutura esperada:**
- date (Date): Data da operação
- investment_type (String): Tipo de aplicação (CDB, LCI, LCA, Tesouro, etc)
- institution (String): Instituição financeira
- operation_type (String): aplicado ou resgatado
- applied_value (Float): Valor aplicado
- redeemed_value (Float): Valor resgatado
- yield_value (Float): Rendimento
- balance (Float): Saldo atual

{pdf_note}

**Colunas encontradas:** {', '.join(columns) if columns else 'Dados extraídos do texto'}
**Amostra:** {data_sample}
**Dados completos:** {file_data}

Processe e retorne em JSON com array "processed_data".
"""
        return prompt
    
    def _create_prompt_process_credit_card_invoices(
        self,
        file_data: str,
        columns: List[str],
        data_sample: str,
        is_pdf_source: bool = False
    ) -> str:
        """
        Cria prompt específico para processar faturas de cartão de crédito
        """
        pdf_note = ""
        if is_pdf_source:
            pdf_note = """
**NOTA IMPORTANTE - Arquivo PDF:**
- Os dados podem incluir texto completo do PDF, cabeçalhos, rodapés e metadados
- Use TODAS as informações disponíveis para identificar campos
"""
        
        prompt = f"""Você é um especialista em processamento de faturas de cartão de crédito.

Analise o arquivo e estruture os dados para importação.

**Estrutura esperada:**
- transaction_date (Date): Data da transação
- description (String): Descrição da transação
- value (Float): Valor
- category (String): Categoria
- establishment (String): Estabelecimento
- installment_number (Integer): Número da parcela
- total_installments (Integer): Total de parcelas
- card_brand (String): Bandeira do cartão

{pdf_note}

**Colunas encontradas:** {', '.join(columns) if columns else 'Dados extraídos do texto'}
**Amostra:** {data_sample}
**Dados completos:** {file_data}

Processe e retorne em JSON com array "processed_data".
"""
        return prompt
    
    def _create_prompt_process_card_machine_statements(
        self,
        file_data: str,
        columns: List[str],
        data_sample: str,
        is_pdf_source: bool = False
    ) -> str:
        """
        Cria prompt específico para processar extratos de máquina de cartão
        """
        pdf_note = ""
        if is_pdf_source:
            pdf_note = """
**NOTA IMPORTANTE - Arquivo PDF:**
- Os dados podem incluir texto completo do PDF, cabeçalhos, rodapés e metadados
- Use TODAS as informações disponíveis para identificar campos
"""
        
        prompt = f"""Você é um especialista em processamento de extratos de máquina de cartão.

Analise o arquivo e estruture os dados para importação.

**Estrutura esperada:**
- date (Date): Data da transação
- gross_value (Float): Valor bruto
- fee (Float): Taxa cobrada
- net_value (Float): Valor líquido
- card_brand (String): Bandeira do cartão (Visa, Mastercard, Elo, etc)
- transaction_type (String): debito ou credito
- description (String): Descrição

{pdf_note}

**Colunas encontradas:** {', '.join(columns) if columns else 'Dados extraídos do texto'}
**Amostra:** {data_sample}
**Dados completos:** {file_data}

Processe e retorne em JSON com array "processed_data".
"""
        return prompt
    
    def _create_prompt_process_inventory(
        self,
        file_data: str,
        columns: List[str],
        data_sample: str,
        is_pdf_source: bool = False
    ) -> str:
        """
        Cria prompt específico para processar controle de estoque
        """
        pdf_note = ""
        if is_pdf_source:
            pdf_note = """
**NOTA IMPORTANTE - Arquivo PDF:**
- Os dados podem incluir texto completo do PDF, cabeçalhos, rodapés e metadados
- Use TODAS as informações disponíveis para identificar campos
"""
        
        prompt = f"""Você é um especialista em processamento de controle de estoque.

Analise o arquivo e estruture os dados para importação.

**Estrutura esperada:**
- product_name (String): Nome do produto
- quantity (Float): Quantidade (pode ser decimal)
- unit_value (Float): Valor unitário
- movement_date (Date): Data do movimento
- movement_type (String): entrada ou saida
- description (String): Descrição

{pdf_note}

**Colunas encontradas:** {', '.join(columns) if columns else 'Dados extraídos do texto'}
**Amostra:** {data_sample}
**Dados completos:** {file_data}

Processe e retorne em JSON com array "processed_data".
"""
        return prompt
    
    def process_and_structure_data(
        self,
        df: pd.DataFrame,
        import_type: str,
        pdf_full_data: Optional[Dict[str, Any]] = None,
        groups_subgroups: Optional[List[Dict[str, Any]]] = None,
        status_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Processa arquivo completo com IA e retorna dados estruturados prontos para importação
        
        Args:
            df: DataFrame com os dados do arquivo
            import_type: Tipo de importação (transactions, bank_statements, etc)
            pdf_full_data: Dados completos do PDF (opcional)
            groups_subgroups: Lista de grupos e subgrupos para classificação automática (opcional)
            status_callback: Função callback(status_message) para atualizar status em tempo real (opcional)
        
        Retorna:
        {
            'success': bool,
            'processed_data': List[Dict],  # Dados processados
            'summary': Dict,  # Estatísticas
            'issues': List[str],  # Problemas encontrados
            'error': str  # Erro se houver
        }
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'IA não configurada ou não disponível',
                'processed_data': [],
                'summary': {},
                'issues': []
            }
        
        try:
            if status_callback:
                status_callback("Analisando estrutura do arquivo...")
            
            # Se for PDF e tiver dados completos, usa informações adicionais
            pdf_context = ""
            if pdf_full_data:
                pdf_context = self._prepare_pdf_context(pdf_full_data, import_type)
            
            # Se DataFrame estiver vazio mas tiver dados de PDF, cria DataFrame do texto
            if df.empty and pdf_full_data and pdf_full_data.get('full_text'):
                # Tenta criar DataFrame básico do texto para processamento
                df = self._text_to_dataframe(pdf_full_data.get('full_text'))
            
            columns = list(df.columns) if not df.empty else []
            
            if status_callback:
                status_callback(f"Preparando dados para processamento ({len(df)} linhas encontradas)...")
            
            # Prepara amostra e dados completos
            # Processa TODO o arquivo, não apenas uma amostra limitada
            is_pdf = pdf_full_data is not None
            max_rows_sample = 30 if is_pdf else 20  # Amostra apenas para exibição no prompt
            
            # Processa TODAS as linhas do DataFrame
            if not df.empty:
                data_sample = self._prepare_data_sample(df, max_rows=max_rows_sample)
                # Usa TODO o DataFrame, não apenas uma amostra
                file_data_df = df.copy()
                file_data_df['_original_index'] = file_data_df.index
            else:
                data_sample = "Dados extraídos do texto do PDF"
                file_data_df = pd.DataFrame()
            
            # Prepara metadados e contexto
            file_metadata = ""
            if import_type == 'bank_statements' or is_pdf:
                metadata_parts = []
                
                if columns:
                    metadata_parts.append(f"- Nome das colunas: {', '.join(columns)}")
                
                if not df.empty:
                    metadata_parts.append(f"- Primeiras 3 linhas do arquivo:\n{df.head(3).to_string()}")
                    if len(df) > 3:
                        metadata_parts.append(f"- Últimas 3 linhas do arquivo:\n{df.tail(3).to_string()}")
                
                if pdf_context:
                    metadata_parts.append(pdf_context)
                
                if metadata_parts:
                    file_metadata = "**Informações adicionais do arquivo:**\n" + "\n".join(metadata_parts) + "\n"
            
            # Prepara dados para JSON
            if not df.empty:
                # Informa quantidade total de linhas no metadata
                total_rows = len(file_data_df)
                if status_callback:
                    status_callback(f"Processando {total_rows} linhas do arquivo...")
                
                file_data = json.dumps(
                    file_data_df.to_dict('records'),
                    indent=2,
                    default=str,
                    ensure_ascii=False
                )
            else:
                # Se não tem DataFrame, usa texto completo do PDF (SEM limitação)
                if pdf_full_data and pdf_full_data.get('full_text'):
                    full_text = pdf_full_data.get('full_text', '')
                    # Usa TODO o texto, não apenas 10k chars
                    file_data = full_text
                    if status_callback:
                        status_callback(f"Processando texto completo do PDF ({len(full_text)} caracteres)...")
                else:
                    file_data = ''
            
            # Adiciona metadados ao file_data
            if file_metadata:
                file_data = file_metadata + "\n**Dados do arquivo:**\n" + file_data
            
            if status_callback:
                status_callback("Criando prompt de processamento...")
            
            # Seleciona prompt baseado no tipo
            # Para PDFs, inclui flag indicando que há contexto adicional
            is_pdf_source = pdf_full_data is not None
            
            if import_type == 'transactions':
                prompt = self._create_prompt_process_transactions(
                    file_data, columns, data_sample, 
                    is_pdf_source=is_pdf_source,
                    groups_subgroups=groups_subgroups
                )
            elif import_type == 'bank_statements':
                prompt = self._create_prompt_process_bank_statements(
                    file_data, columns, data_sample, 
                    is_pdf_source=is_pdf_source,
                    groups_subgroups=groups_subgroups
                )
            elif import_type == 'contracts':
                prompt = self._create_prompt_process_contracts(file_data, columns, data_sample, is_pdf_source=is_pdf_source)
            elif import_type == 'accounts_payable':
                prompt = self._create_prompt_process_accounts_payable(file_data, columns, data_sample, is_pdf_source=is_pdf_source)
            elif import_type == 'accounts_receivable':
                prompt = self._create_prompt_process_accounts_receivable(file_data, columns, data_sample, is_pdf_source=is_pdf_source)
            elif import_type == 'financial_investments':
                prompt = self._create_prompt_process_financial_investments(file_data, columns, data_sample, is_pdf_source=is_pdf_source)
            elif import_type == 'credit_card_invoices':
                prompt = self._create_prompt_process_credit_card_invoices(file_data, columns, data_sample, is_pdf_source=is_pdf_source)
            elif import_type == 'card_machine_statements':
                prompt = self._create_prompt_process_card_machine_statements(file_data, columns, data_sample, is_pdf_source=is_pdf_source)
            elif import_type == 'inventory':
                prompt = self._create_prompt_process_inventory(file_data, columns, data_sample, is_pdf_source=is_pdf_source)
            else:
                return {
                    'success': False,
                    'error': f'Tipo de importação não suportado: {import_type}',
                    'processed_data': [],
                    'summary': {},
                    'issues': []
                }
            
            if status_callback:
                status_callback("Classificando por grupo e subgrupo...")
            
            # Chama IA
            response, error = self._call_ai(prompt, status_callback=status_callback)
            
            if error:
                if status_callback:
                    status_callback(f"❌ Erro: {error}")
                return {
                    'success': False,
                    'error': error,
                    'processed_data': [],
                    'summary': {},
                    'issues': []
                }
            
            if not response:
                if status_callback:
                    status_callback("❌ Sem resposta da IA")
                return {
                    'success': False,
                    'error': 'Sem resposta da IA',
                    'processed_data': [],
                    'summary': {},
                    'issues': []
                }
            
            if status_callback:
                status_callback("Processando resposta da IA...")
            
            # Parse da resposta
            try:
                # Remove markdown code blocks se existirem
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                elif '```' in response:
                    response = response.split('```')[1].split('```')[0]
                
                # Limpa a resposta
                response_clean = response.strip()
                
                # Tenta encontrar o JSON válido na resposta
                # Procura pelo primeiro { e último }
                start_idx = response_clean.find('{')
                if start_idx == -1:
                    raise json.JSONDecodeError("JSON não encontrado na resposta", response_clean, 0)
                
                # Procura o último } válido (pode haver múltiplos objetos)
                end_idx = response_clean.rfind('}')
                if end_idx == -1 or end_idx <= start_idx:
                    raise json.JSONDecodeError("JSON incompleto", response_clean, start_idx)
                
                # Extrai o JSON
                json_str = response_clean[start_idx:end_idx + 1]
                
                # Tenta parsear
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError as e:
                    # Se falhar, tenta reparar strings não terminadas
                    json_str_clean = json_str
                    
                    # Remove quebras de linha dentro de strings (exceto \n escapado)
                    json_str_clean = re.sub(r'(?<!\\)\n', ' ', json_str_clean)
                    json_str_clean = re.sub(r'(?<!\\)\r', ' ', json_str_clean)
                    json_str_clean = re.sub(r'(?<!\\)\t', ' ', json_str_clean)
                    
                    # Tenta encontrar e fechar strings não terminadas
                    # Procura por padrão: "texto sem fechamento
                    # Adiciona " antes de caracteres problemáticos
                    in_string = False
                    escape_next = False
                    result_chars = []
                    
                    for i, char in enumerate(json_str_clean):
                        if escape_next:
                            result_chars.append(char)
                            escape_next = False
                            continue
                        
                        if char == '\\':
                            result_chars.append(char)
                            escape_next = True
                            continue
                        
                        if char == '"':
                            in_string = not in_string
                            result_chars.append(char)
                        elif in_string:
                            # Dentro de string, substitui caracteres problemáticos
                            if char in ['\n', '\r', '\t']:
                                result_chars.append(' ')
                            elif char == '\x00':  # Null bytes
                                result_chars.append(' ')
                            else:
                                result_chars.append(char)
                        else:
                            result_chars.append(char)
                    
                    # Se ainda estiver em string no final, fecha ela
                    if in_string:
                        result_chars.append('"')
                    
                    json_str_clean = ''.join(result_chars)
                    
                    try:
                        result = json.loads(json_str_clean)
                    except json.JSONDecodeError as e2:
                        # Tenta reparar problemas comuns de JSON
                        json_str_final = self._repair_json(json_str_clean, e2)
                        try:
                            result = json.loads(json_str_final)
                        except json.JSONDecodeError as e3:
                            # Última tentativa: extrai apenas o que é possível parsear
                            result = self._extract_partial_json(json_str_clean)
                            if not result:
                                # Se ainda falhar, levanta o erro com contexto
                                raise e2
                
                # Se processou apenas amostra, aplica padrões ao resto
                processed_data = result.get('processed_data', [])
                
                # Valida e corrige datas usando os dados originais do arquivo
                # Garante que as datas correspondam exatamente ao arquivo original
                from utils.validators import parse_date
                
                # Identifica coluna de data no arquivo original
                date_col = None
                for col in file_data_df.columns:
                    if col == '_original_index':
                        continue
                    col_lower = str(col).lower().strip()
                    if any(keyword in col_lower for keyword in ['data', 'date', 'dt', 'transacao', 'lancamento', 'vencimento', 'dia']):
                        date_col = col
                        break
                
                # Se encontrou coluna de data, força o uso das datas originais
                if date_col:
                    for idx, item in enumerate(processed_data):
                        # Tenta usar original_row, mas se não corresponder, usa o índice do array
                        original_row = item.get('original_row', 0)
                        original_idx = original_row - 1 if original_row > 0 else idx
                        
                        # Garante que o índice esteja dentro do range
                        if original_idx < 0 or original_idx >= len(file_data_df):
                            original_idx = idx
                        
                        # Se o índice estiver dentro do range processado, usa a data original
                        if 0 <= original_idx < len(file_data_df):
                            original_row_data = file_data_df.iloc[original_idx]
                            
                            if date_col in original_row_data:
                                original_date = str(original_row_data[date_col])
                                if original_date and original_date != 'nan' and original_date.strip() and original_date.lower() not in ['none', 'null', '']:
                                    try:
                                        # Parse da data original - FORÇA o uso
                                        parsed_original = parse_date(original_date)
                                        if parsed_original:
                                            # FORÇA o uso da data original parseada
                                            item['date'] = parsed_original.strftime('%Y-%m-%d')
                                    except Exception as e:
                                        # Se não conseguir parsear, mantém a data processada pela IA
                                        pass
                
                # Remove _original_index dos dados processados se existir
                for item in processed_data:
                    item.pop('_original_index', None)
                
                # Se houver mais linhas, processa o resto com padrões identificados
                if max_rows_to_process < len(df):
                    # Por enquanto, retorna apenas as processadas
                    # Em produção, poderia aplicar transformações identificadas
                    pass
                
                if status_callback:
                    status_callback(f"✅ Processamento concluído! {len(processed_data)} linhas processadas.")
                
                return {
                    'success': True,
                    'processed_data': processed_data,
                    'summary': result.get('summary', {}),
                    'issues': result.get('issues', []),
                    'error': None
                }
                
            except json.JSONDecodeError as e:
                # Tenta extrair informações úteis do erro
                error_pos = getattr(e, 'pos', None)
                error_line = getattr(e, 'lineno', None)
                error_col = getattr(e, 'colno', None)
                
                error_msg = f'Erro ao parsear resposta da IA: {str(e)}'
                if error_line and error_col:
                    error_msg += f' (linha {error_line}, coluna {error_col})'
                
                # Mostra contexto do erro
                if error_pos and error_pos < len(response):
                    start = max(0, error_pos - 100)
                    end = min(len(response), error_pos + 100)
                    context = response[start:end]
                    error_msg += f'\nContexto: ...{context}...'
                
                if status_callback:
                    status_callback(f"❌ Erro ao processar resposta: {error_msg}")
                
                return {
                    'success': False,
                    'error': error_msg,
                    'processed_data': [],
                    'summary': {},
                    'issues': [],
                    'raw_response': response[:2000] if len(response) > 2000 else response
                }
                
        except Exception as e:
            if status_callback:
                status_callback(f"❌ Erro no processamento: {str(e)}")
            return {
                'success': False,
                'error': f'Erro ao processar dados: {str(e)}',
                'processed_data': [],
                'summary': {},
                'issues': []
            }

    def analyze_structure(
        self,
        df: pd.DataFrame,
        import_type: str
    ) -> Dict[str, Any]:
        """
        Realiza análise estrutural completa do arquivo
        """
        if not self.is_available():
            return {}
        
        try:
            columns = list(df.columns)
            data_sample = self._prepare_data_sample(df, max_rows=10)
            prompt = self._create_prompt_structural_analysis(columns, data_sample, import_type)
            
            response, error = self._call_ai(prompt)
            
            if error:
                print(f"Erro na análise estrutural: {error}")
                return {}
            
            if response:
                try:
                    if '```json' in response:
                        response = response.split('```json')[1].split('```')[0]
                    elif '```' in response:
                        response = response.split('```')[1].split('```')[0]
                    
                    return json.loads(response.strip())
                except json.JSONDecodeError as e:
                    print(f"Erro ao parsear análise estrutural: {e}")
                    return {}
        except Exception as e:
            print(f"Erro na análise estrutural: {e}")
        
        return {}

    def intelligent_mapping(
        self,
        df: pd.DataFrame,
        import_type: str,
        structural_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Realiza mapeamento inteligente com contexto
        """
        if not self.is_available():
            return {}
        
        try:
            columns = list(df.columns)
            data_sample = self._prepare_data_sample(df, max_rows=15)
            analysis_str = json.dumps(structural_analysis, indent=2, ensure_ascii=False) if structural_analysis else None
            prompt = self._create_prompt_intelligent_mapping(columns, data_sample, import_type, analysis_str)
            
            response, error = self._call_ai(prompt)
            
            if error:
                print(f"Erro no mapeamento inteligente: {error}")
                return {}
            
            if response:
                try:
                    if '```json' in response:
                        response = response.split('```json')[1].split('```')[0]
                    elif '```' in response:
                        response = response.split('```')[1].split('```')[0]
                    
                    return json.loads(response.strip())
                except json.JSONDecodeError as e:
                    print(f"Erro ao parsear mapeamento inteligente: {e}")
                    return {}
        except Exception as e:
            print(f"Erro no mapeamento inteligente: {e}")
        
        return {}

    def normalize_data(
        self,
        df: pd.DataFrame,
        import_type: str,
        mapping: Dict[str, str],
        structural_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Normaliza e estrutura os dados
        """
        if not self.is_available():
            return {}
        
        try:
            # Prepara dados (primeiras 20 linhas)
            sample_df = df.head(20)
            file_data = json.dumps(sample_df.to_dict('records'), indent=2, default=str, ensure_ascii=False)
            analysis_str = json.dumps(structural_analysis, indent=2, ensure_ascii=False) if structural_analysis else "{}"
            
            prompt = self._create_prompt_normalization(file_data, import_type, analysis_str, mapping)
            
            response, error = self._call_ai(prompt)
            
            if error:
                print(f"Erro na normalização: {error}")
                return {}
            
            if response:
                try:
                    if '```json' in response:
                        response = response.split('```json')[1].split('```')[0]
                    elif '```' in response:
                        response = response.split('```')[1].split('```')[0]
                    
                    return json.loads(response.strip())
                except json.JSONDecodeError as e:
                    print(f"Erro ao parsear normalização: {e}")
                    return {}
        except Exception as e:
            print(f"Erro na normalização: {e}")
        
        return {}

    def validate_data(
        self,
        normalized_data: List[Dict[str, Any]],
        import_type: str
    ) -> Dict[str, Any]:
        """
        Valida e corrige dados normalizados
        """
        if not self.is_available():
            return {}
        
        try:
            # Limita a 50 registros para não exceder tokens
            data_to_validate = normalized_data[:50]
            data_str = json.dumps(data_to_validate, indent=2, ensure_ascii=False)
            
            prompt = self._create_prompt_validation(data_str, import_type)
            
            response, error = self._call_ai(prompt)
            
            if error:
                print(f"Erro na validação: {error}")
                return {}
            
            if response:
                try:
                    if '```json' in response:
                        response = response.split('```json')[1].split('```')[0]
                    elif '```' in response:
                        response = response.split('```')[1].split('```')[0]
                    
                    return json.loads(response.strip())
                except json.JSONDecodeError as e:
                    print(f"Erro ao parsear validação: {e}")
                    return {}
        except Exception as e:
            print(f"Erro na validação: {e}")
        
        return {}

    def infer_fields(
        self,
        df: pd.DataFrame,
        import_type: str,
        missing_fields: List[str],
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Infere campos faltantes
        """
        if not self.is_available():
            return {}
        
        try:
            # Prepara amostra de dados
            sample_df = df.head(20)
            available_data = json.dumps(sample_df.to_dict('records'), indent=2, default=str, ensure_ascii=False)
            
            prompt = self._create_prompt_inference(available_data, import_type, missing_fields, context)
            
            response, error = self._call_ai(prompt)
            
            if error:
                print(f"Erro na inferência: {error}")
                return {}
            
            if response:
                try:
                    if '```json' in response:
                        response = response.split('```json')[1].split('```')[0]
                    elif '```' in response:
                        response = response.split('```')[1].split('```')[0]
                    
                    return json.loads(response.strip())
                except json.JSONDecodeError as e:
                    print(f"Erro ao parsear inferência: {e}")
                    return {}
        except Exception as e:
            print(f"Erro na inferência: {e}")
        
        return {}

