"""
Serviço de geração de relatórios e análises
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from models.transaction import Transaction, BankStatement
from models.account import AccountPayable, AccountReceivable
from models.contract import Contract
from datetime import datetime, date
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
        Inclui transações (que já incluem extratos convertidos), contratos, contas a pagar e contas a receber
        """
        # Receitas de transações (inclui extratos bancários convertidos automaticamente)
        receitas_trans = db.query(
            func.sum(Transaction.value)
        ).filter(
            Transaction.client_id == client_id,
            Transaction.type == 'entrada',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).scalar() or 0
        
        # Despesas de transações (inclui extratos bancários convertidos automaticamente)
        despesas_trans = db.query(
            func.sum(Transaction.value)
        ).filter(
            Transaction.client_id == client_id,
            Transaction.type == 'saida',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).scalar() or 0
        
        # Receitas de contratos concluídos
        receitas_contratos = db.query(
            func.sum(Contract.service_value + Contract.displacement_value)
        ).filter(
            Contract.client_id == client_id,
            Contract.status == 'concluido',
            Contract.event_date >= start_date,
            Contract.event_date <= end_date
        ).scalar() or 0
        
        # Despesas de contas a pagar pagas
        despesas_contas_pagar = db.query(
            func.sum(AccountPayable.value)
        ).filter(
            AccountPayable.client_id == client_id,
            AccountPayable.paid == True,
            AccountPayable.payment_date >= start_date,
            AccountPayable.payment_date <= end_date
        ).scalar() or 0
        
        # Receitas de contas a receber recebidas
        receitas_contas_receber = db.query(
            func.sum(AccountReceivable.value)
        ).filter(
            AccountReceivable.client_id == client_id,
            AccountReceivable.received == True,
            AccountReceivable.receipt_date >= start_date,
            AccountReceivable.receipt_date <= end_date
        ).scalar() or 0
        
        # Total
        receitas = receitas_trans + receitas_contratos + receitas_contas_receber
        despesas = despesas_trans + despesas_contas_pagar
        
        # Resultado
        resultado = receitas - despesas
        margem = (resultado / receitas * 100) if receitas > 0 else 0
        
        # Agregação por grupos e subgrupos (CLASSIFICAÇÃO PRINCIPAL)
        from models.group import Group, Subgroup
        
        # Receitas por grupo
        receitas_por_grupo = db.query(
            Group.name,
            func.sum(Transaction.value).label('total')
        ).join(Transaction, Transaction.group_id == Group.id).filter(
            Transaction.client_id == client_id,
            Transaction.type == 'entrada',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Group.name).all()
        
        # Despesas por grupo
        despesas_por_grupo = db.query(
            Group.name,
            func.sum(Transaction.value).label('total')
        ).join(Transaction, Transaction.group_id == Group.id).filter(
            Transaction.client_id == client_id,
            Transaction.type == 'saida',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Group.name).all()
        
        # Receitas por subgrupo
        receitas_por_subgrupo = db.query(
            Group.name.label('grupo'),
            Subgroup.name.label('subgrupo'),
            func.sum(Transaction.value).label('total')
        ).join(Transaction, Transaction.subgroup_id == Subgroup.id).join(
            Group, Subgroup.group_id == Group.id
        ).filter(
            Transaction.client_id == client_id,
            Transaction.type == 'entrada',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Group.name, Subgroup.name).all()
        
        # Despesas por subgrupo
        despesas_por_subgrupo = db.query(
            Group.name.label('grupo'),
            Subgroup.name.label('subgrupo'),
            func.sum(Transaction.value).label('total')
        ).join(Transaction, Transaction.subgroup_id == Subgroup.id).join(
            Group, Subgroup.group_id == Group.id
        ).filter(
            Transaction.client_id == client_id,
            Transaction.type == 'saida',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Group.name, Subgroup.name).all()
        
        # Agregação por grupos/subgrupos para contratos
        receitas_por_grupo_contratos = db.query(
            Group.name,
            func.sum(Contract.service_value + Contract.displacement_value).label('total')
        ).join(Contract, Contract.group_id == Group.id).filter(
            Contract.client_id == client_id,
            Contract.status == 'concluido',
            Contract.event_date >= start_date,
            Contract.event_date <= end_date
        ).group_by(Group.name).all()
        
        # Agregação por grupos/subgrupos para contas a pagar
        despesas_por_grupo_contas_pagar = db.query(
            Group.name,
            func.sum(AccountPayable.value).label('total')
        ).join(AccountPayable, AccountPayable.group_id == Group.id).filter(
            AccountPayable.client_id == client_id,
            AccountPayable.paid == True,
            AccountPayable.payment_date >= start_date,
            AccountPayable.payment_date <= end_date
        ).group_by(Group.name).all()
        
        # Agregação por grupos/subgrupos para contas a receber
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
        receitas_por_grupo_consolidado = {}
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
        despesas_por_grupo_consolidado = {}
        for d in despesas_por_grupo:
            grupo = d[0] or 'Sem grupo'
            despesas_por_grupo_consolidado[grupo] = despesas_por_grupo_consolidado.get(grupo, 0) + float(d[1])
        for d in despesas_por_grupo_contas_pagar:
            grupo = d[0] or 'Sem grupo'
            despesas_por_grupo_consolidado[grupo] = despesas_por_grupo_consolidado.get(grupo, 0) + float(d[1])
        
        # Receitas por categoria (FALLBACK - apenas para transações sem grupo/subgrupo)
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
            'receitas_por_grupo': [{'grupo': grupo, 'valor': valor} for grupo, valor in receitas_por_grupo_consolidado.items()],
            'despesas_por_grupo': [{'grupo': grupo, 'valor': valor} for grupo, valor in despesas_por_grupo_consolidado.items()],
            'receitas_por_subgrupo': [{'grupo': r[0] or 'Sem grupo', 'subgrupo': r[1] or 'Sem subgrupo', 'valor': float(r[2])} for r in receitas_por_subgrupo],
            'despesas_por_subgrupo': [{'grupo': d[0] or 'Sem grupo', 'subgrupo': d[1] or 'Sem subgrupo', 'valor': float(d[2])} for d in despesas_por_subgrupo],
            # Classificação SECUNDÁRIA: Categoria (apenas para transações sem grupo/subgrupo)
            'receitas_por_categoria': [{'categoria': r[0] or 'Sem categoria', 'valor': float(r[1])} for r in receitas_por_categoria],
            'despesas_por_categoria': [{'categoria': d[0] or 'Sem categoria', 'valor': float(d[1])} for d in despesas_por_categoria],
            'receitas_contratos': float(receitas_contratos),
            'receitas_contas_receber': float(receitas_contas_receber),
            'despesas_contas_pagar': float(despesas_contas_pagar)
        }

    @staticmethod
    def get_dfc_data(db: Session, client_id: int, start_date: date, end_date: date, 
                     group_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Gera dados para DFC (Demonstração do Fluxo de Caixa)
        Inclui transações (que já incluem extratos convertidos), contratos, contas a pagar e contas a receber
        
        Args:
            db: Sessão do banco de dados
            client_id: ID do cliente
            start_date: Data inicial
            end_date: Data final
            group_id: ID do grupo para filtrar (opcional). Se None, retorna todos os grupos
        """
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
        transactions = db.query(
            extract('year', Transaction.date).label('year'),
            extract('month', Transaction.date).label('month'),
            Transaction.type,
            func.sum(Transaction.value).label('total')
        ).filter(*transaction_filter).group_by('year', 'month', Transaction.type).all()
        
        # Fluxo por grupo (para análises detalhadas)
        from models.group import Group
        fluxo_por_grupo = {}
        
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
        
        # Fluxo por mês - Contratos concluídos
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
        
        # Fluxo por mês - Contas a pagar pagas
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
        
        # Fluxo por mês - Contas a receber recebidas
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
        
        return {
            'fluxo_mensal': fluxo_list,
            'saldo_final': saldo_acumulado,
            'fluxo_por_grupo': fluxo_por_grupo_list  # Agrupamento opcional por grupo
        }

    @staticmethod
    def get_seasonality_data(db: Session, client_id: int) -> Dict[str, Any]:
        """
        Analisa sazonalidade dos dados
        """
        # Receitas por mês (todos os anos)
        receitas_mensal = db.query(
            extract('year', Transaction.date).label('year'),
            extract('month', Transaction.date).label('month'),
            func.sum(Transaction.value).label('total')
        ).filter(
            Transaction.client_id == client_id,
            Transaction.type == 'entrada'
        ).group_by('year', 'month').all()
        
        # Organiza por ano e mês
        data_by_year = {}
        for rec in receitas_mensal:
            year = int(rec.year)
            month = int(rec.month)
            
            if year not in data_by_year:
                data_by_year[year] = {}
            
            data_by_year[year][month] = float(rec.total)
        
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
        
        return {
            'por_ano': data_by_year,
            'media_mensal': month_avg_list
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


