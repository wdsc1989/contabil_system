"""
Página de Gestão de Controle de Estoque
Permite visualizar, editar e excluir movimentações de estoque importadas
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
from models.inventory import Inventory
from models.group import Group, Subgroup
from utils.formatters import format_currency, format_date
from utils.ui_components import show_client_selector
from sqlalchemy.orm import joinedload

st.set_page_config(page_title="Estoque", page_icon="📦", layout="wide")

AuthService.init_session_state()
AuthService.require_auth()

# Usa sidebar centralizada
from utils.sidebar import show_sidebar
show_sidebar()

st.title("📦 Controle de Estoque")

# Seletor de cliente no topo da página
client_id = show_client_selector()

if not client_id:
    st.warning("⚠️ Nenhum cliente disponível.")
    st.stop()

st.markdown("---")

# Tabs
tab1, tab2 = st.tabs(["📋 Lista de Movimentações", "➕ Nova Movimentação"])

db = SessionLocal()

try:
    # TAB 1: Lista de Movimentações
    with tab1:
        st.subheader("Movimentações de Estoque Cadastradas")
        
        # Filtros
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            date_from = st.date_input("Data de:", value=None, key="inventory_from")
        
        with col2:
            date_to = st.date_input("Data até:", value=None, key="inventory_to")
        
        with col3:
            movement_type_filter = st.multiselect(
                "Tipo de Movimento:",
                options=['entrada', 'saida'],
                default=[],
                key="inventory_movement_type_filter"
            )
        
        with col4:
            search = st.text_input("🔍 Buscar", placeholder="Produto ou descrição...")
        
        # Query de movimentações com joins para carregar grupos e subgrupos (evita N+1 queries)
        query = db.query(Inventory).options(
            joinedload(Inventory.group),
            joinedload(Inventory.subgroup)
        ).filter(Inventory.client_id == client_id)
        
        if date_from:
            query = query.filter(Inventory.movement_date >= date_from)
        
        if date_to:
            query = query.filter(Inventory.movement_date <= date_to)
        
        if movement_type_filter:
            query = query.filter(Inventory.movement_type.in_(movement_type_filter))
        
        if search:
            query = query.filter(
                (Inventory.product_name.contains(search)) |
                (Inventory.description.contains(search))
            )
        
        movements = query.order_by(Inventory.movement_date.desc()).limit(500).all()
        
        if movements:
            # Estatísticas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_products = len(set(mov.product_name for mov in movements))
                st.metric("📦 Total de Produtos", total_products)
            
            with col2:
                total_value = sum(mov.total_value for mov in movements)
                st.metric("💰 Valor Total", format_currency(total_value))
            
            with col3:
                entradas = [mov for mov in movements if mov.movement_type == 'entrada']
                total_entradas = sum(mov.total_value for mov in entradas)
                st.metric("📥 Total Entradas", format_currency(total_entradas))
            
            with col4:
                saidas = [mov for mov in movements if mov.movement_type == 'saida']
                total_saidas = sum(mov.total_value for mov in saidas)
                st.metric("📤 Total Saídas", format_currency(total_saidas))
            
            st.markdown("---")
            
            # Tabela de movimentações
            movement_data = []
            for mov in movements:
                # Obtém nomes de grupo e subgrupo usando os relacionamentos carregados
                group_name = mov.group.name if mov.group else '-'
                subgroup_name = mov.subgroup.name if mov.subgroup else '-'
                
                tipo_icon = '📥' if mov.movement_type == 'entrada' else '📤'
                
                movement_data.append({
                    'ID': mov.id,
                    'Data': format_date(mov.movement_date),
                    'Tipo': f"{tipo_icon} {mov.movement_type.title()}",
                    'Produto': mov.product_name,
                    'Quantidade': mov.quantity,
                    'Valor Unit.': format_currency(mov.unit_value),
                    'Valor Total': format_currency(mov.total_value),
                    'Descrição': mov.description[:50] + '...' if mov.description and len(mov.description) > 50 else (mov.description or '-'),
                    'Grupo': group_name,
                    'Subgrupo': subgroup_name
                })
            
            df = pd.DataFrame(movement_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.caption(f"Mostrando até 500 movimentações. Total no filtro: {len(movements)}")
            
            st.markdown("---")
            
            # Edição de movimentação
            st.subheader("✏️ Editar/Excluir Movimentação")
            
            selected_movement_id = st.selectbox(
                "Selecione uma movimentação:",
                options=[mov.id for mov in movements],
                format_func=lambda x: next(
                    f"{format_date(mov.movement_date)} - {mov.product_name} - {format_currency(mov.total_value)}" 
                    for mov in movements if mov.id == x
                )
            )
            
            if selected_movement_id:
                movement = db.query(Inventory).filter(Inventory.id == selected_movement_id).first()
                
                # Obtém grupos e subgrupos
                groups = db.query(Group).filter(Group.client_id == client_id).all()
                
                with st.form("edit_movement_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_date = st.date_input("Data *", value=movement.movement_date)
                        edit_product_name = st.text_input("Produto *", value=movement.product_name)
                        edit_quantity = st.number_input("Quantidade *", value=float(movement.quantity), min_value=0.0, step=1.0)
                        edit_unit_value = st.number_input("Valor Unitário *", value=float(movement.unit_value), min_value=0.0, step=1.0)
                        edit_description = st.text_area("Descrição", value=movement.description or '')
                    
                    with col2:
                        edit_movement_type = st.selectbox(
                            "Tipo de Movimento *",
                            options=['entrada', 'saida'],
                            index=0 if movement.movement_type == 'entrada' else 1
                        )
                        
                        # Calcula valor total automaticamente
                        calculated_total = edit_quantity * edit_unit_value
                        st.info(f"💵 Valor Total: {format_currency(calculated_total)}")
                        
                        if groups:
                            group_options = [None] + groups
                            current_group_idx = 0
                            if movement.group_id:
                                try:
                                    current_group_idx = [g.id if g else None for g in group_options].index(movement.group_id)
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
                                    if movement.subgroup_id:
                                        try:
                                            current_subgroup_idx = [sg.id if sg else None for sg in subgroup_options].index(movement.subgroup_id)
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
                        if edit_date and edit_product_name and edit_quantity > 0 and edit_unit_value > 0:
                            calculated_total = edit_quantity * edit_unit_value
                            movement.movement_date = edit_date
                            movement.product_name = edit_product_name
                            movement.quantity = edit_quantity
                            movement.unit_value = edit_unit_value
                            movement.total_value = calculated_total
                            movement.movement_type = edit_movement_type
                            movement.description = edit_description if edit_description else None
                            movement.group_id = edit_group.id if edit_group else None
                            movement.subgroup_id = edit_subgroup.id if edit_subgroup else None
                            
                            db.commit()
                            st.success("✅ Movimentação atualizada!")
                            st.rerun()
                        else:
                            st.error("❌ Preencha os campos obrigatórios.")
                    
                    if delete:
                        db.delete(movement)
                        db.commit()
                        st.success("✅ Movimentação excluída!")
                        st.rerun()
        
        else:
            st.info("ℹ️ Nenhuma movimentação de estoque encontrada com os filtros aplicados.")
            st.info("💡 Importe movimentações de estoque na página de **Importação de Dados**.")
    
    # TAB 2: Nova Movimentação
    with tab2:
        st.subheader("Cadastrar Nova Movimentação de Estoque")
        
        # Obtém grupos e subgrupos
        groups = db.query(Group).filter(Group.client_id == client_id).all()
        
        with st.form("new_movement_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_date = st.date_input("Data *", value=date.today())
                new_product_name = st.text_input("Produto *", placeholder="Ex: Produto X")
                new_quantity = st.number_input("Quantidade *", min_value=0.0, step=1.0, value=0.0)
                new_unit_value = st.number_input("Valor Unitário *", min_value=0.0, step=1.0, value=0.0)
                new_description = st.text_area("Descrição", placeholder="Ex: Compra de fornecedor")
            
            with col2:
                new_movement_type = st.selectbox("Tipo de Movimento *", options=['entrada', 'saida'])
                
                # Calcula valor total automaticamente
                calculated_total = new_quantity * new_unit_value
                st.info(f"💵 Valor Total: {format_currency(calculated_total)}")
                
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
            
            submit = st.form_submit_button("➕ Cadastrar Movimentação", use_container_width=True)
            
            if submit:
                if new_date and new_product_name and new_quantity > 0 and new_unit_value > 0:
                    calculated_total = new_quantity * new_unit_value
                    new_movement = Inventory(
                        client_id=client_id,
                        movement_date=new_date,
                        product_name=new_product_name,
                        quantity=new_quantity,
                        unit_value=new_unit_value,
                        total_value=calculated_total,
                        movement_type=new_movement_type,
                        description=new_description if new_description else None,
                        group_id=new_group.id if new_group else None,
                        subgroup_id=new_subgroup.id if new_subgroup else None
                    )
                    
                    db.add(new_movement)
                    db.commit()
                    st.success("✅ Movimentação cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Preencha os campos obrigatórios (*).")

finally:
    db.close()

