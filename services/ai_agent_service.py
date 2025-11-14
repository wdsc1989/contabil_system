"""
Serviço de Agente Conversacional de IA para consultas e relatórios
"""
import json
import re
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, or_

from services.ai_service import AIService
from services.report_service import ReportService
from models.transaction import Transaction
from models.contract import Contract
from models.account import AccountPayable, AccountReceivable
from models.group import Group, Subgroup
from utils.formatters import format_currency, format_date


class AIAgentService:
    """
    Serviço para processar perguntas em linguagem natural e gerar respostas com dados
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService(db)
        self.report_service = ReportService()
    
    def analyze_query(self, query: str, client_id: int) -> Dict[str, Any]:
        """
        Analisa uma pergunta em linguagem natural e identifica intenção e parâmetros
        
        Returns:
            Dict com intenção, tipo de dados, período, filtros, formato de saída
        """
        if not self.ai_service.is_available():
            return {
                'intent': 'error',
                'error': 'Serviço de IA não disponível. Configure a IA em Administração > Configuração de IA.'
            }
        
        # Prompt para análise da pergunta
        prompt = f"""Você é um assistente financeiro especializado em análise de dados contábeis.
Analise a seguinte pergunta do usuário e retorne APENAS um JSON válido (sem markdown, sem texto adicional) com:
{{
    "intent": "relatorio|consulta|analise|estatistica|comparacao",
    "data_type": "transacoes|contratos|contas|dre|dfc|sazonalidade|kpis|extratos|estoque",
    "period": {{
        "start": "YYYY-MM-DD ou null",
        "end": "YYYY-MM-DD ou null",
        "type": "mes|trimestre|ano|personalizado|hoje|ultimo_mes|ultimo_trimestre|ultimo_ano"
    }},
    "filters": {{
        "group": "nome_do_grupo ou null",
        "subgroup": "nome_do_subgrupo ou null",
        "category": "categoria ou null",
        "type": "entrada|saida|ambos ou null"
    }},
    "output_format": "tabela|grafico|resumo|completo",
    "comparison": {{
        "enabled": true ou false,
        "period": "periodo_anterior|ano_anterior"
    }}
}}

Pergunta: {query}

