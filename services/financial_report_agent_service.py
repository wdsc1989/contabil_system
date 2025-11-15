"""
Serviço de Agente Analítico Financeiro para Relatórios Gerenciais
Gera relatórios gerenciais completos seguindo layout padronizado
"""
import json
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from services.ai_service import AIService
from services.report_service import ReportService
from models.transaction import Transaction
from models.contract import Contract
from models.account import AccountPayable, AccountReceivable
from models.financial_investment import FinancialInvestment
from models.group import Group, Subgroup
from utils.formatters import format_currency, format_date


class FinancialReportAgentService:
    """
    Serviço especializado em gerar relatórios gerenciais completos
    seguindo layout padronizado do modelo "APURAÇÃO FINANCEIRA"
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService(db)
        self.report_service = ReportService()
    
    def generate_management_report(
        self, 
        client_id: int, 
        period_start: date, 
        period_end: date, 
        client_name: str
    ) -> Dict[str, Any]:
        """
        Gera relatório gerencial completo para o período solicitado
        
        Args:
            client_id: ID do cliente
            period_start: Data inicial do período
            period_end: Data final do período
            client_name: Nome do cliente
            
        Returns:
            Dict com relatório formatado e metadados
        """
        if not self.ai_service.is_available():
            return {
                'success': False,
                'error': 'Serviço de IA não disponível. Configure a IA em Administração > Configuração de IA.'
            }
        
        try:
            # Coleta dados financeiros consolidados
            financial_data = self._collect_financial_data(client_id, period_start, period_end)
            
            # Calcula KPIs
            kpis = self._calculate_kpis(financial_data)
            
            # Cria prompt para a IA
            prompt = self._create_report_prompt(
                financial_data, 
                kpis,
                period_start, 
                period_end, 
                client_name
            )
            
            # Chama IA para gerar relatório
            response, error = self.ai_service._call_ai(prompt)
            
            if error:
                return {
                    'success': False,
                    'error': f'Erro ao gerar relatório: {error}'
                }
            
            if not response:
                return {
                    'success': False,
                    'error': 'Resposta vazia da IA'
                }
            
            # Processa resposta
            report_content = self._process_ai_response(response)
            
            # Cria visualizações (gráficos)
            visualizations = self._create_visualizations(financial_data, kpis, period_start, period_end)
            
            return {
                'success': True,
                'report': report_content,
                'period': {
                    'start': period_start.isoformat(),
                    'end': period_end.isoformat()
                },
                'client_name': client_name,
                'generated_at': datetime.now().isoformat(),
                'financial_data': financial_data,
                'kpis': kpis,
                'visualizations': visualizations
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro ao gerar relatório: {str(e)}'
            }
    
    def _collect_financial_data(
        self, 
        client_id: int, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, Any]:
        """
        Coleta todos os dados financeiros necessários para o relatório
        """
        # Dados do DRE
        dre_data = self.report_service.get_dre_data(self.db, client_id, start_date, end_date)
        
        # Dados do DFC
        dfc_data = self.report_service.get_dfc_data(self.db, client_id, start_date, end_date)
        
        # Disponíveis financeiros (saldo bancário)
        # Busca última transação de cada conta bancária para obter saldo
        bank_balances = {}
        bank_transactions = self.db.query(Transaction).filter(
            Transaction.client_id == client_id,
            Transaction.document_type == 'extrato_bancario',
            Transaction.date <= end_date
        ).order_by(Transaction.date.desc(), Transaction.id.desc()).all()
        
        for trans in bank_transactions:
            bank_name = trans.bank_name or trans.account or 'Banco'
            if bank_name not in bank_balances:
                # Calcula saldo aproximado somando valores até a data
                balance = self.db.query(func.sum(Transaction.value)).filter(
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
        investments = self.db.query(FinancialInvestment).filter(
            FinancialInvestment.client_id == client_id,
            FinancialInvestment.date <= end_date
        ).all()
        
        total_investments = sum(
            float(inv.applied_value or 0) - float(inv.redeemed_value or 0) 
            for inv in investments
        )
        
        # Obrigações financeiras
        # Contas a pagar pendentes
        accounts_payable_pending = self.db.query(
            func.sum(AccountPayable.value)
        ).filter(
            AccountPayable.client_id == client_id,
            AccountPayable.paid == False,
            AccountPayable.due_date <= end_date
        ).scalar() or 0
        
        # Contas a pagar futuras (após o período)
        accounts_payable_future = self.db.query(
            func.sum(AccountPayable.value)
        ).filter(
            AccountPayable.client_id == client_id,
            AccountPayable.paid == False,
            AccountPayable.due_date > end_date
        ).scalar() or 0
        
        # Contas a receber pendentes
        accounts_receivable_pending = self.db.query(
            func.sum(AccountReceivable.value)
        ).filter(
            AccountReceivable.client_id == client_id,
            AccountReceivable.received == False,
            AccountReceivable.due_date <= end_date
        ).scalar() or 0
        
        # Contas a receber futuras
        accounts_receivable_future = self.db.query(
            func.sum(AccountReceivable.value)
        ).filter(
            AccountReceivable.client_id == client_id,
            AccountReceivable.received == False,
            AccountReceivable.due_date > end_date
        ).scalar() or 0
        
        # Entradas detalhadas
        entries_by_group = self.db.query(
            Group.name.label('grupo'),
            Subgroup.name.label('subgrupo'),
            func.sum(Transaction.value).label('total')
        ).join(Transaction, Transaction.group_id == Group.id).join(
            Subgroup, Transaction.subgroup_id == Subgroup.id
        ).filter(
            Transaction.client_id == client_id,
            Transaction.type == 'entrada',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Group.name, Subgroup.name).all()
        
        # Saídas detalhadas
        exits_by_group = self.db.query(
            Group.name.label('grupo'),
            Subgroup.name.label('subgrupo'),
            func.sum(Transaction.value).label('total')
        ).join(Transaction, Transaction.group_id == Group.id).join(
            Subgroup, Transaction.subgroup_id == Subgroup.id
        ).filter(
            Transaction.client_id == client_id,
            Transaction.type == 'saida',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Group.name, Subgroup.name).all()
        
        # Dados acumulados do ano
        year_start = date(start_date.year, 1, 1)
        dre_year = self.report_service.get_dre_data(self.db, client_id, year_start, end_date)
        
        # Comparação com período anterior
        period_days = (end_date - start_date).days
        previous_start = start_date - timedelta(days=period_days + 1)
        previous_end = start_date - timedelta(days=1)
        dre_previous = self.report_service.get_dre_data(
            self.db, client_id, previous_start, previous_end
        )
        
        # Projeções futuras (próximos 3 meses)
        projection_start = end_date + timedelta(days=1)
        projection_end = end_date + relativedelta(months=3)
        dfc_projection = self.report_service.get_dfc_projection(
            self.db, client_id, projection_start, projection_end
        )
        
        # Contratos em andamento
        active_contracts = self.db.query(Contract).filter(
            Contract.client_id == client_id,
            Contract.status.in_(['pendente', 'em_andamento'])
        ).all()
        
        total_contracts_value = sum(
            float(c.service_value or 0) + float(c.displacement_value or 0)
            for c in active_contracts
        )
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
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
            'entradas_detalhadas': [
                {
                    'grupo': e.grupo or 'Sem grupo',
                    'subgrupo': e.subgrupo or 'Sem subgrupo',
                    'valor': float(e.total)
                }
                for e in entries_by_group
            ],
            'saidas_detalhadas': [
                {
                    'grupo': s.grupo or 'Sem grupo',
                    'subgrupo': s.subgrupo or 'Sem subgrupo',
                    'valor': float(s.total)
                }
                for s in exits_by_group
            ],
            'dre_ano': dre_year,
            'dre_periodo_anterior': dre_previous,
            'projecoes': dfc_projection,
            'contratos_ativos': {
                'quantidade': len(active_contracts),
                'valor_total': float(total_contracts_value),
                'contratos': [
                    {
                        'contratante': c.contractor_name or '',
                        'valor': float(c.service_value or 0) + float(c.displacement_value or 0),
                        'data_evento': c.event_date.isoformat() if c.event_date else None
                    }
                    for c in active_contracts[:10]  # Limita a 10
                ]
            }
        }
    
    def _calculate_kpis(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula KPIs automáticos para o relatório
        """
        dre = financial_data.get('dre', {})
        dre_ano = financial_data.get('dre_ano', {})
        dre_anterior = financial_data.get('dre_periodo_anterior', {})
        
        receitas = dre.get('receitas', 0)
        despesas = dre.get('despesas', 0)
        resultado = dre.get('resultado', 0)
        
        receitas_ano = dre_ano.get('receitas', 0)
        despesas_ano = dre_ano.get('despesas', 0)
        resultado_ano = dre_ano.get('resultado', 0)
        
        receitas_anterior = dre_anterior.get('receitas', 0)
        despesas_anterior = dre_anterior.get('despesas', 0)
        
        # Margem operacional
        margem = (resultado / receitas * 100) if receitas > 0 else 0
        
        # Crescimento/queda da receita
        crescimento_receita = 0
        if receitas_anterior > 0:
            crescimento_receita = ((receitas - receitas_anterior) / receitas_anterior * 100)
        
        # Custo sobre receita
        custo_sobre_receita = (despesas / receitas * 100) if receitas > 0 else 0
        
        # Despesas sobre receita
        despesas_sobre_receita = (despesas / receitas * 100) if receitas > 0 else 0
        
        # Mínimo necessário para equilíbrio
        # Se há despesas fixas, calcula receita mínima necessária
        minimo_equilibrio = despesas if despesas > 0 else 0
        
        # Projeção de déficit/superávit
        projecoes = financial_data.get('projecoes', {})
        projecao_mes_seguinte = projecoes.get('projection', {}).get('next_month', {})
        saldo_projetado = projecao_mes_seguinte.get('saldo_projetado', 0) if projecao_mes_seguinte else 0
        
        return {
            'margem_operacional': float(margem),
            'crescimento_receita_percent': float(crescimento_receita),
            'custo_sobre_receita_percent': float(custo_sobre_receita),
            'despesas_sobre_receita_percent': float(despesas_sobre_receita),
            'resultado_acumulado_ano': float(resultado_ano),
            'minimo_equilibrio': float(minimo_equilibrio),
            'saldo_projetado_mes_seguinte': float(saldo_projetado),
            'receitas_periodo': float(receitas),
            'despesas_periodo': float(despesas),
            'resultado_periodo': float(resultado)
        }
    
    def _create_report_prompt(
        self,
        financial_data: Dict[str, Any],
        kpis: Dict[str, Any],
        period_start: date,
        period_end: date,
        client_name: str
    ) -> str:
        """
        Cria prompt detalhado para a IA gerar o relatório gerencial
        """
        period_str = period_start.strftime('%B %Y').title()
        
        # Formata dados financeiros para o prompt
        disponiveis = financial_data.get('disponiveis_financeiros', {})
        obrigacoes = financial_data.get('obrigacoes', {})
        contas_receber = financial_data.get('contas_receber', {})
        dre = financial_data.get('dre', {})
        dre_ano = financial_data.get('dre_ano', {})
        dre_anterior = financial_data.get('dre_periodo_anterior', {})
        projecoes = financial_data.get('projecoes', {})
        contratos = financial_data.get('contratos_ativos', {})
        
        prompt = f"""Você é um agente analítico financeiro especializado em criação de relatórios gerenciais empresariais.

Sua função é gerar um relatório completo e independente, seguindo EXATAMENTE o mesmo layout, estrutura, linguagem e ordem do relatório modelo "APURAÇÃO FINANCEIRA".

DADOS FINANCEIROS DO PERÍODO {period_str.upper()}:

**EMPRESA:** {client_name}
**PERÍODO:** {period_start.strftime('%d/%m/%Y')} a {period_end.strftime('%d/%m/%Y')}

**1. DISPONÍVEIS FINANCEIROS:**
- Saldo Bancário Total: R$ {format_currency(disponiveis.get('saldo_bancario', 0))}
- Aplicações Financeiras: R$ {format_currency(disponiveis.get('aplicacoes', 0))}
- Total Disponível: R$ {format_currency(disponiveis.get('total', 0))}

Detalhamento por Banco:
{chr(10).join([f"- {name}: R$ {format_currency(balance)}" for name, balance in disponiveis.get('bancos', {}).items()])}

**2. OBRIGAÇÕES FINANCEIRAS:**
- Contas a Pagar Pendentes: R$ {format_currency(obrigacoes.get('contas_pagar_pendentes', 0))}
- Contas a Pagar Futuras: R$ {format_currency(obrigacoes.get('contas_pagar_futuras', 0))}
- Total de Obrigações: R$ {format_currency(obrigacoes.get('total_obrigacoes', 0))}

**3. CONTAS A RECEBER:**
- Pendentes: R$ {format_currency(contas_receber.get('pendentes', 0))}
- Futuras: R$ {format_currency(contas_receber.get('futuras', 0))}
- Total: R$ {format_currency(contas_receber.get('total', 0))}

**4. RESULTADOS DO PERÍODO:**
- Receitas: R$ {format_currency(dre.get('receitas', 0))}
- Despesas: R$ {format_currency(dre.get('despesas', 0))}
- Resultado Operacional: R$ {format_currency(dre.get('resultado', 0))}
- Margem Operacional: {kpis.get('margem_operacional', 0):.2f}%

**5. RESULTADOS ACUMULADOS DO ANO:**
- Receitas Acumuladas: R$ {format_currency(dre_ano.get('receitas', 0))}
- Despesas Acumuladas: R$ {format_currency(dre_ano.get('despesas', 0))}
- Resultado Acumulado: R$ {format_currency(dre_ano.get('resultado', 0))}

**6. COMPARAÇÃO COM PERÍODO ANTERIOR:**
- Receitas Período Anterior: R$ {format_currency(dre_anterior.get('receitas', 0))}
- Despesas Período Anterior: R$ {format_currency(dre_anterior.get('despesas', 0))}
- Variação Receitas: {kpis.get('crescimento_receita_percent', 0):.2f}%

**7. ENTRADAS DETALHADAS POR GRUPO/SUBGRUPO:**
{chr(10).join([f"- {e['grupo']} > {e['subgrupo']}: R$ {format_currency(e['valor'])}" for e in financial_data.get('entradas_detalhadas', [])[:10]])}

**8. SAÍDAS DETALHADAS POR GRUPO/SUBGRUPO:**
{chr(10).join([f"- {s['grupo']} > {s['subgrupo']}: R$ {format_currency(s['valor'])}" for s in financial_data.get('saidas_detalhadas', [])[:10]])}

**9. CONTRATOS ATIVOS:**
- Quantidade: {contratos.get('quantidade', 0)}
- Valor Total: R$ {format_currency(contratos.get('valor_total', 0))}

**10. PROJEÇÕES FUTURAS (PRÓXIMOS 3 MESES):**
{self._format_projections(projecoes)}

**11. KPIs CALCULADOS:**
- Margem Operacional: {kpis.get('margem_operacional', 0):.2f}%
- Crescimento/Queda Receita: {kpis.get('crescimento_receita_percent', 0):+.2f}%
- Custo sobre Receita: {kpis.get('custo_sobre_receita_percent', 0):.2f}%
- Despesas sobre Receita: {kpis.get('despesas_sobre_receita_percent', 0):.2f}%
- Resultado Acumulado do Ano: R$ {format_currency(kpis.get('resultado_acumulado_ano', 0))}
- Mínimo Necessário para Equilíbrio: R$ {format_currency(kpis.get('minimo_equilibrio', 0))}
- Saldo Projetado Mês Seguinte: R$ {format_currency(kpis.get('saldo_projetado_mes_seguinte', 0))}

---

INSTRUÇÕES OBRIGATÓRIAS PARA GERAÇÃO DO RELATÓRIO:

1. **ESTRUTURA OBRIGATÓRIA (SEGUIR EXATAMENTE ESTA ORDEM):**

Cabeçalho:
- Nome da Empresa: {client_name}
- Período: {period_str}

Diagnóstico Financeiro (ou "Diagnóstico de {period_str}")

1. Disponíveis Financeiros
   - Apresente saldo bancário consolidado
   - Apresente aplicações financeiras
   - Calcule e apresente total disponível
   - Faça análise de liquidez

2. Obrigações Financeiras
   - Apresente contas a pagar pendentes
   - Apresente contas a pagar futuras
   - Calcule total de obrigações
   - Faça análise de endividamento

3. Resultados
   - Apresente entradas detalhadas por grupo/subgrupo
   - Apresente saídas detalhadas (custos + despesas) por grupo/subgrupo
   - Calcule resultado operacional
   - Compare com período anterior (se houver dados)

4. Lucro / Prejuízo
   - Apresente resultado do mês
   - Apresente resultado acumulado do ano
   - Calcule e apresente margem operacional
   - Faça análise de tendências

5. Projeções de Faturamento
   - Apresente projeções dos próximos 3 meses
   - Inclua contratos em andamento
   - Identifique oportunidades

6. Projeção de Caixa
   - Apresente fluxo projetado
   - Identifique déficits futuros
   - Calcule necessidade de capital

7. Conclusões e Estratégias
   - Diagnóstico de saúde financeira
   - Recomendações operacionais
   - Recomendações de liquidez
   - Recomendações comerciais e de marketing
   - Alertas de riscos (ex: risco de desenquadramento MEI)
   - Oportunidades para reversão de prejuízo (se houver)

2. **FORMATAÇÃO:**
- Use valores sempre em R$ com vírgula e ponto no padrão brasileiro (ex: R$ 1.234,56)
- Use bullet points e negritos exatamente como no modelo
- Títulos numerados sempre alinhados à esquerda
- Parágrafos interpretativos logo após cada conjunto de valores
- Separação clara entre seções com linhas em branco
- Gráficos representados como blocos textuais estruturados (ex: JULHO / AGOSTO / SETEMBRO com valores alinhados)

3. **LINGUAGEM:**
- Português claro, empresarial e profissional
- Texto fluido, sem generalizações
- Interpretação técnica, precisa e fundamentada nos dados
- Evitar generalizações vazias
- Explicações objetivas baseadas nos dados fornecidos

4. **ANÁLISE E INSIGHTS:**
- Identifique tendências (crescimento/queda)
- Faça diagnóstico de saúde financeira
- Identifique riscos e alertas
- Analise liquidez
- Avalie impacto dos custos no resultado
- Sinalize despesas fora da curva
- Avalie efeitos das projeções nos próximos meses

5. **RECOMENDAÇÕES:**
- Estratégias operacionais
- Caminhos para melhorar liquidez
- Ajustes em despesas e custos
- Direcionamentos para comercial e marketing
- Recomendações para equilibrar o caixa
- Alerta de riscos futuros
- Oportunidades para reversão do prejuízo

Gere o relatório completo seguindo EXATAMENTE esta estrutura e formatação. O relatório deve parecer que foi produzido pela mesma pessoa que produziu o modelo "APURAÇÃO FINANCEIRA".

Retorne o relatório formatado em markdown, pronto para exibição."""

        return prompt
    
    def _format_projections(self, projecoes: Dict[str, Any]) -> str:
        """
        Formata projeções para o prompt
        """
        if not projecoes:
            return "Nenhuma projeção disponível."
        
        projection_data = projecoes.get('projection', {})
        if not projection_data:
            return "Nenhuma projeção disponível."
        
        formatted = []
        for month_key, data in sorted(projection_data.items()):
            if isinstance(data, dict):
                entradas = data.get('entradas_previstas', 0)
                saidas = data.get('saidas_previstas', 0)
                saldo = data.get('saldo_projetado', 0)
                formatted.append(
                    f"- {month_key}: Entradas R$ {format_currency(entradas)}, "
                    f"Saídas R$ {format_currency(saidas)}, Saldo R$ {format_currency(saldo)}"
                )
        
        return "\n".join(formatted) if formatted else "Nenhuma projeção disponível."
    
    def _process_ai_response(self, response: str) -> str:
        """
        Processa resposta da IA e formata o relatório
        """
        # Remove markdown code blocks se existirem
        if '```markdown' in response:
            response = response.split('```markdown')[1].split('```')[0]
        elif '```' in response:
            response = response.split('```')[1].split('```')[0]
        
        return response.strip()
    
    def _create_visualizations(
        self, 
        financial_data: Dict[str, Any], 
        kpis: Dict[str, Any],
        period_start: date,
        period_end: date
    ) -> List[Dict[str, Any]]:
        """
        Cria visualizações (gráficos) para o relatório gerencial
        Retorna lista de dicionários com tipo e dados do gráfico
        """
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        visualizations = []
        
        try:
            dre = financial_data.get('dre', {})
            dfc = financial_data.get('dfc', {})
            disponiveis = financial_data.get('disponiveis_financeiros', {})
            obrigacoes = financial_data.get('obrigacoes', {})
            entradas_detalhadas = financial_data.get('entradas_detalhadas', [])
            saidas_detalhadas = financial_data.get('saidas_detalhadas', [])
            projecoes = financial_data.get('projecoes', {})
            
            # 1. Gráfico: Disponíveis Financeiros vs Obrigações
            if disponiveis.get('total', 0) > 0 or obrigacoes.get('total_obrigacoes', 0) > 0:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name='Disponíveis',
                    x=['Disponíveis Financeiros'],
                    y=[disponiveis.get('total', 0)],
                    marker_color='#2ecc71',
                    text=[format_currency(disponiveis.get('total', 0))],
                    textposition='auto'
                ))
                fig.add_trace(go.Bar(
                    name='Obrigações',
                    x=['Obrigações Financeiras'],
                    y=[obrigacoes.get('total_obrigacoes', 0)],
                    marker_color='#e74c3c',
                    text=[format_currency(obrigacoes.get('total_obrigacoes', 0))],
                    textposition='auto'
                ))
                fig.update_layout(
                    title='Disponíveis Financeiros vs Obrigações',
                    yaxis_title='Valor (R$)',
                    height=400,
                    showlegend=True
                )
                visualizations.append({
                    'type': 'chart',
                    'data': fig,
                    'section': 'disponiveis_obrigacoes',
                    'title': 'Disponíveis Financeiros vs Obrigações'
                })
            
            # 2. Gráfico: Receitas vs Despesas (Pizza)
            receitas = dre.get('receitas', 0)
            despesas = abs(dre.get('despesas', 0))
            if receitas > 0 or despesas > 0:
                fig = go.Figure(data=[go.Pie(
                    labels=['Receitas', 'Despesas'],
                    values=[receitas, despesas],
                    marker_colors=['#2ecc71', '#e74c3c'],
                    hole=0.4,
                    textinfo='label+percent+value',
                    texttemplate='%{label}<br>%{percent}<br>%{text}',
                    hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>Percentual: %{percent}<extra></extra>'
                )])
                fig.update_layout(
                    title='Distribuição: Receitas vs Despesas',
                    height=400,
                    annotations=[dict(text=f'Resultado<br>{format_currency(dre.get("resultado", 0))}', 
                                    x=0.5, y=0.5, font_size=14, showarrow=False)]
                )
                visualizations.append({
                    'type': 'chart',
                    'data': fig,
                    'section': 'receitas_despesas',
                    'title': 'Distribuição: Receitas vs Despesas'
                })
            
            # 3. Gráfico: Entradas por Grupo/Subgrupo (Top 10)
            if entradas_detalhadas:
                top_entradas = sorted(entradas_detalhadas, key=lambda x: x['valor'], reverse=True)[:10]
                grupos_labels = [f"{e['grupo']} > {e['subgrupo']}" for e in top_entradas]
                valores = [e['valor'] for e in top_entradas]
                
                fig = go.Figure(data=[go.Bar(
                    x=valores,
                    y=grupos_labels,
                    orientation='h',
                    marker_color='#2ecc71',
                    text=[format_currency(v) for v in valores],
                    textposition='auto'
                )])
                fig.update_layout(
                    title='Top 10 Entradas por Grupo/Subgrupo',
                    xaxis_title='Valor (R$)',
                    yaxis_title='Grupo / Subgrupo',
                    height=500,
                    yaxis={'categoryorder': 'total ascending'}
                )
                visualizations.append({
                    'type': 'chart',
                    'data': fig,
                    'section': 'entradas_detalhadas',
                    'title': 'Top 10 Entradas por Grupo/Subgrupo'
                })
            
            # 4. Gráfico: Saídas por Grupo/Subgrupo (Top 10)
            if saidas_detalhadas:
                top_saidas = sorted(saidas_detalhadas, key=lambda x: x['valor'], reverse=True)[:10]
                grupos_labels = [f"{s['grupo']} > {s['subgrupo']}" for s in top_saidas]
                valores = [s['valor'] for s in top_saidas]
                
                fig = go.Figure(data=[go.Bar(
                    x=valores,
                    y=grupos_labels,
                    orientation='h',
                    marker_color='#e74c3c',
                    text=[format_currency(v) for v in valores],
                    textposition='auto'
                )])
                fig.update_layout(
                    title='Top 10 Saídas por Grupo/Subgrupo',
                    xaxis_title='Valor (R$)',
                    yaxis_title='Grupo / Subgrupo',
                    height=500,
                    yaxis={'categoryorder': 'total ascending'}
                )
                visualizations.append({
                    'type': 'chart',
                    'data': fig,
                    'section': 'saidas_detalhadas',
                    'title': 'Top 10 Saídas por Grupo/Subgrupo'
                })
            
            # 5. Gráfico: Fluxo de Caixa Mensal (se houver dados do DFC)
            if dfc.get('fluxo_mensal'):
                fluxo_mensal = dfc.get('fluxo_mensal', [])
                meses = [f['mes'] for f in fluxo_mensal]
                entradas = [f.get('entradas', 0) for f in fluxo_mensal]
                saidas = [abs(f.get('saidas', 0)) for f in fluxo_mensal]
                saldo_mes = [f.get('saldo_mes', 0) for f in fluxo_mensal]
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name='Entradas',
                    x=meses,
                    y=entradas,
                    marker_color='#2ecc71',
                    text=[format_currency(v) for v in entradas],
                    textposition='auto'
                ))
                fig.add_trace(go.Bar(
                    name='Saídas',
                    x=meses,
                    y=saidas,
                    marker_color='#e74c3c',
                    text=[format_currency(v) for v in saidas],
                    textposition='auto'
                ))
                fig.add_trace(go.Scatter(
                    name='Saldo do Mês',
                    x=meses,
                    y=saldo_mes,
                    mode='lines+markers',
                    line=dict(color='#3498db', width=3),
                    marker=dict(size=8),
                    yaxis='y2'
                ))
                fig.update_layout(
                    title='Fluxo de Caixa Mensal',
                    xaxis_title='Mês',
                    yaxis_title='Valor (R$)',
                    yaxis2=dict(
                        title='Saldo (R$)',
                        overlaying='y',
                        side='right'
                    ),
                    barmode='group',
                    height=500,
                    hovermode='x unified',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                visualizations.append({
                    'type': 'chart',
                    'data': fig,
                    'section': 'fluxo_caixa',
                    'title': 'Fluxo de Caixa Mensal'
                })
            
            # 6. Gráfico: Projeções Futuras (se houver)
            if projecoes.get('projection'):
                projection_data = projecoes.get('projection', {})
                meses_proj = sorted(projection_data.keys())
                entradas_proj = [projection_data[m].get('entradas_previstas', 0) for m in meses_proj]
                saidas_proj = [projection_data[m].get('saidas_previstas', 0) for m in meses_proj]
                saldo_proj = [projection_data[m].get('saldo_projetado', 0) for m in meses_proj]
                
                if meses_proj:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        name='Entradas Previstas',
                        x=meses_proj,
                        y=entradas_proj,
                        marker_color='#2ecc71',
                        opacity=0.7,
                        text=[format_currency(v) for v in entradas_proj],
                        textposition='auto'
                    ))
                    fig.add_trace(go.Bar(
                        name='Saídas Previstas',
                        x=meses_proj,
                        y=saidas_proj,
                        marker_color='#e74c3c',
                        opacity=0.7,
                        text=[format_currency(v) for v in saidas_proj],
                        textposition='auto'
                    ))
                    fig.add_trace(go.Scatter(
                        name='Saldo Projetado',
                        x=meses_proj,
                        y=saldo_proj,
                        mode='lines+markers',
                        line=dict(color='#9b59b6', width=3, dash='dash'),
                        marker=dict(size=8),
                        yaxis='y2'
                    ))
                    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                    fig.update_layout(
                        title='Projeções de Caixa (Próximos 3 Meses)',
                        xaxis_title='Mês',
                        yaxis_title='Valor (R$)',
                        yaxis2=dict(
                            title='Saldo (R$)',
                            overlaying='y',
                            side='right'
                        ),
                        barmode='group',
                        height=500,
                        hovermode='x unified',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    visualizations.append({
                        'type': 'chart',
                        'data': fig,
                        'section': 'projecoes',
                        'title': 'Projeções de Caixa (Próximos 3 Meses)'
                    })
            
            # 7. Gráfico: KPIs Principais (Gauge/Métrica)
            if kpis.get('margem_operacional') is not None:
                margem = kpis.get('margem_operacional', 0)
                fig = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=margem,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Margem Operacional (%)"},
                    delta={'reference': 10},
                    gauge={
                        'axis': {'range': [None, 50]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 10], 'color': "lightgray"},
                            {'range': [10, 20], 'color': "gray"},
                            {'range': [20, 50], 'color': "lightgreen"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 10
                        }
                    }
                ))
                fig.update_layout(height=300)
                visualizations.append({
                    'type': 'chart',
                    'data': fig,
                    'section': 'kpis',
                    'title': 'Margem Operacional'
                })
            
        except Exception as e:
            # Em caso de erro, retorna lista vazia
            pass
        
        return visualizations

