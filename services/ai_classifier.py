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
                response = client.chat.completions.create(
                    model=model,
                    messages=[{'role': 'user', 'content': prompt}],
                    temperature=0.1,
                    max_tokens=4000
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
            
            if not json_data or 'classified_records' not in json_data:
                return {
                    'success': False,
                    'error': 'Resposta da IA não contém dados classificados válidos',
                    'classified_data': [],
                    'issues': ['Resposta da IA não contém JSON válido']
                }
            
            classified_records = json_data.get('classified_records', [])
            issues = json_data.get('issues', [])
            
            # Garante que todos os registros foram classificados
            if len(classified_records) < len(records):
                issues.append(f"Apenas {len(classified_records)} de {len(records)} registros foram classificados")
                # Adiciona registros faltantes sem classificação
                for idx in range(len(classified_records), len(records)):
                    record = records[idx].copy()
                    record['group_id'] = None
                    record['subgroup_id'] = None
                    record['classification_confidence'] = 0.0
                    classified_records.append(record)
            
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
        
        # Prepara amostra de dados
        sample_data = json.dumps(records[:10], ensure_ascii=False, indent=2, default=str)
        
        prompt = f"""Você é um especialista em classificação contábil. Sua tarefa é classificar registros financeiros por grupo e subgrupo.

Tipo de dado: {import_type or 'Não especificado - detecte automaticamente'}

Grupos e Subgrupos disponíveis para classificação:
{groups_info if groups_info else 'Nenhum grupo disponível - use group_id e subgroup_id como null'}

Dados a classificar ({len(records)} registros):
{sample_data}
{f'... e mais {len(records) - 10} registros' if len(records) > 10 else ''}

INSTRUÇÕES:
1. Para CADA registro, analise a descrição e valor
2. Identifique o grupo e subgrupo mais apropriado baseado no contexto
3. Retorne group_id e subgroup_id (IDs numéricos) para cada registro
4. Informe classification_confidence (0.0 a 1.0) para cada classificação
5. Se não conseguir classificar com confiança, use null para group_id/subgroup_id e confidence baixa

FORMATO DE RESPOSTA (JSON válido):
{{
    "classified_records": [
        {{
            ... (todos os campos do registro original) ...,
            "group_id": 1,
            "subgroup_id": 2,
            "classification_confidence": 0.85
        }}
    ],
    "issues": ["Lista de problemas encontrados, se houver"]
}}

IMPORTANTE:
- Retorne TODOS os {len(records)} registros classificados
- Mantenha todos os campos originais de cada registro
- Adicione apenas group_id, subgroup_id e classification_confidence
- Retorne APENAS JSON válido, sem texto adicional
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
        
        # Procura por JSON
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Tenta parse direto
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        return None