Retorne APENAS o JSON, sem explicações ou markdown."""

        try:
            client, error = self.ai_service._get_client()
            if error:
                return {'intent': 'error', 'error': error}
            
            config = self.ai_service.config
            provider = config['provider']
            model = config.get('model', '')
            
            # Chama a IA
            if provider == 'openai':
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                result_text = response.choices[0].message.content
            elif provider == 'gemini':
                response = client.generate_content(prompt)
                result_text = response.text
            elif provider == 'groq':
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                result_text = response.choices[0].message.content
            elif provider == 'ollama':
                response = client.chat(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    options={"temperature": 0.3}
                )
                result_text = response['message']['content']
            else:
                return {'intent': 'error', 'error': f'Provedor {provider} não suportado'}
            
            # Parse do JSON
            result_text = result_text.strip()
            # Remove markdown code blocks se houver
            if result_text.startswith('```'):
                result_text = re.sub(r'^```(?:json)?\s*', '', result_text, flags=re.MULTILINE)
                result_text = re.sub(r'```\s*$', '', result_text, flags=re.MULTILINE)
            
            analysis = json.loads(result_text)
            
            # Processa período
            analysis['period'] = self._process_period(analysis.get('period', {}))
            
            return analysis
            
        except json.JSONDecodeError as e:
            return {
                'intent': 'error',
                'error': f'Erro ao parsear resposta da IA: {str(e)}'
            }
        except Exception as e:
            return {
                'intent': 'error',
                'error': f'Erro ao analisar pergunta: {str(e)}'
            }
    
    def _process_period(self, period_info: Dict) -> Dict[str, Any]:
        """
        Processa informações de período e retorna datas start/end
        """
        period_type = period_info.get('type', 'personalizado')
        start_str = period_info.get('start')
        end_str = period_info.get('end')
        
        today = date.today()
        
        # Se já tem datas específicas, usa elas
        if start_str and end_str and start_str != 'null' and end_str != 'null':
            try:
                return {
                    'start': datetime.strptime(start_str, '%Y-%m-%d').date(),
                    'end': datetime.strptime(end_str, '%Y-%m-%d').date(),
                    'type': 'personalizado'
                }
            except:
                pass
        
        # Processa tipos de período
        if period_type == 'hoje':
            return {
                'start': today,
                'end': today,
                'type': 'hoje'
            }
        elif period_type == 'ultimo_mes' or period_type == 'mes':
            start = today - relativedelta(months=1)
            return {
                'start': start.replace(day=1),
                'end': today,
                'type': 'ultimo_mes'
            }
        elif period_type == 'ultimo_trimestre' or period_type == 'trimestre':
            start = today - relativedelta(months=3)
            return {
                'start': start.replace(day=1),
                'end': today,
                'type': 'ultimo_trimestre'
            }
        elif period_type == 'ultimo_ano' or period_type == 'ano':
            start = today - relativedelta(years=1)
            return {
                'start': start.replace(day=1, month=1),
                'end': today,
                'type': 'ultimo_ano'
            }
        else:
            # Default: último mês
            start = today - relativedelta(months=1)
            return {
                'start': start.replace(day=1),
                'end': today,
                'type': 'ultimo_mes'
            }
    
    def execute_query(self, db: Session, client_id: int, query_analysis: Dict) -> Dict[str, Any]:
        """
        Executa consulta ao banco de dados baseada na análise da pergunta
        """
        intent = query_analysis.get('intent')
        data_type = query_analysis.get('data_type')
        period = query_analysis.get('period', {})
        filters = query_analysis.get('filters', {})
        
        start_date = period.get('start', date.today() - relativedelta(months=1))
        end_date = period.get('end', date.today())
        
        try:
            # Relatórios completos
            if intent == 'relatorio':
                if data_type == 'dre':
                    return {
                        'type': 'dre',
                        'data': self.report_service.get_dre_data(db, client_id, start_date, end_date)
                    }
                elif data_type == 'dfc':
                    return {
                        'type': 'dfc',
                        'data': self.report_service.get_dfc_data(db, client_id, start_date, end_date)
                    }
                elif data_type == 'sazonalidade':
                    return {
                        'type': 'sazonalidade',
                        'data': self.report_service.get_seasonality_data(db, client_id)
                    }
                elif data_type == 'kpis':
                    return {
                        'type': 'kpis',
                        'data': self.report_service.get_kpis(db, client_id, start_date, end_date)
                    }
            
            # Consultas de dados
            if data_type == 'transacoes':
                return self._query_transactions(db, client_id, start_date, end_date, filters)
            elif data_type == 'contratos':
                return self._query_contracts(db, client_id, start_date, end_date, filters)
            elif data_type == 'contas':
                return self._query_accounts(db, client_id, start_date, end_date, filters)
            elif data_type == 'extratos':
                return self._query_bank_statements(db, client_id, start_date, end_date, filters)
            elif data_type == 'kpis':
                return {
                    'type': 'kpis',
                    'data': self.report_service.get_kpis(db, client_id, start_date, end_date)
                }
            
            # Análises e comparações
            if intent == 'analise' or intent == 'comparacao':
                if data_type == 'dre':
                    return {
                        'type': 'dre',
                        'data': self.report_service.get_dre_data(db, client_id, start_date, end_date),
                        'comparison': query_analysis.get('comparison', {})
                    }
                elif data_type == 'dfc':
                    return {
                        'type': 'dfc',
                        'data': self.report_service.get_dfc_data(db, client_id, start_date, end_date),
                        'comparison': query_analysis.get('comparison', {})
                    }
            
            # Default: consulta de transações
            return self._query_transactions(db, client_id, start_date, end_date, filters)
            
        except Exception as e:
            return {
                'type': 'error',
                'error': f'Erro ao executar consulta: {str(e)}'
            }
    
    def _query_transactions(self, db: Session, client_id: int, start_date: date, 
                           end_date: date, filters: Dict) -> Dict[str, Any]:
        """Consulta transações com filtros"""
        query = db.query(Transaction).filter(
            Transaction.client_id == client_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
        
        # Filtro por tipo
        if filters.get('type') == 'entrada':
            query = query.filter(Transaction.type == 'entrada')
        elif filters.get('type') == 'saida':
            query = query.filter(Transaction.type == 'saida')
        
        # Filtro por grupo
        if filters.get('group'):
            group = db.query(Group).filter(
                Group.client_id == client_id,
                Group.name.ilike(f"%{filters['group']}%")
            ).first()
            if group:
                query = query.filter(Transaction.group_id == group.id)
        
        # Filtro por subgrupo
        if filters.get('subgroup'):
            subgroup = db.query(Subgroup).filter(
                Subgroup.client_id == client_id,
                Subgroup.name.ilike(f"%{filters['subgroup']}%")
            ).first()
            if subgroup:
                query = query.filter(Transaction.subgroup_id == subgroup.id)
        
        transactions = query.order_by(Transaction.date.desc()).all()
        
        # Agregações
        total_entradas = sum(t.value for t in transactions if t.type == 'entrada')
        total_saidas = sum(t.value for t in transactions if t.type == 'saida')
        
        return {
            'type': 'transacoes',
            'data': {
                'transactions': [
                    {
                        'date': t.date.isoformat(),
                        'description': t.description,
                        'value': float(t.value),
                        'type': t.type,
                        'category': t.category,
                        'group': t.group.name if t.group else None,
                        'subgroup': t.subgroup.name if t.subgroup else None
                    }
                    for t in transactions
                ],
                'total_entradas': float(total_entradas),
                'total_saidas': float(total_saidas),
                'saldo': float(total_entradas - total_saidas),
                'count': len(transactions)
            }
        }
    
    def _query_contracts(self, db: Session, client_id: int, start_date: date,
                        end_date: date, filters: Dict) -> Dict[str, Any]:
        """Consulta contratos"""
        query = db.query(Contract).filter(
            Contract.client_id == client_id,
            Contract.event_date >= start_date,
            Contract.event_date <= end_date
        )
        
        if filters.get('status'):
            query = query.filter(Contract.status == filters['status'])
        
        contracts = query.order_by(Contract.event_date.desc()).all()
        
        total_value = sum(c.service_value + (c.displacement_value or 0) for c in contracts)
        
        return {
            'type': 'contratos',
            'data': {
                'contracts': [
                    {
                        'event_date': c.event_date.isoformat(),
                        'contractor_name': c.contractor_name,
                        'service_value': float(c.service_value),
                        'displacement_value': float(c.displacement_value or 0),
                        'total_value': float(c.service_value + (c.displacement_value or 0)),
                        'status': c.status,
                        'group': c.group.name if c.group else None
                    }
                    for c in contracts
                ],
                'total_value': float(total_value),
                'count': len(contracts)
            }
        }
    
    def _query_accounts(self, db: Session, client_id: int, start_date: date,
                       end_date: date, filters: Dict) -> Dict[str, Any]:
        """Consulta contas a pagar e receber"""
        accounts_payable = db.query(AccountPayable).filter(
            AccountPayable.client_id == client_id,
            AccountPayable.due_date >= start_date,
            AccountPayable.due_date <= end_date
        ).all()
        
        accounts_receivable = db.query(AccountReceivable).filter(
            AccountReceivable.client_id == client_id,
            AccountReceivable.due_date >= start_date,
            AccountReceivable.due_date <= end_date
        ).all()
        
        total_payable = sum(a.value for a in accounts_payable)
        total_receivable = sum(a.value for a in accounts_receivable)
        pending_payable = sum(a.value for a in accounts_payable if not a.paid)
        pending_receivable = sum(a.value for a in accounts_receivable if not a.received)
        
        return {
            'type': 'contas',
            'data': {
                'accounts_payable': [
                    {
                        'account_name': a.account_name,
                        'due_date': a.due_date.isoformat(),
                        'value': float(a.value),
                        'paid': a.paid,
                        'group': a.group.name if a.group else None
                    }
                    for a in accounts_payable
                ],
                'accounts_receivable': [
                    {
                        'account_name': a.account_name,
                        'due_date': a.due_date.isoformat(),
                        'value': float(a.value),
                        'received': a.received,
                        'group': a.group.name if a.group else None
                    }
                    for a in accounts_receivable
                ],
                'total_payable': float(total_payable),
                'total_receivable': float(total_receivable),
                'pending_payable': float(pending_payable),
                'pending_receivable': float(pending_receivable)
            }
        }
    
    def _query_bank_statements(self, db: Session, client_id: int, start_date: date,
                              end_date: date, filters: Dict) -> Dict[str, Any]:
        """Consulta extratos bancários (via transações)"""
        query = db.query(Transaction).filter(
            Transaction.client_id == client_id,
            Transaction.document_type == 'extrato_bancario',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
        
        transactions = query.order_by(Transaction.date.desc()).all()
        
        total_entradas = sum(t.value for t in transactions if t.type == 'entrada')
        total_saidas = sum(t.value for t in transactions if t.type == 'saida')
        
        return {
            'type': 'extratos',
            'data': {
                'statements': [
                    {
                        'date': t.date.isoformat(),
                        'description': t.description,
                        'value': float(t.value),
                        'type': t.type,
                        'bank_name': t.bank_name
                    }
                    for t in transactions
                ],
                'total_entradas': float(total_entradas),
                'total_saidas': float(total_saidas),
                'saldo': float(total_entradas - total_saidas),
                'count': len(transactions)
            }
        }
    
    def format_response(self, query_result: Dict, query_analysis: Dict, 
                       original_query: str) -> str:
        """
        Formata resposta em markdown para exibição
        """
        if query_result.get('type') == 'error':
            return f"❌ **Erro:** {query_result.get('error', 'Erro desconhecido')}"
        
        # Usa IA para gerar resposta formatada
        if not self.ai_service.is_available():
            return self._format_response_simple(query_result, query_analysis)
        
        data = query_result.get('data', {})
        query_type = query_result.get('type', '')
        
        prompt = f"""Com base nos dados fornecidos, gere uma resposta clara e objetiva em português.
