"""
Serviço de geração de relatórios e análises
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from models.transaction import Transaction
from models.account import AccountPayable, AccountReceivable
from models.contract import Contract
from datetime import datetime, date
from typing import Dict, List, Any
import pandas as pd


class ReportService:
    """
    Serviço para gerar relatórios e análises financeiras
    """

    @staticmethod
    def get_dre_data(db: Session, client_id: int, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Gera dados para DRE (Demonstração do Resultado do Exercício)
        """
        # Receitas
        receitas = db.query(
            func.sum(Transaction.value)
        ).filter(
            Transaction.client_id == client_id,
            Transaction.type == 'entrada',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).scalar() or 0
        
        # Despesas
        despesas = db.query(
            func.sum(Transaction.value)
        ).filter(
            Transaction.client_id == client_id,
            Transaction.type == 'saida',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).scalar() or 0
        
        # Resultado
        resultado = receitas - despesas
        margem = (resultado / receitas * 100) if receitas > 0 else 0
        
        # Receitas por categoria
        receitas_por_categoria = db.query(
            Transaction.category,
            func.sum(Transaction.value).label('total')
        ).filter(
            Transaction.client_id == client_id,
            Transaction.type == 'entrada',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Transaction.category).all()
        
        # Despesas por categoria
        despesas_por_categoria = db.query(
            Transaction.category,
            func.sum(Transaction.value).label('total')
        ).filter(
            Transaction.client_id == client_id,
            Transaction.type == 'saida',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Transaction.category).all()
        
        return {
            'receitas': float(receitas),
            'despesas': float(despesas),
            'resultado': float(resultado),
            'margem': float(margem),
            'receitas_por_categoria': [{'categoria': r[0] or 'Sem categoria', 'valor': float(r[1])} for r in receitas_por_categoria],
            'despesas_por_categoria': [{'categoria': d[0] or 'Sem categoria', 'valor': float(d[1])} for d in despesas_por_categoria]
        }

    @staticmethod
    def get_dfc_data(db: Session, client_id: int, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Gera dados para DFC (Demonstração do Fluxo de Caixa)
        """
        # Fluxo por mês
        transactions = db.query(
            extract('year', Transaction.date).label('year'),
            extract('month', Transaction.date).label('month'),
            Transaction.type,
            func.sum(Transaction.value).label('total')
        ).filter(
            Transaction.client_id == client_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by('year', 'month', Transaction.type).all()
        
        # Organiza por mês
        fluxo_mensal = {}
        for trans in transactions:
            month_key = f"{int(trans.year)}-{int(trans.month):02d}"
            if month_key not in fluxo_mensal:
                fluxo_mensal[month_key] = {'entradas': 0, 'saidas': 0}
            
            if trans.type == 'entrada':
                fluxo_mensal[month_key]['entradas'] = float(trans.total)
            else:
                fluxo_mensal[month_key]['saidas'] = float(trans.total)
        
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
        
        return {
            'fluxo_mensal': fluxo_list,
            'saldo_final': saldo_acumulado
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


