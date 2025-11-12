"""
Página de Contas a Pagar e Receber
"""
import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from models.client import Client
from models.account import AccountPayable, AccountReceivable
from utils.formatters import format_currency, format_date, format_cpf_cnpj

st.set_page_config(page_title="Contas", page_icon="💰", layout="wide")

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

st.title("💰 Contas a Pagar e Receber")
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

# Tabs principais
tab1, tab2 = st.tabs(["💸 Contas a Pagar", "💰 Contas a Receber"])

db = SessionLocal()

try:
    # TAB 1: Contas a Pagar
    with tab1:
        st.subheader("Contas a Pagar")
        
        # Sub-tabs
        subtab1, subtab2 = st.tabs(["📋 Lista", "➕ Nova Conta"])
        
        with subtab1:
            # Filtros
            col1, col2, col3 = st.columns(3)
            
            with col1:
                show_paid = st.checkbox("Mostrar pagas", value=False)
            
            with col2:
                date_from = st.date_input("Vencimento de:", value=None, key="payable_from")
            
            with col3:
                date_to = st.date_input("Vencimento até:", value=None, key="payable_to")
            
            # Query
            query = db.query(AccountPayable).filter(AccountPayable.client_id == client_id)
            
            if not show_paid:
                query = query.filter(AccountPayable.paid == False)
            
            if date_from:
                query = query.filter(AccountPayable.due_date >= date_from)
            
            if date_to:
                query = query.filter(AccountPayable.due_date <= date_to)
            
            accounts = query.order_by(AccountPayable.due_date).all()
            
            if accounts:
                # Alertas de vencimento
                today = date.today()
                overdue = [a for a in accounts if a.due_date < today and not a.paid]
                due_soon = [a for a in accounts if a.due_date >= today and a.due_date <= today + timedelta(days=7) and not a.paid]
                
                if overdue:
                    st.error(f"⚠️ {len(overdue)} conta(s) vencida(s)!")
                
                if due_soon:
                    st.warning(f"⏰ {len(due_soon)} conta(s) vencem nos próximos 7 dias!")
                
                # Tabela
                account_data = []
                for account in accounts:
                    status = "✅ Paga" if account.paid else "⏳ Pendente"
                    
                    if not account.paid and account.due_date < today:
                        status = "❌ Vencida"
                    elif not account.paid and account.due_date <= today + timedelta(days=7):
                        status = "⚠️ Vence em breve"
                    
                    account_data.append({
                        'ID': account.id,
                        'Conta': account.account_name,
                        'CPF/CNPJ': format_cpf_cnpj(account.cpf_cnpj) if account.cpf_cnpj else '-',
                        'Vencimento': format_date(account.due_date),
                        'Valor': format_currency(account.value),
                        'Status': status,
                        'Pagamento': format_date(account.payment_date) if account.payment_date else '-'
                    })
                
                df = pd.DataFrame(account_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Estatísticas
                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total de Contas", len(accounts))
                
                with col2:
                    total_value = sum(a.value for a in accounts)
                    st.metric("Valor Total", format_currency(total_value))
                
                with col3:
                    pending_value = sum(a.value for a in accounts if not a.paid)
                    st.metric("A Pagar", format_currency(pending_value))
                
                with col4:
                    paid_value = sum(a.value for a in accounts if a.paid)
                    st.metric("Pago", format_currency(paid_value))
                
                st.markdown("---")
                
                # Marcar como paga
                st.subheader("💳 Registrar Pagamento")
                
                unpaid_accounts = [a for a in accounts if not a.paid]
                
                if unpaid_accounts:
                    selected_account_id = st.selectbox(
                        "Selecione a conta:",
                        options=[a.id for a in unpaid_accounts],
                        format_func=lambda x: next(f"{a.account_name} - {format_currency(a.value)} (Venc: {format_date(a.due_date)})" for a in unpaid_accounts if a.id == x),
                        key="pay_select"
                    )
                    
                    payment_date = st.date_input("Data do pagamento:", value=date.today(), key="payment_date")
                    
                    if st.button("✅ Marcar como Paga", use_container_width=True):
                        account = db.query(AccountPayable).filter(AccountPayable.id == selected_account_id).first()
                        account.paid = True
                        account.payment_date = payment_date
                        db.commit()
                        st.success("✅ Pagamento registrado!")
                        st.rerun()
                else:
                    st.info("ℹ️ Todas as contas estão pagas!")
                
                st.markdown("---")
                
                # Editar/Excluir conta
                st.subheader("✏️ Editar/Excluir Conta")
                
                if accounts:
                    edit_account_id = st.selectbox(
                        "Selecione a conta para editar:",
                        options=[a.id for a in accounts],
                        format_func=lambda x: next(f"{a.account_name} - {format_currency(a.value)} (Venc: {format_date(a.due_date)})" for a in accounts if a.id == x),
                        key="edit_payable_select"
                    )
                    
                    if edit_account_id:
                        account = db.query(AccountPayable).filter(AccountPayable.id == edit_account_id).first()
                        
                        with st.form("edit_payable_form"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                edit_name = st.text_input("Nome da Conta *", value=account.account_name)
                                edit_cpf_cnpj = st.text_input("CPF/CNPJ", value=account.cpf_cnpj or '')
                            
                            with col2:
                                edit_due_date = st.date_input("Vencimento *", value=account.due_date)
                                edit_value = st.number_input("Valor *", value=float(account.value), min_value=0.0, step=10.0)
                            
                            col1, col2 = st.columns([1, 1])
                            
                            with col1:
                                submit_edit = st.form_submit_button("💾 Salvar", use_container_width=True)
                            
                            with col2:
                                delete_btn = st.form_submit_button("🗑️ Excluir", use_container_width=True)
                            
                            if submit_edit:
                                if edit_name and edit_value > 0:
                                    account.account_name = edit_name
                                    account.cpf_cnpj = edit_cpf_cnpj if edit_cpf_cnpj else None
                                    account.due_date = edit_due_date
                                    account.value = edit_value
                                    account.month_ref = edit_due_date.strftime('%Y-%m')
                                    db.commit()
                                    st.success("✅ Conta atualizada!")
                                    st.rerun()
                                else:
                                    st.error("❌ Preencha os campos obrigatórios.")
                            
                            if delete_btn:
                                db.delete(account)
                                db.commit()
                                st.success("✅ Conta excluída!")
                                st.rerun()
            
            else:
                st.info("ℹ️ Nenhuma conta a pagar encontrada.")
        
        with subtab2:
            st.subheader("Cadastrar Nova Conta a Pagar")
            
            with st.form("new_payable_form"):
                account_name = st.text_input("Nome da Conta *", placeholder="Fornecedor, serviço, etc")
                cpf_cnpj = st.text_input("CPF/CNPJ", placeholder="000.000.000-00 ou 00.000.000/0000-00")
                due_date = st.date_input("Data de Vencimento *", value=date.today())
                value = st.number_input("Valor *", min_value=0.0, step=10.0)
                
                submit = st.form_submit_button("➕ Cadastrar", use_container_width=True)
                
                if submit:
                    if account_name and value > 0:
                        new_account = AccountPayable(
                            client_id=client_id,
                            account_name=account_name,
                            cpf_cnpj=cpf_cnpj if cpf_cnpj else None,
                            due_date=due_date,
                            value=value,
                            month_ref=due_date.strftime('%Y-%m'),
                            paid=False
                        )
                        
                        db.add(new_account)
                        db.commit()
                        st.success("✅ Conta cadastrada com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Preencha todos os campos obrigatórios.")
    
    # TAB 2: Contas a Receber
    with tab2:
        st.subheader("Contas a Receber")
        
        # Sub-tabs
        subtab1, subtab2 = st.tabs(["📋 Lista", "➕ Nova Conta"])
        
        with subtab1:
            # Filtros
            col1, col2, col3 = st.columns(3)
            
            with col1:
                show_received = st.checkbox("Mostrar recebidas", value=False, key="show_received")
            
            with col2:
                date_from = st.date_input("Vencimento de:", value=None, key="receivable_from")
            
            with col3:
                date_to = st.date_input("Vencimento até:", value=None, key="receivable_to")
            
            # Query
            query = db.query(AccountReceivable).filter(AccountReceivable.client_id == client_id)
            
            if not show_received:
                query = query.filter(AccountReceivable.received == False)
            
            if date_from:
                query = query.filter(AccountReceivable.due_date >= date_from)
            
            if date_to:
                query = query.filter(AccountReceivable.due_date <= date_to)
            
            accounts = query.order_by(AccountReceivable.due_date).all()
            
            if accounts:
                # Alertas
                today = date.today()
                overdue = [a for a in accounts if a.due_date < today and not a.received]
                due_soon = [a for a in accounts if a.due_date >= today and a.due_date <= today + timedelta(days=7) and not a.received]
                
                if overdue:
                    st.error(f"⚠️ {len(overdue)} conta(s) atrasada(s)!")
                
                if due_soon:
                    st.info(f"💰 {len(due_soon)} recebimento(s) previsto(s) nos próximos 7 dias!")
                
                # Tabela
                account_data = []
                for account in accounts:
                    status = "✅ Recebida" if account.received else "⏳ Pendente"
                    
                    if not account.received and account.due_date < today:
                        status = "❌ Atrasada"
                    elif not account.received and account.due_date <= today + timedelta(days=7):
                        status = "💰 A receber"
                    
                    account_data.append({
                        'ID': account.id,
                        'Conta': account.account_name,
                        'CPF/CNPJ': format_cpf_cnpj(account.cpf_cnpj) if account.cpf_cnpj else '-',
                        'Vencimento': format_date(account.due_date),
                        'Valor': format_currency(account.value),
                        'Status': status,
                        'Recebimento': format_date(account.receipt_date) if account.receipt_date else '-'
                    })
                
                df = pd.DataFrame(account_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Estatísticas
                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total de Contas", len(accounts))
                
                with col2:
                    total_value = sum(a.value for a in accounts)
                    st.metric("Valor Total", format_currency(total_value))
                
                with col3:
                    pending_value = sum(a.value for a in accounts if not a.received)
                    st.metric("A Receber", format_currency(pending_value))
                
                with col4:
                    received_value = sum(a.value for a in accounts if a.received)
                    st.metric("Recebido", format_currency(received_value))
                
                st.markdown("---")
                
                # Marcar como recebida
                st.subheader("💵 Registrar Recebimento")
                
                unreceived_accounts = [a for a in accounts if not a.received]
                
                if unreceived_accounts:
                    selected_account_id = st.selectbox(
                        "Selecione a conta:",
                        options=[a.id for a in unreceived_accounts],
                        format_func=lambda x: next(f"{a.account_name} - {format_currency(a.value)} (Venc: {format_date(a.due_date)})" for a in unreceived_accounts if a.id == x),
                        key="receive_select"
                    )
                    
                    receipt_date = st.date_input("Data do recebimento:", value=date.today(), key="receipt_date")
                    
                    if st.button("✅ Marcar como Recebida", use_container_width=True):
                        account = db.query(AccountReceivable).filter(AccountReceivable.id == selected_account_id).first()
                        account.received = True
                        account.receipt_date = receipt_date
                        db.commit()
                        st.success("✅ Recebimento registrado!")
                        st.rerun()
                else:
                    st.info("ℹ️ Todas as contas foram recebidas!")
                
                st.markdown("---")
                
                # Editar/Excluir conta
                st.subheader("✏️ Editar/Excluir Conta")
                
                if accounts:
                    edit_account_id = st.selectbox(
                        "Selecione a conta para editar:",
                        options=[a.id for a in accounts],
                        format_func=lambda x: next(f"{a.account_name} - {format_currency(a.value)} (Venc: {format_date(a.due_date)})" for a in accounts if a.id == x),
                        key="edit_receivable_select"
                    )
                    
                    if edit_account_id:
                        account = db.query(AccountReceivable).filter(AccountReceivable.id == edit_account_id).first()
                        
                        with st.form("edit_receivable_form"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                edit_name = st.text_input("Nome da Conta *", value=account.account_name)
                                edit_cpf_cnpj = st.text_input("CPF/CNPJ", value=account.cpf_cnpj or '')
                            
                            with col2:
                                edit_due_date = st.date_input("Vencimento *", value=account.due_date)
                                edit_value = st.number_input("Valor *", value=float(account.value), min_value=0.0, step=10.0)
                            
                            col1, col2 = st.columns([1, 1])
                            
                            with col1:
                                submit_edit = st.form_submit_button("💾 Salvar", use_container_width=True)
                            
                            with col2:
                                delete_btn = st.form_submit_button("🗑️ Excluir", use_container_width=True)
                            
                            if submit_edit:
                                if edit_name and edit_value > 0:
                                    account.account_name = edit_name
                                    account.cpf_cnpj = edit_cpf_cnpj if edit_cpf_cnpj else None
                                    account.due_date = edit_due_date
                                    account.value = edit_value
                                    account.month_ref = edit_due_date.strftime('%Y-%m')
                                    db.commit()
                                    st.success("✅ Conta atualizada!")
                                    st.rerun()
                                else:
                                    st.error("❌ Preencha os campos obrigatórios.")
                            
                            if delete_btn:
                                db.delete(account)
                                db.commit()
                                st.success("✅ Conta excluída!")
                                st.rerun()
            
            else:
                st.info("ℹ️ Nenhuma conta a receber encontrada.")
        
        with subtab2:
            st.subheader("Cadastrar Nova Conta a Receber")
            
            with st.form("new_receivable_form"):
                account_name = st.text_input("Nome da Conta *", placeholder="Cliente, serviço, etc")
                cpf_cnpj = st.text_input("CPF/CNPJ", placeholder="000.000.000-00 ou 00.000.000/0000-00")
                due_date = st.date_input("Data de Vencimento *", value=date.today())
                value = st.number_input("Valor *", min_value=0.0, step=10.0)
                
                submit = st.form_submit_button("➕ Cadastrar", use_container_width=True)
                
                if submit:
                    if account_name and value > 0:
                        new_account = AccountReceivable(
                            client_id=client_id,
                            account_name=account_name,
                            cpf_cnpj=cpf_cnpj if cpf_cnpj else None,
                            due_date=due_date,
                            value=value,
                            month_ref=due_date.strftime('%Y-%m'),
                            received=False
                        )
                        
                        db.add(new_account)
                        db.commit()
                        st.success("✅ Conta cadastrada com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Preencha todos os campos obrigatórios.")

finally:
    db.close()

