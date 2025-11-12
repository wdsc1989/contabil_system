"""
Página de Gestão Manual de Transações
Permite criar, editar e excluir transações manualmente
"""
import streamlit as st
import sys
import os
import pandas as pd
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from models.client import Client
from models.transaction import Transaction
from models.group import Group, Subgroup
from utils.formatters import format_currency, format_date
from utils.ui_components import show_client_selector, show_sidebar_navigation

st.set_page_config(page_title="Transações", page_icon="💳", layout="wide")

AuthService.init_session_state()
AuthService.require_auth()


show_sidebar_navigation()

st.title("💳 Gestão de Transações")

# Seletor de cliente no topo da página
client_id = show_client_selector()

if not client_id:
    st.warning("⚠️ Nenhum cliente disponível.")
    st.stop()

st.markdown("---")

# Tabs
tab1, tab2 = st.tabs(["📋 Lista de Transações", "➕ Nova Transação"])

db = SessionLocal()

try:
    # TAB 1: Lista de Transações
    with tab1:
        st.subheader("Transações Cadastradas")
        
        # Filtros
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            tipo_filter = st.multiselect(
                "Tipo:",
                options=['entrada', 'saida'],
                default=['entrada', 'saida'],
                format_func=lambda x: '💰 Entrada' if x == 'entrada' else '💸 Saída'
            )
        
        with col2:
            date_from = st.date_input("Data de:", value=None, key="trans_from")
        
        with col3:
            date_to = st.date_input("Data até:", value=None, key="trans_to")
        
        with col4:
            search = st.text_input("🔍 Buscar", placeholder="Descrição...")
        
        # Query de transações
        query = db.query(Transaction).filter(Transaction.client_id == client_id)
        
        if tipo_filter:
            query = query.filter(Transaction.type.in_(tipo_filter))
        
        if date_from:
            query = query.filter(Transaction.date >= date_from)
        
        if date_to:
            query = query.filter(Transaction.date <= date_to)
        
        if search:
            query = query.filter(Transaction.description.contains(search))
        
        transactions = query.order_by(Transaction.date.desc()).limit(100).all()
        
        if transactions:
            # Estatísticas
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_entradas = sum(t.value for t in transactions if t.type == 'entrada')
                st.metric("💰 Total Entradas", format_currency(total_entradas))
            
            with col2:
                total_saidas = sum(t.value for t in transactions if t.type == 'saida')
                st.metric("💸 Total Saídas", format_currency(total_saidas))
            
            with col3:
                saldo = total_entradas - total_saidas
                st.metric("📊 Saldo", format_currency(saldo))
            
            st.markdown("---")
            
            # Tabela de transações
            trans_data = []
            for trans in transactions:
                tipo_icon = '💰' if trans.type == 'entrada' else '💸'
                trans_data.append({
                    'ID': trans.id,
                    'Data': format_date(trans.date),
                    'Tipo': f"{tipo_icon} {trans.type.title()}",
                    'Descrição': trans.description[:50] + '...' if len(trans.description) > 50 else trans.description,
                    'Valor': format_currency(trans.value),
                    'Categoria': trans.category or '-',
                    'Origem': trans.imported_from or 'Manual'
                })
            
            df = pd.DataFrame(trans_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.caption(f"Mostrando últimas 100 transações. Total no filtro: {len(transactions)}")
            
            st.markdown("---")
            
            # Edição de transação
            st.subheader("✏️ Editar/Excluir Transação")
            
            selected_trans_id = st.selectbox(
                "Selecione uma transação:",
                options=[t.id for t in transactions],
                format_func=lambda x: next(
                    f"{format_date(t.date)} - {t.description[:30]} - {format_currency(t.value)}" 
                    for t in transactions if t.id == x
                )
            )
            
            if selected_trans_id:
                trans = db.query(Transaction).filter(Transaction.id == selected_trans_id).first()
                
                # Obtém grupos e subgrupos
                groups = db.query(Group).filter(Group.client_id == client_id).all()
                
                with st.form("edit_transaction_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_date = st.date_input("Data *", value=trans.date)
                        edit_description = st.text_area("Descrição *", value=trans.description)
                        edit_value = st.number_input("Valor *", value=float(trans.value), min_value=0.0, step=10.0)
                        edit_type = st.selectbox(
                            "Tipo *",
                            options=['entrada', 'saida'],
                            index=['entrada', 'saida'].index(trans.type)
                        )
                    
                    with col2:
                        edit_category = st.text_input("Categoria", value=trans.category or '')
                        
                        if groups:
                            group_options = [None] + groups
                            current_group_idx = 0
                            if trans.group_id:
                                try:
                                    current_group_idx = [g.id if g else None for g in group_options].index(trans.group_id)
                                except:
                                    pass
                            
                            edit_group = st.selectbox(
                                "Grupo",
                                options=group_options,
                                index=current_group_idx,
                                format_func=lambda x: "Nenhum" if x is None else x.name
                            )
                            
                            if edit_group:
                                subgroups = db.query(Subgroup).filter(Subgroup.group_id == edit_group.id).all()
                                if subgroups:
                                    subgroup_options = [None] + subgroups
                                    current_subgroup_idx = 0
                                    if trans.subgroup_id:
                                        try:
                                            current_subgroup_idx = [sg.id if sg else None for sg in subgroup_options].index(trans.subgroup_id)
                                        except:
                                            pass
                                    
                                    edit_subgroup = st.selectbox(
                                        "Subgrupo",
                                        options=subgroup_options,
                                        index=current_subgroup_idx,
                                        format_func=lambda x: "Nenhum" if x is None else x.name
                                    )
                                else:
                                    edit_subgroup = None
                            else:
                                edit_subgroup = None
                        else:
                            edit_group = None
                            edit_subgroup = None
                        
                        edit_account = st.text_input("Conta", value=trans.account or '')
                    
                    col1, col2, col3 = st.columns([1, 1, 2])
                    
                    with col1:
                        submit = st.form_submit_button("💾 Salvar", use_container_width=True)
                    
                    with col2:
                        delete = st.form_submit_button("🗑️ Excluir", use_container_width=True)
                    
                    if submit:
                        if edit_description and edit_value > 0:
                            trans.date = edit_date
                            trans.description = edit_description
                            trans.value = edit_value
                            trans.type = edit_type
                            trans.category = edit_category if edit_category else None
                            trans.group_id = edit_group.id if edit_group else None
                            trans.subgroup_id = edit_subgroup.id if edit_subgroup else None
                            trans.account = edit_account if edit_account else None
                            
                            db.commit()
                            st.success("✅ Transação atualizada!")
                            st.rerun()
                        else:
                            st.error("❌ Preencha os campos obrigatórios.")
                    
                    if delete:
                        db.delete(trans)
                        db.commit()
                        st.success("✅ Transação excluída!")
                        st.rerun()
        
        else:
            st.info("ℹ️ Nenhuma transação encontrada com os filtros aplicados.")
    
    # TAB 2: Nova Transação
    with tab2:
        st.subheader("Cadastrar Nova Transação")
        
        # Obtém grupos e subgrupos
        groups = db.query(Group).filter(Group.client_id == client_id).all()
        
        with st.form("new_transaction_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_date = st.date_input("Data *", value=date.today())
                new_description = st.text_area("Descrição *", placeholder="Ex: Pagamento de fornecedor")
                new_value = st.number_input("Valor *", min_value=0.0, step=10.0, value=0.0)
                new_type = st.selectbox("Tipo *", options=['entrada', 'saida'])
            
            with col2:
                new_category = st.text_input("Categoria", placeholder="Ex: Despesa Operacional")
                
                if groups:
                    new_group = st.selectbox(
                        "Grupo",
                        options=[None] + groups,
                        format_func=lambda x: "Nenhum" if x is None else x.name
                    )
                    
                    if new_group:
                        subgroups = db.query(Subgroup).filter(Subgroup.group_id == new_group.id).all()
                        if subgroups:
                            new_subgroup = st.selectbox(
                                "Subgrupo",
                                options=[None] + subgroups,
                                format_func=lambda x: "Nenhum" if x is None else x.name
                            )
                        else:
                            new_subgroup = None
                            st.info("ℹ️ Este grupo não tem subgrupos.")
                    else:
                        new_subgroup = None
                else:
                    new_group = None
                    new_subgroup = None
                    st.info("ℹ️ Crie grupos na página de Administração.")
                
                new_account = st.text_input("Conta", placeholder="Ex: Banco Itaú")
            
            submit = st.form_submit_button("➕ Cadastrar Transação", use_container_width=True)
            
            if submit:
                if new_description and new_value > 0:
                    new_transaction = Transaction(
                        client_id=client_id,
                        date=new_date,
                        description=new_description,
                        value=new_value,
                        type=new_type,
                        category=new_category if new_category else None,
                        group_id=new_group.id if new_group else None,
                        subgroup_id=new_subgroup.id if new_subgroup else None,
                        account=new_account if new_account else None,
                        document_type='manual',
                        imported_from='manual'
                    )
                    
                    db.add(new_transaction)
                    db.commit()
                    st.success("✅ Transação cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Preencha os campos obrigatórios (*).")

finally:
    db.close()