Inclua:
- Resumo executivo (2-3 frases)
- Principais insights e descobertas
- Dados numéricos formatados (valores em R$)
- Recomendações (se aplicável)
- Formate usando markdown

Pergunta original: {original_query}
Tipo de consulta: {query_type}
Dados: {json.dumps(data, default=str, ensure_ascii=False)}

Retorne a resposta formatada em markdown."""

        try:
            client, error = self.ai_service._get_client()
            if error:
                return self._format_response_simple(query_result, query_analysis)
            
            config = self.ai_service.config
            provider = config['provider']
            model = config.get('model', '')
            
            if provider == 'openai':
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                return response.choices[0].message.content
            elif provider == 'gemini':
                response = client.generate_content(prompt)
                return response.text
            elif provider == 'groq':
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                return response.choices[0].message.content
            elif provider == 'ollama':
                response = client.chat(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    options={"temperature": 0.7}
                )
                return response['message']['content']
            else:
                return self._format_response_simple(query_result, query_analysis)
                
        except Exception as e:
            return self._format_response_simple(query_result, query_analysis)
    
    def _format_response_simple(self, query_result: Dict, query_analysis: Dict) -> str:
        """Formata resposta simples sem IA"""
        query_type = query_result.get('type', '')
        data = query_result.get('data', {})
        
        if query_type == 'transacoes':
            return f"""## 📊 Transações

