"""
Serviço para gerenciamento de contratos e eventos
"""
from sqlalchemy.orm import Session
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Any, Optional
from models.contract import Contract
from models.account import AccountReceivable
from models.group import Group, Subgroup


class ContractService:
    """
    Serviço para operações relacionadas a contratos/eventos
    """
    
    @staticmethod
    def generate_receivables(
        db: Session,
        contract_id: int,
        payment_plan: Dict[str, Any]
    ) -> List[AccountReceivable]:
        """
        Gera contas a receber automaticamente baseado no contrato e plano de pagamento
        
        Args:
            db: Sessão do banco de dados
            contract_id: ID do contrato
            payment_plan: Dicionário com:
                - num_installments: Número de parcelas (1 = à vista)
                - first_due_date: Data do primeiro vencimento
                - interval_days: Intervalo em dias entre parcelas (padrão: 30)
                - payment_method: Forma de pagamento (ex: "PIX", "Transferência")
        
        Returns:
            Lista de AccountReceivable criados
        """
        # Busca contrato
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        
        if not contract:
            raise ValueError(f"Contrato #{contract_id} não encontrado")
        
        # Calcula valor total
        total_value = contract.service_value + (contract.displacement_value or 0)
        
        # Extrai parâmetros do plano de pagamento
        num_installments = payment_plan.get('num_installments', 1)
        first_due_date = payment_plan.get('first_due_date', contract.event_date + timedelta(days=15))
        interval_days = payment_plan.get('interval_days', 30)
        payment_method = payment_plan.get('payment_method', 'Transferência')
        
        # Calcula valor por parcela
        value_per_installment = total_value / num_installments
        
        # Remove parcelas existentes deste contrato (se houver)
        db.query(AccountReceivable).filter(
            AccountReceivable.contract_id == contract_id
        ).delete()
        db.commit()
        
        # Cria parcelas
        receivables = []
        for i in range(num_installments):
            # Calcula vencimento
            due_date = first_due_date + timedelta(days=interval_days * i)
            
            receivable = AccountReceivable(
                client_id=contract.client_id,
                account_name=contract.contractor_name,
                due_date=due_date,
                value=value_per_installment,
                month_ref=due_date.strftime('%Y-%m'),
                received=False,
                receipt_date=None,
                event_date=contract.event_date,
                contract_value=total_value,
                payment_method=payment_method,
                monthly_installments=num_installments,
                total_expected_inflow=total_value,
                installment_number=i + 1,
                contract_id=contract_id,  # Vínculo com contrato
                group_id=contract.group_id,
                subgroup_id=contract.subgroup_id
            )
            
            receivables.append(receivable)
        
        # Salva no banco
        db.bulk_save_objects(receivables)
        db.commit()
        
        return receivables
    
    @staticmethod
    def get_contract_receivables(db: Session, contract_id: int) -> List[AccountReceivable]:
        """
        Retorna todas as contas a receber vinculadas a um contrato
        """
        return db.query(AccountReceivable).filter(
            AccountReceivable.contract_id == contract_id
        ).order_by(AccountReceivable.installment_number).all()
    
    @staticmethod
    def calculate_contract_status(db: Session, contract_id: int) -> Dict[str, Any]:
        """
        Calcula status financeiro de um contrato
        
        Returns:
            {
                'total_value': float,
                'total_received': float,
                'total_pending': float,
                'percent_received': float,
                'num_installments': int,
                'num_received': int,
                'num_pending': int,
                'overdue_count': int,
                'overdue_value': float
            }
        """
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        
        if not contract:
            return {}
        
        receivables = ContractService.get_contract_receivables(db, contract_id)
        
        if not receivables:
            return {
                'total_value': contract.service_value + (contract.displacement_value or 0),
                'total_received': 0,
                'total_pending': contract.service_value + (contract.displacement_value or 0),
                'percent_received': 0,
                'num_installments': 0,
                'num_received': 0,
                'num_pending': 0,
                'overdue_count': 0,
                'overdue_value': 0
            }
        
        total_value = sum(r.value for r in receivables)
        total_received = sum(r.value for r in receivables if r.received)
        total_pending = total_value - total_received
        percent_received = (total_received / total_value * 100) if total_value > 0 else 0
        
        num_received = sum(1 for r in receivables if r.received)
        num_pending = len(receivables) - num_received
        
        # Verifica parcelas vencidas
        today = date.today()
        overdue = [r for r in receivables if not r.received and r.due_date < today]
        overdue_count = len(overdue)
        overdue_value = sum(r.value for r in overdue)
        
        return {
            'total_value': total_value,
            'total_received': total_received,
            'total_pending': total_pending,
            'percent_received': percent_received,
            'num_installments': len(receivables),
            'num_received': num_received,
            'num_pending': num_pending,
            'overdue_count': overdue_count,
            'overdue_value': overdue_value
        }
    
    @staticmethod
    def get_events_calendar(
        db: Session,
        client_id: int,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Retorna eventos formatados para exibição em calendário
        """
        contracts = db.query(Contract).filter(
            Contract.client_id == client_id,
            Contract.event_date >= start_date,
            Contract.event_date <= end_date
        ).order_by(Contract.event_date).all()
        
        events = []
        for c in contracts:
            events.append({
                'id': c.id,
                'title': f"{c.event_type or 'Evento'} - {c.contractor_name}",
                'date': c.event_date,
                'value': c.service_value + (c.displacement_value or 0),
                'guests': c.guests_count,
                'location': c.event_location,
                'seller': c.seller_name,
                'status': c.status,
                'invoice': c.invoice_number
            })
        
        return events
    
    @staticmethod
    def get_seller_performance(
        db: Session,
        client_id: int,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Retorna performance de cada vendedor no período
        """
        from sqlalchemy import func
        
        # Agrupa contratos por vendedor
        results = db.query(
            Contract.seller_name,
            func.count(Contract.id).label('num_events'),
            func.sum(Contract.service_value + Contract.displacement_value).label('total_revenue'),
            func.avg(Contract.service_value + Contract.displacement_value).label('avg_ticket'),
            func.sum(Contract.guests_count).label('total_guests')
        ).filter(
            Contract.client_id == client_id,
            Contract.event_date >= start_date,
            Contract.event_date <= end_date,
            Contract.seller_name.isnot(None)
        ).group_by(Contract.seller_name).all()
        
        performance = []
        for r in results:
            performance.append({
                'seller': r.seller_name or 'Sem vendedor',
                'num_events': int(r.num_events or 0),
                'total_revenue': float(r.total_revenue or 0),
                'avg_ticket': float(r.avg_ticket or 0),
                'total_guests': int(r.total_guests or 0)
            })
        
        return sorted(performance, key=lambda x: x['total_revenue'], reverse=True)
    
    @staticmethod
    def get_pending_invoices(db: Session, client_id: int) -> List[Contract]:
        """
        Retorna contratos concluídos sem número de NF
        """
        return db.query(Contract).filter(
            Contract.client_id == client_id,
            Contract.status == 'concluido',
            Contract.invoice_number.is_(None)
        ).order_by(Contract.event_date.desc()).all()

