"""
Página de Gestão de Contratos e Eventos
"""
import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from models.client import Client
from models.contract import Contract
from utils.formatters import format_currency, format_date

st.set_page_config(page_title="Contratos", page_icon="📝", layout="wide")

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

st.title("📝 Gestão de Contratos e Eventos")
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

# Tabs
tab1, tab2 = st.tabs(["📋 Lista de Contratos", "➕ Novo Contrato"])

db = SessionLocal()

try:
    # TAB 1: Lista de Contratos
    with tab1:
        st.subheader("Contratos Cadastrados")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.multiselect(
                "Status:",
                options=['pendente', 'em_andamento', 'concluido', 'cancelado'],
                default=['pendente', 'em_andamento'],
                format_func=lambda x: {
                    'pendente': '⏳ Pendente',
                    'em_andamento': '▶️ Em Andamento',
                    'concluido': '✅ Concluído',
                    'cancelado': '❌ Cancelado'
                }[x]
            )
        
        with col2:
            date_from = st.date_input("Data do evento de:", value=None)
        
        with col3:
            date_to = st.date_input("Data do evento até:", value=None)
        
        # Query de contratos
        query = db.query(Contract).filter(Contract.client_id == client_id)
        
        if status_filter:
            query = query.filter(Contract.status.in_(status_filter))
        
        if date_from:
            query = query.filter(Contract.event_date >= date_from)
        
        if date_to:
            query = query.filter(Contract.event_date <= date_to)
        
        contracts = query.order_by(Contract.event_date.desc()).all()
        
        if contracts:
            # Exibe contratos
            contract_data = []
            for contract in contracts:
                status_emoji = {
                    'pendente': '⏳',
                    'em_andamento': '▶️',
                    'concluido': '✅',
                    'cancelado': '❌'
                }.get(contract.status, '❓')
                
                contract_data.append({
                    'ID': contract.id,
                    'Contratante': contract.contractor_name,
                    'Data Evento': format_date(contract.event_date),
                    'Valor Serviço': format_currency(contract.service_value),
                    'Valor Total': format_currency(contract.service_value + contract.displacement_value),
                    'Status': f"{status_emoji} {contract.status.title()}",
                    'Tipo': contract.event_type or '-',
                    'Convidados': contract.guests_count or '-'
                })
            
            df = pd.DataFrame(contract_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Estatísticas
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Contratos", len(contracts))
            
            with col2:
                total_value = sum(c.service_value + c.displacement_value for c in contracts)
                st.metric("Valor Total", format_currency(total_value))
            
            with col3:
                pending = len([c for c in contracts if c.status == 'pendente'])
                st.metric("Pendentes", pending)
            
            with col4:
                completed = len([c for c in contracts if c.status == 'concluido'])
                st.metric("Concluídos", completed)
            
            st.markdown("---")
            
            # Edição de contrato
            st.subheader("✏️ Editar Contrato")
            
            selected_contract_id = st.selectbox(
                "Selecione um contrato:",
                options=[c.id for c in contracts],
                format_func=lambda x: next(f"{c.contractor_name} - {format_date(c.event_date)}" for c in contracts if c.id == x)
            )
            
            if selected_contract_id:
                contract = db.query(Contract).filter(Contract.id == selected_contract_id).first()
                
                with st.form("edit_contract_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        contractor_name = st.text_input("Contratante *", value=contract.contractor_name)
                        contract_start = st.date_input("Início do Contrato *", value=contract.contract_start)
                        event_date = st.date_input("Data do Evento *", value=contract.event_date)
                        event_type = st.text_input("Tipo de Evento", value=contract.event_type or '')
                        service_sold = st.text_input("Serviço Vendido", value=contract.service_sold or '')
                    
                    with col2:
                        service_value = st.number_input("Valor do Serviço *", value=float(contract.service_value), min_value=0.0, step=100.0)
                        displacement_value = st.number_input("Valor Deslocamento", value=float(contract.displacement_value), min_value=0.0, step=50.0)
                        guests_count = st.number_input("Número de Convidados", value=contract.guests_count or 0, min_value=0, step=1)
                        status = st.selectbox("Status", 
                                            options=['pendente', 'em_andamento', 'concluido', 'cancelado'],
                                            index=['pendente', 'em_andamento', 'concluido', 'cancelado'].index(contract.status))
                        payment_terms = st.text_area("Forma de Pagamento", value=contract.payment_terms or '')
                    
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        submit = st.form_submit_button("💾 Salvar", use_container_width=True)
                    
                    with col2:
                        delete = st.form_submit_button("🗑️ Excluir", use_container_width=True)
                    
                    if submit:
                        if contractor_name and contract_start and event_date and service_value:
                            contract.contractor_name = contractor_name
                            contract.contract_start = contract_start
                            contract.event_date = event_date
                            contract.event_type = event_type
                            contract.service_sold = service_sold
                            contract.service_value = service_value
                            contract.displacement_value = displacement_value
                            contract.guests_count = guests_count if guests_count > 0 else None
                            contract.status = status
                            contract.payment_terms = payment_terms
                            
                            db.commit()
                            st.success("✅ Contrato atualizado com sucesso!")
                            st.rerun()
                        else:
                            st.error("❌ Preencha todos os campos obrigatórios.")
                    
                    if delete:
                        db.delete(contract)
                        db.commit()
                        st.success("✅ Contrato excluído com sucesso!")
                        st.rerun()
        
        else:
            st.info("ℹ️ Nenhum contrato encontrado com os filtros aplicados.")
    
    # TAB 2: Novo Contrato
    with tab2:
        st.subheader("Cadastrar Novo Contrato")
        
        with st.form("new_contract_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                contractor_name = st.text_input("Contratante *")
                contract_start = st.date_input("Início do Contrato *", value=date.today())
                event_date = st.date_input("Data do Evento *", value=date.today())
                event_type = st.text_input("Tipo de Evento", placeholder="Casamento, Aniversário, etc")
                service_sold = st.text_input("Serviço Vendido", placeholder="Buffet, Decoração, etc")
            
            with col2:
                service_value = st.number_input("Valor do Serviço *", min_value=0.0, step=100.0)
                displacement_value = st.number_input("Valor Deslocamento", min_value=0.0, step=50.0, value=0.0)
                guests_count = st.number_input("Número de Convidados", min_value=0, step=1, value=0)
                status = st.selectbox("Status", options=['pendente', 'em_andamento', 'concluido', 'cancelado'])
                payment_terms = st.text_area("Forma de Pagamento", placeholder="Ex: 50% entrada, 50% na data do evento")
            
            submit = st.form_submit_button("➕ Cadastrar Contrato", use_container_width=True)
            
            if submit:
                if contractor_name and contract_start and event_date and service_value:
                    new_contract = Contract(
                        client_id=client_id,
                        contractor_name=contractor_name,
                        contract_start=contract_start,
                        event_date=event_date,
                        event_type=event_type if event_type else None,
                        service_sold=service_sold if service_sold else None,
                        service_value=service_value,
                        displacement_value=displacement_value,
                        guests_count=guests_count if guests_count > 0 else None,
                        status=status,
                        payment_terms=payment_terms if payment_terms else None
                    )
                    
                    db.add(new_contract)
                    db.commit()
                    st.success("✅ Contrato cadastrado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Preencha todos os campos obrigatórios (*).")

finally:
    db.close()

