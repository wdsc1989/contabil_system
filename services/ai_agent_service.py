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
    
    def pre_analyze_client(self, client_id: int) -> Dict[str, Any]:
        """
        Faz uma pré-análise do cliente para gerar sugestões proativas
        Retorna KPIs, alertas e oportunidades
        """
        from datetime import date, timedelta
        from dateutil.relativedelta import relativedelta
        
        today = date.today()
        last_month_start = (today - relativedelta(months=1)).replace(day=1)
        last_month_end = today
        
        # Busca KPIs do último mês
        kpis = self.report_service.get_kpis(self.db, client_id, last_month_start, last_month_end)
        
        # Busca dados do DRE
        dre = self.report_service.get_dre_data(self.db, client_id, last_month_start, last_month_end)
        
        # Identifica alertas e oportunidades
        alerts = []
        opportunities = []
        suggestions = []
        
        # Alertas
        if kpis.get('contas_pagar', 0) > 0:
            alerts.append({
                'type': 'warning',
                'message': f"⚠️ Há {format_currency(kpis.get('contas_pagar', 0))} em contas a pagar pendentes"
            })
        
        if kpis.get('margem', 0) < 10:
            alerts.append({
                'type': 'critical',
                'message': f"🔴 Margem de lucro baixa: {kpis.get('margem', 0):.2f}%"
            })
        
        if dre.get('resultado', 0) < 0:
            alerts.append({
                'type': 'critical',
                'message': f"🔴 Resultado negativo no período: {format_currency(abs(dre.get('resultado', 0)))}"
            })
        
        # Oportunidades
        if kpis.get('contas_receber', 0) > 0:
            opportunities.append({
                'type': 'info',
                'message': f"💰 {format_currency(kpis.get('contas_receber', 0))} em contas a receber podem melhorar o fluxo de caixa"
            })
        
        if kpis.get('contratos_ativos', 0) > 0:
            opportunities.append({
                'type': 'success',
                'message': f"📝 {kpis.get('contratos_ativos', 0)} contratos ativos com valor total de {format_currency(kpis.get('valor_contratos', 0))}"
            })
        
        # Sugestões baseadas nos dados
        if dre.get('receitas', 0) > 0:
            suggestions.append("Analisar receitas do último mês")
            suggestions.append("Verificar distribuição de receitas por grupo")
        
        if dre.get('despesas', 0) > 0:
            suggestions.append("Analisar despesas e identificar oportunidades de redução")
            suggestions.append("Comparar despesas com período anterior")
        
        if kpis.get('margem', 0) > 0:
            suggestions.append("Analisar margem de lucro e tendências")
        
        return {
            'kpis': kpis,
            'dre': dre,
            'alerts': alerts,
            'opportunities': opportunities,
            'suggestions': suggestions
        }
    
    def generate_greeting_with_suggestions(self, client_id: int, client_name: str) -> str:
        """
        Gera saudação proativa com sugestões baseadas na pré-análise do cliente
        """
        if not self.ai_service.is_available():
            return f"Olá! Sou seu assistente contábil. Como posso ajudá-lo hoje com **{client_name}**?"
        
        # Faz pré-análise
        pre_analysis = self.pre_analyze_client(client_id)
        
        # Prepara contexto para a IA
        context = f"""
Cliente: {client_name}
KPIs do último mês:
- Receitas: {format_currency(pre_analysis['kpis'].get('receitas', 0))}
- Despesas: {format_currency(pre_analysis['kpis'].get('despesas', 0))}
- Resultado: {format_currency(pre_analysis['kpis'].get('resultado', 0))}
- Margem: {pre_analysis['kpis'].get('margem', 0):.2f}%
- Contas a pagar pendentes: {format_currency(pre_analysis['kpis'].get('contas_pagar', 0))}
- Contas a receber pendentes: {format_currency(pre_analysis['kpis'].get('contas_receber', 0))}

Alertas: {len(pre_analysis['alerts'])}
Oportunidades: {len(pre_analysis['opportunities'])}
Sugestões: {', '.join(pre_analysis['suggestions'][:3])}
"""
        
        prompt = f"""Você é um administrador contábil profissional e experiente, especializado em análise financeira e contábil.
Seu papel é ser proativo, oferecendo insights valiosos e sugestões baseadas nos dados do cliente.

Contexto do cliente {client_name}:
{context}

Gere uma saudação profissional e amigável em português que:
1. Se apresente como administrador contábil do sistema
2. Pergunte o que vamos analisar hoje
3. Apresente 3-4 sugestões de análises baseadas nos dados acima
4. Seja conciso mas informativo
5. Use tom profissional mas acessível

Formate a resposta em markdown, destacando as sugestões de forma clara."""

        try:
            client, error = self.ai_service._get_client()
            if error:
                # Fallback simples
                suggestions_text = "\n".join([f"- {s}" for s in pre_analysis['suggestions'][:3]])
                return f"""Olá! 👋 Sou seu **administrador contábil** do sistema.

O que vamos analisar hoje sobre **{client_name}**?

Com base nos dados do último mês, sugiro que analisemos:

{suggestions_text}

Como prefere prosseguir?"""
            
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
                # Fallback
                suggestions_text = "\n".join([f"- {s}" for s in pre_analysis['suggestions'][:3]])
                return f"Olá! Sou seu administrador contábil. O que vamos analisar hoje?\n\nSugestões:\n{suggestions_text}"
                
        except Exception as e:
            # Fallback em caso de erro
            suggestions_text = "\n".join([f"- {s}" for s in pre_analysis['suggestions'][:3]])
            return f"""Olá! 👋 Sou seu **administrador contábil** do sistema.

O que vamos analisar hoje sobre **{client_name}**?

Sugestões de análises:
{suggestions_text}"""
    
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
        prompt = f"""Você é um administrador contábil profissional e experiente, especializado em análise financeira e contábil.
Analise a seguinte pergunta do usuário e retorne APENAS um JSON válido (sem markdown, sem texto adicional) com:
{{
    "intent": "relatorio_gerencial|relatorio|consulta|analise|estatistica|comparacao",
    "data_type": "transacoes|contratos|contas|dre|dfc|sazonalidade|kpis|extratos|estoque|relatorio_gerencial",
    "period": {{
        "start": "YYYY-MM-DD ou null",
        "end": "YYYY-MM-DD ou null",
        "type": "mes|trimestre|ano|personalizado|hoje|ultimo_mes|ultimo_trimestre|ultimo_ano",
        "month": "nome_do_mes ou null (ex: outubro, novembro)",
        "year": "YYYY ou null"
    }},
    "filters": {{
        "group": "nome_do_grupo ou null",
        "subgroup": "nome_do_subgrupo ou null",
        "category": "categoria ou null",
        "type": "entrada|saida|ambos ou null"
    }},
    "output_format": "tabela|grafico|resumo|completo|relatorio_gerencial",
    "comparison": {{
        "enabled": true ou false,
        "period": "periodo_anterior|ano_anterior"
    }}
}}

IMPORTANTE: Se o usuário solicitar "gerar relatório gerencial", "relatório de [mês/ano]", "apuração financeira", "relatório gerencial de [período]", 
ou qualquer variação similar, defina:
- "intent": "relatorio_gerencial"
- "data_type": "relatorio_gerencial"
- "output_format": "relatorio_gerencial"
- Extraia o mês e ano do período solicitado no campo "period"

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
        month_name = period_info.get('month')
        year_str = period_info.get('year')
        
        today = date.today()
        
        # Se tem mês e ano específicos (para relatório gerencial)
        if month_name and year_str:
            try:
                month_map = {
                    'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
                    'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
                    'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
                }
                month_num = month_map.get(month_name.lower(), today.month)
                year = int(year_str) if year_str else today.year
                
                # Primeiro e último dia do mês
                from calendar import monthrange
                start = date(year, month_num, 1)
                end = date(year, month_num, monthrange(year, month_num)[1])
                
                return {
                    'start': start,
                    'end': end,
                    'type': 'mes_especifico',
                    'month': month_name,
                    'year': year
                }
            except:
                pass
        
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
            # Relatório gerencial
            if intent == 'relatorio_gerencial' or data_type == 'relatorio_gerencial':
                from services.financial_report_agent_service import FinancialReportAgentService
                from models.client import Client
                
                client = db.query(Client).filter(Client.id == client_id).first()
                client_name = client.name if client else 'Cliente'
                
                report_agent = FinancialReportAgentService(db)
                result = report_agent.generate_management_report(
                    client_id, start_date, end_date, client_name
                )
                
                if result.get('success'):
                    return {
                        'type': 'relatorio_gerencial',
                        'data': result.get('report', ''),
                        'period': result.get('period', {}),
                        'client_name': result.get('client_name', ''),
                        'financial_data': result.get('financial_data', {}),
                        'kpis': result.get('kpis', {}),
                        'visualizations': result.get('visualizations', [])
                    }
                else:
                    return {
                        'type': 'error',
                        'error': result.get('error', 'Erro ao gerar relatório gerencial')
                    }
            
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
        
        prompt = f"""Você é um administrador contábil profissional. Com base nos dados fornecidos, gere uma resposta clara, objetiva e profissional em português.
Inclua:
- Resumo executivo (2-3 frases)
- Principais insights e descobertas
- Dados numéricos formatados (valores em R$)
- Recomendações profissionais (se aplicável)
- Use tom de administrador contábil experiente
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

