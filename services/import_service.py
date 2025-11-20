"""
Serviço de importação de dados com mapeamento de colunas
"""
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime
from models.transaction import Transaction, BankStatement
from models.contract import Contract
from models.account import AccountPayable, AccountReceivable, ImportMapping
from models.financial_investment import FinancialInvestment
from models.credit_card import CreditCardInvoice
from models.card_machine import CardMachineStatement
from models.inventory import Inventory
from models.group import Group, Subgroup
from utils.validators import parse_date, parse_currency
from config.database import engine
import json


def _ensure_columns_exist(db: Session, table_name: str):
    """
    Garante que as colunas group_id e subgroup_id existem na tabela
    """
    try:
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            return
        
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        if 'group_id' not in columns:
            try:
                db.execute(text(f"""
                    ALTER TABLE {table_name} 
                    ADD COLUMN group_id INTEGER REFERENCES groups(id)
                """))
                db.commit()
            except Exception as e:
                db.rollback()
                # Ignora erro se coluna já existir ou outro problema
                pass
        
        if 'subgroup_id' not in columns:
            try:
                db.execute(text(f"""
                    ALTER TABLE {table_name} 
                    ADD COLUMN subgroup_id INTEGER REFERENCES subgroups(id)
                """))
                db.commit()
            except Exception as e:
                db.rollback()
                # Ignora erro se coluna já existir ou outro problema
                pass
    except Exception as e:
        # Se houver erro, continua - pode ser que as colunas já existam
        pass


def _validate_group_subgroup(db: Session, client_id: int, group_id: Optional[int], subgroup_id: Optional[int]) -> Tuple[Optional[int], Optional[int]]:
    """
    Valida se group_id e subgroup_id existem no banco de dados para o cliente.
    Retorna (group_id_validado, subgroup_id_validado) ou (None, None) se não existirem.
    """
    validated_group_id = None
    validated_subgroup_id = None
    
    # Valida group_id
    if group_id is not None:
        group = db.query(Group).filter(
            Group.id == group_id,
            Group.client_id == client_id
        ).first()
        if group:
            validated_group_id = group_id
            
            # Valida subgroup_id apenas se group_id for válido
            if subgroup_id is not None:
                subgroup = db.query(Subgroup).filter(
                    Subgroup.id == subgroup_id,
                    Subgroup.group_id == group_id
                ).first()
                if subgroup:
                    validated_subgroup_id = subgroup_id
    
    return validated_group_id, validated_subgroup_id


def _validate_group_subgroup(db: Session, client_id: int, group_id: Optional[int], subgroup_id: Optional[int]) -> Tuple[Optional[int], Optional[int]]:
    """
    Valida se group_id e subgroup_id existem no banco de dados para o cliente.
    Retorna (group_id_validado, subgroup_id_validado) ou (None, None) se não existirem.
    """
    validated_group_id = None
    validated_subgroup_id = None
    
    # Valida group_id
    if group_id is not None:
        group = db.query(Group).filter(
            Group.id == group_id,
            Group.client_id == client_id
        ).first()
        if group:
            validated_group_id = group_id
            
            # Valida subgroup_id apenas se group_id for válido
            if subgroup_id is not None:
                subgroup = db.query(Subgroup).filter(
                    Subgroup.id == subgroup_id,
                    Subgroup.group_id == group_id
                ).first()
                if subgroup:
                    validated_subgroup_id = subgroup_id
    
    return validated_group_id, validated_subgroup_id


def _get_row_group_subgroup(row, group_id, subgroup_id):
    """
    Helper function para extrair group_id e subgroup_id de uma linha do DataFrame.
    Se a linha tiver esses valores, usa-os; senão, usa os valores padrão.
    """
    row_group_id = row.get('group_id')
    if row_group_id is not None and (isinstance(row_group_id, (int, float)) and not pd.isna(row_group_id)):
        row_group_id = int(row_group_id)
    else:
        row_group_id = group_id
    
    row_subgroup_id = row.get('subgroup_id')
    if row_subgroup_id is not None and (isinstance(row_subgroup_id, (int, float)) and not pd.isna(row_subgroup_id)):
        row_subgroup_id = int(row_subgroup_id)
    else:
        row_subgroup_id = subgroup_id
    
    return row_group_id, row_subgroup_id


def _process_in_chunks(df: pd.DataFrame, chunk_size: int = 1000, 
                       callback: Optional[Callable] = None) -> List[pd.DataFrame]:
    """
    Divide DataFrame em chunks para processamento
    """
    chunks = []
    total_rows = len(df)
    
    for i in range(0, total_rows, chunk_size):
        chunk = df.iloc[i:i + chunk_size].copy()
        chunks.append(chunk)
        
        if callback:
            progress = min(100, int((i + len(chunk)) / total_rows * 100))
            callback(f"Processando: {i + len(chunk)}/{total_rows} linhas ({progress}%)")
    
    return chunks


def _parse_dates_batch(series: pd.Series) -> pd.Series:
    """
    Aplica parse_date em batch usando apply
    """
    return series.astype(str).apply(lambda x: parse_date(x) if pd.notna(x) and x else None)


def _parse_currency_batch(series: pd.Series) -> pd.Series:
    """
    Aplica parse_currency em batch usando apply
    """
    return series.astype(str).apply(lambda x: parse_currency(x) if pd.notna(x) and x else None)


