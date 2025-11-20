"""
Modelos do banco de dados
"""
from models.user import User, UserClientPermission
from models.group import Group, Subgroup
from models.transaction import Transaction, BankStatement
from models.contract import Contract
from models.account import AccountPayable, AccountReceivable, ImportMapping
from models.financial_investment import FinancialInvestment
from models.credit_card import CreditCardInvoice
from models.card_machine import CardMachineStatement
from models.inventory import Inventory
from models.client_report_config import ClientReportConfig
from models.ai_config import AIConfig
from models.client import Client  # Client por último para evitar referências circulares

__all__ = [
    'User',
    'UserClientPermission',
    'Client',
    'Group',
    'Subgroup',
    'Transaction',
    'BankStatement',
    'Contract',
    'AccountPayable',
    'AccountReceivable',
    'ImportMapping',
    'AIConfig',
    'FinancialInvestment',
    'CreditCardInvoice',
    'CardMachineStatement',
    'Inventory',
    'ClientReportConfig',
]



