"""
Página de Gestão de Aplicações Financeiras
Permite visualizar, editar e excluir aplicações financeiras importadas
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
from models.financial_investment import FinancialInvestment
from models.group import Group, Subgroup
from utils.formatters import format_currency, format_date
from utils.ui_components import show_client_selector
from sqlalchemy.orm import joinedload

st.set_page_config(page_title="Aplicações Financeiras", page_icon="📈", layout="wide")

AuthService.init_session_state()
AuthService.require_auth()

# Usa sidebar centralizada
from utils.sidebar import show_sidebar
show_sidebar()

st.title("📈 Aplicações Financeiras")

# Seletor de cliente no topo da página
client_id = show_client_selector()

if not client_id:
    st.warning("⚠️ Nenhum cliente disponível.")
    st.stop()

st.markdown("---")

# Tabs
tab1, tab2 = st.tabs(["📋 Lista de Aplicações", "➕ Nova Aplicação"])

db = SessionLocal()

try:
    # TAB 1: Lista de Aplicações
    with tab1:
        st.subheader("Aplicações Financeiras Cadastradas")
        
        # Filtros
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            date_from = st.date_input("Data de:", value=None, key="investment_from")
        
        with col2:
            date_to = st.date_input("Data até:", value=None, key="investment_to")
        
        with col3:
            investment_type_filter = st.multiselect(
                "Tipo de Investimento:",
                options=[],
                default=[],
                key="investment_type_filter"
            )
        
        with col4:
            search = st.text_input("🔍 Buscar", placeholder="Descrição ou instituição...")
        
        # Query de aplicações com joins para carregar grupos e subgrupos (evita N+1 queries)
        query = db.query(FinancialInvestment).options(
            joinedload(FinancialInvestment.group),
            joinedload(FinancialInvestment.subgroup)
        ).filter(FinancialInvestment.client_id == client_id)
        
        if date_from:
            query = query.filter(FinancialInvestment.date >= date_from)
        
        if date_to:
            query = query.filter(FinancialInvestment.date <= date_to)
        
        if investment_type_filter:
            query = query.filter(FinancialInvestment.investment_type.in_(investment_type_filter))
        
        if search:
            query = query.filter(
                (FinancialInvestment.description.contains(search)) |
                (FinancialInvestment.institution.contains(search))
            )
        
        investments = query.order_by(FinancialInvestment.date.desc()).limit(500).all()
        
        # Busca tipos únicos para o filtro
        if not investment_type_filter:
            all_investments = db.query(FinancialInvestment.investment_type).filter(
                FinancialInvestment.client_id == client_id,
                FinancialInvestment.investment_type.isnot(None)
            ).distinct().all()
            investment_types = [inv_type[0] for inv_type in all_investments if inv_type[0]]
        else:
            investment_types = []
        
        if investments:
            # Estatísticas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_applied = sum(inv.applied_value or 0 for inv in investments)
                st.metric("💰 Total Aplicado", format_currency(total_applied))
            
            with col2:
                total_redeemed = sum(inv.redeemed_value or 0 for inv in investments)
                st.metric("💸 Total Resgatado", format_currency(total_redeemed))
            
            with col3:
                total_yield = sum(inv.yield_value or 0 for inv in investments)
                st.metric("📊 Rendimento Total", format_currency(total_yield))
            
            with col4:
                # Saldo atual (último balance ou calculado)
                latest_balance = investments[0].balance if investments[0].balance else 0
                st.metric("💵 Saldo Atual", format_currency(latest_balance))
            
            st.markdown("---")
            
            # Tabela de aplicações
            investment_data = []
            for inv in investments:
                # Obtém nomes de grupo e subgrupo usando os relacionamentos carregados
                group_name = inv.group.name if inv.group else '-'
                subgroup_name = inv.subgroup.name if inv.subgroup else '-'
                
                # Determina valor da operação
                operation_value = inv.applied_value if inv.applied_value else (inv.redeemed_value or 0)
                operation_label = "Aplicado" if inv.applied_value else "Resgatado"
                
                investment_data.append({
                    'ID': inv.id,
                    'Data': format_date(inv.date),
                    'Tipo': inv.investment_type or '-',
                    'Instituição': inv.institution or '-',
                    'Operação': inv.operation_type or '-',
                    'Valor': format_currency(operation_value),
                    'Rendimento': format_currency(inv.yield_value) if inv.yield_value else '-',
                    'Saldo': format_currency(inv.balance) if inv.balance else '-',
                    'Descrição': inv.description[:50] + '...' if inv.description and len(inv.description) > 50 else (inv.description or '-'),
                    'Grupo': group_name,
                    'Subgrupo': subgroup_name
                })
            
            df = pd.DataFrame(investment_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.caption(f"Mostrando até 500 aplicações. Total no filtro: {len(investments)}")
            
            st.markdown("---")
            
            # Edição de aplicação
            st.subheader("✏️ Editar/Excluir Aplicação")
            
            selected_investment_id = st.selectbox(
                "Selecione uma aplicação:",
                options=[inv.id for inv in investments],
                format_func=lambda x: next(
                    f"{format_date(inv.date)} - {inv.investment_type or 'N/A'} - {format_currency(inv.applied_value or inv.redeemed_value or 0)}" 
                    for inv in investments if inv.id == x
                )
            )
            
            if selected_investment_id:
                investment = db.query(FinancialInvestment).filter(FinancialInvestment.id == selected_investment_id).first()
                
                # Obtém grupos e subgrupos
                groups = db.query(Group).filter(Group.client_id == client_id).all()
                
                with st.form("edit_investment_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_date = st.date_input("Data *", value=investment.date)
                        edit_investment_type = st.text_input("Tipo de Investimento", value=investment.investment_type or '')
                        edit_institution = st.text_input("Instituição", value=investment.institution or '')
                        edit_operation_type = st.selectbox(
                            "Tipo de Operação",
                            options=['aplicado', 'resgatado'],
                            index=0 if investment.operation_type == 'aplicado' else 1
                        )
                        edit_description = st.text_area("Descrição", value=investment.description or '')
                    
                    with col2:
                        edit_applied_value = st.number_input(
                            "Valor Aplicado", 
                            value=float(investment.applied_value) if investment.applied_value else 0.0, 
                            min_value=0.0, 
                            step=100.0
                        )
                        edit_redeemed_value = st.number_input(
                            "Valor Resgatado", 
                            value=float(investment.redeemed_value) if investment.redeemed_value else 0.0, 
                            min_value=0.0, 
                            step=100.0
                        )
                        edit_yield_value = st.number_input(
                            "Rendimento", 
                            value=float(investment.yield_value) if investment.yield_value else 0.0, 
                            min_value=0.0, 
                            step=10.0
                        )
                        edit_balance = st.number_input(
                            "Saldo", 
                            value=float(investment.balance) if investment.balance else 0.0, 
                            min_value=0.0, 
                            step=100.0
                        )
                        
                        if groups:
                            group_options = [None] + groups
                            current_group_idx = 0
                            if investment.group_id:
                                try:
                                    current_group_idx = [g.id if g else None for g in group_options].index(investment.group_id)
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
                                    if investment.subgroup_id:
                                        try:
                                            current_subgroup_idx = [sg.id if sg else None for sg in subgroup_options].index(investment.subgroup_id)
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
                        if edit_date:
                            investment.date = edit_date
                            investment.investment_type = edit_investment_type if edit_investment_type else None
                            investment.institution = edit_institution if edit_institution else None
                            investment.operation_type = edit_operation_type
                            investment.applied_value = edit_applied_value if edit_applied_value > 0 else None
                            investment.redeemed_value = edit_redeemed_value if edit_redeemed_value > 0 else None
                            investment.yield_value = edit_yield_value if edit_yield_value > 0 else None
                            investment.balance = edit_balance if edit_balance > 0 else None
                            investment.description = edit_description if edit_description else None
                            investment.group_id = edit_group.id if edit_group else None
                            investment.subgroup_id = edit_subgroup.id if edit_subgroup else None
                            
                            db.commit()
                            st.success("✅ Aplicação atualizada!")
                            st.rerun()
                        else:
                            st.error("❌ Preencha os campos obrigatórios.")
                    
                    if delete:
                        db.delete(investment)
                        db.commit()
                        st.success("✅ Aplicação excluída!")
                        st.rerun()
        
        else:
            st.info("ℹ️ Nenhuma aplicação financeira encontrada com os filtros aplicados.")
            st.info("💡 Importe aplicações financeiras na página de **Importação de Dados**.")
    
    # TAB 2: Nova Aplicação
    with tab2:
        st.subheader("Cadastrar Nova Aplicação Financeira")
        
        # Obtém grupos e subgrupos
        groups = db.query(Group).filter(Group.client_id == client_id).all()
        
        with st.form("new_investment_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_date = st.date_input("Data *", value=date.today())
                new_investment_type = st.text_input("Tipo de Investimento", placeholder="Ex: CDB, LCI, LCA, Tesouro")
                new_institution = st.text_input("Instituição", placeholder="Ex: Banco Inter, Nubank")
                new_operation_type = st.selectbox("Tipo de Operação *", options=['aplicado', 'resgatado'])
                new_description = st.text_area("Descrição", placeholder="Ex: Aplicação em CDB DI")
            
            with col2:
                new_applied_value = st.number_input("Valor Aplicado", min_value=0.0, step=100.0, value=0.0)
                new_redeemed_value = st.number_input("Valor Resgatado", min_value=0.0, step=100.0, value=0.0)
                new_yield_value = st.number_input("Rendimento", min_value=0.0, step=10.0, value=0.0)
                new_balance = st.number_input("Saldo", min_value=0.0, step=100.0, value=0.0)
                
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
            
            submit = st.form_submit_button("➕ Cadastrar Aplicação", use_container_width=True)
            
            if submit:
                if new_date and (new_applied_value > 0 or new_redeemed_value > 0):
                    new_investment = FinancialInvestment(
                        client_id=client_id,
                        date=new_date,
                        investment_type=new_investment_type if new_investment_type else None,
                        institution=new_institution if new_institution else None,
                        operation_type=new_operation_type,
                        applied_value=new_applied_value if new_applied_value > 0 else None,
                        redeemed_value=new_redeemed_value if new_redeemed_value > 0 else None,
                        yield_value=new_yield_value if new_yield_value > 0 else None,
                        balance=new_balance if new_balance > 0 else None,
                        description=new_description if new_description else None,
                        group_id=new_group.id if new_group else None,
                        subgroup_id=new_subgroup.id if new_subgroup else None
                    )
                    
                    db.add(new_investment)
                    db.commit()
                    st.success("✅ Aplicação cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Preencha os campos obrigatórios (*). Deve ter pelo menos um valor aplicado ou resgatado.")

finally:
    db.close()
