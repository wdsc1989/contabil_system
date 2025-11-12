"""
Página de Geração e Exportação de Relatórios
"""
import streamlit as st
import sys
import os
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from services.report_service import ReportService
from models.client import Client
from models.transaction import Transaction
from models.contract import Contract
from models.account import AccountPayable, AccountReceivable
from utils.formatters import format_currency, format_date

st.set_page_config(page_title="Relatórios", page_icon="📑", layout="wide")

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

st.title("📑 Relatórios e Exportação")
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

# Tipo de relatório
st.subheader("📋 Selecione o Tipo de Relatório")

report_type = st.selectbox(
    "Tipo de relatório:",
    options=['DRE', 'DFC', 'Transações', 'Contratos', 'Contas a Pagar', 'Contas a Receber', 'Relatório Completo']
)

st.markdown("---")

# Filtros de período
st.subheader("📅 Período")

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input("Data inicial:", value=date.today() - relativedelta(months=1))

with col2:
    end_date = st.date_input("Data final:", value=date.today())

st.markdown("---")

# Botão de geração
if st.button("📊 Gerar Relatório", use_container_width=True, type="primary"):
    db = SessionLocal()
    
    try:
        with st.spinner("Gerando relatório..."):
            # Container para o relatório
            st.subheader(f"📄 {report_type}")
            st.markdown(f"**Período:** {format_date(start_date)} a {format_date(end_date)}")
            st.markdown(f"**Cliente:** {client.name}")
            st.markdown("---")
            
            # Dados para exportação
            export_data = {}
            
            # DRE
            if report_type in ['DRE', 'Relatório Completo']:
                st.markdown("### 📊 DRE - Demonstração do Resultado")
                
                dre_data = ReportService.get_dre_data(db, client_id, start_date, end_date)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Receitas", format_currency(dre_data['receitas']))
                
                with col2:
                    st.metric("Despesas", format_currency(dre_data['despesas']))
                
                with col3:
                    st.metric("Resultado", format_currency(dre_data['resultado']))
                
                # DataFrame para exportação
                dre_df = pd.DataFrame([
                    {'Descrição': 'Receitas', 'Valor': dre_data['receitas']},
                    {'Descrição': 'Despesas', 'Valor': dre_data['despesas']},
                    {'Descrição': 'Resultado', 'Valor': dre_data['resultado']},
                    {'Descrição': 'Margem (%)', 'Valor': dre_data['margem']}
                ])
                
                export_data['DRE'] = dre_df
                
                st.markdown("---")
            
            # DFC
            if report_type in ['DFC', 'Relatório Completo']:
                st.markdown("### 💵 DFC - Fluxo de Caixa")
                
                dfc_data = ReportService.get_dfc_data(db, client_id, start_date, end_date)
                
                if dfc_data['fluxo_mensal']:
                    dfc_df = pd.DataFrame([
                        {
                            'Mês': f['mes'],
                            'Entradas': f['entradas'],
                            'Saídas': f['saidas'],
                            'Saldo do Mês': f['saldo_mes'],
                            'Saldo Acumulado': f['saldo_acumulado']
                        }
                        for f in dfc_data['fluxo_mensal']
                    ])
                    
                    st.dataframe(dfc_df, use_container_width=True, hide_index=True)
                    export_data['DFC'] = dfc_df
                else:
                    st.info("Nenhuma transação no período.")
                
                st.markdown("---")
            
            # Transações
            if report_type in ['Transações', 'Relatório Completo']:
                st.markdown("### 💳 Transações")
                
                transactions = db.query(Transaction).filter(
                    Transaction.client_id == client_id,
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                ).order_by(Transaction.date.desc()).all()
                
                if transactions:
                    trans_df = pd.DataFrame([
                        {
                            'Data': format_date(t.date),
                            'Descrição': t.description,
                            'Tipo': t.type.title(),
                            'Valor': t.value,
                            'Categoria': t.category or '-'
                        }
                        for t in transactions
                    ])
                    
                    st.dataframe(trans_df, use_container_width=True, hide_index=True)
                    st.caption(f"Total: {len(transactions)} transações")
                    
                    export_data['Transações'] = trans_df
                else:
                    st.info("Nenhuma transação no período.")
                
                st.markdown("---")
            
            # Contratos
            if report_type in ['Contratos', 'Relatório Completo']:
                st.markdown("### 📝 Contratos")
                
                contracts = db.query(Contract).filter(
                    Contract.client_id == client_id,
                    Contract.event_date >= start_date,
                    Contract.event_date <= end_date
                ).order_by(Contract.event_date.desc()).all()
                
                if contracts:
                    contracts_df = pd.DataFrame([
                        {
                            'Data Evento': format_date(c.event_date),
                            'Contratante': c.contractor_name,
                            'Tipo': c.event_type or '-',
                            'Valor Serviço': c.service_value,
                            'Valor Total': c.service_value + c.displacement_value,
                            'Status': c.status.title()
                        }
                        for c in contracts
                    ])
                    
                    st.dataframe(contracts_df, use_container_width=True, hide_index=True)
                    st.caption(f"Total: {len(contracts)} contratos")
                    
                    export_data['Contratos'] = contracts_df
                else:
                    st.info("Nenhum contrato no período.")
                
                st.markdown("---")
            
            # Contas a Pagar
            if report_type in ['Contas a Pagar', 'Relatório Completo']:
                st.markdown("### 💸 Contas a Pagar")
                
                accounts_payable = db.query(AccountPayable).filter(
                    AccountPayable.client_id == client_id,
                    AccountPayable.due_date >= start_date,
                    AccountPayable.due_date <= end_date
                ).order_by(AccountPayable.due_date).all()
                
                if accounts_payable:
                    payable_df = pd.DataFrame([
                        {
                            'Conta': a.account_name,
                            'Vencimento': format_date(a.due_date),
                            'Valor': a.value,
                            'Status': 'Paga' if a.paid else 'Pendente',
                            'Pagamento': format_date(a.payment_date) if a.payment_date else '-'
                        }
                        for a in accounts_payable
                    ])
                    
                    st.dataframe(payable_df, use_container_width=True, hide_index=True)
                    
                    total = sum(a.value for a in accounts_payable)
                    pendente = sum(a.value for a in accounts_payable if not a.paid)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total", format_currency(total))
                    with col2:
                        st.metric("Pendente", format_currency(pendente))
                    
                    export_data['Contas a Pagar'] = payable_df
                else:
                    st.info("Nenhuma conta a pagar no período.")
                
                st.markdown("---")
            
            # Contas a Receber
            if report_type in ['Contas a Receber', 'Relatório Completo']:
                st.markdown("### 💰 Contas a Receber")
                
                accounts_receivable = db.query(AccountReceivable).filter(
                    AccountReceivable.client_id == client_id,
                    AccountReceivable.due_date >= start_date,
                    AccountReceivable.due_date <= end_date
                ).order_by(AccountReceivable.due_date).all()
                
                if accounts_receivable:
                    receivable_df = pd.DataFrame([
                        {
                            'Conta': a.account_name,
                            'Vencimento': format_date(a.due_date),
                            'Valor': a.value,
                            'Status': 'Recebida' if a.received else 'Pendente',
                            'Recebimento': format_date(a.receipt_date) if a.receipt_date else '-'
                        }
                        for a in accounts_receivable
                    ])
                    
                    st.dataframe(receivable_df, use_container_width=True, hide_index=True)
                    
                    total = sum(a.value for a in accounts_receivable)
                    pendente = sum(a.value for a in accounts_receivable if not a.received)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total", format_currency(total))
                    with col2:
                        st.metric("Pendente", format_currency(pendente))
                    
                    export_data['Contas a Receber'] = receivable_df
                else:
                    st.info("Nenhuma conta a receber no período.")
                
                st.markdown("---")
            
            # Botão de exportação
            st.subheader("💾 Exportar Relatório")
            
            if export_data:
                # Exporta para Excel
                excel_data = ReportService.export_to_excel(export_data, f"relatorio_{report_type}.xlsx")
                
                st.download_button(
                    label="📥 Download Excel",
                    data=excel_data,
                    file_name=f"relatorio_{client.name}_{start_date}_{end_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                st.success("✅ Relatório gerado com sucesso!")
            else:
                st.warning("⚠️ Nenhum dado para exportar.")
    
    finally:
        db.close()

# Informações
with st.expander("ℹ️ Sobre os Relatórios"):
    st.markdown("""
    ### Tipos de Relatórios Disponíveis
    
    **DRE (Demonstração do Resultado)**
    - Receitas vs Despesas
    - Resultado líquido e margem
    
    **DFC (Fluxo de Caixa)**
    - Entradas e saídas mensais
    - Saldo acumulado
    
    **Transações**
    - Lista detalhada de todas as transações
    - Filtradas por período
    
    **Contratos**
    - Contratos e eventos do período
    - Status e valores
    
    **Contas a Pagar/Receber**
    - Contas com vencimento no período
    - Status de pagamento/recebimento
    
    **Relatório Completo**
    - Todos os relatórios acima em um único arquivo Excel
    - Múltiplas abas com dados organizados
    
    ### Formatos de Exportação
    
    - **Excel (.xlsx)**: Formato ideal para análise e edição
    - Múltiplas abas organizadas por tipo de dado
    - Formatação preservada
    """)