**Total de Entradas:** {format_currency(data.get('total_entradas', 0))}
**Total de Saídas:** {format_currency(data.get('total_saidas', 0))}
**Saldo:** {format_currency(data.get('saldo', 0))}
**Quantidade:** {data.get('count', 0)} transações"""
        
        elif query_type == 'dre':
            return f"""## 📊 DRE - Demonstração do Resultado

**Receitas:** {format_currency(data.get('receitas', 0))}
**Despesas:** {format_currency(data.get('despesas', 0))}
**Resultado:** {format_currency(data.get('resultado', 0))}
**Margem:** {data.get('margem', 0):.2f}%"""
        
        elif query_type == 'dfc':
            return f"""## 💵 DFC - Fluxo de Caixa

**Total Entradas:** {format_currency(data.get('total_entradas', 0))}
**Total Saídas:** {format_currency(data.get('total_saidas', 0))}
**Saldo Final:** {format_currency(data.get('saldo_final', 0))}"""
        
        elif query_type == 'kpis':
            return f"""## 📈 KPIs Financeiros

**Receitas:** {format_currency(data.get('receitas', 0))}
**Despesas:** {format_currency(data.get('despesas', 0))}
**Margem:** {data.get('margem', 0):.2f}%"""
        
        else:
            return f"## Resultado\n\nDados disponíveis: {query_type}"

