"""
Serviço de classificação de dados usando IA
Focado exclusivamente em classificar dados já extraídos (não faz extração)
"""
import pandas as pd
from typing import Dict, List, Optional, Any
import json
from sqlalchemy.orm import Session

from config.ai_config import AIConfigManager


class AIClassifier:
    """
    Serviço para classificar dados usando IA
    Recebe DataFrame já extraído e classifica com group_id e subgroup_id
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o classificador com configuração do banco
        """
        self.db = db
        self.config = AIConfigManager.get_config_dict(db)
        self._client = None
    
    def _get_client(self):
        """
        Obtém cliente de IA configurado
        """
        if not self.config:
            return None, "Configuração de IA não encontrada"
        
        if self._client is not None:
            return self._client, None
        
        provider = self.config.get('provider', '')
        api_key = self.config.get('api_key', '').strip()
        model = self.config.get('model', '')
        
        if not api_key:
            return None, "API key não configurada"
        
        try:
            if provider == 'openai':
                from openai import OpenAI
                self._client = OpenAI(api_key=api_key)
            elif provider == 'gemini':
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self._client = genai.GenerativeModel(model)
            elif provider == 'groq':
                from groq import Groq
                self._client = Groq(api_key=api_key)
            elif provider == 'ollama':
                # Ollama não precisa de API key, usa URL local
                from openai import OpenAI
                base_url = self.config.get('base_url', 'http://localhost:11434/v1')
                api_key = 'ollama'  # Placeholder
                self._client = OpenAI(base_url=base_url, api_key=api_key)
            else:
                return None, f"Provedor {provider} não suportado"
            
            return self._client, None
        except Exception as e:
            return None, f"Erro ao inicializar cliente de IA: {str(e)}"
    
    def is_available(self) -> bool:
        """
        Verifica se IA está disponível
        """
        client, error = self._get_client()
        return client is not None
    
    def classify_dataframe(
        self,
        df: pd.DataFrame,
        groups_subgroups: Optional[List[Dict[str, Any]]] = None,
        import_type: Optional[str] = None,
        status_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Classifica DataFrame completo usando IA
        
        Args:
            df: DataFrame já extraído (completo)
            groups_subgroups: Lista de grupos e subgrupos para classificação
            import_type: Tipo de importação (opcional, será detectado se None)
            status_callback: Função callback(status_message) para atualizar status
        
        Returns:
            {
                'success': bool,
                'classified_data': List[Dict],  # Dados classificados
                'detected_type': str,  # Tipo detectado (se não foi especificado)
                'issues': List[str],
                'error': str
            }
        """
        if df is None or df.empty:
            return {
                'success': False,
                'error': 'DataFrame vazio - nenhum dado para classificar',
                'classified_data': [],
                'detected_type': import_type,
                'issues': []
            }
        
        if not self.is_available():
            return {
                'success': False,
                'error': 'IA não configurada ou não disponível',
                'classified_data': [],
                'detected_type': import_type,
                'issues': []
            }
        
        try:
            # Prepara dados para classificação
            if status_callback:
                status_callback(f"Preparando {len(df)} registros para classificação...")
            
            # Converte DataFrame para formato de lista de dicionários
            records = df.to_dict('records')
            
            # Classifica em lotes para melhor performance
            batch_size = 100  # Processa 100 registros por vez
            all_classified = []
            issues = []
            
            total_batches = (len(records) + batch_size - 1) // batch_size
            
            for batch_idx in range(0, len(records), batch_size):
                batch = records[batch_idx:batch_idx + batch_size]
                current_batch = (batch_idx // batch_size) + 1
                
                if status_callback:
                    status_callback(f"Classificando lote {current_batch}/{total_batches} ({len(batch)} registros)...")
                
                # Classifica lote
                batch_result = self.classify_batch(
                    batch,
                    groups_subgroups,
                    import_type,
                    batch_start_idx=batch_idx
                )
                
                if batch_result.get('success'):
                    all_classified.extend(batch_result.get('classified_data', []))
                    if batch_result.get('issues'):
                        issues.extend(batch_result.get('issues', []))
                else:
                    # Se um lote falhar, adiciona registros sem classificação
                    issues.append(f"Erro ao classificar lote {current_batch}: {batch_result.get('error', 'Erro desconhecido')}")
                    # Adiciona registros sem classificação (group_id e subgroup_id como None)
                    for record in batch:
                        record['group_id'] = None
                        record['subgroup_id'] = None
                        record['classification_confidence'] = 0.0
                        all_classified.append(record)
            
            # Detecta tipo se não foi especificado
            detected_type = import_type
            if not detected_type and all_classified:
                detected_type = self.detect_data_type(df)
            
            return {
                'success': True,
                'classified_data': all_classified,
                'detected_type': detected_type,
                'issues': issues
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Erro ao classificar dados: {str(e)}",
                'classified_data': [],
                'detected_type': import_type,
                'issues': [str(e)]
            }
    
    def classify_batch(
        self,
        records: List[Dict],
        groups_subgroups: Optional[List[Dict[str, Any]]] = None,
        import_type: Optional[str] = None,
        batch_start_idx: int = 0
    ) -> Dict[str, Any]:
        """
        Classifica um lote de registros usando IA
        
        Args:
            records: Lista de registros a classificar
            groups_subgroups: Lista de grupos e subgrupos
            import_type: Tipo de importação
            batch_start_idx: Índice inicial do lote (para numeração)
        
        Returns:
            Dict com classified_data e issues
        """
        if not records:
            return {
                'success': True,
                'classified_data': [],
                'issues': []
            }
        
        client, error = self._get_client()
        if not client:
            return {
                'success': False,
                'error': error or 'Cliente de IA não disponível',
                'classified_data': [],
                'issues': []
            }
        
        try:
            # Prepara prompt de classificação
            prompt = self._build_classification_prompt(records, groups_subgroups, import_type)
            
            # Chama IA
            provider = self.config.get('provider', '')
            model = self.config.get('model', '')
            
            if provider == 'openai':
                # Aumenta max_tokens para lotes maiores
                estimated_tokens = len(records) * 50  # Estimativa: ~50 tokens por registro
                max_tokens = max(4000, min(16000, estimated_tokens + 2000))  # Entre 4k e 16k
                
                response = client.chat.completions.create(
                    model=model,
                    messages=[{'role': 'user', 'content': prompt}],
                    temperature=0.1,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"} if "gpt-4o" in model.lower() or "gpt-4-turbo" in model.lower() else None
                )
                content = response.choices[0].message.content
            elif provider == 'gemini':
                response = client.generate_content(prompt)
                content = response.text
            elif provider == 'groq':
                response = client.chat.completions.create(
                    model=model,
                    messages=[{'role': 'user', 'content': prompt}],
                    temperature=0.1
                )
                content = response.choices[0].message.content
            elif provider == 'ollama':
                response = client.chat.completions.create(
                    model=model,
                    messages=[{'role': 'user', 'content': prompt}],
                    temperature=0.1
                )
                content = response.choices[0].message.content
            else:
                return {
                    'success': False,
                    'error': f'Provedor {provider} não suportado',
                    'classified_data': [],
                    'issues': []
                }
            
            # Extrai JSON da resposta
            json_data = self._extract_json_from_response(content)
            
            if not json_data:
                # Tenta extrair novamente com método mais agressivo
                json_data = self._extract_json_from_response_aggressive(content)
                
                if not json_data:
                    # Se ainda não conseguiu, tenta criar classificação básica dos registros originais
                    return {
                        'success': False,
                        'error': 'Resposta da IA não contém dados classificados válidos',
                        'classified_data': self._create_fallback_classification(records),
                        'issues': [
                            'Resposta da IA não contém JSON válido',
                            f'Resposta recebida (primeiros 500 chars): {content[:500] if content else "vazia"}'
                        ]
                    }
            
            if 'classified_records' not in json_data:
                # Tenta encontrar dados classificados com nomes alternativos
                classified_records = (
                    json_data.get('classified_records') or
                    json_data.get('records') or
                    json_data.get('data') or
                    json_data.get('results') or
                    []
                )
                
                if not classified_records:
                    return {
                        'success': False,
                        'error': 'Resposta da IA não contém dados classificados válidos',
                        'classified_data': self._create_fallback_classification(records),
                        'issues': [
                            'Resposta da IA não contém campo "classified_records"',
                            f'Estrutura recebida: {list(json_data.keys())}',
                            f'Resposta (primeiros 500 chars): {content[:500] if content else "vazia"}'
                        ]
                    }
                
                # Se encontrou dados com nome alternativo, normaliza
                json_data['classified_records'] = classified_records
            
            classified_records = json_data.get('classified_records', [])
            issues = json_data.get('issues', [])
            
            # Valida e corrige registros classificados
            # CRÍTICO: Garante que a estrutura original seja preservada
            validated_records = []
            for idx, original_record in enumerate(records):
                # Procura registro correspondente na resposta da IA
                classified_record = None
                if idx < len(classified_records):
                    classified_record = classified_records[idx]
                else:
                    # Tenta encontrar por índice ou campos únicos
                    for cr in classified_records:
                        # Compara campos chave para encontrar correspondência
                        if self._records_match(original_record, cr):
                            classified_record = cr
                            break
                
                # SEMPRE começa com o registro original para preservar estrutura
                validated_record = dict(original_record)
                
                if classified_record:
                    # Extrai APENAS os campos de classificação da resposta da IA
                    # Mantém TODOS os outros campos do registro original
                    validated_record['group_id'] = self._validate_id(classified_record.get('group_id'))
                    validated_record['subgroup_id'] = self._validate_id(classified_record.get('subgroup_id'))
                    validated_record['classification_confidence'] = float(classified_record.get('classification_confidence', 0.0))
                    
                    # Validação crítica: verifica se a IA não alterou campos originais
                    original_keys = set(original_record.keys())
                    classified_keys = set(classified_record.keys())
                    
                    # Remove campos de classificação da comparação
                    original_keys.discard('group_id')
                    original_keys.discard('subgroup_id')
                    original_keys.discard('classification_confidence')
                    classified_keys.discard('group_id')
                    classified_keys.discard('subgroup_id')
                    classified_keys.discard('classification_confidence')
                    
                    # Se a IA adicionou ou removeu campos, usa apenas os originais
                    if original_keys != classified_keys:
                        issues.append(f"Registro {idx+1}: IA alterou estrutura (campos originais preservados)")
                        # Garante que todos os campos originais estão presentes
                        for key in original_keys:
                            if key not in validated_record:
                                validated_record[key] = original_record.get(key)
                else:
                    # Registro não foi classificado, adiciona sem classificação
                    validated_record['group_id'] = None
                    validated_record['subgroup_id'] = None
                    validated_record['classification_confidence'] = 0.0
                
                validated_records.append(validated_record)
            
            # Garante que todos os registros foram processados
            if len(validated_records) < len(records):
                issues.append(f"Apenas {len(validated_records)} de {len(records)} registros foram processados")
                # Adiciona registros faltantes sem classificação
                for idx in range(len(validated_records), len(records)):
                    record = records[idx].copy()
                    record['group_id'] = None
                    record['subgroup_id'] = None
                    record['classification_confidence'] = 0.0
                    validated_records.append(record)
            
            classified_records = validated_records
            
            return {
                'success': True,
                'classified_data': classified_records,
                'issues': issues
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Erro ao classificar lote: {str(e)}",
                'classified_data': [],
                'issues': [str(e)]
            }
    
    def _build_classification_prompt(
        self,
        records: List[Dict],
        groups_subgroups: Optional[List[Dict[str, Any]]] = None,
        import_type: Optional[str] = None
    ) -> str:
        """
        Constrói prompt para classificação por IA
        """
        # Prepara informações de grupos/subgrupos
        groups_info = ""
        if groups_subgroups:
            groups_list = []
            for group in groups_subgroups:
                group_name = group.get('name', '')
                group_id = group.get('id', '')
                subgroups = group.get('subgroups', [])
                subgroup_list = []
                for sg in subgroups:
                    sg_name = sg.get('name', '')
                    sg_id = sg.get('id', '')
                    subgroup_list.append(f"  - {sg_name} (ID: {sg_id})")
                
                groups_list.append(f"- {group_name} (ID: {group_id}):")
                groups_list.extend(subgroup_list)
            
            groups_info = "\n".join(groups_list)
        
        # Prepara amostra de dados com estrutura explícita
        # Mostra estrutura completa dos primeiros registros
        sample_records = records[:min(10, len(records))]
        
        # Cria exemplo explícito da estrutura esperada
        example_structure = {}
        if sample_records:
            example_structure = sample_records[0].copy()
            # Remove campos de classificação se existirem
            example_structure.pop('group_id', None)
            example_structure.pop('subgroup_id', None)
            example_structure.pop('classification_confidence', None)
        
        sample_data = json.dumps(sample_records, ensure_ascii=False, indent=2, default=str)
        structure_example = json.dumps(example_structure, ensure_ascii=False, indent=2, default=str)
        
        # Lista todas as colunas/chaves dos registros
        all_keys = set()
        for record in sample_records:
            all_keys.update(record.keys())
        all_keys.discard('group_id')
        all_keys.discard('subgroup_id')
        all_keys.discard('classification_confidence')
        columns_list = sorted(list(all_keys))
        
        prompt = f"""Você é um especialista em classificação contábil. Sua tarefa é classificar registros financeiros por grupo e subgrupo.

Tipo de dado: {import_type or 'Não especificado - detecte automaticamente'}

Grupos e Subgrupos disponíveis para classificação:
{groups_info if groups_info else 'Nenhum grupo disponível - use group_id e subgroup_id como null'}

ESTRUTURA DOS DADOS (IMPORTANTE - MANTENHA EXATAMENTE ESTA ESTRUTURA):
Colunas/chaves dos registros: {', '.join(columns_list)}

Exemplo de estrutura de um registro:
{structure_example}

Dados a classificar ({len(records)} registros):
{sample_data}
{f'... e mais {len(records) - 10} registros' if len(records) > 10 else ''}

INSTRUÇÕES CRÍTICAS:
1. MANTENHA A ESTRUTURA ORIGINAL: Cada registro DEVE manter TODAS as colunas/chaves originais com seus valores originais
2. NÃO ALTERE: Não renomeie colunas, não transforme valores em nomes de colunas, não mude a estrutura
3. APENAS ADICIONE: Adicione APENAS os campos group_id, subgroup_id e classification_confidence
4. Para CADA registro, analise a descrição e valor para identificar grupo e subgrupo
5. Retorne group_id e subgroup_id (IDs numéricos) para cada registro
6. Informe classification_confidence (0.0 a 1.0) para cada classificação
7. Se não conseguir classificar com confiança, use null para group_id/subgroup_id e confidence baixa

FORMATO DE RESPOSTA (JSON válido):
{{
    "classified_records": [
        {{
            "coluna1": "valor_original_1",
            "coluna2": "valor_original_2",
            ... (TODAS as colunas originais com seus valores originais) ...,
            "group_id": 1,
            "subgroup_id": 2,
            "classification_confidence": 0.85
        }}
    ],
    "issues": ["Lista de problemas encontrados, se houver"]
}}

REGRAS ABSOLUTAS:
- Retorne TODOS os {len(records)} registros classificados
- MANTENHA TODOS os campos originais de cada registro EXATAMENTE como estão
- NÃO transforme valores em nomes de colunas
- NÃO renomeie colunas existentes
- NÃO altere valores dos campos originais
- Adicione APENAS: group_id, subgroup_id e classification_confidence
- Retorne APENAS JSON válido, sem texto adicional ou explicações
"""
        
        return prompt
    
    def detect_data_type(self, df: pd.DataFrame) -> str:
        """
        Detecta tipo de dado automaticamente baseado nas colunas do DataFrame
        """
        if df is None or df.empty:
            return 'transactions'  # Default
        
        columns_lower = [col.lower() for col in df.columns]
        
        # Padrões de detecção
        if any(col in columns_lower for col in ['bank_name', 'banco', 'account', 'conta', 'agencia', 'agência']):
            return 'bank_statements'
        elif any(col in columns_lower for col in ['contract_start', 'event_date', 'contractor_name', 'contratante']):
            return 'contracts'
        elif any(col in columns_lower for col in ['due_date', 'vencimento']) and any(col in columns_lower for col in ['account_name', 'credor', 'devedor']):
            if 'credor' in columns_lower or 'fornecedor' in columns_lower:
                return 'accounts_payable'
            else:
                return 'accounts_receivable'
        elif any(col in columns_lower for col in ['product_name', 'produto', 'quantity', 'quantidade']):
            return 'inventory'
        elif any(col in columns_lower for col in ['transaction_date', 'data_transacao']):
            return 'credit_card_invoices'
        else:
            return 'transactions'  # Default
    
    def _validate_id(self, id_value: Any) -> Optional[int]:
        """
        Valida e converte ID para inteiro ou None
        """
        if id_value is None:
            return None
        try:
            id_int = int(id_value)
            return id_int if id_int > 0 else None
        except (ValueError, TypeError):
            return None
    
    def _records_match(self, record1: Dict, record2: Dict) -> bool:
        """
        Verifica se dois registros correspondem (para matching quando a ordem pode estar diferente)
        """
        # Compara campos chave comuns
        key_fields = ['date', 'value', 'description', 'descricao', 'valor', 'data']
        
        for field in key_fields:
            if field in record1 and field in record2:
                val1 = record1.get(field)
                val2 = record2.get(field)
                if val1 is not None and val2 is not None:
                    # Compara valores (tolerante a diferenças de tipo)
                    try:
                        if str(val1).strip() == str(val2).strip():
                            return True
                    except:
                        pass
        
        return False
    
    def _extract_json_from_response(self, content: str) -> Optional[Dict]:
        """
        Extrai JSON da resposta da IA
        """
        import re
        
        if not content:
            return None
        
        # Remove markdown code blocks
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        content = content.strip()
        
        # Procura por JSON (procura por chaves balanceadas)
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(0)
                # Tenta encontrar chaves balanceadas
                start = json_str.find('{')
                if start != -1:
                    depth = 0
                    end = start
                    for i, char in enumerate(json_str[start:], start):
                        if char == '{':
                            depth += 1
                        elif char == '}':
                            depth -= 1
                            if depth == 0:
                                end = i + 1
                                break
                    
                    if depth == 0:
                        balanced_json = json_str[start:end]
                        return json.loads(balanced_json)
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Tenta parse direto
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _extract_json_from_response_aggressive(self, content: str) -> Optional[Dict]:
        """
        Extrai JSON da resposta da IA usando método mais agressivo
        """
        import re
        
        if not content:
            return None
        
        # Remove tudo antes da primeira {
        start_idx = content.find('{')
        if start_idx == -1:
            return None
        
        content = content[start_idx:]
        
        # Tenta encontrar JSON válido procurando por padrões
        # Procura por "classified_records" ou "records" no conteúdo
        patterns = [
            r'\{[^{}]*"classified_records"[^{}]*\}',
            r'\{[^{}]*"records"[^{}]*\}',
            r'\{.*"classified_records".*\}',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                try:
                    # Tenta extrair JSON balanceado a partir do match
                    json_str = match.group(0)
                    start = json_str.find('{')
                    if start != -1:
                        # Encontra chave de fechamento balanceada
                        depth = 0
                        end = start
                        for i, char in enumerate(json_str[start:], start):
                            if char == '{':
                                depth += 1
                            elif char == '}':
                                depth -= 1
                                if depth == 0:
                                    end = i + 1
                                    break
                        
                        if depth == 0:
                            balanced_json = json_str[start:end]
                            return json.loads(balanced_json)
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return None
    
    def _create_fallback_classification(self, records: List[Dict]) -> List[Dict]:
        """
        Cria classificação básica quando a IA falha
        Adiciona campos de classificação vazios aos registros originais
        """
        fallback_records = []
        for record in records:
            record_copy = dict(record)
            record_copy['group_id'] = None
            record_copy['subgroup_id'] = None
            record_copy['classification_confidence'] = 0.0
            fallback_records.append(record_copy)
        return fallback_records

