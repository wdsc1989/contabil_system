"""
Painel de Controle Unificado
Dashboard executivo com visão geral, alertas e ações rápidas
"""
import streamlit as st
import sys
import os
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from services.report_service import ReportService
from services.contract_service import ContractService
from models.client import Client
from models.contract import Contract
from models.account import AccountPayable, AccountReceivable
from models.transaction import Transaction
from utils.formatters import format_currency, format_date

st.set_page_config(page_title="Painel de Controle", page_icon="🎯", layout="wide")

from utils.hide_auto_menu import hide_streamlit_menu
hide_streamlit_menu()

AuthService.init_session_state()
AuthService.require_auth()

from utils.sidebar import show_sidebar
show_sidebar()

st.title("🎯 Painel de Controle Executivo")
st.markdown("Visão geral do negócio em tempo real")
st.markdown("---")

if not st.session_state.get('selected_client_id'):
    st.warning("⚠️ Selecione um cliente na página inicial.")
    st.stop()

client_id = st.session_state.selected_client_id

db = SessionLocal()
try:
    client = db.query(Client).filter(Client.id == client_id).first()
    if client:
        st.info(f"📌 Cliente: **{client.name}**")
finally:
    db.close()

today = date.today()
primeiro_dia_mes = date(today.year, today.month, 1)
inicio_mes_passado = primeiro_dia_mes - relativedelta(months=1)
fim_mes_passado = primeiro_dia_mes - timedelta(days=1)

