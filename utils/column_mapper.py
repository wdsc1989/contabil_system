"""
Utilitário para mapeamento inteligente de colunas
"""
from typing import Dict, List, Optional
import difflib
import pandas as pd
from sqlalchemy.orm import Session


class ColumnMapper:
    """
    Classe para sugerir mapeamentos automáticos de colunas
    """

    # Dicionário de sinônimos para cada campo alvo
    SYNONYMS = {
        'date': ['data', 'dt', 'date', 'fecha', 'datum', 'dia'],
        'description': ['descricao', 'description', 'desc', 'historico', 'memo', 'detalhes'],
        'value': ['valor', 'value', 'amount', 'montante', 'vlr', 'quantia'],
        'balance': ['saldo', 'balance', 'balanço'],
        'type': ['tipo', 'type', 'categoria_tipo'],
        'category': ['categoria', 'category', 'cat'],
        'account': ['conta', 'account', 'acc'],
        'contract_start': ['inicio_contrato', 'data_inicio', 'contract_start', 'start_date'],
        'event_date': ['data_evento', 'event_date', 'data_realizacao'],
        'service_value': ['valor_servico', 'service_value', 'valor'],
        'displacement_value': ['valor_deslocamento', 'displacement_value', 'deslocamento'],
        'event_type': ['tipo_evento', 'event_type', 'tipo'],
        'service_sold': ['servico_vendido', 'service_sold', 'servico'],
        'guests_count': ['numero_convidados', 'guests_count', 'convidados', 'qtd_convidados'],
        'contractor_name': ['nome_contratante', 'contractor_name', 'contratante', 'cliente'],
        'payment_terms': ['forma_pagamento', 'payment_terms', 'pagamento'],
        'status': ['status', 'situacao', 'estado'],
        'account_name': ['nome_conta', 'account_name', 'fornecedor', 'cliente'],
        'cpf_cnpj': ['cpf_cnpj', 'cpf', 'cnpj', 'documento'],
        'due_date': ['vencimento', 'due_date', 'data_vencimento'],
        'paid': ['pago', 'paid', 'quitado'],
        'received': ['recebido', 'received', 'quitado']
    }

    @staticmethod
    def normalize_column_name(col_name: str) -> str:
        """
        Normaliza nome de coluna (lowercase, sem acentos, sem espaços)
        """
        import unicodedata
        
        # Remove acentos
        col_name = unicodedata.normalize('NFKD', col_name)
        col_name = col_name.encode('ASCII', 'ignore').decode('ASCII')
        
        # Lowercase e remove caracteres especiais
        col_name = col_name.lower()
        col_name = col_name.replace(' ', '_')
        col_name = ''.join(c for c in col_name if c.isalnum() or c == '_')
        
        return col_name

    @staticmethod
    def suggest_mapping(
        source_columns: List[str],
        target_columns: List[str],
        df: Optional[pd.DataFrame] = None,
        db: Optional[Session] = None,
        import_type: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Sugere mapeamento automático de colunas
        Tenta usar IA se disponível, caso contrário usa método tradicional
        """
        # Tenta usar IA se disponível
        if df is not None and db is not None and import_type is not None:
            try:
                from services.ai_service import AIService
                ai_service = AIService(db)
                
                if ai_service.is_available():
                    ai_mapping = ai_service.suggest_column_mapping(df, import_type, target_columns)
                    if ai_mapping:
                        # Completa com 'ignore' para colunas não mapeadas pela IA
                        for col in source_columns:
                            if col not in ai_mapping:
                                ai_mapping[col] = 'ignore'
                        return ai_mapping
            except Exception as e:
                print(f"Erro ao usar IA para mapeamento: {e}")
                # Continua com método tradicional
        
        # Método tradicional (fallback)
        mapping = {}
        used_targets = set()
        
        for source_col in source_columns:
            normalized_source = ColumnMapper.normalize_column_name(source_col)
            
            best_match = None
            best_score = 0
            
            for target_col in target_columns:
                if target_col in used_targets:
                    continue
                
                # Verifica sinônimos
                synonyms = ColumnMapper.SYNONYMS.get(target_col, [])
                synonyms.append(target_col)
                
                for synonym in synonyms:
                    normalized_synonym = ColumnMapper.normalize_column_name(synonym)
                    
                    # Calcula similaridade
                    score = difflib.SequenceMatcher(None, normalized_source, normalized_synonym).ratio()
                    
                    # Match exato
                    if normalized_source == normalized_synonym:
                        score = 1.0
                    
                    # Contém o sinônimo
                    elif normalized_synonym in normalized_source or normalized_source in normalized_synonym:
                        score = max(score, 0.8)
                    
                    if score > best_score:
                        best_score = score
                        best_match = target_col
            
            # Aceita match se score > 0.6
            if best_match and best_score > 0.6:
                mapping[source_col] = best_match
                used_targets.add(best_match)
            else:
                mapping[source_col] = 'ignore'
        
        return mapping

    @staticmethod
    def validate_mapping(mapping: Dict[str, str], required_fields: List[str]) -> tuple[bool, List[str]]:
        """
        Valida se o mapeamento contém todos os campos obrigatórios
        Retorna (is_valid, missing_fields)
        """
        mapped_targets = set(mapping.values())
        missing_fields = [field for field in required_fields if field not in mapped_targets]
        
        return len(missing_fields) == 0, missing_fields

    @staticmethod
    def get_required_fields(import_type: str) -> List[str]:
        """
        Retorna campos obrigatórios para cada tipo de importação
        """
        required_map = {
            'transactions': ['date', 'description', 'value'],
            'bank_statements': ['date', 'description', 'value'],
            'contracts': ['contract_start', 'event_date', 'service_value', 'contractor_name'],
            'accounts_payable': ['account_name', 'due_date', 'value'],
            'accounts_receivable': ['account_name', 'due_date', 'value']
        }
        
        return required_map.get(import_type, [])