class ImportService:
    """
    Serviço para importar dados com mapeamento de colunas
    """

    @staticmethod
    def save_mapping(db: Session, client_id: int, import_type: str, 
                    mapping: Dict[str, str]) -> None:
        """
        Salva template de mapeamento para reutilização
        """
        # Remove mapeamentos antigos deste tipo
        db.query(ImportMapping).filter(
            ImportMapping.client_id == client_id,
            ImportMapping.import_type == import_type
        ).delete()
        
        # Salva novos mapeamentos
        for source_col, target_col in mapping.items():
            if target_col and target_col != 'ignore':
                mapping_obj = ImportMapping(
                    client_id=client_id,
                    import_type=import_type,
                    source_column=source_col,
                    target_column=target_col
                )
                db.add(mapping_obj)
        
        db.commit()

    @staticmethod
    def load_mapping(db: Session, client_id: int, import_type: str) -> Dict[str, str]:
        """
        Carrega template de mapeamento salvo
        """
        mappings = db.query(ImportMapping).filter(
            ImportMapping.client_id == client_id,
            ImportMapping.import_type == import_type
        ).all()
        
        return {m.source_column: m.target_column for m in mappings}

    @staticmethod
    def apply_mapping(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
        """
        Aplica mapeamento de colunas ao DataFrame
        """
        # Cria novo DataFrame apenas com colunas mapeadas
        mapped_df = pd.DataFrame()
        
        for source_col, target_col in mapping.items():
            if target_col and target_col != 'ignore' and source_col in df.columns:
                mapped_df[target_col] = df[source_col]
        
        return mapped_df

    @staticmethod
    def import_transactions(db: Session, client_id: int, df: pd.DataFrame,
                          document_type: str, filename: str,
                          group_id: Optional[int] = None,
                          subgroup_id: Optional[int] = None,
                          progress_callback: Optional[Callable] = None) -> int:
        """
        Importa transações financeiras usando bulk insert para melhor performance
        Colunas esperadas: date, description, value, type (opcional), category (opcional)
        """
        if df.empty:
            return 0
        
        # Processa em chunks se arquivo for grande
        chunk_size = 5000 if len(df) > 5000 else len(df)
        chunks = _process_in_chunks(df, chunk_size, progress_callback)
        
        total_imported = 0
        
        for chunk_df in chunks:
            # Processa dados em batch
            chunk_df = chunk_df.copy()
            
            # Parse de datas em batch
            chunk_df['_parsed_date'] = _parse_dates_batch(chunk_df.get('date', pd.Series()))
            chunk_df['_parsed_value'] = _parse_currency_batch(chunk_df.get('value', pd.Series()))
            
            # Filtra linhas válidas
            valid_mask = chunk_df['_parsed_date'].notna() & chunk_df['_parsed_value'].notna()
            valid_df = chunk_df[valid_mask].copy()
            
            if valid_df.empty:
                continue
            
            # Prepara dados para bulk insert
            bulk_data = []
            
            # Usa iterrows() que é mais seguro para colunas com underscore
            for idx, row in valid_df.iterrows():
                try:
                    parsed_date = row.get('_parsed_date')
                    parsed_value = row.get('_parsed_value')
                    
                    if pd.isna(parsed_date) or pd.isna(parsed_value):
                        continue
                    
                    date_obj = parsed_date.date() if hasattr(parsed_date, 'date') else parsed_date
                    value = abs(parsed_value)
                    
                    # Determina tipo
                    trans_type = str(row.get('type', '')).lower() if pd.notna(row.get('type', None)) else ''
                    if not trans_type:
                        trans_type = 'entrada' if parsed_value > 0 else 'saida'
                    
                    # Group/subgroup
                    row_group_id = row.get('group_id')
                    if row_group_id is not None and pd.notna(row_group_id):
                        try:
                            row_group_id = int(row_group_id)
                        except:
                            row_group_id = group_id
                    else:
                        row_group_id = group_id
                    
                    row_subgroup_id = row.get('subgroup_id')
                    if row_subgroup_id is not None and pd.notna(row_subgroup_id):
                        try:
                            row_subgroup_id = int(row_subgroup_id)
                        except:
                            row_subgroup_id = subgroup_id
                    else:
                        row_subgroup_id = subgroup_id
                    
                    # Valida se group_id e subgroup_id existem no banco
                    validated_group_id, validated_subgroup_id = _validate_group_subgroup(
                        db, client_id, row_group_id, row_subgroup_id
                    )
                    
                    bulk_data.append({
                        'client_id': client_id,
                        'date': date_obj,
                        'description': str(row.get('description', '')),
                        'value': value,
                        'type': trans_type,
                        'category': str(row.get('category', '')) if pd.notna(row.get('category', None)) else None,
                        'group_id': validated_group_id,
                        'subgroup_id': validated_subgroup_id,
                        'account': str(row.get('account', '')) if pd.notna(row.get('account', None)) else None,
                        'document_type': document_type,
                        'imported_from': filename
                    })
                except Exception as e:
                    print(f"Erro ao preparar linha: {e}")
                    continue
            
            if bulk_data:
                # Bulk insert
                db.bulk_insert_mappings(Transaction, bulk_data)
                total_imported += len(bulk_data)
        
        db.commit()
        return total_imported

    @staticmethod
    def import_bank_statements(db: Session, client_id: int, df: pd.DataFrame,
                              bank_name: str, filename: str,
                              group_id: Optional[int] = None,
                              subgroup_id: Optional[int] = None,
                              progress_callback: Optional[Callable] = None) -> Dict[str, int]:
        """
        Importa extratos bancários usando bulk insert para melhor performance
        Salva em bank_statements E cria transações automaticamente
        Colunas esperadas: date, description, value, balance (opcional)
        Retorna: {'statements': count, 'transactions': count}
        """
        # Garante que as colunas existem antes de importar
        _ensure_columns_exist(db, 'bank_statements')
        
        if df.empty:
            return {'statements': 0, 'transactions': 0}
        
        # Processa em chunks se arquivo for grande
        chunk_size = 5000 if len(df) > 5000 else len(df)
        chunks = _process_in_chunks(df, chunk_size, progress_callback)
        
        total_statements = 0
        total_transactions = 0
        imported_at = datetime.utcnow()
        
        # Busca transações existentes uma única vez para evitar queries N+1
        # Cria um set de tuplas (date, description, value) para verificação O(1)
        existing_transactions = set()
        if len(df) > 0:
            existing = db.query(Transaction.date, Transaction.description, Transaction.value).filter(
                Transaction.client_id == client_id,
                Transaction.document_type == 'extrato_bancario'
            ).all()
            existing_transactions = {(t.date, t.description, float(t.value)) for t in existing}
        
        for chunk_df in chunks:
            # Processa dados em batch
            chunk_df = chunk_df.copy()
            
            # Parse de datas e valores em batch
            chunk_df['_parsed_date'] = _parse_dates_batch(chunk_df.get('date', pd.Series()))
            chunk_df['_parsed_value'] = _parse_currency_batch(chunk_df.get('value', pd.Series()))
            if 'balance' in chunk_df.columns:
                chunk_df['_parsed_balance'] = _parse_currency_batch(chunk_df['balance'])
            else:
                chunk_df['_parsed_balance'] = None
            
            # Filtra linhas válidas
            valid_mask = chunk_df['_parsed_date'].notna() & chunk_df['_parsed_value'].notna()
            valid_df = chunk_df[valid_mask].copy()
            
            if valid_df.empty:
                continue
            
            # Prepara dados para bulk insert
            statements_data = []
            transactions_data = []
            
            for idx, row in valid_df.iterrows():
                try:
                    parsed_date = row.get('_parsed_date')
                    parsed_value = row.get('_parsed_value')
                    parsed_balance = row.get('_parsed_balance')
                    
                    if pd.isna(parsed_date) or pd.isna(parsed_value):
                        continue
                    
                    date_obj = parsed_date.date() if hasattr(parsed_date, 'date') else parsed_date
                    value = parsed_value
                    description = str(row.get('description', ''))
                    account = str(row.get('account', '')) if pd.notna(row.get('account', None)) else None
                    balance = parsed_balance if pd.notna(parsed_balance) else None
                    
                    # Group/subgroup - extrai valores
                    row_group_id = row.get('group_id')
                    if row_group_id is not None and pd.notna(row_group_id):
                        try:
                            row_group_id = int(row_group_id)
                        except:
                            row_group_id = group_id
                    else:
                        row_group_id = group_id
                    
                    row_subgroup_id = row.get('subgroup_id')
                    if row_subgroup_id is not None and pd.notna(row_subgroup_id):
                        try:
                            row_subgroup_id = int(row_subgroup_id)
                        except:
                            row_subgroup_id = subgroup_id
                    else:
                        row_subgroup_id = subgroup_id
                    
                    # Valida se group_id e subgroup_id existem no banco
                    validated_group_id, validated_subgroup_id = _validate_group_subgroup(
                        db, client_id, row_group_id, row_subgroup_id
                    )
                    
                    # 1. Prepara extrato bancário
                    statements_data.append({
                        'client_id': client_id,
                        'bank_name': bank_name,
                        'account': account,
                        'date': date_obj,
                        'description': description,
                        'value': value,
                        'balance': balance,
                        'imported_at': imported_at,
                        'group_id': validated_group_id,
                        'subgroup_id': validated_subgroup_id
                    })
                    
                    # 2. Prepara transação (verifica duplicata usando set)
                    value_abs = abs(value)
                    trans_key = (date_obj, description, value_abs)
                    
                    if trans_key not in existing_transactions:
                        transactions_data.append({
                            'client_id': client_id,
                            'date': date_obj,
                            'description': description,
                            'value': value_abs,
                            'type': 'entrada' if value > 0 else 'saida',
                            'account': account,
                            'bank_name': bank_name,
                            'document_type': 'extrato_bancario',
                            'imported_from': filename,
                            'group_id': validated_group_id,
                            'subgroup_id': validated_subgroup_id
                        })
                        # Adiciona ao set para evitar duplicatas no mesmo chunk
                        existing_transactions.add(trans_key)
                
                except Exception as e:
                    print(f"Erro ao preparar linha: {e}")
                    continue
            
            # Bulk insert
            if statements_data:
                db.bulk_insert_mappings(BankStatement, statements_data)
                total_statements += len(statements_data)
            
            if transactions_data:
                db.bulk_insert_mappings(Transaction, transactions_data)
                total_transactions += len(transactions_data)
        
        db.commit()
        return {'statements': total_statements, 'transactions': total_transactions}

    @staticmethod
    def import_contracts(db: Session, client_id: int, df: pd.DataFrame,
                        group_id: Optional[int] = None,
                        subgroup_id: Optional[int] = None,
                        progress_callback: Optional[Callable] = None) -> int:
        """
        Importa contratos usando bulk insert para melhor performance
        Colunas esperadas: contract_start, event_date, service_value, contractor_name, etc
        """
        # Garante que as colunas existem antes de importar
        _ensure_columns_exist(db, 'contracts')
        
        if df.empty:
            return 0
        
        chunk_size = 5000 if len(df) > 5000 else len(df)
        chunks = _process_in_chunks(df, chunk_size, progress_callback)
        
        total_imported = 0
        
        for chunk_df in chunks:
            chunk_df = chunk_df.copy()
            
            # Parse em batch
            chunk_df['_parsed_contract_start'] = _parse_dates_batch(chunk_df.get('contract_start', pd.Series()))
            chunk_df['_parsed_event_date'] = _parse_dates_batch(chunk_df.get('event_date', pd.Series()))
            chunk_df['_parsed_service_value'] = _parse_currency_batch(chunk_df.get('service_value', pd.Series()))
            if 'displacement_value' in chunk_df.columns:
                chunk_df['_parsed_displacement_value'] = _parse_currency_batch(chunk_df['displacement_value'])
            else:
                chunk_df['_parsed_displacement_value'] = 0
            
            # Filtra válidos
            valid_mask = (chunk_df['_parsed_contract_start'].notna() & 
                         chunk_df['_parsed_event_date'].notna() & 
                         chunk_df['_parsed_service_value'].notna())
            valid_df = chunk_df[valid_mask].copy()
            
            if valid_df.empty:
                continue
            
            bulk_data = []
            
            for idx, row in valid_df.iterrows():
                try:
                    parsed_contract_start = row.get('_parsed_contract_start')
                    parsed_event_date = row.get('_parsed_event_date')
                    parsed_service_value = row.get('_parsed_service_value')
                    parsed_displacement_value = row.get('_parsed_displacement_value', 0)
                    
                    if pd.isna(parsed_contract_start) or pd.isna(parsed_event_date) or pd.isna(parsed_service_value):
                        continue
                    
                    contract_start = parsed_contract_start.date() if hasattr(parsed_contract_start, 'date') else parsed_contract_start
                    event_date = parsed_event_date.date() if hasattr(parsed_event_date, 'date') else parsed_event_date
                    service_value = parsed_service_value
                    displacement_value = parsed_displacement_value if pd.notna(parsed_displacement_value) else 0
                    
                    # Group/subgroup
                    row_group_id = row.get('group_id')
                    if row_group_id is not None and pd.notna(row_group_id):
                        try:
                            row_group_id = int(row_group_id)
                        except:
                            row_group_id = group_id
                    else:
                        row_group_id = group_id
                    
                    row_subgroup_id = row.get('subgroup_id')
                    if row_subgroup_id is not None and pd.notna(row_subgroup_id):
                        try:
                            row_subgroup_id = int(row_subgroup_id)
                        except:
                            row_subgroup_id = subgroup_id
                    else:
                        row_subgroup_id = subgroup_id
                    
                    # Valida se group_id e subgroup_id existem no banco
                    validated_group_id, validated_subgroup_id = _validate_group_subgroup(
                        db, client_id, row_group_id, row_subgroup_id
                    )
                    
                    bulk_data.append({
                        'client_id': client_id,
                        'contract_start': contract_start,
                        'event_date': event_date,
                        'service_value': service_value,
                        'displacement_value': displacement_value,
                        'contractor_name': str(row.get('contractor_name', '')),
                        'event_type': str(row.get('event_type', '')) if pd.notna(row.get('event_type', None)) else None,
                        'service_sold': str(row.get('service_sold', '')) if pd.notna(row.get('service_sold', None)) else None,
                        'num_guests': int(row.get('num_guests', 0)) if pd.notna(row.get('num_guests', None)) else None,
                        'status': str(row.get('status', 'pendente')) if pd.notna(row.get('status', None)) else 'pendente',
                        'group_id': validated_group_id,
                        'subgroup_id': validated_subgroup_id
                    })
                except Exception as e:
                    print(f"Erro ao preparar linha: {e}")
                    continue
            
            if bulk_data:
                db.bulk_insert_mappings(Contract, bulk_data)
                total_imported += len(bulk_data)
        
        db.commit()
        return total_imported

    @staticmethod
    def import_accounts_payable(db: Session, client_id: int, df: pd.DataFrame,
                               group_id: Optional[int] = None,
                               subgroup_id: Optional[int] = None,
                               progress_callback: Optional[Callable] = None) -> int:
        """
        Importa contas a pagar usando bulk insert para melhor performance
        Colunas esperadas: account_name, due_date, value, cpf_cnpj (opcional)
        """
        # Garante que as colunas existem antes de importar
        _ensure_columns_exist(db, 'accounts_payable')
        
        if df.empty:
            return 0
        
        chunk_size = 5000 if len(df) > 5000 else len(df)
        chunks = _process_in_chunks(df, chunk_size, progress_callback)
        
        total_imported = 0
        
        for chunk_df in chunks:
            chunk_df = chunk_df.copy()
            
            # Parse em batch
            chunk_df['_parsed_due_date'] = _parse_dates_batch(chunk_df.get('due_date', pd.Series()))
            chunk_df['_parsed_value'] = _parse_currency_batch(chunk_df.get('value', pd.Series()))
            if 'total_monthly_outflow' in chunk_df.columns:
                chunk_df['_parsed_total_monthly_outflow'] = _parse_currency_batch(chunk_df['total_monthly_outflow'])
            else:
                chunk_df['_parsed_total_monthly_outflow'] = None
            
            # Filtra válidos
            valid_mask = chunk_df['_parsed_due_date'].notna() & chunk_df['_parsed_value'].notna()
            valid_df = chunk_df[valid_mask].copy()
            
            if valid_df.empty:
                continue
            
            bulk_data = []
            
            for idx, row in valid_df.iterrows():
                try:
                    parsed_due_date = row.get('_parsed_due_date')
                    parsed_value = row.get('_parsed_value')
                    parsed_total_monthly_outflow = row.get('_parsed_total_monthly_outflow')
                    
                    if pd.isna(parsed_due_date) or pd.isna(parsed_value):
                        continue
                    
                    due_date = parsed_due_date.date() if hasattr(parsed_due_date, 'date') else parsed_due_date
                    value = parsed_value
                    
                    # Group/subgroup
                    row_group_id = row.get('group_id')
                    if row_group_id is not None and pd.notna(row_group_id):
                        try:
                            row_group_id = int(row_group_id)
                        except:
                            row_group_id = group_id
                    else:
                        row_group_id = group_id
                    
                    row_subgroup_id = row.get('subgroup_id')
                    if row_subgroup_id is not None and pd.notna(row_subgroup_id):
                        try:
                            row_subgroup_id = int(row_subgroup_id)
                        except:
                            row_subgroup_id = subgroup_id
                    else:
                        row_subgroup_id = subgroup_id
                    
                    # Valida se group_id e subgroup_id existem no banco
                    validated_group_id, validated_subgroup_id = _validate_group_subgroup(
                        db, client_id, row_group_id, row_subgroup_id
                    )
                    
                    bulk_data.append({
                        'client_id': client_id,
                        'account_name': str(row.get('account_name', '')),
                        'cpf_cnpj': str(row.get('cpf_cnpj', '')) if pd.notna(row.get('cpf_cnpj', None)) else None,
                        'due_date': due_date,
                        'value': value,
                        'month_ref': due_date.strftime('%Y-%m'),
                        'paid': bool(row.get('paid', False)) if pd.notna(row.get('paid', None)) else False,
                        'monthly_installments': int(row.get('monthly_installments', 1)) if pd.notna(row.get('monthly_installments', None)) else None,
                        'total_monthly_outflow': parsed_total_monthly_outflow if pd.notna(parsed_total_monthly_outflow) else None,
                        'installment_number': int(row.get('installment_number', 1)) if pd.notna(row.get('installment_number', None)) else None,
                        'group_id': validated_group_id,
                        'subgroup_id': validated_subgroup_id
                    })
                except Exception as e:
                    print(f"Erro ao preparar linha: {e}")
                    continue
            
            if bulk_data:
                db.bulk_insert_mappings(AccountPayable, bulk_data)
                total_imported += len(bulk_data)
        
        db.commit()
        return total_imported

    @staticmethod
    def import_accounts_receivable(db: Session, client_id: int, df: pd.DataFrame,
                                  group_id: Optional[int] = None,
                                  subgroup_id: Optional[int] = None,
                                  progress_callback: Optional[Callable] = None) -> int:
        """
        Importa contas a receber usando bulk insert para melhor performance
        Colunas esperadas: account_name, due_date, value, cpf_cnpj (opcional)
        """
        # Garante que as colunas existem antes de importar
        _ensure_columns_exist(db, 'accounts_receivable')
        
        if df.empty:
            return 0
        
        chunk_size = 5000 if len(df) > 5000 else len(df)
        chunks = _process_in_chunks(df, chunk_size, progress_callback)
        
        total_imported = 0
        
        for chunk_df in chunks:
            chunk_df = chunk_df.copy()
            
            # Parse em batch
            chunk_df['_parsed_due_date'] = _parse_dates_batch(chunk_df.get('due_date', pd.Series()))
            chunk_df['_parsed_value'] = _parse_currency_batch(chunk_df.get('value', pd.Series()))
            if 'event_date' in chunk_df.columns:
                chunk_df['_parsed_event_date'] = _parse_dates_batch(chunk_df['event_date'])
            else:
                chunk_df['_parsed_event_date'] = None
            if 'contract_value' in chunk_df.columns:
                chunk_df['_parsed_contract_value'] = _parse_currency_batch(chunk_df['contract_value'])
            else:
                chunk_df['_parsed_contract_value'] = None
            if 'total_expected_inflow' in chunk_df.columns:
                chunk_df['_parsed_total_expected_inflow'] = _parse_currency_batch(chunk_df['total_expected_inflow'])
            else:
                chunk_df['_parsed_total_expected_inflow'] = None
            
            # Filtra válidos
            valid_mask = chunk_df['_parsed_due_date'].notna() & chunk_df['_parsed_value'].notna()
            valid_df = chunk_df[valid_mask].copy()
            
            if valid_df.empty:
                continue
            
            bulk_data = []
            
            for idx, row in valid_df.iterrows():
                try:
                    parsed_due_date = row.get('_parsed_due_date')
                    parsed_value = row.get('_parsed_value')
                    parsed_event_date = row.get('_parsed_event_date')
                    parsed_contract_value = row.get('_parsed_contract_value')
                    parsed_total_expected_inflow = row.get('_parsed_total_expected_inflow')
                    
                    if pd.isna(parsed_due_date) or pd.isna(parsed_value):
                        continue
                    
                    due_date = parsed_due_date.date() if hasattr(parsed_due_date, 'date') else parsed_due_date
                    value = parsed_value
                    event_date = None
                    if pd.notna(parsed_event_date):
                        event_date = parsed_event_date.date() if hasattr(parsed_event_date, 'date') else parsed_event_date
                    
                    # Group/subgroup
                    row_group_id = row.get('group_id')
                    if row_group_id is not None and pd.notna(row_group_id):
                        try:
                            row_group_id = int(row_group_id)
                        except:
                            row_group_id = group_id
                    else:
                        row_group_id = group_id
                    
                    row_subgroup_id = row.get('subgroup_id')
                    if row_subgroup_id is not None and pd.notna(row_subgroup_id):
                        try:
                            row_subgroup_id = int(row_subgroup_id)
                        except:
                            row_subgroup_id = subgroup_id
                    else:
                        row_subgroup_id = subgroup_id
                    
                    # Valida se group_id e subgroup_id existem no banco
                    validated_group_id, validated_subgroup_id = _validate_group_subgroup(
                        db, client_id, row_group_id, row_subgroup_id
                    )
                    
                    bulk_data.append({
                        'client_id': client_id,
                        'account_name': str(row.get('account_name', '')),
                        'cpf_cnpj': str(row.get('cpf_cnpj', '')) if pd.notna(row.get('cpf_cnpj', None)) else None,
                        'due_date': due_date,
                        'value': value,
                        'month_ref': due_date.strftime('%Y-%m'),
                        'received': bool(row.get('received', False)) if pd.notna(row.get('received', None)) else False,
                        'event_date': event_date,
                        'contract_value': parsed_contract_value if pd.notna(parsed_contract_value) else None,
                        'payment_method': str(row.get('payment_method', '')) if pd.notna(row.get('payment_method', None)) else None,
                        'monthly_installments': int(row.get('monthly_installments', 1)) if pd.notna(row.get('monthly_installments', None)) else None,
                        'total_expected_inflow': parsed_total_expected_inflow if pd.notna(parsed_total_expected_inflow) else None,
                        'installment_number': int(row.get('installment_number', 1)) if pd.notna(row.get('installment_number', None)) else None,
                        'group_id': validated_group_id,
                        'subgroup_id': validated_subgroup_id
                    })
                except Exception as e:
                    print(f"Erro ao preparar linha: {e}")
                    continue
            
            if bulk_data:
                db.bulk_insert_mappings(AccountReceivable, bulk_data)
                total_imported += len(bulk_data)
        
        db.commit()
        return total_imported

    @staticmethod
    def import_financial_investments(db: Session, client_id: int, df: pd.DataFrame,
                                    group_id: Optional[int] = None,
                                    subgroup_id: Optional[int] = None,
                                    progress_callback: Optional[Callable] = None) -> int:
        """
        Importa extratos de aplicações financeiras usando bulk insert para melhor performance
        Colunas esperadas: date, investment_type, institution, operation_type, applied_value, redeemed_value, yield_value
        """
        # Garante que as colunas existem antes de importar
        _ensure_columns_exist(db, 'financial_investments')
        
        if df.empty:
            return 0
        
        chunk_size = 5000 if len(df) > 5000 else len(df)
        chunks = _process_in_chunks(df, chunk_size, progress_callback)
        
        total_imported = 0
        
        for chunk_df in chunks:
            chunk_df = chunk_df.copy()
            
            # Parse em batch
            chunk_df['_parsed_date'] = _parse_dates_batch(chunk_df.get('date', pd.Series()))
            currency_cols = ['applied_value', 'redeemed_value', 'yield_value', 'balance']
            for col in currency_cols:
                if col in chunk_df.columns:
                    chunk_df[f'_parsed_{col}'] = _parse_currency_batch(chunk_df[col])
                else:
                    chunk_df[f'_parsed_{col}'] = None
            
            # Filtra válidos (só precisa de data)
            valid_mask = chunk_df['_parsed_date'].notna()
            valid_df = chunk_df[valid_mask].copy()
            
            if valid_df.empty:
                continue
            
            bulk_data = []
            
            for idx, row in valid_df.iterrows():
                try:
                    parsed_date = row.get('_parsed_date')
                    if pd.isna(parsed_date):
                        continue
                    
                    date_obj = parsed_date.date() if hasattr(parsed_date, 'date') else parsed_date
                    
                    # Group/subgroup
                    row_group_id = row.get('group_id')
                    if row_group_id is not None and pd.notna(row_group_id):
                        try:
                            row_group_id = int(row_group_id)
                        except:
                            row_group_id = group_id
                    else:
                        row_group_id = group_id
                    
                    row_subgroup_id = row.get('subgroup_id')
                    if row_subgroup_id is not None and pd.notna(row_subgroup_id):
                        try:
                            row_subgroup_id = int(row_subgroup_id)
                        except:
                            row_subgroup_id = subgroup_id
                    else:
                        row_subgroup_id = subgroup_id
                    
                    # Valida se group_id e subgroup_id existem no banco
                    validated_group_id, validated_subgroup_id = _validate_group_subgroup(
                        db, client_id, row_group_id, row_subgroup_id
                    )
                    
                    bulk_data.append({
                        'client_id': client_id,
                        'date': date_obj,
                        'investment_type': str(row.get('investment_type', '')) if pd.notna(row.get('investment_type', None)) else None,
                        'institution': str(row.get('institution', '')) if pd.notna(row.get('institution', None)) else None,
                        'operation_type': str(row.get('operation_type', '')) if pd.notna(row.get('operation_type', None)) else None,
                        'applied_value': row.get('_parsed_applied_value') if pd.notna(row.get('_parsed_applied_value', None)) else None,
                        'redeemed_value': row.get('_parsed_redeemed_value') if pd.notna(row.get('_parsed_redeemed_value', None)) else None,
                        'yield_value': row.get('_parsed_yield_value') if pd.notna(row.get('_parsed_yield_value', None)) else None,
                        'balance': row.get('_parsed_balance') if pd.notna(row.get('_parsed_balance', None)) else None,
                        'description': str(row.get('description', '')) if pd.notna(row.get('description', None)) else None,
                        'group_id': validated_group_id,
                        'subgroup_id': validated_subgroup_id
                    })
                except Exception as e:
                    print(f"Erro ao preparar linha: {e}")
                    continue
            
            if bulk_data:
                db.bulk_insert_mappings(FinancialInvestment, bulk_data)
                total_imported += len(bulk_data)
        
        db.commit()
        return total_imported

    @staticmethod
    def import_credit_card_invoices(db: Session, client_id: int, df: pd.DataFrame,
                                   group_id: Optional[int] = None,
                                   subgroup_id: Optional[int] = None,
                                   progress_callback: Optional[Callable] = None) -> int:
        """
        Importa faturas de cartão de crédito usando bulk insert para melhor performance
        Colunas esperadas: transaction_date, description, value, category, establishment, installment_number
        """
        # Garante que as colunas existem antes de importar
        _ensure_columns_exist(db, 'credit_card_invoices')
        
        if df.empty:
            return 0
        
        chunk_size = 5000 if len(df) > 5000 else len(df)
        chunks = _process_in_chunks(df, chunk_size, progress_callback)
        
        total_imported = 0
        
        for chunk_df in chunks:
            chunk_df = chunk_df.copy()
            
            # Parse em batch
            chunk_df['_parsed_transaction_date'] = _parse_dates_batch(chunk_df.get('transaction_date', pd.Series()))
            chunk_df['_parsed_value'] = _parse_currency_batch(chunk_df.get('value', pd.Series()))
            
            # Filtra válidos
            valid_mask = chunk_df['_parsed_transaction_date'].notna() & chunk_df['_parsed_value'].notna()
            valid_df = chunk_df[valid_mask].copy()
            
            if valid_df.empty:
                continue
            
            bulk_data = []
            
            for idx, row in valid_df.iterrows():
                try:
                    parsed_transaction_date = row.get('_parsed_transaction_date')
                    parsed_value = row.get('_parsed_value')
                    
                    if pd.isna(parsed_transaction_date) or pd.isna(parsed_value):
                        continue
                    
                    transaction_date = parsed_transaction_date.date() if hasattr(parsed_transaction_date, 'date') else parsed_transaction_date
                    value = parsed_value
                    
                    # Group/subgroup
                    row_group_id = row.get('group_id')
                    if row_group_id is not None and pd.notna(row_group_id):
                        try:
                            row_group_id = int(row_group_id)
                        except:
                            row_group_id = group_id
                    else:
                        row_group_id = group_id
                    
                    row_subgroup_id = row.get('subgroup_id')
                    if row_subgroup_id is not None and pd.notna(row_subgroup_id):
                        try:
                            row_subgroup_id = int(row_subgroup_id)
                        except:
                            row_subgroup_id = subgroup_id
                    else:
                        row_subgroup_id = subgroup_id
                    
                    # Valida se group_id e subgroup_id existem no banco
                    validated_group_id, validated_subgroup_id = _validate_group_subgroup(
                        db, client_id, row_group_id, row_subgroup_id
                    )
                    
                    bulk_data.append({
                        'client_id': client_id,
                        'transaction_date': transaction_date,
                        'description': str(row.get('description', '')),
                        'value': value,
                        'category': str(row.get('category', '')) if pd.notna(row.get('category', None)) else None,
                        'establishment': str(row.get('establishment', '')) if pd.notna(row.get('establishment', None)) else None,
                        'installment_number': int(row.get('installment_number', 1)) if pd.notna(row.get('installment_number', None)) else None,
                        'total_installments': int(row.get('total_installments', 1)) if pd.notna(row.get('total_installments', None)) else None,
                        'card_brand': str(row.get('card_brand', '')) if pd.notna(row.get('card_brand', None)) else None,
                        'group_id': validated_group_id,
                        'subgroup_id': validated_subgroup_id
                    })
                except Exception as e:
                    print(f"Erro ao preparar linha: {e}")
                    continue
            
            if bulk_data:
                db.bulk_insert_mappings(CreditCardInvoice, bulk_data)
                total_imported += len(bulk_data)
        
        db.commit()
        return total_imported

    @staticmethod
    def import_card_machine_statements(db: Session, client_id: int, df: pd.DataFrame,
                                      group_id: Optional[int] = None,
                                      subgroup_id: Optional[int] = None,
                                      progress_callback: Optional[Callable] = None) -> int:
        """
        Importa extratos de máquina de cartão usando bulk insert para melhor performance
        Colunas esperadas: date, gross_value, fee, net_value, card_brand, transaction_type
        """
        # Garante que as colunas existem antes de importar
        _ensure_columns_exist(db, 'card_machine_statements')
        
        if df.empty:
            return 0
        
        chunk_size = 5000 if len(df) > 5000 else len(df)
        chunks = _process_in_chunks(df, chunk_size, progress_callback)
        
        total_imported = 0
        
        for chunk_df in chunks:
            chunk_df = chunk_df.copy()
            
            # Parse em batch
            chunk_df['_parsed_date'] = _parse_dates_batch(chunk_df.get('date', pd.Series()))
            chunk_df['_parsed_gross_value'] = _parse_currency_batch(chunk_df.get('gross_value', pd.Series()))
            chunk_df['_parsed_net_value'] = _parse_currency_batch(chunk_df.get('net_value', pd.Series()))
            if 'fee' in chunk_df.columns:
                chunk_df['_parsed_fee'] = _parse_currency_batch(chunk_df['fee'])
            else:
                chunk_df['_parsed_fee'] = None
            
            # Preenche valores faltantes
            chunk_df['_parsed_net_value'] = chunk_df['_parsed_net_value'].fillna(chunk_df['_parsed_gross_value'])
            chunk_df['_parsed_gross_value'] = chunk_df['_parsed_gross_value'].fillna(chunk_df['_parsed_net_value'])
            
            # Filtra válidos (precisa de data e pelo menos um valor)
            valid_mask = (chunk_df['_parsed_date'].notna() & 
                         (chunk_df['_parsed_gross_value'].notna() | chunk_df['_parsed_net_value'].notna()))
            valid_df = chunk_df[valid_mask].copy()
            
            if valid_df.empty:
                continue
            
            bulk_data = []
            
            for idx, row in valid_df.iterrows():
                try:
                    parsed_date = row.get('_parsed_date')
                    parsed_gross_value = row.get('_parsed_gross_value')
                    parsed_net_value = row.get('_parsed_net_value')
                    parsed_fee = row.get('_parsed_fee')
                    
                    if pd.isna(parsed_date):
                        continue
                    
                    date_obj = parsed_date.date() if hasattr(parsed_date, 'date') else parsed_date
                    gross_value = parsed_gross_value if pd.notna(parsed_gross_value) else parsed_net_value
                    net_value = parsed_net_value if pd.notna(parsed_net_value) else parsed_gross_value
                    
                    # Group/subgroup
                    row_group_id = row.get('group_id')
                    if row_group_id is not None and pd.notna(row_group_id):
                        try:
                            row_group_id = int(row_group_id)
                        except:
                            row_group_id = group_id
                    else:
                        row_group_id = group_id
                    
                    row_subgroup_id = row.get('subgroup_id')
                    if row_subgroup_id is not None and pd.notna(row_subgroup_id):
                        try:
                            row_subgroup_id = int(row_subgroup_id)
                        except:
                            row_subgroup_id = subgroup_id
                    else:
                        row_subgroup_id = subgroup_id
                    
                    # Valida se group_id e subgroup_id existem no banco
                    validated_group_id, validated_subgroup_id = _validate_group_subgroup(
                        db, client_id, row_group_id, row_subgroup_id
                    )
                    
                    bulk_data.append({
                        'client_id': client_id,
                        'date': date_obj,
                        'gross_value': gross_value,
                        'fee': parsed_fee if pd.notna(parsed_fee) else None,
                        'net_value': net_value,
                        'card_brand': str(row.get('card_brand', '')) if pd.notna(row.get('card_brand', None)) else None,
                        'transaction_type': str(row.get('transaction_type', '')) if pd.notna(row.get('transaction_type', None)) else None,
                        'description': str(row.get('description', '')) if pd.notna(row.get('description', None)) else None,
                        'group_id': validated_group_id,
                        'subgroup_id': validated_subgroup_id
                    })
                except Exception as e:
                    print(f"Erro ao preparar linha: {e}")
                    continue
            
            if bulk_data:
                db.bulk_insert_mappings(CardMachineStatement, bulk_data)
                total_imported += len(bulk_data)
        
        db.commit()
        return total_imported

    @staticmethod
    def import_inventory(db: Session, client_id: int, df: pd.DataFrame,
                        group_id: Optional[int] = None,
                        subgroup_id: Optional[int] = None,
                        progress_callback: Optional[Callable] = None) -> int:
        """
        Importa controle de estoque usando bulk insert para melhor performance
        Colunas esperadas: product_name, quantity, unit_value, movement_date, movement_type
        """
        # Garante que as colunas existem antes de importar
        _ensure_columns_exist(db, 'inventory')
        
        if df.empty:
            return 0
        
        chunk_size = 5000 if len(df) > 5000 else len(df)
        chunks = _process_in_chunks(df, chunk_size, progress_callback)
        
        total_imported = 0
        
        for chunk_df in chunks:
            chunk_df = chunk_df.copy()
            
            # Parse em batch
            chunk_df['_parsed_movement_date'] = _parse_dates_batch(chunk_df.get('movement_date', pd.Series()))
            chunk_df['_parsed_unit_value'] = _parse_currency_batch(chunk_df.get('unit_value', pd.Series()))
            
            # Converte quantity para float
            if 'quantity' in chunk_df.columns:
                chunk_df['_parsed_quantity'] = pd.to_numeric(chunk_df['quantity'], errors='coerce')
            else:
                chunk_df['_parsed_quantity'] = 0
            
            # Calcula total_value
            chunk_df['_total_value'] = chunk_df['_parsed_quantity'] * chunk_df['_parsed_unit_value']
            
            # Filtra válidos
            valid_mask = (chunk_df['_parsed_movement_date'].notna() & 
                         chunk_df['_parsed_quantity'].notna() & 
                         (chunk_df['_parsed_quantity'] != 0) &
                         chunk_df['_parsed_unit_value'].notna())
            valid_df = chunk_df[valid_mask].copy()
            
            if valid_df.empty:
                continue
            
            bulk_data = []
            
            for idx, row in valid_df.iterrows():
                try:
                    parsed_movement_date = row.get('_parsed_movement_date')
                    parsed_quantity = row.get('_parsed_quantity')
                    parsed_unit_value = row.get('_parsed_unit_value')
                    total_value = row.get('_total_value')
                    
                    if pd.isna(parsed_movement_date) or pd.isna(parsed_quantity) or pd.isna(parsed_unit_value):
                        continue
                    
                    movement_date = parsed_movement_date.date() if hasattr(parsed_movement_date, 'date') else parsed_movement_date
                    quantity = abs(float(parsed_quantity))
                    unit_value = parsed_unit_value
                    
                    # Determina movement_type
                    movement_type = str(row.get('movement_type', '')).lower() if pd.notna(row.get('movement_type', None)) else ''
                    if movement_type not in ['entrada', 'saida']:
                        movement_type = 'entrada' if parsed_quantity > 0 else 'saida'
                    
                    # Group/subgroup
                    row_group_id = row.get('group_id')
                    if row_group_id is not None and pd.notna(row_group_id):
                        try:
                            row_group_id = int(row_group_id)
                        except:
                            row_group_id = group_id
                    else:
                        row_group_id = group_id
                    
                    row_subgroup_id = row.get('subgroup_id')
                    if row_subgroup_id is not None and pd.notna(row_subgroup_id):
                        try:
                            row_subgroup_id = int(row_subgroup_id)
                        except:
                            row_subgroup_id = subgroup_id
                    else:
                        row_subgroup_id = subgroup_id
                    
                    # Valida se group_id e subgroup_id existem no banco
                    validated_group_id, validated_subgroup_id = _validate_group_subgroup(
                        db, client_id, row_group_id, row_subgroup_id
                    )
                    
                    bulk_data.append({
                        'client_id': client_id,
                        'product_name': str(row.get('product_name', '')),
                        'quantity': quantity,
                        'unit_value': unit_value,
                        'total_value': total_value,
                        'movement_date': movement_date,
                        'movement_type': movement_type,
                        'description': str(row.get('description', '')) if pd.notna(row.get('description', None)) else None,
                        'group_id': validated_group_id,
                        'subgroup_id': validated_subgroup_id
                    })
                except Exception as e:
                    print(f"Erro ao preparar linha: {e}")
                    continue
            
            if bulk_data:
                db.bulk_insert_mappings(Inventory, bulk_data)
                total_imported += len(bulk_data)
        
        db.commit()
        return total_imported

    @staticmethod
    def get_target_columns(import_type: str) -> List[str]:
        """
        Retorna lista de colunas alvo para um tipo de importação
        """
        columns_map = {
            'transactions': ['date', 'description', 'value', 'type', 'category', 'account', 'group_id', 'subgroup_id'],
            'bank_statements': ['date', 'description', 'value', 'balance', 'account', 'bank_name', 'group_id', 'subgroup_id'],
            'contracts': ['contract_start', 'event_date', 'service_value', 'contractor_name', 'displacement_value', 'event_type', 'service_sold', 'num_guests', 'status', 'group_id', 'subgroup_id'],
            'accounts_payable': ['account_name', 'due_date', 'value', 'cpf_cnpj', 'month_ref', 'paid', 'monthly_installments', 'total_monthly_outflow', 'installment_number', 'group_id', 'subgroup_id'],
            'accounts_receivable': ['account_name', 'due_date', 'value', 'cpf_cnpj', 'month_ref', 'received', 'event_date', 'contract_value', 'payment_method', 'monthly_installments', 'total_expected_inflow', 'installment_number', 'group_id', 'subgroup_id'],
            'financial_investments': ['date', 'investment_type', 'institution', 'operation_type', 'applied_value', 'redeemed_value', 'yield_value', 'balance', 'description', 'group_id', 'subgroup_id'],
            'credit_card_invoices': ['transaction_date', 'description', 'value', 'category', 'establishment', 'installment_number', 'total_installments', 'card_brand', 'group_id', 'subgroup_id'],
            'card_machine_statements': ['date', 'gross_value', 'fee', 'net_value', 'card_brand', 'transaction_type', 'description', 'group_id', 'subgroup_id'],
            'inventory': ['product_name', 'quantity', 'unit_value', 'movement_date', 'movement_type', 'description', 'group_id', 'subgroup_id']
        }
        
        return columns_map.get(import_type, [])
