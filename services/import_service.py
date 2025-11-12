"""
Serviço de importação de dados com mapeamento de colunas
"""
import pandas as pd
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from datetime import datetime
from models.transaction import Transaction, BankStatement
from models.contract import Contract
from models.account import AccountPayable, AccountReceivable, ImportMapping
from models.group import Group, Subgroup
from utils.validators import parse_date, parse_currency
import json


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
                          subgroup_id: Optional[int] = None) -> int:
        """
        Importa transações financeiras
        Colunas esperadas: date, description, value, type (opcional), category (opcional)
        """
        imported_count = 0
        
        for _, row in df.iterrows():
            try:
                # Parse da data
                date = parse_date(str(row.get('date', '')))
                if not date:
                    continue
                
                # Parse do valor
                value = parse_currency(str(row.get('value', 0)))
                if value is None:
                    continue
                
                # Determina tipo (entrada/saida)
                trans_type = str(row.get('type', '')).lower()
                if not trans_type:
                    trans_type = 'entrada' if value > 0 else 'saida'
                
                # Cria transação
                transaction = Transaction(
                    client_id=client_id,
                    date=date.date(),
                    description=str(row.get('description', '')),
                    value=abs(value),
                    type=trans_type,
                    category=str(row.get('category', '')) if 'category' in row else None,
                    group_id=group_id,
                    subgroup_id=subgroup_id,
                    account=str(row.get('account', '')) if 'account' in row else None,
                    document_type=document_type,
                    imported_from=filename
                )
                
                db.add(transaction)
                imported_count += 1
            
            except Exception as e:
                print(f"Erro ao importar linha: {e}")
                continue
        
        db.commit()
        return imported_count

    @staticmethod
    def import_bank_statements(db: Session, client_id: int, df: pd.DataFrame,
                              bank_name: str, filename: str) -> int:
        """
        Importa extratos bancários
        Colunas esperadas: date, description, value, balance (opcional)
        """
        imported_count = 0
        
        for _, row in df.iterrows():
            try:
                # Parse da data
                date = parse_date(str(row.get('date', '')))
                if not date:
                    continue
                
                # Parse do valor
                value = parse_currency(str(row.get('value', 0)))
                if value is None:
                    continue
                
                # Parse do saldo (opcional)
                balance = None
                if 'balance' in row:
                    balance = parse_currency(str(row.get('balance', '')))
                
                # Cria extrato
                statement = BankStatement(
                    client_id=client_id,
                    bank_name=bank_name,
                    account=str(row.get('account', '')) if 'account' in row else None,
                    date=date.date(),
                    description=str(row.get('description', '')),
                    value=value,
                    balance=balance
                )
                
                db.add(statement)
                imported_count += 1
            
            except Exception as e:
                print(f"Erro ao importar linha: {e}")
                continue
        
        db.commit()
        return imported_count

    @staticmethod
    def import_contracts(db: Session, client_id: int, df: pd.DataFrame) -> int:
        """
        Importa contratos
        Colunas esperadas: contract_start, event_date, service_value, contractor_name, etc
        """
        imported_count = 0
        
        for _, row in df.iterrows():
            try:
                # Parse das datas
                contract_start = parse_date(str(row.get('contract_start', '')))
                event_date = parse_date(str(row.get('event_date', '')))
                
                if not contract_start or not event_date:
                    continue
                
                # Parse dos valores
                service_value = parse_currency(str(row.get('service_value', 0)))
                if service_value is None:
                    continue
                
                displacement_value = 0
                if 'displacement_value' in row:
                    displacement_value = parse_currency(str(row.get('displacement_value', 0))) or 0
                
                # Cria contrato
                contract = Contract(
                    client_id=client_id,
                    contract_start=contract_start.date(),
                    event_date=event_date.date(),
                    service_value=service_value,
                    displacement_value=displacement_value,
                    event_type=str(row.get('event_type', '')) if 'event_type' in row else None,
                    service_sold=str(row.get('service_sold', '')) if 'service_sold' in row else None,
                    guests_count=int(row.get('guests_count', 0)) if 'guests_count' in row else None,
                    contractor_name=str(row.get('contractor_name', '')),
                    payment_terms=str(row.get('payment_terms', '')) if 'payment_terms' in row else None,
                    status=str(row.get('status', 'pendente'))
                )
                
                db.add(contract)
                imported_count += 1
            
            except Exception as e:
                print(f"Erro ao importar linha: {e}")
                continue
        
        db.commit()
        return imported_count

    @staticmethod
    def import_accounts_payable(db: Session, client_id: int, df: pd.DataFrame) -> int:
        """
        Importa contas a pagar
        Colunas esperadas: account_name, due_date, value, cpf_cnpj (opcional)
        """
        imported_count = 0
        
        for _, row in df.iterrows():
            try:
                # Parse da data
                due_date = parse_date(str(row.get('due_date', '')))
                if not due_date:
                    continue
                
                # Parse do valor
                value = parse_currency(str(row.get('value', 0)))
                if value is None:
                    continue
                
                # Cria conta a pagar
                account = AccountPayable(
                    client_id=client_id,
                    account_name=str(row.get('account_name', '')),
                    cpf_cnpj=str(row.get('cpf_cnpj', '')) if 'cpf_cnpj' in row else None,
                    due_date=due_date.date(),
                    value=value,
                    month_ref=due_date.strftime('%Y-%m'),
                    paid=bool(row.get('paid', False)) if 'paid' in row else False
                )
                
                db.add(account)
                imported_count += 1
            
            except Exception as e:
                print(f"Erro ao importar linha: {e}")
                continue
        
        db.commit()
        return imported_count

    @staticmethod
    def import_accounts_receivable(db: Session, client_id: int, df: pd.DataFrame) -> int:
        """
        Importa contas a receber
        Colunas esperadas: account_name, due_date, value, cpf_cnpj (opcional)
        """
        imported_count = 0
        
        for _, row in df.iterrows():
            try:
                # Parse da data
                due_date = parse_date(str(row.get('due_date', '')))
                if not due_date:
                    continue
                
                # Parse do valor
                value = parse_currency(str(row.get('value', 0)))
                if value is None:
                    continue
                
                # Cria conta a receber
                account = AccountReceivable(
                    client_id=client_id,
                    account_name=str(row.get('account_name', '')),
                    cpf_cnpj=str(row.get('cpf_cnpj', '')) if 'cpf_cnpj' in row else None,
                    due_date=due_date.date(),
                    value=value,
                    month_ref=due_date.strftime('%Y-%m'),
                    received=bool(row.get('received', False)) if 'received' in row else False
                )
                
                db.add(account)
                imported_count += 1
            
            except Exception as e:
                print(f"Erro ao importar linha: {e}")
                continue
        
        db.commit()
        return imported_count

    @staticmethod
    def get_target_columns(import_type: str) -> List[str]:
        """
        Retorna lista de colunas alvo para cada tipo de importação
        """
        columns_map = {
            'transactions': ['date', 'description', 'value', 'type', 'category', 'account'],
            'bank_statements': ['date', 'description', 'value', 'balance', 'account'],
            'contracts': ['contract_start', 'event_date', 'service_value', 'displacement_value',
                         'event_type', 'service_sold', 'guests_count', 'contractor_name',
                         'payment_terms', 'status'],
            'accounts_payable': ['account_name', 'cpf_cnpj', 'due_date', 'value', 'paid'],
            'accounts_receivable': ['account_name', 'cpf_cnpj', 'due_date', 'value', 'received']
        }
        
        return columns_map.get(import_type, [])


