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
from models.financial_investment import FinancialInvestment
from models.credit_card import CreditCardInvoice
from models.card_machine import CardMachineStatement
from models.inventory import Inventory
from models.group import Group, Subgroup
from utils.validators import parse_date, parse_currency
import json


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
                
                # Usa group_id e subgroup_id da linha se disponíveis, senão usa os parâmetros
                row_group_id, row_subgroup_id = _get_row_group_subgroup(row, group_id, subgroup_id)
                
                # Cria transação
                transaction = Transaction(
                    client_id=client_id,
                    date=date.date(),
                    description=str(row.get('description', '')),
                    value=abs(value),
                    type=trans_type,
                    category=str(row.get('category', '')) if 'category' in row else None,
                    group_id=row_group_id,
                    subgroup_id=row_subgroup_id,
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
                              bank_name: str, filename: str,
                              group_id: Optional[int] = None,
                              subgroup_id: Optional[int] = None) -> Dict[str, int]:
        """
        Importa extratos bancários
        Salva em bank_statements E cria transações automaticamente
        Colunas esperadas: date, description, value, balance (opcional)
        Retorna: {'statements': count, 'transactions': count}
        """
        statements_count = 0
        transactions_count = 0
        
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
                
                account = str(row.get('account', '')) if 'account' in row else None
                description = str(row.get('description', ''))
                date_obj = date.date()
                
                # Usa group_id e subgroup_id da linha se disponíveis, senão usa os parâmetros
                row_group_id, row_subgroup_id = _get_row_group_subgroup(row, group_id, subgroup_id)
                
                # 1. Salva extrato bancário (para consulta/conciliação)
                statement = BankStatement(
                    client_id=client_id,
                    bank_name=bank_name,
                    account=account,
                    date=date_obj,
                    description=description,
                    value=value,
                    balance=balance,
                    imported_at=datetime.utcnow(),  # Marca como importado
                    group_id=row_group_id,
                    subgroup_id=row_subgroup_id
                )
                
                db.add(statement)
                statements_count += 1
                
                # 2. Cria transação correspondente (para DRE/DFC)
                # Verifica se já existe para evitar duplicação
                existing = db.query(Transaction).filter(
                    Transaction.client_id == client_id,
                    Transaction.date == date_obj,
                    Transaction.description == description,
                    Transaction.value == abs(value),
                    Transaction.document_type == 'extrato_bancario'
                ).first()
                
                if not existing:
                    transaction = Transaction(
                        client_id=client_id,
                        date=date_obj,
                        description=description,
                        value=abs(value),
                        type='entrada' if value > 0 else 'saida',
                        account=account,
                        bank_name=bank_name,  # Salva nome do banco na transação
                        document_type='extrato_bancario',
                        imported_from=filename,
                        group_id=row_group_id,
                        subgroup_id=row_subgroup_id
                    )
                    
                    db.add(transaction)
                    transactions_count += 1
            
            except Exception as e:
                print(f"Erro ao importar linha: {e}")
                continue
        
        db.commit()
        return {'statements': statements_count, 'transactions': transactions_count}

    @staticmethod
    def import_contracts(db: Session, client_id: int, df: pd.DataFrame,
                        group_id: Optional[int] = None,
                        subgroup_id: Optional[int] = None) -> int:
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
                
                # Usa group_id e subgroup_id da linha se disponíveis, senão usa os parâmetros
                row_group_id, row_subgroup_id = _get_row_group_subgroup(row, group_id, subgroup_id)
                
                # Cria contrato
                contract = Contract(
                    client_id=client_id,
                    contract_start=contract_start.date(),
                    event_date=event_date.date(),
                    service_value=service_value,
                    displacement_value=displacement_value,
                    contractor_name=str(row.get('contractor_name', '')),
                    event_type=str(row.get('event_type', '')) if 'event_type' in row else None,
                    service_sold=str(row.get('service_sold', '')) if 'service_sold' in row else None,
                    num_guests=int(row.get('num_guests', 0)) if 'num_guests' in row else None,
                    status=str(row.get('status', 'pendente')) if 'status' in row else 'pendente',
                    group_id=row_group_id,
                    subgroup_id=row_subgroup_id
                )
                
                db.add(contract)
                imported_count += 1
            
            except Exception as e:
                print(f"Erro ao importar linha: {e}")
                continue
        
        db.commit()
        return imported_count

    @staticmethod
    def import_accounts_payable(db: Session, client_id: int, df: pd.DataFrame,
                               group_id: Optional[int] = None,
                               subgroup_id: Optional[int] = None) -> int:
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
                
                # Usa group_id e subgroup_id da linha se disponíveis, senão usa os parâmetros
                row_group_id, row_subgroup_id = _get_row_group_subgroup(row, group_id, subgroup_id)
                
                # Cria conta a pagar
                account = AccountPayable(
                    client_id=client_id,
                    account_name=str(row.get('account_name', '')),
                    cpf_cnpj=str(row.get('cpf_cnpj', '')) if 'cpf_cnpj' in row else None,
                    due_date=due_date.date(),
                    value=value,
                    month_ref=due_date.strftime('%Y-%m'),
                    paid=bool(row.get('paid', False)) if 'paid' in row else False,
                    monthly_installments=int(row.get('monthly_installments', 1)) if 'monthly_installments' in row else None,
                    total_monthly_outflow=parse_currency(str(row.get('total_monthly_outflow', ''))) if 'total_monthly_outflow' in row else None,
                    installment_number=int(row.get('installment_number', 1)) if 'installment_number' in row else None,
                    group_id=row_group_id,
                    subgroup_id=row_subgroup_id
                )
                
                db.add(account)
                imported_count += 1
            
            except Exception as e:
                print(f"Erro ao importar linha: {e}")
                continue
        
        db.commit()
        return imported_count

    @staticmethod
    def import_accounts_receivable(db: Session, client_id: int, df: pd.DataFrame,
                                  group_id: Optional[int] = None,
                                  subgroup_id: Optional[int] = None) -> int:
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
                
                # Parse de data do evento (opcional)
                event_date = None
                if 'event_date' in row:
                    event_date_parsed = parse_date(str(row.get('event_date', '')))
                    if event_date_parsed:
                        event_date = event_date_parsed.date()
                
                # Usa group_id e subgroup_id da linha se disponíveis, senão usa os parâmetros
                row_group_id, row_subgroup_id = _get_row_group_subgroup(row, group_id, subgroup_id)
                
                # Cria conta a receber
                account = AccountReceivable(
                    client_id=client_id,
                    account_name=str(row.get('account_name', '')),
                    cpf_cnpj=str(row.get('cpf_cnpj', '')) if 'cpf_cnpj' in row else None,
                    due_date=due_date.date(),
                    value=value,
                    month_ref=due_date.strftime('%Y-%m'),
                    received=bool(row.get('received', False)) if 'received' in row else False,
                    event_date=event_date,
                    contract_value=parse_currency(str(row.get('contract_value', ''))) if 'contract_value' in row else None,
                    payment_method=str(row.get('payment_method', '')) if 'payment_method' in row else None,
                    monthly_installments=int(row.get('monthly_installments', 1)) if 'monthly_installments' in row else None,
                    total_expected_inflow=parse_currency(str(row.get('total_expected_inflow', ''))) if 'total_expected_inflow' in row else None,
                    installment_number=int(row.get('installment_number', 1)) if 'installment_number' in row else None,
                    group_id=row_group_id,
                    subgroup_id=row_subgroup_id
                )
                
                db.add(account)
                imported_count += 1
            
            except Exception as e:
                print(f"Erro ao importar linha: {e}")
                continue
        
        db.commit()
        return imported_count

    @staticmethod
    def import_financial_investments(db: Session, client_id: int, df: pd.DataFrame,
                                    group_id: Optional[int] = None,
                                    subgroup_id: Optional[int] = None) -> int:
        """
        Importa extratos de aplicações financeiras
        Colunas esperadas: date, investment_type, institution, operation_type, applied_value, redeemed_value, yield_value
        """
        imported_count = 0
        
        for _, row in df.iterrows():
            try:
                date = parse_date(str(row.get('date', '')))
                if not date:
                    continue
                
                # Usa group_id e subgroup_id da linha se disponíveis, senão usa os parâmetros
                row_group_id, row_subgroup_id = _get_row_group_subgroup(row, group_id, subgroup_id)
                
                investment = FinancialInvestment(
                    client_id=client_id,
                    date=date.date(),
                    investment_type=str(row.get('investment_type', '')) if 'investment_type' in row else None,
                    institution=str(row.get('institution', '')) if 'institution' in row else None,
                    operation_type=str(row.get('operation_type', '')) if 'operation_type' in row else None,
                    applied_value=parse_currency(str(row.get('applied_value', ''))) if 'applied_value' in row else None,
                    redeemed_value=parse_currency(str(row.get('redeemed_value', ''))) if 'redeemed_value' in row else None,
                    yield_value=parse_currency(str(row.get('yield_value', ''))) if 'yield_value' in row else None,
                    balance=parse_currency(str(row.get('balance', ''))) if 'balance' in row else None,
                    description=str(row.get('description', '')) if 'description' in row else None,
                    group_id=row_group_id,
                    subgroup_id=row_subgroup_id
                )
                
                db.add(investment)
                imported_count += 1
            
            except Exception as e:
                print(f"Erro ao importar linha: {e}")
                continue
        
        db.commit()
        return imported_count

    @staticmethod
    def import_credit_card_invoices(db: Session, client_id: int, df: pd.DataFrame,
                                   group_id: Optional[int] = None,
                                   subgroup_id: Optional[int] = None) -> int:
        """
        Importa faturas de cartão de crédito
        Colunas esperadas: transaction_date, description, value, category, establishment, installment_number
        """
        imported_count = 0
        
        for _, row in df.iterrows():
            try:
                transaction_date = parse_date(str(row.get('transaction_date', '')))
                if not transaction_date:
                    continue
                
                value = parse_currency(str(row.get('value', 0)))
                if value is None:
                    continue
                
                # Usa group_id e subgroup_id da linha se disponíveis, senão usa os parâmetros
                row_group_id, row_subgroup_id = _get_row_group_subgroup(row, group_id, subgroup_id)
                
                invoice = CreditCardInvoice(
                    client_id=client_id,
                    transaction_date=transaction_date.date(),
                    description=str(row.get('description', '')),
                    value=value,
                    category=str(row.get('category', '')) if 'category' in row else None,
                    establishment=str(row.get('establishment', '')) if 'establishment' in row else None,
                    installment_number=int(row.get('installment_number', 1)) if 'installment_number' in row else None,
                    total_installments=int(row.get('total_installments', 1)) if 'total_installments' in row else None,
                    card_brand=str(row.get('card_brand', '')) if 'card_brand' in row else None,
                    group_id=row_group_id,
                    subgroup_id=row_subgroup_id
                )
                
                db.add(invoice)
                imported_count += 1
            
            except Exception as e:
                print(f"Erro ao importar linha: {e}")
                continue
        
        db.commit()
        return imported_count

    @staticmethod
    def import_card_machine_statements(db: Session, client_id: int, df: pd.DataFrame,
                                      group_id: Optional[int] = None,
                                      subgroup_id: Optional[int] = None) -> int:
        """
        Importa extratos de máquina de cartão
        Colunas esperadas: date, gross_value, fee, net_value, card_brand, transaction_type
        """
        imported_count = 0
        
        for _, row in df.iterrows():
            try:
                date = parse_date(str(row.get('date', '')))
                if not date:
                    continue
                
                gross_value = parse_currency(str(row.get('gross_value', 0)))
                net_value = parse_currency(str(row.get('net_value', 0)))
                
                if gross_value is None and net_value is None:
                    continue
                
                if net_value is None:
                    net_value = gross_value
                if gross_value is None:
                    gross_value = net_value
                
                # Usa group_id e subgroup_id da linha se disponíveis, senão usa os parâmetros
                row_group_id, row_subgroup_id = _get_row_group_subgroup(row, group_id, subgroup_id)
                
                statement = CardMachineStatement(
                    client_id=client_id,
                    date=date.date(),
                    gross_value=gross_value,
                    fee=parse_currency(str(row.get('fee', ''))) if 'fee' in row else None,
                    net_value=net_value,
                    card_brand=str(row.get('card_brand', '')) if 'card_brand' in row else None,
                    transaction_type=str(row.get('transaction_type', '')) if 'transaction_type' in row else None,
                    description=str(row.get('description', '')) if 'description' in row else None,
                    group_id=row_group_id,
                    subgroup_id=row_subgroup_id
                )
                
                db.add(statement)
                imported_count += 1
            
            except Exception as e:
                print(f"Erro ao importar linha: {e}")
                continue
        
        db.commit()
        return imported_count

    @staticmethod
    def import_inventory(db: Session, client_id: int, df: pd.DataFrame,
                        group_id: Optional[int] = None,
                        subgroup_id: Optional[int] = None) -> int:
        """
        Importa controle de estoque
        Colunas esperadas: product_name, quantity, unit_value, movement_date, movement_type
        """
        imported_count = 0
        
        for _, row in df.iterrows():
            try:
                movement_date = parse_date(str(row.get('movement_date', '')))
                if not movement_date:
                    continue
                
                quantity = float(row.get('quantity', 0))
                unit_value = parse_currency(str(row.get('unit_value', 0)))
                
                if quantity == 0 or unit_value is None:
                    continue
                
                total_value = quantity * unit_value
                movement_type = str(row.get('movement_type', '')).lower()
                if movement_type not in ['entrada', 'saida']:
                    movement_type = 'entrada' if quantity > 0 else 'saida'
                
                # Usa group_id e subgroup_id da linha se disponíveis, senão usa os parâmetros
                row_group_id, row_subgroup_id = _get_row_group_subgroup(row, group_id, subgroup_id)
                
                inventory = Inventory(
                    client_id=client_id,
                    product_name=str(row.get('product_name', '')),
                    quantity=abs(quantity),
                    unit_value=unit_value,
                    total_value=total_value,
                    movement_date=movement_date.date(),
                    movement_type=movement_type,
                    description=str(row.get('description', '')) if 'description' in row else None,
                    group_id=row_group_id,
                    subgroup_id=row_subgroup_id
                )
                
                db.add(inventory)
                imported_count += 1
            
            except Exception as e:
                print(f"Erro ao importar linha: {e}")
                continue
        
        db.commit()
        return imported_count

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
