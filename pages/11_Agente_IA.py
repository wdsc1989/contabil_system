"""
Página do Agente Conversacional de IA
"""
import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from dateutil.relativedelta import relativedelta
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from services.ai_agent_service import AIAgentService
from models.client import Client
from utils.formatters import format_currency, format_date

st.set_page_config(page_title="Agente IA", page_icon="🤖", layout="wide")

# Esconde o menu automático do Streamlit
from utils.hide_auto_menu import hide_streamlit_menu
hide_streamlit_menu()

AuthService.init_session_state()
AuthService.require_auth()


# Usa sidebar centralizada
from utils.sidebar import show_sidebar
show_sidebar()

st.title("🤖 Administrador Contábil - Agente IA")
st.markdown("""
Seu assistente contábil inteligente. Faça perguntas em linguagem natural e receba análises profissionais com insights e visualizações.

**Recursos disponíveis:**
- 📊 Análise de dados financeiros em tempo real (PostgreSQL)
- 📈 Relatórios gerenciais completos com visualizações interativas
- 🖼️ Suporte a OCR para processamento de imagens e PDFs escaneados
- 🤖 Processamento inteligente garantindo análise completa de todos os dados
- 📑 Exportação de relatórios em múltiplos formatos
""")
st.markdown("---")

# Inicializa histórico de conversas
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.greeting_sent = False

# Seleção de cliente
db = SessionLocal()
try:
    user = AuthService.get_current_user()
    clients = AuthService.get_user_clients(db, user['id'])
    
    if not clients:
        st.warning("⚠️ Nenhum cliente disponível.")
        st.stop()
    
    # Seleção de cliente
    client_options = {}
    for c in clients:
        tipo_info = f" [{c.tipo_empresa}]" if c.tipo_empresa else ""
        client_options[c.id] = f"{c.name}{tipo_info}"
    
    default_client = st.session_state.get('selected_client_id')
    if default_client not in client_options:
        default_client = list(client_options.keys())[0]
        st.session_state.selected_client_id = default_client
    
    selected_client_id = st.selectbox(
        "🏢 Selecione o cliente:",
        options=list(client_options.keys()),
        format_func=lambda x: client_options[x],
        index=list(client_options.keys()).index(default_client) if default_client in client_options else 0,
        key="agent_client_selector"
    )
    
    st.session_state.selected_client_id = selected_client_id
    
    selected_client = next((c for c in clients if c.id == selected_client_id), None)
    if selected_client:
        st.info(f"📌 Cliente: **{selected_client.name}** | 📋 {selected_client.cpf_cnpj}")
        
        # Envia saudação proativa se ainda não foi enviada
        if not st.session_state.get('greeting_sent', False) or st.session_state.get('last_client_id') != selected_client_id:
            agent_service = AIAgentService(db)
            greeting = agent_service.generate_greeting_with_suggestions(selected_client_id, selected_client.name)
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': greeting,
                'visualizations': []
            })
            st.session_state.greeting_sent = True
            st.session_state.last_client_id = selected_client_id
finally:
    db.close()

st.markdown("---")