db = SessionLocal()
try:
    # Verifica tipos habilitados (usa configuração de DFC por padrão)
    from services.report_config_service import ReportConfigService
    enabled_types = ReportConfigService.get_enabled_data_types(db, client_id, 'dfc')
    
    # Cartões de Status Principais
    st.subheader("📊 Status em Tempo Real")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Caixa Disponível
    with col1:
        dfc_mes_atual = ReportService.get_dfc_data(db, client_id, primeiro_dia_mes, today)
        saldo_atual = dfc_mes_atual.get('saldo_final', 0) if dfc_mes_atual.get('fluxo_mensal') else 0
        
        st.metric(
            "💰 Caixa Disponível",
            format_currency(saldo_atual),
            help="Saldo acumulado até hoje"
        )
    
    # A Receber (próximos 30 dias) - APENAS se habilitado
    with col2:
        hoje_30d = today + timedelta(days=30)
        
        receber_30d = []
        total_receber = 0
        
        if 'accounts_receivable' in enabled_types:
            receber_30d = db.query(AccountReceivable).filter(
                AccountReceivable.client_id == client_id,
                AccountReceivable.received == False,
                AccountReceivable.due_date >= today,
                AccountReceivable.due_date <= hoje_30d
            ).all()
            total_receber = sum(c.value for c in receber_30d)
        
        st.metric(
            "💵 A Receber (30d)",
            format_currency(total_receber),
            help=f"{len(receber_30d)} conta(s)" if 'accounts_receivable' in enabled_types else "Tipo desabilitado"
        )
    
    # A Pagar (próximos 30 dias) - APENAS se habilitado
    with col3:
        pagar_30d = []
        total_pagar = 0
        
        if 'accounts_payable' in enabled_types:
            pagar_30d = db.query(AccountPayable).filter(
                AccountPayable.client_id == client_id,
                AccountPayable.paid == False,
                AccountPayable.due_date >= today,
                AccountPayable.due_date <= hoje_30d
            ).all()
            total_pagar = sum(c.value for c in pagar_30d)
        
        st.metric(
            "💸 A Pagar (30d)",
            format_currency(total_pagar),
            delta_color="inverse",
            help=f"{len(pagar_30d)} conta(s)" if 'accounts_payable' in enabled_types else "Tipo desabilitado"
        )
    
    # Eventos Próximos - APENAS se habilitado
    with col4:
        eventos_proximos = 0
        
        if 'contracts' in enabled_types:
            eventos_proximos = db.query(Contract).filter(
                Contract.client_id == client_id,
                Contract.event_date >= today,
                Contract.event_date <= hoje_30d
            ).count()
        
        st.metric(
            "🎉 Eventos (30d)",
            eventos_proximos,
            help="Eventos agendados próximos 30 dias" if 'contracts' in enabled_types else "Tipo desabilitado"
        )
    
    st.markdown("---")
    
    # Timeline de Eventos (Gantt) - APENAS se habilitado
    if 'contracts' in enabled_types:
        st.subheader("📅 Timeline de Eventos (Próximos 3 Meses)")
        
        eventos_3m = db.query(Contract).filter(
            Contract.client_id == client_id,
            Contract.event_date >= today,
            Contract.event_date <= today + relativedelta(months=3)
        ).order_by(Contract.event_date).all()
    else:
        eventos_3m = []
    
    if eventos_3m:
        gantt_data = []
        for ev in eventos_3m:
            status_color = {
                'pendente': '#f39c12',
                'em_andamento': '#3498db',
                'concluido': '#2ecc71',
                'cancelado': '#e74c3c'
            }.get(ev.status, '#95a5a6')
            
            gantt_data.append({
                'Task': f"{ev.contractor_name} - {ev.event_type or 'Evento'}",
                'Start': ev.event_date,
                'Finish': ev.event_date,
                'Resource': ev.seller_name or 'Sem vendedor',
                'Color': status_color
            })
        
        df_gantt = pd.DataFrame(gantt_data)
        
        fig = go.Figure()
        
        for idx, row in df_gantt.iterrows():
            fig.add_trace(go.Scatter(
                x=[row['Start'], row['Finish']],
                y=[row['Task'], row['Task']],
                mode='markers',
                marker=dict(size=15, color=row['Color'], symbol='diamond'),
                name=row['Resource'],
                showlegend=False,
                hovertemplate=f"<b>{row['Task']}</b><br>Data: {row['Start']}<br>Vendedor: {row['Resource']}<extra></extra>"
            ))
        
        fig.update_layout(
            height=max(300, len(gantt_data) * 30),
            xaxis_title="Data",
            yaxis_title="",
            hovermode='closest'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ Nenhum evento agendado para os próximos 3 meses")
    
    st.markdown("---")
    
    # Alertas Prioritários
    st.subheader("🚨 Alertas Prioritários")
    
    alertas = []
    
    # Contas vencidas (APENAS se habilitado)
    if 'accounts_receivable' in enabled_types:
        receber_vencido = db.query(AccountReceivable).filter(
            AccountReceivable.client_id == client_id,
            AccountReceivable.received == False,
            AccountReceivable.due_date < today
        ).all()
        
        if receber_vencido:
            total_vencido = sum(c.value for c in receber_vencido)
            alertas.append({
                'tipo': 'error',
                'mensagem': f"🔴 {len(receber_vencido)} conta(s) a receber vencida(s) - {format_currency(total_vencido)}"
            })
    
    if 'accounts_payable' in enabled_types:
        pagar_vencido = db.query(AccountPayable).filter(
            AccountPayable.client_id == client_id,
            AccountPayable.paid == False,
            AccountPayable.due_date < today
        ).all()
        
        if pagar_vencido:
            total_vencido_pagar = sum(c.value for c in pagar_vencido)
            alertas.append({
                'tipo': 'error',
                'mensagem': f"🔴 {len(pagar_vencido)} conta(s) a pagar vencida(s) - {format_currency(total_vencido_pagar)}"
            })
    
    # Eventos sem NF (APENAS se habilitado)
    if 'contracts' in enabled_types:
        eventos_sem_nf = ContractService.get_pending_invoices(db, client_id)
        
        if eventos_sem_nf:
            alertas.append({
                'tipo': 'warning',
                'mensagem': f"⚠️ {len(eventos_sem_nf)} evento(s) concluído(s) sem NF emitida"
            })
    
    # Saldo baixo
    if saldo_atual < 5000:
        alertas.append({
            'tipo': 'error',
            'mensagem': f"🔴 Saldo baixo: {format_currency(saldo_atual)}"
        })
    
    # Exibe alertas
    if alertas:
        for alerta in alertas:
            if alerta['tipo'] == 'error':
                st.error(alerta['mensagem'])
            elif alerta['tipo'] == 'warning':
                st.warning(alerta['mensagem'])
            else:
                st.info(alerta['mensagem'])
    else:
        st.success("✅ Nenhum alerta! Tudo sob controle.")
    
    st.markdown("---")
    
    # Resumo do Dia (APENAS se habilitado)
    if 'transactions' in enabled_types or 'bank_statements' in enabled_types:
        st.subheader("📋 Resumo de Hoje")
        
        # Transações de hoje
        trans_hoje = db.query(Transaction).filter(
            Transaction.client_id == client_id,
            Transaction.date == today
        ).all()
    else:
        trans_hoje = []
    
    if trans_hoje:
        entradas_hoje = sum(t.value for t in trans_hoje if t.type == 'entrada')
        saidas_hoje = sum(t.value for t in trans_hoje if t.type == 'saida')
        
        col_h1, col_h2, col_h3 = st.columns(3)
        
        with col_h1:
            st.metric("💰 Entradas Hoje", format_currency(entradas_hoje))
        
        with col_h2:
            st.metric("💸 Saídas Hoje", format_currency(saidas_hoje))
        
        with col_h3:
            saldo_hoje = entradas_hoje - saidas_hoje
            st.metric("📊 Saldo do Dia", format_currency(saldo_hoje))
        
        # Lista transações
        with st.expander(f"Ver {len(trans_hoje)} transação(ões) de hoje"):
            hoje_data = []
            for t in trans_hoje:
                hoje_data.append({
                    'Descrição': t.description,
                    'Valor': format_currency(t.value),
                    'Tipo': '💰' if t.type == 'entrada' else '💸',
                    'Banco': t.bank_name or '-'
                })
            
            st.dataframe(pd.DataFrame(hoje_data), use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ Nenhuma transação registrada hoje")
    
    st.markdown("---")
    
    # Ações Rápidas
    st.subheader("⚡ Ações Rápidas")
    
    col_a1, col_a2, col_a3, col_a4 = st.columns(4)
    
    with col_a1:
        st.page_link("pages/2_Transacoes.py", label="➕ Adicionar Transação", icon="💳", use_container_width=True)
    
    with col_a2:
        st.page_link("pages/4_Contratos.py", label="📝 Novo Contrato", icon="📝", use_container_width=True)
    
    with col_a3:
        st.page_link("pages/5_Contas.py", label="💰 Gerenciar Contas", icon="💰", use_container_width=True)
    
    with col_a4:
        st.page_link("pages/2_Importacao_Dados.py", label="📥 Importar Dados", icon="📥", use_container_width=True)

finally:
    db.close()







