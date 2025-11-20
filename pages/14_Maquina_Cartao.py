"""
Página de Gestão de Extratos de Máquina de Cartão
Permite visualizar, editar e excluir extratos de máquina de cartão importados
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
from models.card_machine import CardMachineStatement
from models.group import Group, Subgroup
from utils.formatters import format_currency, format_date
from utils.ui_components import show_client_selector, show_sidebar_navigation
from sqlalchemy.orm import joinedload

st.set_page_config(page_title="Máquina de Cartão", page_icon="🏪", layout="wide")

AuthService.init_session_state()
AuthService.require_auth()

show_sidebar_navigation()

st.title("🏪 Extratos de Máquina de Cartão")

# Seletor de cliente no topo da página
client_id = show_client_selector()

if not client_id:
    st.warning("⚠️ Nenhum cliente disponível.")
    st.stop()

st.markdown("---")

# Tabs
tab1, tab2 = st.tabs(["📋 Lista de Extratos", "➕ Novo Extrato"])

db = SessionLocal()

try:
    # TAB 1: Lista de Extratos
    with tab1:
        st.subheader("Extratos de Máquina de Cartão Cadastrados")
        
        # Filtros
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            date_from = st.date_input("Data de:", value=None, key="machine_from")
        
        with col2:
            date_to = st.date_input("Data até:", value=None, key="machine_to")
        
        with col3:
            card_brand_filter = st.multiselect(
                "Bandeira:",
                options=[],
                default=[],
                key="machine_card_brand_filter"
            )
        
        with col4:
            transaction_type_filter = st.multiselect(
                "Tipo:",
                options=['debito', 'credito'],
                default=[],
                key="machine_transaction_type_filter"
            )
        
        # Query de extratos com joins para carregar grupos e subgrupos (evita N+1 queries)
        query = db.query(CardMachineStatement).options(
            joinedload(CardMachineStatement.group),
            joinedload(CardMachineStatement.subgroup)
        ).filter(CardMachineStatement.client_id == client_id)
        
        if date_from:
            query = query.filter(CardMachineStatement.date >= date_from)
        
        if date_to:
            query = query.filter(CardMachineStatement.date <= date_to)
        
        if card_brand_filter:
            query = query.filter(CardMachineStatement.card_brand.in_(card_brand_filter))
        
        if transaction_type_filter:
            query = query.filter(CardMachineStatement.transaction_type.in_(transaction_type_filter))
        
        statements = query.order_by(CardMachineStatement.date.desc()).limit(500).all()
        
        # Busca bandeiras únicas para o filtro
        if not card_brand_filter:
            all_statements = db.query(CardMachineStatement.card_brand).filter(
                CardMachineStatement.client_id == client_id,
                CardMachineStatement.card_brand.isnot(None)
            ).distinct().all()
            card_brands = [brand[0] for brand in all_statements if brand[0]]
        else:
            card_brands = []
        
        if statements:
            # Estatísticas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_gross = sum(stmt.gross_value for stmt in statements)
                st.metric("💰 Valor Bruto Total", format_currency(total_gross))
            
            with col2:
                total_fees = sum(stmt.fee or 0 for stmt in statements)
                st.metric("💸 Taxas Total", format_currency(total_fees))
            
            with col3:
                total_net = sum(stmt.net_value for stmt in statements)
                st.metric("💵 Valor Líquido Total", format_currency(total_net))
            
            with col4:
                total_count = len(statements)
                st.metric("📊 Total de Transações", total_count)
            
            st.markdown("---")
            
            # Tabela de extratos
            statement_data = []
            for stmt in statements:
                # Obtém nomes de grupo e subgrupo usando os relacionamentos carregados
                group_name = stmt.group.name if stmt.group else '-'
                subgroup_name = stmt.subgroup.name if stmt.subgroup else '-'
                
                statement_data.append({
                    'ID': stmt.id,
                    'Data': format_date(stmt.date),
                    'Valor Bruto': format_currency(stmt.gross_value),
                    'Taxa': format_currency(stmt.fee) if stmt.fee else '-',
                    'Valor Líquido': format_currency(stmt.net_value),
                    'Bandeira': stmt.card_brand or '-',
                    'Tipo': stmt.transaction_type or '-',
                    'Descrição': stmt.description[:50] + '...' if stmt.description and len(stmt.description) > 50 else (stmt.description or '-'),
                    'Grupo': group_name,
                    'Subgrupo': subgroup_name
                })
            
            df = pd.DataFrame(statement_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.caption(f"Mostrando até 500 extratos. Total no filtro: {len(statements)}")
            
            st.markdown("---")
            
            # Edição de extrato
            st.subheader("✏️ Editar/Excluir Extrato")
            
            selected_statement_id = st.selectbox(
                "Selecione um extrato:",
                options=[stmt.id for stmt in statements],
                format_func=lambda x: next(
                    f"{format_date(stmt.date)} - {format_currency(stmt.net_value)} - {stmt.transaction_type or 'N/A'}" 
                    for stmt in statements if stmt.id == x
                )
            )
            
            if selected_statement_id:
                statement = db.query(CardMachineStatement).filter(CardMachineStatement.id == selected_statement_id).first()
                
                # Obtém grupos e subgrupos
                groups = db.query(Group).filter(Group.client_id == client_id).all()
                
                with st.form("edit_statement_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_date = st.date_input("Data *", value=statement.date)
                        edit_gross_value = st.number_input("Valor Bruto *", value=float(statement.gross_value), min_value=0.0, step=10.0)
                        edit_fee = st.number_input("Taxa", value=float(statement.fee) if statement.fee else 0.0, min_value=0.0, step=1.0)
                        edit_net_value = st.number_input("Valor Líquido *", value=float(statement.net_value), min_value=0.0, step=10.0)
                        edit_description = st.text_area("Descrição", value=statement.description or '')
                    
                    with col2:
                        edit_card_brand = st.text_input("Bandeira do Cartão", value=statement.card_brand or '')
                        edit_transaction_type = st.selectbox(
                            "Tipo de Transação",
                            options=['debito', 'credito'],
                            index=0 if statement.transaction_type == 'debito' else 1
                        )
                        
                        if groups:
                            group_options = [None] + groups
                            current_group_idx = 0
                            if statement.group_id:
                                try:
                                    current_group_idx = [g.id if g else None for g in group_options].index(statement.group_id)
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
                                    if statement.subgroup_id:
                                        try:
                                            current_subgroup_idx = [sg.id if sg else None for sg in subgroup_options].index(statement.subgroup_id)
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
                    
                    col1, col2, col3 = st.columns([1, 1, 2])
                    
                    with col1:
                        submit = st.form_submit_button("💾 Salvar", use_container_width=True)
                    
                    with col2:
                        delete = st.form_submit_button("🗑️ Excluir", use_container_width=True)
                    
                    if submit:
                        if edit_date and edit_gross_value > 0 and edit_net_value > 0:
                            statement.date = edit_date
                            statement.gross_value = edit_gross_value
                            statement.fee = edit_fee if edit_fee > 0 else None
                            statement.net_value = edit_net_value
                            statement.card_brand = edit_card_brand if edit_card_brand else None
                            statement.transaction_type = edit_transaction_type
                            statement.description = edit_description if edit_description else None
                            statement.group_id = edit_group.id if edit_group else None
                            statement.subgroup_id = edit_subgroup.id if edit_subgroup else None
                            
                            db.commit()
                            st.success("✅ Extrato atualizado!")
                            st.rerun()
                        else:
                            st.error("❌ Preencha os campos obrigatórios.")
                    
                    if delete:
                        db.delete(statement)
                        db.commit()
                        st.success("✅ Extrato excluído!")
                        st.rerun()
        
        else:
            st.info("ℹ️ Nenhum extrato de máquina de cartão encontrado com os filtros aplicados.")
            st.info("💡 Importe extratos de máquina de cartão na página de **Importação de Dados**.")
    
    # TAB 2: Novo Extrato
    with tab2:
        st.subheader("Cadastrar Novo Extrato de Máquina de Cartão")
        
        # Obtém grupos e subgrupos
        groups = db.query(Group).filter(Group.client_id == client_id).all()
        
        with st.form("new_statement_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_date = st.date_input("Data *", value=date.today())
                new_gross_value = st.number_input("Valor Bruto *", min_value=0.0, step=10.0, value=0.0)
                new_fee = st.number_input("Taxa", min_value=0.0, step=1.0, value=0.0)
                new_net_value = st.number_input("Valor Líquido *", min_value=0.0, step=10.0, value=0.0)
                new_description = st.text_area("Descrição", placeholder="Ex: Vendas do dia")
            
            with col2:
                new_card_brand = st.text_input("Bandeira do Cartão", placeholder="Ex: Visa, Mastercard, Elo")
                new_transaction_type = st.selectbox("Tipo de Transação *", options=['debito', 'credito'])
                
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
            
            submit = st.form_submit_button("➕ Cadastrar Extrato", use_container_width=True)
            
            if submit:
                if new_date and new_gross_value > 0 and new_net_value > 0:
                    new_statement = CardMachineStatement(
                        client_id=client_id,
                        date=new_date,
                        gross_value=new_gross_value,
                        fee=new_fee if new_fee > 0 else None,
                        net_value=new_net_value,
                        card_brand=new_card_brand if new_card_brand else None,
                        transaction_type=new_transaction_type,
                        description=new_description if new_description else None,
                        group_id=new_group.id if new_group else None,
                        subgroup_id=new_subgroup.id if new_subgroup else None
                    )
                    
                    db.add(new_statement)
                    db.commit()
                    st.success("✅ Extrato cadastrado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Preencha os campos obrigatórios (*).")

finally:
    db.close()
