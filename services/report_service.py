"""
Serviço de geração de relatórios e análises
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from collections import defaultdict
from models.transaction import Transaction, BankStatement
from models.account import AccountPayable, AccountReceivable
from models.contract import Contract
from models.financial_investment import FinancialInvestment
from models.credit_card import CreditCardInvoice
from models.card_machine import CardMachineStatement
from models.inventory import Inventory
from services.report_config_service import ReportConfigService
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd


class ReportService:
    """
    Serviço para gerar relatórios e análises financeiras
    """

    @staticmethod
    def get_dre_data(db: Session, client_id: int, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Gera dados para DRE (Demonstração do Resultado do Exercício)
        Inclui apenas os tipos de dados habilitados na configuração do cliente
        """
        # Verifica quais tipos de dados estão habilitados para DRE
        enabled_types = ReportConfigService.get_enabled_data_types(db, client_id, 'dre')
        
        # Receitas de transações (inclui extratos bancários convertidos automaticamente)
        receitas_trans = 0
        despesas_trans = 0
        if 'transactions' in enabled_types or 'bank_statements' in enabled_types:
            receitas_trans = db.query(
                func.sum(Transaction.value)
            ).filter(
                Transaction.client_id == client_id,
                Transaction.type == 'entrada',
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).scalar() or 0
            
            despesas_trans = db.query(
                func.sum(Transaction.value)
            ).filter(
                Transaction.client_id == client_id,
                Transaction.type == 'saida',
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).scalar() or 0
        
        # Receitas de contratos concluídos
        receitas_contratos = 0
        if 'contracts' in enabled_types:
            receitas_contratos = db.query(
                func.sum(Contract.service_value + Contract.displacement_value)
            ).filter(
                Contract.client_id == client_id,
                Contract.status == 'concluido',
                Contract.event_date >= start_date,
                Contract.event_date <= end_date
            ).scalar() or 0
        
        # Despesas de contas a pagar pagas
        despesas_contas_pagar = 0
        if 'accounts_payable' in enabled_types:
            despesas_contas_pagar = db.query(
                func.sum(AccountPayable.value)
            ).filter(
                AccountPayable.client_id == client_id,
                AccountPayable.paid == True,
                AccountPayable.payment_date >= start_date,
                AccountPayable.payment_date <= end_date
            ).scalar() or 0
        
        # Receitas de contas a receber recebidas
        receitas_contas_receber = 0
        if 'accounts_receivable' in enabled_types:
            receitas_contas_receber = db.query(
                func.sum(AccountReceivable.value)
            ).filter(
                AccountReceivable.client_id == client_id,
                AccountReceivable.received == True,
                AccountReceivable.receipt_date >= start_date,
                AccountReceivable.receipt_date <= end_date
            ).scalar() or 0
        
        # Receitas de faturas de cartão (despesas)
        despesas_cartao = 0
        if 'credit_card_invoices' in enabled_types:
            despesas_cartao = db.query(
                func.sum(CreditCardInvoice.value)
            ).filter(
                CreditCardInvoice.client_id == client_id,
                CreditCardInvoice.transaction_date >= start_date,
                CreditCardInvoice.transaction_date <= end_date
            ).scalar() or 0
        
        # Receitas de máquina de cartão (receitas líquidas)
        receitas_maquina_cartao = 0
        if 'card_machine_statements' in enabled_types:
            receitas_maquina_cartao = db.query(
                func.sum(CardMachineStatement.net_value)
            ).filter(
                CardMachineStatement.client_id == client_id,
                CardMachineStatement.date >= start_date,
                CardMachineStatement.date <= end_date
            ).scalar() or 0
        
        # Receitas de aplicações financeiras (rendimentos)
        receitas_aplicacoes = 0
        if 'financial_investments' in enabled_types:
            receitas_aplicacoes = db.query(
                func.sum(FinancialInvestment.yield_value)
            ).filter(
                FinancialInvestment.client_id == client_id,
                FinancialInvestment.date >= start_date,
                FinancialInvestment.date <= end_date,
                FinancialInvestment.yield_value.isnot(None)
            ).scalar() or 0
        
        # Custos de estoque (saídas de estoque = custo de produtos vendidos)
        custos_estoque = 0
        if 'inventory' in enabled_types:
            custos_estoque = db.query(
                func.sum(Inventory.total_value)
            ).filter(
                Inventory.client_id == client_id,
                Inventory.movement_type == 'saida',
                Inventory.movement_date >= start_date,
                Inventory.movement_date <= end_date
            ).scalar() or 0
        
        # Total - RESPEITA CONFIGURAÇÃO (soma apenas tipos habilitados)
        receitas = 0
        if 'transactions' in enabled_types or 'bank_statements' in enabled_types:
            receitas += receitas_trans
        if 'contracts' in enabled_types:
            receitas += receitas_contratos
        if 'accounts_receivable' in enabled_types:
            receitas += receitas_contas_receber
        if 'card_machine_statements' in enabled_types:
            receitas += receitas_maquina_cartao
        if 'financial_investments' in enabled_types:
            receitas += receitas_aplicacoes
        
        despesas = 0
        if 'transactions' in enabled_types or 'bank_statements' in enabled_types:
            despesas += despesas_trans
        if 'accounts_payable' in enabled_types:
            despesas += despesas_contas_pagar
        if 'credit_card_invoices' in enabled_types:
            despesas += despesas_cartao
        if 'inventory' in enabled_types:
            despesas += custos_estoque
        
        # Resultado
        resultado = receitas - despesas
        margem = (resultado / receitas * 100) if receitas > 0 else 0
        
        # Agregação por grupos e subgrupos (CLASSIFICAÇÃO PRINCIPAL)
        from models.group import Group, Subgroup
        receitas_subgrupo_totals = defaultdict(float)
        despesas_subgrupo_totals = defaultdict(float)

        def _append_subgrupo_rows(rows, target):
            for row in rows:
                total_value = float(getattr(row, 'total', 0) or 0)
                if total_value == 0:
                    continue
                grupo_nome = getattr(row, 'grupo', None) or 'Sem grupo'
                subgrupo_nome = getattr(row, 'subgrupo', None) or 'Sem subgrupo'
                target[(grupo_nome, subgrupo_nome)] += total_value
        
        # Receitas por grupo (apenas se transactions/bank_statements habilitados)
        receitas_por_grupo = []
        if 'transactions' in enabled_types or 'bank_statements' in enabled_types:
            receitas_por_grupo = db.query(
                Group.name,
                func.sum(Transaction.value).label('total')
            ).join(Transaction, Transaction.group_id == Group.id).filter(
                Transaction.client_id == client_id,
                Transaction.type == 'entrada',
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(Group.name).all()
        
        # Despesas por grupo (apenas se transactions/bank_statements habilitados)
        despesas_por_grupo = []
        if 'transactions' in enabled_types or 'bank_statements' in enabled_types:
            despesas_por_grupo = db.query(
                Group.name,
                func.sum(Transaction.value).label('total')
            ).join(Transaction, Transaction.group_id == Group.id).filter(
                Transaction.client_id == client_id,
                Transaction.type == 'saida',
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(Group.name).all()
        
        # Receitas por subgrupo (apenas se transactions/bank_statements habilitados)
        if 'transactions' in enabled_types or 'bank_statements' in enabled_types:
            receitas_por_subgrupo = db.query(
                Group.name.label('grupo'),
                Subgroup.name.label('subgrupo'),
                func.sum(Transaction.value).label('total')
            ).outerjoin(Subgroup, Transaction.subgroup_id == Subgroup.id).outerjoin(
                Group, Transaction.group_id == Group.id
            ).filter(
                Transaction.client_id == client_id,
                Transaction.type == 'entrada',
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(Group.name, Subgroup.name).all()
            _append_subgrupo_rows(receitas_por_subgrupo, receitas_subgrupo_totals)
        
        # Despesas por subgrupo (apenas se transactions/bank_statements habilitados)
        if 'transactions' in enabled_types or 'bank_statements' in enabled_types:
            despesas_por_subgrupo = db.query(
                Group.name.label('grupo'),
                Subgroup.name.label('subgrupo'),
                func.sum(Transaction.value).label('total')
            ).outerjoin(Subgroup, Transaction.subgroup_id == Subgroup.id).outerjoin(
                Group, Transaction.group_id == Group.id
            ).filter(
                Transaction.client_id == client_id,
                Transaction.type == 'saida',
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(Group.name, Subgroup.name).all()
            _append_subgrupo_rows(despesas_por_subgrupo, despesas_subgrupo_totals)

        # Agregações adicionais por subgrupos
        if 'contracts' in enabled_types:
            receitas_por_subgrupo_contratos = db.query(
                Group.name.label('grupo'),
                Subgroup.name.label('subgrupo'),
                func.sum(Contract.service_value + Contract.displacement_value).label('total')
            ).outerjoin(Group, Contract.group_id == Group.id).outerjoin(
                Subgroup, Contract.subgroup_id == Subgroup.id
            ).filter(
                Contract.client_id == client_id,
                Contract.status == 'concluido',
                Contract.event_date >= start_date,
                Contract.event_date <= end_date
            ).group_by(Group.name, Subgroup.name).all()
            _append_subgrupo_rows(receitas_por_subgrupo_contratos, receitas_subgrupo_totals)

        if 'accounts_receivable' in enabled_types:
            receitas_por_subgrupo_contas = db.query(
                Group.name.label('grupo'),
                Subgroup.name.label('subgrupo'),
                func.sum(AccountReceivable.value).label('total')
            ).outerjoin(Group, AccountReceivable.group_id == Group.id).outerjoin(
                Subgroup, AccountReceivable.subgroup_id == Subgroup.id
            ).filter(
                AccountReceivable.client_id == client_id,
                AccountReceivable.received == True,
                AccountReceivable.receipt_date >= start_date,
                AccountReceivable.receipt_date <= end_date
            ).group_by(Group.name, Subgroup.name).all()
            _append_subgrupo_rows(receitas_por_subgrupo_contas, receitas_subgrupo_totals)

        if 'card_machine_statements' in enabled_types:
            receitas_por_subgrupo_maquina = db.query(
                Group.name.label('grupo'),
                Subgroup.name.label('subgrupo'),
                func.sum(CardMachineStatement.net_value).label('total')
            ).outerjoin(Group, CardMachineStatement.group_id == Group.id).outerjoin(
                Subgroup, CardMachineStatement.subgroup_id == Subgroup.id
            ).filter(
                CardMachineStatement.client_id == client_id,
                CardMachineStatement.date >= start_date,
                CardMachineStatement.date <= end_date
            ).group_by(Group.name, Subgroup.name).all()
            _append_subgrupo_rows(receitas_por_subgrupo_maquina, receitas_subgrupo_totals)

        if 'financial_investments' in enabled_types:
            receitas_por_subgrupo_invest = db.query(
                Group.name.label('grupo'),
                Subgroup.name.label('subgrupo'),
                func.sum(FinancialInvestment.yield_value).label('total')
            ).outerjoin(Group, FinancialInvestment.group_id == Group.id).outerjoin(
                Subgroup, FinancialInvestment.subgroup_id == Subgroup.id
            ).filter(
                FinancialInvestment.client_id == client_id,
                FinancialInvestment.date >= start_date,
                FinancialInvestment.date <= end_date,
                FinancialInvestment.yield_value.isnot(None)
            ).group_by(Group.name, Subgroup.name).all()
            _append_subgrupo_rows(receitas_por_subgrupo_invest, receitas_subgrupo_totals)

        if 'accounts_payable' in enabled_types:
            despesas_por_subgrupo_contas = db.query(
                Group.name.label('grupo'),
                Subgroup.name.label('subgrupo'),
                func.sum(AccountPayable.value).label('total')
            ).outerjoin(Group, AccountPayable.group_id == Group.id).outerjoin(
                Subgroup, AccountPayable.subgroup_id == Subgroup.id
            ).filter(
                AccountPayable.client_id == client_id,
                AccountPayable.paid == True,
                AccountPayable.payment_date >= start_date,
                AccountPayable.payment_date <= end_date
            ).group_by(Group.name, Subgroup.name).all()
            _append_subgrupo_rows(despesas_por_subgrupo_contas, despesas_subgrupo_totals)

        if 'credit_card_invoices' in enabled_types:
            despesas_por_subgrupo_cartao = db.query(
                Group.name.label('grupo'),
                Subgroup.name.label('subgrupo'),
                func.sum(CreditCardInvoice.value).label('total')
            ).outerjoin(Group, CreditCardInvoice.group_id == Group.id).outerjoin(
                Subgroup, CreditCardInvoice.subgroup_id == Subgroup.id
            ).filter(
                CreditCardInvoice.client_id == client_id,
                CreditCardInvoice.transaction_date >= start_date,
                CreditCardInvoice.transaction_date <= end_date
            ).group_by(Group.name, Subgroup.name).all()
            _append_subgrupo_rows(despesas_por_subgrupo_cartao, despesas_subgrupo_totals)

        if 'inventory' in enabled_types:
            despesas_por_subgrupo_estoque = db.query(
                Group.name.label('grupo'),
                Subgroup.name.label('subgrupo'),
                func.sum(Inventory.total_value).label('total')
            ).outerjoin(Group, Inventory.group_id == Group.id).outerjoin(
                Subgroup, Inventory.subgroup_id == Subgroup.id
            ).filter(
                Inventory.client_id == client_id,
                Inventory.movement_type == 'saida',
                Inventory.movement_date >= start_date,
                Inventory.movement_date <= end_date
            ).group_by(Group.name, Subgroup.name).all()
            _append_subgrupo_rows(despesas_por_subgrupo_estoque, despesas_subgrupo_totals)
        
        # Agregação por grupos/subgrupos para contratos (apenas se habilitado)
        receitas_por_grupo_contratos = []
        if 'contracts' in enabled_types:
            receitas_por_grupo_contratos = db.query(
                Group.name,
                func.sum(Contract.service_value + Contract.displacement_value).label('total')
            ).join(Contract, Contract.group_id == Group.id).filter(
                Contract.client_id == client_id,
                Contract.status == 'concluido',
                Contract.event_date >= start_date,
                Contract.event_date <= end_date
            ).group_by(Group.name).all()
        
        # Agregação por grupos/subgrupos para contas a pagar (apenas se habilitado)
        despesas_por_grupo_contas_pagar = []
        if 'accounts_payable' in enabled_types:
            despesas_por_grupo_contas_pagar = db.query(
                Group.name,
                func.sum(AccountPayable.value).label('total')
            ).join(AccountPayable, AccountPayable.group_id == Group.id).filter(
                AccountPayable.client_id == client_id,
                AccountPayable.paid == True,
                AccountPayable.payment_date >= start_date,
                AccountPayable.payment_date <= end_date
            ).group_by(Group.name).all()
        
        # Agregação por grupos/subgrupos para contas a receber (apenas se habilitado)
        receitas_por_grupo_contas_receber = []
        if 'accounts_receivable' in enabled_types:
            receitas_por_grupo_contas_receber = db.query(
                Group.name,
                func.sum(AccountReceivable.value).label('total')
            ).join(AccountReceivable, AccountReceivable.group_id == Group.id).filter(
                AccountReceivable.client_id == client_id,
                AccountReceivable.received == True,
                AccountReceivable.receipt_date >= start_date,
                AccountReceivable.receipt_date <= end_date
            ).group_by(Group.name).all()
        
        # Consolidar receitas por grupo (todas as fontes)
        receitas_por_grupo_consolidado = defaultdict(float)
        for (grupo, _subgrupo), valor in receitas_subgrupo_totals.items():
            receitas_por_grupo_consolidado[grupo] += valor
        for r in receitas_por_grupo:
            grupo = r[0] or 'Sem grupo'
            receitas_por_grupo_consolidado[grupo] = receitas_por_grupo_consolidado.get(grupo, 0) + float(r[1])
        for r in receitas_por_grupo_contratos:
            grupo = r[0] or 'Sem grupo'
            receitas_por_grupo_consolidado[grupo] = receitas_por_grupo_consolidado.get(grupo, 0) + float(r[1])
        for r in receitas_por_grupo_contas_receber:
            grupo = r[0] or 'Sem grupo'
            receitas_por_grupo_consolidado[grupo] = receitas_por_grupo_consolidado.get(grupo, 0) + float(r[1])
        
        # Consolidar despesas por grupo (todas as fontes)
        despesas_por_grupo_consolidado = defaultdict(float)
        for (grupo, _subgrupo), valor in despesas_subgrupo_totals.items():
            despesas_por_grupo_consolidado[grupo] += valor
        for d in despesas_por_grupo:
            grupo = d[0] or 'Sem grupo'
            despesas_por_grupo_consolidado[grupo] = despesas_por_grupo_consolidado.get(grupo, 0) + float(d[1])
        for d in despesas_por_grupo_contas_pagar:
            grupo = d[0] or 'Sem grupo'
            despesas_por_grupo_consolidado[grupo] = despesas_por_grupo_consolidado.get(grupo, 0) + float(d[1])
        
        # Receitas por categoria (FALLBACK - apenas para transações sem grupo/subgrupo)
        receitas_por_categoria = []
        if 'transactions' in enabled_types or 'bank_statements' in enabled_types:
            receitas_por_categoria = db.query(
                Transaction.category,
                func.sum(Transaction.value).label('total')
            ).filter(
                Transaction.client_id == client_id,
                Transaction.type == 'entrada',
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.group_id.is_(None)  # Apenas transações sem grupo
            ).group_by(Transaction.category).all()
        
        # Despesas por categoria (FALLBACK - apenas para transações sem grupo/subgrupo)
        despesas_por_categoria = []
        if 'transactions' in enabled_types or 'bank_statements' in enabled_types:
            despesas_por_categoria = db.query(
                Transaction.category,
                func.sum(Transaction.value).label('total')
            ).filter(
                Transaction.client_id == client_id,
                Transaction.type == 'saida',
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.group_id.is_(None)  # Apenas transações sem grupo
            ).group_by(Transaction.category).all()
        
        return {
            'receitas': float(receitas),
            'despesas': float(despesas),
            'resultado': float(resultado),
            'margem': float(margem),
            # Classificação PRINCIPAL: Grupo e Subgrupo
            'receitas_por_grupo': sorted(
                [{'grupo': grupo, 'valor': valor} for grupo, valor in receitas_por_grupo_consolidado.items()],
                key=lambda item: item['valor'],
                reverse=True
            ),
            'despesas_por_grupo': sorted(
                [{'grupo': grupo, 'valor': valor} for grupo, valor in despesas_por_grupo_consolidado.items()],
                key=lambda item: item['valor'],
                reverse=True
            ),
            'receitas_por_subgrupo': sorted(
                [
                    {'grupo': grupo, 'subgrupo': subgrupo, 'valor': valor}
                    for (grupo, subgrupo), valor in receitas_subgrupo_totals.items()
                ],
                key=lambda item: item['valor'],
                reverse=True
            ),
            'despesas_por_subgrupo': sorted(
                [
                    {'grupo': grupo, 'subgrupo': subgrupo, 'valor': valor}
                    for (grupo, subgrupo), valor in despesas_subgrupo_totals.items()
                ],
                key=lambda item: item['valor'],
                reverse=True
            ),
            # Classificação SECUNDÁRIA: Categoria (apenas para transações sem grupo/subgrupo)
            'receitas_por_categoria': [{'categoria': r[0] or 'Sem categoria', 'valor': float(r[1])} for r in receitas_por_categoria] if ('transactions' in enabled_types or 'bank_statements' in enabled_types) else [],
            'despesas_por_categoria': [{'categoria': d[0] or 'Sem categoria', 'valor': float(d[1])} for d in despesas_por_categoria] if ('transactions' in enabled_types or 'bank_statements' in enabled_types) else [],
            # Retorna valores individuais APENAS se tipo estiver habilitado
            'receitas_contratos': float(receitas_contratos) if 'contracts' in enabled_types else 0,
            'receitas_contas_receber': float(receitas_contas_receber) if 'accounts_receivable' in enabled_types else 0,
            'despesas_contas_pagar': float(despesas_contas_pagar) if 'accounts_payable' in enabled_types else 0,
            'receitas_maquina_cartao': float(receitas_maquina_cartao) if 'card_machine_statements' in enabled_types else 0,
            'receitas_aplicacoes': float(receitas_aplicacoes) if 'financial_investments' in enabled_types else 0,
            'despesas_cartao': float(despesas_cartao) if 'credit_card_invoices' in enabled_types else 0,
            'custos_estoque': float(custos_estoque) if 'inventory' in enabled_types else 0,
            'enabled_data_types': enabled_types  # Lista de tipos habilitados
        }

    @staticmethod
    def get_dfc_data(db: Session, client_id: int, start_date: date, end_date: date, 
                     group_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Gera dados para DFC (Demonstração do Fluxo de Caixa)
        Inclui apenas os tipos de dados habilitados na configuração do cliente
        
        Args:
            db: Sessão do banco de dados
            client_id: ID do cliente
            start_date: Data inicial
            end_date: Data final
            group_id: ID do grupo para filtrar (opcional). Se None, retorna todos os grupos
        """
        # Verifica quais tipos de dados estão habilitados para DFC
        enabled_types = ReportConfigService.get_enabled_data_types(db, client_id, 'dfc')
        
        # Filtro base
        transaction_filter = [
            Transaction.client_id == client_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ]
        
        # Adiciona filtro por grupo se fornecido
        if group_id is not None:
            transaction_filter.append(Transaction.group_id == group_id)
        
        # Fluxo por mês - Transações (inclui extratos bancários convertidos automaticamente)
        transactions = []
        if 'transactions' in enabled_types or 'bank_statements' in enabled_types:
            transactions = db.query(
                extract('year', Transaction.date).label('year'),
                extract('month', Transaction.date).label('month'),
                Transaction.type,
                func.sum(Transaction.value).label('total')
            ).filter(*transaction_filter).group_by('year', 'month', Transaction.type).all()
        
        # Fluxo por grupo (para análises detalhadas)
        from models.group import Group
        fluxo_por_grupo = {}
        
        transactions_por_grupo = []
        if 'transactions' in enabled_types or 'bank_statements' in enabled_types:
            transactions_por_grupo = db.query(
                Group.name.label('grupo'),
                extract('year', Transaction.date).label('year'),
                extract('month', Transaction.date).label('month'),
                Transaction.type,
                func.sum(Transaction.value).label('total')
            ).join(Transaction, Transaction.group_id == Group.id).filter(
                Transaction.client_id == client_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(Group.name, 'year', 'month', Transaction.type).all()
        
        # Organiza fluxo por grupo
        for trans in transactions_por_grupo:
            grupo = trans.grupo or 'Sem grupo'
            month_key = f"{int(trans.year)}-{int(trans.month):02d}"
            
            if grupo not in fluxo_por_grupo:
                fluxo_por_grupo[grupo] = {}
            
            if month_key not in fluxo_por_grupo[grupo]:
                fluxo_por_grupo[grupo][month_key] = {'entradas': 0, 'saidas': 0}
            
            if trans.type == 'entrada':
                fluxo_por_grupo[grupo][month_key]['entradas'] += float(trans.total)
            else:
                fluxo_por_grupo[grupo][month_key]['saidas'] += float(trans.total)
        
        # Fluxo por mês - Contratos concluídos (apenas se habilitado)
        contracts = []
        if 'contracts' in enabled_types:
            contracts = db.query(
                extract('year', Contract.event_date).label('year'),
                extract('month', Contract.event_date).label('month'),
                func.sum(Contract.service_value + Contract.displacement_value).label('total')
            ).filter(
                Contract.client_id == client_id,
                Contract.status == 'concluido',
                Contract.event_date >= start_date,
                Contract.event_date <= end_date
            ).group_by('year', 'month').all()
        
        # Fluxo por mês - Contas a pagar pagas (apenas se habilitado)
        accounts_payable = []
        if 'accounts_payable' in enabled_types:
            accounts_payable = db.query(
                extract('year', AccountPayable.payment_date).label('year'),
                extract('month', AccountPayable.payment_date).label('month'),
                func.sum(AccountPayable.value).label('total')
            ).filter(
                AccountPayable.client_id == client_id,
                AccountPayable.paid == True,
                AccountPayable.payment_date >= start_date,
                AccountPayable.payment_date <= end_date
            ).group_by('year', 'month').all()
        
        # Fluxo por mês - Contas a receber recebidas (apenas se habilitado)
        accounts_receivable = []
        if 'accounts_receivable' in enabled_types:
            accounts_receivable = db.query(
                extract('year', AccountReceivable.receipt_date).label('year'),
                extract('month', AccountReceivable.receipt_date).label('month'),
                func.sum(AccountReceivable.value).label('total')
            ).filter(
                AccountReceivable.client_id == client_id,
                AccountReceivable.received == True,
                AccountReceivable.receipt_date >= start_date,
                AccountReceivable.receipt_date <= end_date
            ).group_by('year', 'month').all()
        
        # Fluxo por mês - Faturas de cartão (despesas) (apenas se habilitado)
        credit_card_invoices = []
        if 'credit_card_invoices' in enabled_types:
            credit_card_invoices = db.query(
                extract('year', CreditCardInvoice.transaction_date).label('year'),
                extract('month', CreditCardInvoice.transaction_date).label('month'),
                func.sum(CreditCardInvoice.value).label('total')
            ).filter(
                CreditCardInvoice.client_id == client_id,
                CreditCardInvoice.transaction_date >= start_date,
                CreditCardInvoice.transaction_date <= end_date
            ).group_by('year', 'month').all()
        
        # Fluxo por mês - Máquina de cartão (receitas líquidas) (apenas se habilitado)
        card_machine_statements = []
        if 'card_machine_statements' in enabled_types:
            card_machine_statements = db.query(
                extract('year', CardMachineStatement.date).label('year'),
                extract('month', CardMachineStatement.date).label('month'),
                func.sum(CardMachineStatement.net_value).label('total')
            ).filter(
                CardMachineStatement.client_id == client_id,
                CardMachineStatement.date >= start_date,
                CardMachineStatement.date <= end_date
            ).group_by('year', 'month').all()
        
        # Fluxo por mês - Aplicações financeiras (rendimentos) (apenas se habilitado)
        financial_investments = []
        if 'financial_investments' in enabled_types:
            financial_investments = db.query(
                extract('year', FinancialInvestment.date).label('year'),
                extract('month', FinancialInvestment.date).label('month'),
                func.sum(FinancialInvestment.yield_value).label('total')
            ).filter(
                FinancialInvestment.client_id == client_id,
                FinancialInvestment.date >= start_date,
                FinancialInvestment.date <= end_date,
                FinancialInvestment.yield_value.isnot(None)
            ).group_by('year', 'month').all()
        
        # Organiza por mês
        fluxo_mensal = {}
        
        # Adiciona transações
        for trans in transactions:
            month_key = f"{int(trans.year)}-{int(trans.month):02d}"
            if month_key not in fluxo_mensal:
                fluxo_mensal[month_key] = {'entradas': 0, 'saidas': 0}
            
            if trans.type == 'entrada':
                fluxo_mensal[month_key]['entradas'] += float(trans.total)
            else:
                fluxo_mensal[month_key]['saidas'] += float(trans.total)
        
        # Adiciona contratos concluídos (entradas)
        for contract in contracts:
            month_key = f"{int(contract.year)}-{int(contract.month):02d}"
            if month_key not in fluxo_mensal:
                fluxo_mensal[month_key] = {'entradas': 0, 'saidas': 0}
            fluxo_mensal[month_key]['entradas'] += float(contract.total)
        
        # Adiciona contas a pagar pagas (saídas)
        for account in accounts_payable:
            month_key = f"{int(account.year)}-{int(account.month):02d}"
            if month_key not in fluxo_mensal:
                fluxo_mensal[month_key] = {'entradas': 0, 'saidas': 0}
            fluxo_mensal[month_key]['saidas'] += float(account.total)
        
        # Adiciona contas a receber recebidas (entradas)
        for account in accounts_receivable:
            month_key = f"{int(account.year)}-{int(account.month):02d}"
            if month_key not in fluxo_mensal:
                fluxo_mensal[month_key] = {'entradas': 0, 'saidas': 0}
            fluxo_mensal[month_key]['entradas'] += float(account.total)
        
        # Adiciona faturas de cartão (saídas)
        for invoice in credit_card_invoices:
            month_key = f"{int(invoice.year)}-{int(invoice.month):02d}"
            if month_key not in fluxo_mensal:
                fluxo_mensal[month_key] = {'entradas': 0, 'saidas': 0}
            fluxo_mensal[month_key]['saidas'] += float(invoice.total)
        
        # Adiciona máquina de cartão (entradas líquidas)
        for machine in card_machine_statements:
            month_key = f"{int(machine.year)}-{int(machine.month):02d}"
            if month_key not in fluxo_mensal:
                fluxo_mensal[month_key] = {'entradas': 0, 'saidas': 0}
            fluxo_mensal[month_key]['entradas'] += float(machine.total)
        
        # Adiciona aplicações financeiras (entradas - rendimentos)
        for investment in financial_investments:
            month_key = f"{int(investment.year)}-{int(investment.month):02d}"
            if month_key not in fluxo_mensal:
                fluxo_mensal[month_key] = {'entradas': 0, 'saidas': 0}
            fluxo_mensal[month_key]['entradas'] += float(investment.total)
        
        # Adiciona movimentações de estoque (saídas)
        inventory_movements = []
        if 'inventory' in enabled_types:
            inventory_movements = db.query(
                extract('year', Inventory.movement_date).label('year'),
                extract('month', Inventory.movement_date).label('month'),
                func.sum(Inventory.total_value).label('total')
            ).filter(
                Inventory.client_id == client_id,
                Inventory.movement_type == 'saida',
                Inventory.movement_date >= start_date,
                Inventory.movement_date <= end_date
            ).group_by('year', 'month').all()
        
        for inv in inventory_movements:
            month_key = f"{int(inv.year)}-{int(inv.month):02d}"
            if month_key not in fluxo_mensal:
                fluxo_mensal[month_key] = {'entradas': 0, 'saidas': 0}
            fluxo_mensal[month_key]['saidas'] += float(inv.total)
        
        # Calcula saldo acumulado
        saldo_acumulado = 0
        fluxo_list = []
        
        for month_key in sorted(fluxo_mensal.keys()):
            entradas = fluxo_mensal[month_key]['entradas']
            saidas = fluxo_mensal[month_key]['saidas']
            saldo_mes = entradas - saidas
            saldo_acumulado += saldo_mes
            
            fluxo_list.append({
                'mes': month_key,
                'entradas': entradas,
                'saidas': saidas,
                'saldo_mes': saldo_mes,
                'saldo_acumulado': saldo_acumulado
            })
        
        # Converte fluxo por grupo para lista
        fluxo_por_grupo_list = []
        for grupo, meses in fluxo_por_grupo.items():
            grupo_fluxo = []
            saldo_grupo = 0
            for month_key in sorted(meses.keys()):
                entradas = meses[month_key]['entradas']
                saidas = meses[month_key]['saidas']
                saldo_mes = entradas - saidas
                saldo_grupo += saldo_mes
                
                grupo_fluxo.append({
                    'mes': month_key,
                    'entradas': entradas,
                    'saidas': saidas,
                    'saldo_mes': saldo_mes,
                    'saldo_acumulado': saldo_grupo
                })
            
            fluxo_por_grupo_list.append({
                'grupo': grupo,
                'fluxo_mensal': grupo_fluxo,
                'saldo_final': saldo_grupo
            })
        
        source_totals = []

        def _add_source_entry(label: str, value: float, natureza: str):
            if value and abs(value) > 0:
                source_totals.append({
                    'fonte': label,
                    'valor': float(value),
                    'tipo': natureza
                })

        trans_entradas_total = sum(float(trans.total) for trans in transactions if getattr(trans, 'type', '') == 'entrada')
        trans_saidas_total = sum(float(trans.total) for trans in transactions if getattr(trans, 'type', '') == 'saida')
        _add_source_entry('Transações (entradas)', trans_entradas_total, 'entrada')
        _add_source_entry('Transações (saídas)', trans_saidas_total, 'saida')
        _add_source_entry('Contratos concluídos', sum(float(contract.total) for contract in contracts), 'entrada')
        _add_source_entry('Contas a pagar (pagas)', sum(float(account.total) for account in accounts_payable), 'saida')
        _add_source_entry('Contas a receber (recebidas)', sum(float(account.total) for account in accounts_receivable), 'entrada')
        _add_source_entry('Faturas de cartão', sum(float(invoice.total) for invoice in credit_card_invoices), 'saida')
        _add_source_entry('Extratos máquina de cartão', sum(float(machine.total) for machine in card_machine_statements), 'entrada')
        _add_source_entry('Aplicações financeiras (rendimentos)', sum(float(investment.total) for investment in financial_investments), 'entrada')
        _add_source_entry('Estoque (saídas)', sum(float(inv.total) for inv in inventory_movements), 'saida')

        return {
            'fluxo_mensal': fluxo_list,
            'saldo_final': saldo_acumulado,
            'fluxo_por_grupo': fluxo_por_grupo_list,  # Agrupamento opcional por grupo
            'enabled_data_types': enabled_types,  # Lista de tipos habilitados
            'source_totals': source_totals
        }

    @staticmethod
    def get_seasonality_data(db: Session, client_id: int) -> Dict[str, Any]:
        """
        Analisa sazonalidade dos dados
        Inclui apenas os tipos de dados habilitados na configuração do cliente
        """
        # Verifica quais tipos de dados estão habilitados para Sazonalidade
        enabled_types = ReportConfigService.get_enabled_data_types(db, client_id, 'sazonalidade')
        
        # Receitas por mês (todos os anos) - Transações
        receitas_mensal = []
        if 'transactions' in enabled_types or 'bank_statements' in enabled_types:
            receitas_mensal = db.query(
                extract('year', Transaction.date).label('year'),
                extract('month', Transaction.date).label('month'),
                func.sum(Transaction.value).label('total')
            ).filter(
                Transaction.client_id == client_id,
                Transaction.type == 'entrada'
            ).group_by('year', 'month').all()
        
        # Receitas de contratos por mês
        receitas_contratos_mensal = []
        if 'contracts' in enabled_types:
            receitas_contratos_mensal = db.query(
                extract('year', Contract.event_date).label('year'),
                extract('month', Contract.event_date).label('month'),
                func.sum(Contract.service_value + Contract.displacement_value).label('total')
            ).filter(
                Contract.client_id == client_id,
                Contract.status == 'concluido'
            ).group_by('year', 'month').all()
        
        # Receitas de contas a receber por mês
        receitas_contas_receber_mensal = []
        if 'accounts_receivable' in enabled_types:
            receitas_contas_receber_mensal = db.query(
                extract('year', AccountReceivable.receipt_date).label('year'),
                extract('month', AccountReceivable.receipt_date).label('month'),
                func.sum(AccountReceivable.value).label('total')
            ).filter(
                AccountReceivable.client_id == client_id,
                AccountReceivable.received == True
            ).group_by('year', 'month').all()
        
        # Receitas de máquina de cartão por mês
        receitas_maquina_cartao_mensal = []
        if 'card_machine_statements' in enabled_types:
            receitas_maquina_cartao_mensal = db.query(
                extract('year', CardMachineStatement.date).label('year'),
                extract('month', CardMachineStatement.date).label('month'),
                func.sum(CardMachineStatement.net_value).label('total')
            ).filter(
                CardMachineStatement.client_id == client_id
            ).group_by('year', 'month').all()
        
        # Receitas de aplicações financeiras por mês (rendimentos)
        receitas_aplicacoes_mensal = []
        if 'financial_investments' in enabled_types:
            receitas_aplicacoes_mensal = db.query(
                extract('year', FinancialInvestment.date).label('year'),
                extract('month', FinancialInvestment.date).label('month'),
                func.sum(FinancialInvestment.yield_value).label('total')
            ).filter(
                FinancialInvestment.client_id == client_id,
                FinancialInvestment.yield_value.isnot(None)
            ).group_by('year', 'month').all()
        
        # Consolida todas as receitas
        all_receitas = {}
        receitas_por_grupo_mes = defaultdict(lambda: defaultdict(float))
        source_data = defaultdict(lambda: defaultdict(float))
        
        # Helper para consolidar
        def _consolidate_receitas(records, source_label):
            for rec in records:
                year = int(rec.year)
                month = int(rec.month)
                key = (year, month)
                value = float(rec.total)
                all_receitas[key] = all_receitas.get(key, 0) + value
                source_data[key][source_label] += value
        
        _consolidate_receitas(receitas_mensal, 'Transações')
        _consolidate_receitas(receitas_contratos_mensal, 'Contratos')
        _consolidate_receitas(receitas_contas_receber_mensal, 'Contas a Receber')
        _consolidate_receitas(receitas_maquina_cartao_mensal, 'Máquina de Cartão')
        _consolidate_receitas(receitas_aplicacoes_mensal, 'Aplicações Financeiras')
        
        # Receitas por grupo/subgrupo - Transações
        from models.group import Group, Subgroup
        if 'transactions' in enabled_types or 'bank_statements' in enabled_types:
            receitas_grupo_mensal = db.query(
                extract('year', Transaction.date).label('year'),
                extract('month', Transaction.date).label('month'),
                Group.name.label('grupo'),
                Subgroup.name.label('subgrupo'),
                func.sum(Transaction.value).label('total')
            ).outerjoin(Group, Transaction.group_id == Group.id).outerjoin(
                Subgroup, Transaction.subgroup_id == Subgroup.id
            ).filter(
                Transaction.client_id == client_id,
                Transaction.type == 'entrada'
            ).group_by('year', 'month', Group.name, Subgroup.name).all()
            
            for rec in receitas_grupo_mensal:
                year = int(rec.year)
                month = int(rec.month)
                grupo = rec.grupo or 'Sem grupo'
                subgrupo = rec.subgrupo or 'Sem subgrupo'
                key = (year, month)
                receitas_por_grupo_mes[key][f"{grupo} > {subgrupo}"] += float(rec.total)
        
        # Organiza por ano e mês
        data_by_year = {}
        for (year, month), total in all_receitas.items():
            if year not in data_by_year:
                data_by_year[year] = {}
            data_by_year[year][month] = total
        
        # Média por mês (considerando todos os anos)
        month_averages = {}
        for year, months in data_by_year.items():
            for month, value in months.items():
                if month not in month_averages:
                    month_averages[month] = []
                month_averages[month].append(value)
        
        month_avg_list = []
        for month in range(1, 13):
            if month in month_averages:
                avg = sum(month_averages[month]) / len(month_averages[month])
            else:
                avg = 0
            
            month_avg_list.append({
                'mes': month,
                'media': avg
            })
        
        # Converte dados de origem para lista
        source_breakdown = []
        for (year, month), sources in source_data.items():
            for source_name, value in sources.items():
                source_breakdown.append({
                    'ano': year,
                    'mes': month,
                    'fonte': source_name,
                    'valor': value
                })
        
        # Converte grupos por mês para lista
        grupos_por_mes = []
        for (year, month), grupos in receitas_por_grupo_mes.items():
            for grupo_label, value in grupos.items():
                grupos_por_mes.append({
                    'ano': year,
                    'mes': month,
                    'grupo_subgrupo': grupo_label,
                    'valor': value
                })
        
        return {
            'por_ano': data_by_year,
            'media_mensal': month_avg_list,
            'por_grupo_mes': grupos_por_mes,
            'por_fonte': source_breakdown,
            'enabled_data_types': enabled_types  # Lista de tipos habilitados
        }

    @staticmethod
    def get_kpis(db: Session, client_id: int, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Calcula KPIs principais
        """
        dre = ReportService.get_dre_data(db, client_id, start_date, end_date)
        
        # Contas a pagar pendentes
        contas_pagar = db.query(
            func.sum(AccountPayable.value)
        ).filter(
            AccountPayable.client_id == client_id,
            AccountPayable.paid == False
        ).scalar() or 0
        
        # Contas a receber pendentes
        contas_receber = db.query(
            func.sum(AccountReceivable.value)
        ).filter(
            AccountReceivable.client_id == client_id,
            AccountReceivable.received == False
        ).scalar() or 0
        
        # Contratos ativos
        contratos_ativos = db.query(func.count(Contract.id)).filter(
            Contract.client_id == client_id,
            Contract.status.in_(['pendente', 'em_andamento'])
        ).scalar() or 0
        
        # Valor total de contratos ativos
        valor_contratos = db.query(
            func.sum(Contract.service_value + Contract.displacement_value)
        ).filter(
            Contract.client_id == client_id,
            Contract.status.in_(['pendente', 'em_andamento'])
        ).scalar() or 0
        
        return {
            'receitas': dre['receitas'],
            'despesas': dre['despesas'],
            'resultado': dre['resultado'],
            'margem': dre['margem'],
            'contas_pagar': float(contas_pagar),
            'contas_receber': float(contas_receber),
            'contratos_ativos': int(contratos_ativos),
            'valor_contratos': float(valor_contratos)
        }

    @staticmethod
    def get_bank_statements_data(db: Session, client_id: int, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Gera dados específicos de extratos bancários
        Busca de transactions onde document_type == 'extrato_bancario' (fonte única de verdade)
        """
        # Busca de transactions (fonte única)
        statements = db.query(Transaction).filter(
            Transaction.client_id == client_id,
            Transaction.document_type == 'extrato_bancario',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).order_by(Transaction.date).all()
        
        # Estatísticas
        total_creditos = sum(s.value for s in statements if s.type == 'entrada')
        total_debitos = sum(s.value for s in statements if s.type == 'saida')
        saldo_final = total_creditos - total_debitos
        
        # Por banco
        bank_stats = {}
        for stmt in statements:
            bank = stmt.bank_name or 'Sem banco'
            if bank not in bank_stats:
                bank_stats[bank] = {'creditos': 0, 'debitos': 0, 'count': 0}
            
            if stmt.type == 'entrada':
                bank_stats[bank]['creditos'] += stmt.value
            else:
                bank_stats[bank]['debitos'] += stmt.value
            bank_stats[bank]['count'] += 1
        
        # Por mês
        monthly_stats = {}
        for stmt in statements:
            month_key = stmt.date.strftime('%Y-%m')
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {'creditos': 0, 'debitos': 0, 'count': 0}
            
            if stmt.type == 'entrada':
                monthly_stats[month_key]['creditos'] += stmt.value
            else:
                monthly_stats[month_key]['debitos'] += stmt.value
            monthly_stats[month_key]['count'] += 1
        
        # Busca saldos de bank_statements para exibição (join opcional)
        # Cria mapeamento de saldos
        bank_statements_map = {}
        bank_stmts = db.query(BankStatement).filter(
            BankStatement.client_id == client_id,
            BankStatement.date >= start_date,
            BankStatement.date <= end_date
        ).all()
        for bs in bank_stmts:
            key = (bs.date, bs.description, abs(bs.value))
            bank_statements_map[key] = bs.balance
        
        # Prepara lista de extratos com saldo (se disponível)
        extratos_list = []
        for s in statements:
            balance = None
            key = (s.date, s.description, s.value)
            if key in bank_statements_map:
                balance = bank_statements_map[key]
            
            extratos_list.append({
                'id': s.id,
                'date': s.date,
                'bank_name': s.bank_name,
                'account': s.account,
                'description': s.description,
                'value': float(s.value),
                'type': s.type,
                'balance': float(balance) if balance is not None else None
            })
        
        return {
            'total_creditos': float(total_creditos),
            'total_debitos': float(total_debitos),
            'saldo_final': float(saldo_final),
            'total_registros': len(statements),
            'por_banco': bank_stats,
            'por_mes': monthly_stats,
            'extratos': extratos_list
        }
    
    @staticmethod
    def get_dfc_projection(db: Session, client_id: int, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Gera projeção de DFC baseada em contas a receber e contas a pagar futuras
        Usa parcelas mensais para projetar fluxo de caixa
        """
        from dateutil.relativedelta import relativedelta
        
        # Busca contas a receber não recebidas (futuras)
        accounts_receivable = db.query(AccountReceivable).filter(
            AccountReceivable.client_id == client_id,
            AccountReceivable.received == False,
            AccountReceivable.due_date >= start_date,
            AccountReceivable.due_date <= end_date
        ).order_by(AccountReceivable.due_date).all()
        
        # Busca contas a pagar não pagas (futuras)
        accounts_payable = db.query(AccountPayable).filter(
            AccountPayable.client_id == client_id,
            AccountPayable.paid == False,
            AccountPayable.due_date >= start_date,
            AccountPayable.due_date <= end_date
        ).order_by(AccountPayable.due_date).all()
        
        # Organiza por mês
        projection = {}
        
        # Adiciona entradas previstas (contas a receber)
        for ar in accounts_receivable:
            month_key = ar.due_date.strftime('%Y-%m')
            if month_key not in projection:
                projection[month_key] = {'entradas_previstas': 0, 'saidas_previstas': 0, 'saldo_projetado': 0}
            projection[month_key]['entradas_previstas'] += float(ar.value)
        
        # Adiciona saídas previstas (contas a pagar)
        for ap in accounts_payable:
            month_key = ap.due_date.strftime('%Y-%m')
            if month_key not in projection:
                projection[month_key] = {'entradas_previstas': 0, 'saidas_previstas': 0, 'saldo_projetado': 0}
            projection[month_key]['saidas_previstas'] += float(ap.value)
        
        # Calcula saldo projetado por mês
        saldo_acumulado = 0
        projection_list = []
        
        for month_key in sorted(projection.keys()):
            entradas = projection[month_key]['entradas_previstas']
            saidas = projection[month_key]['saidas_previstas']
            saldo_mes = entradas - saidas
            saldo_acumulado += saldo_mes
            
            projection_list.append({
                'mes': month_key,
                'entradas_previstas': entradas,
                'saidas_previstas': saidas,
                'saldo_mes': saldo_mes,
                'saldo_acumulado': saldo_acumulado
            })
        
        # Identifica possíveis déficits (meses com saldo negativo)
        deficits = [p for p in projection_list if p['saldo_acumulado'] < 0]
        
        return {
            'projecao_mensal': projection_list,
            'saldo_final_projetado': saldo_acumulado,
            'deficits': deficits,
            'total_entradas_previstas': sum(p['entradas_previstas'] for p in projection_list),
            'total_saidas_previstas': sum(p['saidas_previstas'] for p in projection_list)
        }

    @staticmethod
    def export_to_excel(data: Dict[str, pd.DataFrame], filename: str) -> bytes:
        """
        Exporta dados para Excel
        """
        from io import BytesIO
        
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for sheet_name, df in data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        output.seek(0)
        return output.getvalue()
    
    @staticmethod
    def get_consolidated_financial_data(
        db: Session, 
        client_id: int, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, Any]:
        """
        Retorna dados financeiros consolidados para relatórios gerenciais
        Inclui disponíveis financeiros, obrigações, entradas/saídas detalhadas, etc.
        """
        # Dados do DRE
        dre_data = ReportService.get_dre_data(db, client_id, start_date, end_date)
        
        # Dados do DFC
        dfc_data = ReportService.get_dfc_data(db, client_id, start_date, end_date)
        
        # Disponíveis financeiros (saldo bancário)
        bank_balances = {}
        bank_transactions = db.query(Transaction).filter(
            Transaction.client_id == client_id,
            Transaction.document_type == 'extrato_bancario',
            Transaction.date <= end_date
        ).order_by(Transaction.date.desc(), Transaction.id.desc()).all()
        
        for trans in bank_transactions:
            bank_name = trans.bank_name or trans.account or 'Banco'
            if bank_name not in bank_balances:
                balance = db.query(func.sum(Transaction.value)).filter(
                    Transaction.client_id == client_id,
                    Transaction.account == trans.account,
                    Transaction.date <= end_date
                ).scalar() or 0
                bank_balances[bank_name] = {
                    'account': trans.account or '',
                    'balance': float(balance)
                }
        
        total_bank_balance = sum(b['balance'] for b in bank_balances.values())
        
        # Aplicações financeiras
        from models.financial_investment import FinancialInvestment
        investments = db.query(FinancialInvestment).filter(
            FinancialInvestment.client_id == client_id,
            FinancialInvestment.date <= end_date
        ).all()
        
        total_investments = sum(
            float(inv.applied_value or 0) - float(inv.redeemed_value or 0) 
            for inv in investments
        )
        
        # Obrigações financeiras
        accounts_payable_pending = db.query(
            func.sum(AccountPayable.value)
        ).filter(
            AccountPayable.client_id == client_id,
            AccountPayable.paid == False,
            AccountPayable.due_date <= end_date
        ).scalar() or 0
        
        accounts_payable_future = db.query(
            func.sum(AccountPayable.value)
        ).filter(
            AccountPayable.client_id == client_id,
            AccountPayable.paid == False,
            AccountPayable.due_date > end_date
        ).scalar() or 0
        
        # Contas a receber
        accounts_receivable_pending = db.query(
            func.sum(AccountReceivable.value)
        ).filter(
            AccountReceivable.client_id == client_id,
            AccountReceivable.received == False,
            AccountReceivable.due_date <= end_date
        ).scalar() or 0
        
        accounts_receivable_future = db.query(
            func.sum(AccountReceivable.value)
        ).filter(
            AccountReceivable.client_id == client_id,
            AccountReceivable.received == False,
            AccountReceivable.due_date > end_date
        ).scalar() or 0
        
        # Dados acumulados do ano
        year_start = date(start_date.year, 1, 1)
        dre_year = ReportService.get_dre_data(db, client_id, year_start, end_date)
        
        # Comparação com período anterior
        from datetime import timedelta
        period_days = (end_date - start_date).days
        previous_start = start_date - timedelta(days=period_days + 1)
        previous_end = start_date - timedelta(days=1)
        dre_previous = ReportService.get_dre_data(
            db, client_id, previous_start, previous_end
        )
        
        return {
            'dre': dre_data,
            'dfc': dfc_data,
            'disponiveis_financeiros': {
                'saldo_bancario': float(total_bank_balance),
                'bancos': {name: data['balance'] for name, data in bank_balances.items()},
                'aplicacoes': float(total_investments),
                'total': float(total_bank_balance + total_investments)
            },
            'obrigacoes': {
                'contas_pagar_pendentes': float(accounts_payable_pending),
                'contas_pagar_futuras': float(accounts_payable_future),
                'total_obrigacoes': float(accounts_payable_pending + accounts_payable_future)
            },
            'contas_receber': {
                'pendentes': float(accounts_receivable_pending),
                'futuras': float(accounts_receivable_future),
                'total': float(accounts_receivable_pending + accounts_receivable_future)
            },
            'dre_ano': dre_year,
            'dre_periodo_anterior': dre_previous
        }
    
    @staticmethod
    def get_financial_projections(
        db: Session, 
        client_id: int, 
        months_ahead: int = 3
    ) -> Dict[str, Any]:
        """
        Gera projeções financeiras futuras
        Retorna projeções de faturamento, caixa e contas a pagar/receber
        """
        from dateutil.relativedelta import relativedelta
        
        today = date.today()
        start_date = today + timedelta(days=1)
        end_date = today + relativedelta(months=months_ahead)
        
        # Usa método existente de projeção
        projection = ReportService.get_dfc_projection(db, client_id, start_date, end_date)
        
        # Organiza projeções por mês
        projection_by_month = {}
        for proj in projection.get('projecao_mensal', []):
            month_key = proj.get('mes', '')
            projection_by_month[month_key] = {
                'entradas_previstas': proj.get('entradas_previstas', 0),
                'saidas_previstas': proj.get('saidas_previstas', 0),
                'saldo_projetado': proj.get('saldo_mes', 0),
                'saldo_acumulado': proj.get('saldo_acumulado', 0)
            }
        
        return {
            'projection': projection_by_month,
            'deficits': projection.get('deficits', []),
            'total_entradas_previstas': projection.get('total_entradas_previstas', 0),
            'total_saidas_previstas': projection.get('total_saidas_previstas', 0),
            'saldo_final_projetado': projection.get('saldo_final_projetado', 0)
        }