def create_visualizations(query_result: dict, query_analysis: dict) -> list:
    """
    Cria visualizações simples baseadas no resultado da consulta.
    Retorna apenas tabelas simples quando necessário, sem gráficos complexos.
    """
    visualizations = []
    query_type = query_result.get('type', '')
    data = query_result.get('data', {})
    output_format = query_analysis.get('output_format', 'completo')
    
    # Não cria visualizações para resumo ou relatórios gerenciais
    if output_format == 'resumo' or query_type == 'relatorio_gerencial':
        return visualizations
    
    try:
        # Apenas tabelas simples quando o usuário pedir explicitamente
        # Removemos todos os gráficos para manter a interface clean
        if query_type == 'transacoes' and output_format == 'tabela':
            # Tabela de transações (apenas se solicitado explicitamente)
            if data.get('transactions'):
                df = pd.DataFrame(data['transactions'][:20])
                if not df.empty:
                    df['date'] = pd.to_datetime(df['date']).dt.strftime('%d/%m/%Y')
                    df['value'] = df['value'].apply(lambda x: format_currency(x))
                    df = df[['date', 'description', 'value', 'type']]
                    df.columns = ['Data', 'Descrição', 'Valor', 'Tipo']
                    visualizations.append({'type': 'table', 'data': df})
        
        elif query_type == 'contratos' and output_format == 'tabela':
            # Tabela de contratos (apenas se solicitado explicitamente)
            if data.get('contracts'):
                df = pd.DataFrame(data['contracts'][:10])
                if not df.empty:
                    df['event_date'] = pd.to_datetime(df['event_date']).dt.strftime('%d/%m/%Y')
                    df['service_value'] = df['service_value'].apply(lambda x: format_currency(x))
                    df['total_value'] = df['total_value'].apply(lambda x: format_currency(x))
                    df = df[['event_date', 'contractor_name', 'total_value', 'status']]
                    df.columns = ['Data do Evento', 'Contratante', 'Valor Total', 'Status']
                    visualizations.append({'type': 'table', 'data': df})
        
        elif query_type == 'contas' and output_format == 'tabela':
            # Tabelas de contas (apenas se solicitado explicitamente)
            if data.get('accounts_payable'):
                df = pd.DataFrame(data['accounts_payable'][:10])
                if not df.empty:
                    df['due_date'] = pd.to_datetime(df['due_date']).dt.strftime('%d/%m/%Y')
                    df['value'] = df['value'].apply(lambda x: format_currency(x))
                    df = df[['account_name', 'due_date', 'value', 'paid']]
                    df.columns = ['Conta', 'Vencimento', 'Valor', 'Pago']
                    visualizations.append({'type': 'table', 'data': df})
            
            if data.get('accounts_receivable'):
                df = pd.DataFrame(data['accounts_receivable'][:10])
                if not df.empty:
                    df['due_date'] = pd.to_datetime(df['due_date']).dt.strftime('%d/%m/%Y')
                    df['value'] = df['value'].apply(lambda x: format_currency(x))
                    df = df[['account_name', 'due_date', 'value', 'received']]
                    df.columns = ['Conta', 'Vencimento', 'Valor', 'Recebido']
                    visualizations.append({'type': 'table', 'data': df})
    
    except Exception as e:
        # Silenciosamente ignora erros de visualização
        pass
    
    return visualizations


# Verifica se IA está disponível
db = SessionLocal()
try:
    agent_service = AIAgentService(db)
    ai_available = agent_service.ai_service.is_available()
    
    if not ai_available:
        st.error("⚠️ Serviço de IA não está configurado. Configure a IA em **Administração > Configuração de IA**.")
        st.stop()
finally:
    db.close()

# Container para histórico de chat
chat_container = st.container()

