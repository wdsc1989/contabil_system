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

AuthService.init_session_state()
AuthService.require_auth()


def show_sidebar():
    with st.sidebar:
        st.title("📊 Sistema Contábil")
        user = AuthService.get_current_user()
        st.markdown(f"**Usuário:** {user['username']}")
        st.markdown(f"**Perfil:** {user['role'].title()}")
        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True):
            AuthService.logout()
            st.rerun()


show_sidebar()

st.title("🤖 Administrador Contábil - Agente IA")
st.markdown("Seu assistente contábil inteligente. Faça perguntas em linguagem natural e receba análises profissionais com insights e visualizações.")
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
    """Cria visualizações baseadas no resultado da consulta"""
    visualizations = []
    query_type = query_result.get('type', '')
    data = query_result.get('data', {})
    output_format = query_analysis.get('output_format', 'completo')
    
    if output_format == 'resumo':
        return visualizations  # Não cria visualizações para resumo
    
    try:
        if query_type == 'transacoes':
            # Gráfico de barras: Entradas vs Saídas
            if data.get('total_entradas', 0) > 0 or data.get('total_saidas', 0) > 0:
                fig = go.Figure(data=[
                    go.Bar(name='Entradas', x=['Entradas'], y=[data.get('total_entradas', 0)], marker_color='green'),
                    go.Bar(name='Saídas', x=['Saídas'], y=[data.get('total_saidas', 0)], marker_color='red')
                ])
                fig.update_layout(
                    title='Entradas vs Saídas',
                    yaxis_title='Valor (R$)',
                    barmode='group',
                    height=400
                )
                visualizations.append({'type': 'chart', 'data': fig})
            
            # Tabela de transações (primeiras 20)
            if data.get('transactions'):
                df = pd.DataFrame(data['transactions'][:20])
                if not df.empty:
                    df['date'] = pd.to_datetime(df['date']).dt.strftime('%d/%m/%Y')
                    df['value'] = df['value'].apply(lambda x: format_currency(x))
                    df = df[['date', 'description', 'value', 'type']]
                    df.columns = ['Data', 'Descrição', 'Valor', 'Tipo']
                    visualizations.append({'type': 'table', 'data': df})
        
        elif query_type == 'dre':
            # Gráfico de pizza: Receitas vs Despesas
            receitas = data.get('receitas', 0)
            despesas = abs(data.get('despesas', 0))
            
            if receitas > 0 or despesas > 0:
                fig = go.Figure(data=[go.Pie(
                    labels=['Receitas', 'Despesas'],
                    values=[receitas, despesas],
                    marker_colors=['green', 'red']
                )])
                fig.update_layout(
                    title='Distribuição: Receitas vs Despesas',
                    height=400
                )
                visualizations.append({'type': 'chart', 'data': fig})
            
            # Gráfico de barras: Receitas por grupo
            if data.get('receitas_por_grupo'):
                grupos = [r['grupo'] for r in data['receitas_por_grupo']]
                valores = [r['valor'] for r in data['receitas_por_grupo']]
                
                fig = go.Figure(data=[go.Bar(x=grupos, y=valores, marker_color='green')])
                fig.update_layout(
                    title='Receitas por Grupo',
                    xaxis_title='Grupo',
                    yaxis_title='Valor (R$)',
                    height=400
                )
                visualizations.append({'type': 'chart', 'data': fig})
            
            # Gráfico de barras: Despesas por grupo
            if data.get('despesas_por_grupo'):
                grupos = [d['grupo'] for d in data['despesas_por_grupo']]
                valores = [d['valor'] for d in data['despesas_por_grupo']]
                
                fig = go.Figure(data=[go.Bar(x=grupos, y=valores, marker_color='red')])
                fig.update_layout(
                    title='Despesas por Grupo',
                    xaxis_title='Grupo',
                    yaxis_title='Valor (R$)',
                    height=400
                )
                visualizations.append({'type': 'chart', 'data': fig})
        
        elif query_type == 'dfc':
            # Gráfico de linha: Fluxo mensal
            if data.get('fluxo_mensal'):
                meses = sorted(data['fluxo_mensal'].keys())
                entradas = [data['fluxo_mensal'][m].get('entradas', 0) for m in meses]
                saidas = [abs(data['fluxo_mensal'][m].get('saidas', 0)) for m in meses]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=meses, y=entradas, name='Entradas', line=dict(color='green')))
                fig.add_trace(go.Scatter(x=meses, y=saidas, name='Saídas', line=dict(color='red')))
                fig.update_layout(
                    title='Fluxo de Caixa Mensal',
                    xaxis_title='Mês',
                    yaxis_title='Valor (R$)',
                    height=400
                )
                visualizations.append({'type': 'chart', 'data': fig})
        
        elif query_type == 'kpis':
            # KPIs serão exibidos no texto da resposta, não como visualização separada
            pass
        
        elif query_type == 'contratos':
            # Tabela de contratos
            if data.get('contracts'):
                df = pd.DataFrame(data['contracts'])
                if not df.empty:
                    df['event_date'] = pd.to_datetime(df['event_date']).dt.strftime('%d/%m/%Y')
                    df['service_value'] = df['service_value'].apply(lambda x: format_currency(x))
                    df['total_value'] = df['total_value'].apply(lambda x: format_currency(x))
                    df = df[['event_date', 'contractor_name', 'total_value', 'status']]
                    df.columns = ['Data do Evento', 'Contratante', 'Valor Total', 'Status']
                    visualizations.append({'type': 'table', 'data': df})
        
        elif query_type == 'contas':
            # Tabelas de contas a pagar e receber
            if data.get('accounts_payable'):
                df = pd.DataFrame(data['accounts_payable'])
                if not df.empty:
                    df['due_date'] = pd.to_datetime(df['due_date']).dt.strftime('%d/%m/%Y')
                    df['value'] = df['value'].apply(lambda x: format_currency(x))
                    df = df[['account_name', 'due_date', 'value', 'paid']]
                    df.columns = ['Conta', 'Vencimento', 'Valor', 'Pago']
                    visualizations.append({'type': 'table', 'data': df})
            
            if data.get('accounts_receivable'):
                df = pd.DataFrame(data['accounts_receivable'])
                if not df.empty:
                    df['due_date'] = pd.to_datetime(df['due_date']).dt.strftime('%d/%m/%Y')
                    df['value'] = df['value'].apply(lambda x: format_currency(x))
                    df = df[['account_name', 'due_date', 'value', 'received']]
                    df.columns = ['Conta', 'Vencimento', 'Valor', 'Recebido']
                    visualizations.append({'type': 'table', 'data': df})
    
    except Exception as e:
        st.error(f"Erro ao criar visualização: {str(e)}")
    
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
                st.markdown(message['content'])
                
                # Exibe visualizações se houver
                if 'visualizations' in message and message['visualizations']:
                    for viz in message['visualizations']:
                        if viz['type'] == 'chart':
                            st.plotly_chart(viz['data'], use_container_width=True)
                        elif viz['type'] == 'table':
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
            
            # Formata resposta
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
            "Quais são as receitas do último mês?",
            "Mostre as despesas por grupo",
            "Gere um DRE do último trimestre",
            "Qual é o saldo atual?",
            "Quantas contas estão pendentes?",
            "Mostre o fluxo de caixa dos últimos 6 meses",
            "Qual foi o melhor mês em receitas?",
            "Compare as receitas deste ano com o ano passado",
            "Quais são as principais despesas?",
            "Crie um relatório de sazonalidade"
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