# Exibe histórico de conversas
with chat_container:
    for i, message in enumerate(st.session_state.chat_history):
        if message['role'] == 'user':
            with st.chat_message("user"):
                st.write(message['content'])
        else:
            with st.chat_message("assistant"):
                # Verifica se é relatório gerencial
                if message.get('is_management_report'):
                    period = message.get('period', {})
                    client_name = message.get('client_name', '')
                    visualizations = message.get('visualizations', [])
                    # Obtém dados financeiros e KPIs do query_result se disponível
                    query_result = message.get('query_result', {})
                    financial_data = query_result.get('financial_data', {}) if query_result else {}
                    kpis = query_result.get('kpis', {}) if query_result else {}
                    
                    # Container principal com estilo visual melhorado
                    with st.container():
                        # Cabeçalho do relatório (estilo visual melhorado)
                        st.markdown("""
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                            <h1 style="color: white; margin: 0; font-size: 32px; font-weight: bold;">📊 Relatório Gerencial</h1>
                            <h2 style="color: rgba(255,255,255,0.95); margin: 10px 0 0 0; font-size: 24px; font-weight: 500;">{}</h2>
                        </div>
                        """.format(client_name), unsafe_allow_html=True)
                        
                        if period.get('start') and period.get('end'):
                            from datetime import datetime
                            start_date = datetime.fromisoformat(period['start']).date()
                            end_date = datetime.fromisoformat(period['end']).date()
                            
                            # Cards de KPIs principais no topo
                            if kpis:
                                col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
                                
                                with col_kpi1:
                                    st.metric(
                                        label="💰 Resultado",
                                        value=format_currency(kpis.get('resultado_periodo', 0)),
                                        delta=f"{kpis.get('crescimento_receita_percent', 0):.1f}% vs anterior" if kpis.get('crescimento_receita_percent') else None
                                    )
                                
                                with col_kpi2:
                                    st.metric(
                                        label="📈 Margem Operacional",
                                        value=f"{kpis.get('margem_operacional', 0):.2f}%",
                                        delta="Meta: 10%" if kpis.get('margem_operacional', 0) < 10 else None
                                    )
                                
                                with col_kpi3:
                                    st.metric(
                                        label="💵 Receitas",
                                        value=format_currency(kpis.get('receitas_periodo', 0))
                                    )
                                
                                with col_kpi4:
                                    st.metric(
                                        label="💸 Despesas",
                                        value=format_currency(kpis.get('despesas_periodo', 0))
                                    )
                            
                            st.markdown(f"""
                            <div style="background-color: #ecf0f1; padding: 15px; border-radius: 8px; margin-bottom: 25px; border-left: 4px solid #3498db;">
                                <strong style="font-size: 16px;">📅 Período:</strong> <span style="font-size: 16px;">{start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}</span>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Cards de disponíveis e obrigações
                            if financial_data:
                                disponiveis = financial_data.get('disponiveis_financeiros', {})
                                obrigacoes = financial_data.get('obrigacoes', {})
                                
                                col_disp1, col_disp2, col_disp3 = st.columns(3)
                                
                                with col_disp1:
                                    st.markdown("""
                                    <div style="background-color: #d5f4e6; padding: 15px; border-radius: 10px; border-left: 4px solid #2ecc71;">
                                        <h3 style="margin: 0 0 10px 0; color: #27ae60; font-size: 14px;">💰 DISPONÍVEIS</h3>
                                        <p style="margin: 0; font-size: 20px; font-weight: bold; color: #1e8449;">{}</p>
                                    </div>
                                    """.format(format_currency(disponiveis.get('total', 0))), unsafe_allow_html=True)
                                
                                with col_disp2:
                                    st.markdown("""
                                    <div style="background-color: #fadbd8; padding: 15px; border-radius: 10px; border-left: 4px solid #e74c3c;">
                                        <h3 style="margin: 0 0 10px 0; color: #c0392b; font-size: 14px;">💸 OBRIGAÇÕES</h3>
                                        <p style="margin: 0; font-size: 20px; font-weight: bold; color: #922b21;">{}</p>
                                    </div>
                                    """.format(format_currency(obrigacoes.get('total_obrigacoes', 0))), unsafe_allow_html=True)
                                
                                with col_disp3:
                                    saldo_liquido = disponiveis.get('total', 0) - obrigacoes.get('total_obrigacoes', 0)
                                    cor_saldo = "#2ecc71" if saldo_liquido >= 0 else "#e74c3c"
                                    bg_saldo = "#d5f4e6" if saldo_liquido >= 0 else "#fadbd8"
                                    st.markdown(f"""
                                    <div style="background-color: {bg_saldo}; padding: 15px; border-radius: 10px; border-left: 4px solid {cor_saldo};">
                                        <h3 style="margin: 0 0 10px 0; color: {cor_saldo}; font-size: 14px;">⚖️ SALDO LÍQUIDO</h3>
                                        <p style="margin: 0; font-size: 20px; font-weight: bold; color: {cor_saldo};">{format_currency(saldo_liquido)}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            st.markdown("---")
                        
                        # Divide o conteúdo do relatório em seções e intercala com gráficos
                        report_content = message['content']
                        
                        # Mapeia visualizações por seção
                        viz_by_section = {}
                        for viz in visualizations:
                            section = viz.get('section', 'geral')
                            if section not in viz_by_section:
                                viz_by_section[section] = []
                            viz_by_section[section].append(viz)
                        
                        # Exibe conteúdo do relatório com gráficos intercalados
                        # Para relatórios gerenciais, exibimos o texto completo primeiro
                        # e depois os gráficos organizados por seção
                        st.markdown("### 📄 Análise e Diagnóstico")
                        
                        # Container com estilo de documento profissional
                        st.markdown("""
                        <div style="background-color: #ffffff; padding: 25px; border-radius: 10px; border: 1px solid #e0e0e0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); line-height: 1.8; font-size: 15px;">
                        """, unsafe_allow_html=True)
                        st.markdown(report_content)
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Para relatórios gerenciais, não exibimos gráficos complexos
                        # O conteúdo textual já contém todas as informações necessárias
                        
                        # Botões para exportar relatório
                        st.markdown("---")
                        col_exp1, col_exp2, col_exp3 = st.columns([1, 1, 2])
                        with col_exp1:
                            report_text = message['content']
                            st.download_button(
                                label="📥 Exportar Markdown",
                                data=report_text,
                                file_name=f"relatorio_gerencial_{period.get('start', '')}.md",
                                mime="text/markdown",
                                use_container_width=True
                            )
                        with col_exp2:
                            # Exportar como HTML formatado
                            if period.get('start') and period.get('end'):
                                from datetime import datetime
                                start_export = datetime.fromisoformat(period['start']).date()
                                end_export = datetime.fromisoformat(period['end']).date()
                                
                                # Converte markdown para HTML básico
                                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Relatório Gerencial - {client_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 40px; line-height: 1.8; max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #555; margin-top: 20px; }}
        .period {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .content {{ margin-top: 20px; }}
        .content p {{ margin: 10px 0; }}
        .content ul, .content ol {{ margin: 10px 0; padding-left: 30px; }}
        .content strong {{ color: #2c3e50; }}
    </style>
</head>
<body>
    <h1>📊 Relatório Gerencial</h1>
    <h2>{client_name}</h2>
    <div class="period">
        <strong>Período:</strong> {start_export.strftime('%d/%m/%Y')} a {end_export.strftime('%d/%m/%Y')}
    </div>
    <div class="content">
        {report_content.replace(chr(10), '<br>').replace('**', '<strong>').replace('**', '</strong>')}
    </div>
</body>
</html>
"""
                                st.download_button(
                                    label="📄 Exportar HTML",
                                    data=html_content,
                                    file_name=f"relatorio_gerencial_{period.get('start', '')}.html",
                                    mime="text/html",
                                    use_container_width=True
                                )
                else:
                    st.markdown(message['content'])
                
                # Exibe apenas tabelas simples se houver (sem gráficos)
                if not message.get('is_management_report') and 'visualizations' in message and message['visualizations']:
                    for viz in message['visualizations']:
                        if viz['type'] == 'table':
                            st.markdown("---")
                            st.dataframe(viz['data'], use_container_width=True, hide_index=True)

# Input de pergunta
st.markdown("---")
query = st.chat_input("Faça uma pergunta sobre seus dados financeiros...")

if query:
    # Detecta se é uma saudação
    greeting_keywords = ['oi', 'olá', 'bom dia', 'boa tarde', 'boa noite', 'hello', 'hi', 'e aí']
    is_greeting = any(keyword in query.lower() for keyword in greeting_keywords)
    
    # Adiciona pergunta ao histórico
    st.session_state.chat_history.append({
        'role': 'user',
        'content': query
    })
    
    # Processa pergunta
    db = SessionLocal()
    try:
        agent_service = AIAgentService(db)
        
        # Se for saudação, envia saudação proativa
        if is_greeting:
            client_obj = db.query(Client).filter(Client.id == selected_client_id).first()
            if client_obj:
                greeting = agent_service.generate_greeting_with_suggestions(selected_client_id, client_obj.name)
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': greeting,
                    'visualizations': []
                })
                st.rerun()
        
        with st.spinner("🤔 Analisando sua pergunta..."):
            # Analisa a pergunta
            query_analysis = agent_service.analyze_query(query, selected_client_id)
            
            if query_analysis.get('intent') == 'error':
                error_msg = query_analysis.get('error', 'Erro desconhecido')
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': f"❌ **Erro:** {error_msg}",
                    'visualizations': []
                })
                st.rerun()
            
            # Executa consulta
            with st.spinner("📊 Consultando dados..."):
                query_result = agent_service.execute_query(db, selected_client_id, query_analysis)
            
            if query_result.get('type') == 'error':
                error_msg = query_result.get('error', 'Erro desconhecido')
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': f"❌ **Erro:** {error_msg}",
                    'visualizations': []
                })
                st.rerun()
            
            # Verifica se é relatório gerencial
            if query_result.get('type') == 'relatorio_gerencial':
                # Para relatório gerencial, usa o conteúdo diretamente da IA
                report_content = query_result.get('data', '')
                period = query_result.get('period', {})
                client_name = query_result.get('client_name', '')
                visualizations = query_result.get('visualizations', [])
                
                # Adiciona relatório ao histórico
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': report_content,
                    'visualizations': visualizations,
                    'query_result': query_result,
                    'is_management_report': True,
                    'period': period,
                    'client_name': client_name
                })
                st.rerun()
            else:
                # Formata resposta normal
                with st.spinner("✍️ Gerando resposta..."):
                    response_text = agent_service.format_response(query_result, query_analysis, query)
                
                # Cria visualizações
                visualizations = create_visualizations(query_result, query_analysis)
                
                # Adiciona resposta ao histórico
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': response_text,
                    'visualizations': visualizations,
                    'query_result': query_result
                })
                
                st.rerun()
            
    except Exception as e:
        st.error(f"❌ Erro ao processar pergunta: {str(e)}")
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': f"❌ **Erro:** {str(e)}",
            'visualizations': []
        })
        st.rerun()
    finally:
        db.close()

# Botões de ação
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🗑️ Limpar Histórico", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

with col2:
    if st.button("📋 Exemplos de Perguntas", use_container_width=True):
        examples = [
            "Gerar relatório gerencial de Outubro 2025",
            "Quais são as receitas do último mês?",
            "Mostre as despesas por grupo",
            "Gere um DRE do último trimestre",
            "Qual é o saldo atual?",
            "Quantas contas estão pendentes?",
            "Mostre o fluxo de caixa dos últimos 6 meses",
            "Qual foi o melhor mês em receitas?",
            "Compare as receitas deste ano com o ano passado",
            "Quais são as principais despesas?",
            "Crie um relatório de sazonalidade",
            "Analise a performance de vendedores",
            "Mostre o dashboard de contas a pagar e receber",
            "Qual é a margem operacional atual?",
            "Quais são os contratos ativos?",
            "Analise despesas CPF vs CNPJ",
            "Mostre o diário de gastos do mês"
        ]
        st.info("💡 **Exemplos de perguntas que você pode fazer:**\n\n" + "\n".join(f"- {ex}" for ex in examples))

with col3:
    if st.session_state.chat_history:
        # Botão para exportar última resposta
        last_message = st.session_state.chat_history[-1]
        if last_message['role'] == 'assistant' and 'query_result' in last_message:
            try:
                data = last_message['query_result'].get('data', {})
                query_type = last_message['query_result'].get('type', '')
                
                # Cria DataFrame baseado no tipo
                df = None
                filename = 'resultado.xlsx'
                
                if query_type == 'transacoes' and data.get('transactions'):
                    df = pd.DataFrame(data['transactions'])
                    filename = 'transacoes.xlsx'
                elif query_type == 'dre':
                    df = pd.DataFrame([{
                        'Receitas': data.get('receitas', 0),
                        'Despesas': data.get('despesas', 0),
                        'Resultado': data.get('resultado', 0),
                        'Margem (%)': data.get('margem', 0)
                    }])
                    filename = 'dre.xlsx'
                elif query_type == 'dfc' and data.get('fluxo_mensal'):
                    df = pd.DataFrame([
                        {
                            'Mês': mes,
                            'Entradas': fluxo.get('entradas', 0),
                            'Saídas': fluxo.get('saidas', 0),
                            'Saldo': fluxo.get('entradas', 0) - abs(fluxo.get('saidas', 0))
                        }
                        for mes, fluxo in data['fluxo_mensal'].items()
                    ])
                    filename = 'dfc.xlsx'
                
                if df is not None and not df.empty:
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Dados')
                    
                    st.download_button(
                        label="📥 Baixar Excel",
                        data=output.getvalue(),
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            except:
                pass  # Ignora erros na exportação









