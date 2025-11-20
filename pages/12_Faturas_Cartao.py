"""
Página de Gestão de Faturas de Cartão de Crédito
Permite visualizar, editar e excluir faturas de cartão importadas
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
from models.credit_card import CreditCardInvoice
from models.group import Group, Subgroup
from utils.formatters import format_currency, format_date
from utils.ui_components import show_client_selector
from sqlalchemy.orm import joinedload

st.set_page_config(page_title="Faturas de Cartão", page_icon="💳", layout="wide")

# Esconde o menu automático do Streamlit
from utils.hide_auto_menu import hide_streamlit_menu
hide_streamlit_menu()

AuthService.init_session_state()
AuthService.require_auth()

# Usa sidebar centralizada
from utils.sidebar import show_sidebar
show_sidebar()

st.title("💳 Faturas de Cartão de Crédito")

# Seletor de cliente no topo da página
client_id = show_client_selector()

if not client_id:
    st.warning("⚠️ Nenhum cliente disponível.")
    st.stop()

st.markdown("---")

# Tabs
tab1, tab2 = st.tabs(["📋 Lista de Faturas", "➕ Nova Fatura"])

db = SessionLocal()

try:
    # TAB 1: Lista de Faturas
    with tab1:
        st.subheader("Faturas de Cartão Cadastradas")
        
        # Filtros
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            date_from = st.date_input("Data de:", value=None, key="invoice_from")
        
        with col2:
            date_to = st.date_input("Data até:", value=None, key="invoice_to")
        
        with col3:
            card_brand_filter = st.multiselect(
                "Bandeira:",
                options=[],
                default=[],
                key="card_brand_filter"
            )
        
        with col4:
            search = st.text_input("🔍 Buscar", placeholder="Descrição ou estabelecimento...")
        
        # Query de faturas com joins para carregar grupos e subgrupos (evita N+1 queries)
        query = db.query(CreditCardInvoice).options(
            joinedload(CreditCardInvoice.group),
            joinedload(CreditCardInvoice.subgroup)
        ).filter(CreditCardInvoice.client_id == client_id)
        
        if date_from:
            query = query.filter(CreditCardInvoice.transaction_date >= date_from)
        
        if date_to:
            query = query.filter(CreditCardInvoice.transaction_date <= date_to)
        
        if card_brand_filter:
            query = query.filter(CreditCardInvoice.card_brand.in_(card_brand_filter))
        
        if search:
            query = query.filter(
                (CreditCardInvoice.description.contains(search)) |
                (CreditCardInvoice.establishment.contains(search))
            )
        
        invoices = query.order_by(CreditCardInvoice.transaction_date.desc()).limit(500).all()
        
        # Busca bandeiras únicas para o filtro
        if not card_brand_filter:
            all_invoices = db.query(CreditCardInvoice.card_brand).filter(
                CreditCardInvoice.client_id == client_id,
                CreditCardInvoice.card_brand.isnot(None)
            ).distinct().all()
            card_brands = [brand[0] for brand in all_invoices if brand[0]]
        else:
            card_brands = []
        
        if invoices:
            # Estatísticas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_value = sum(inv.value for inv in invoices)
                st.metric("💰 Valor Total", format_currency(total_value))
            
            with col2:
                total_count = len(invoices)
                st.metric("📊 Total de Faturas", total_count)
            
            with col3:
                avg_value = total_value / total_count if total_count > 0 else 0
                st.metric("📈 Valor Médio", format_currency(avg_value))
            
            with col4:
                # Conta parcelas
                parceladas = [inv for inv in invoices if inv.total_installments and inv.total_installments > 1]
                st.metric("🔢 Parceladas", len(parceladas))
            
            st.markdown("---")
            
            # Tabela de faturas
            invoice_data = []
            for inv in invoices:
                # Obtém nomes de grupo e subgrupo usando os relacionamentos carregados
                group_name = inv.group.name if inv.group else '-'
                subgroup_name = inv.subgroup.name if inv.subgroup else '-'
                
                # Formata parcela
                parcela_info = ""
                if inv.total_installments and inv.total_installments > 1:
                    parcela_info = f"{inv.installment_number}/{inv.total_installments}"
                
                invoice_data.append({
                    'ID': inv.id,
                    'Data': format_date(inv.transaction_date),
                    'Descrição': inv.description[:50] + '...' if len(inv.description) > 50 else inv.description,
                    'Estabelecimento': inv.establishment or '-',
                    'Valor': format_currency(inv.value),
                    'Bandeira': inv.card_brand or '-',
                    'Parcela': parcela_info or '-',
                    'Categoria': inv.category or '-',
                    'Grupo': group_name,
                    'Subgrupo': subgroup_name
                })
            
            df = pd.DataFrame(invoice_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.caption(f"Mostrando até 500 faturas. Total no filtro: {len(invoices)}")
            
            st.markdown("---")
            
            # Edição de fatura
            st.subheader("✏️ Editar/Excluir Fatura")
            
            selected_invoice_id = st.selectbox(
                "Selecione uma fatura:",
                options=[inv.id for inv in invoices],
                format_func=lambda x: next(
                    f"{format_date(inv.transaction_date)} - {inv.description[:30]} - {format_currency(inv.value)}" 
                    for inv in invoices if inv.id == x
                )
            )
            
            if selected_invoice_id:
                invoice = db.query(CreditCardInvoice).filter(CreditCardInvoice.id == selected_invoice_id).first()
                
                # Obtém grupos e subgrupos
                groups = db.query(Group).filter(Group.client_id == client_id).all()
                
                with st.form("edit_invoice_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_date = st.date_input("Data *", value=invoice.transaction_date)
                        edit_description = st.text_area("Descrição *", value=invoice.description)
                        edit_value = st.number_input("Valor *", value=float(invoice.value), min_value=0.0, step=10.0)
                        edit_establishment = st.text_input("Estabelecimento", value=invoice.establishment or '')
                        edit_card_brand = st.text_input("Bandeira do Cartão", value=invoice.card_brand or '')
                    
                    with col2:
                        edit_category = st.text_input("Categoria", value=invoice.category or '')
                        
                        col_parcela1, col_parcela2 = st.columns(2)
                        with col_parcela1:
                            edit_installment = st.number_input("Parcela Nº", value=invoice.installment_number or 1, min_value=1, step=1)
                        with col_parcela2:
                            edit_total_installments = st.number_input("Total de Parcelas", value=invoice.total_installments or 1, min_value=1, step=1)
                        
                        if groups:
                            group_options = [None] + groups
                            current_group_idx = 0
                            if invoice.group_id:
                                try:
                                    current_group_idx = [g.id if g else None for g in group_options].index(invoice.group_id)
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
                                    if invoice.subgroup_id:
                                        try:
                                            current_subgroup_idx = [sg.id if sg else None for sg in subgroup_options].index(invoice.subgroup_id)
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
                        if edit_description and edit_value > 0:
                            invoice.transaction_date = edit_date
                            invoice.description = edit_description
                            invoice.value = edit_value
                            invoice.establishment = edit_establishment if edit_establishment else None
                            invoice.card_brand = edit_card_brand if edit_card_brand else None
                            invoice.category = edit_category if edit_category else None
                            invoice.installment_number = int(edit_installment) if edit_installment > 0 else None
                            invoice.total_installments = int(edit_total_installments) if edit_total_installments > 0 else None
                            invoice.group_id = edit_group.id if edit_group else None
                            invoice.subgroup_id = edit_subgroup.id if edit_subgroup else None
                            
                            db.commit()
                            st.success("✅ Fatura atualizada!")
                            st.rerun()
                        else:
                            st.error("❌ Preencha os campos obrigatórios.")
                    
                    if delete:
                        db.delete(invoice)
                        db.commit()
                        st.success("✅ Fatura excluída!")
                        st.rerun()
        
        else:
            st.info("ℹ️ Nenhuma fatura de cartão encontrada com os filtros aplicados.")
            st.info("💡 Importe faturas de cartão na página de **Importação de Dados**.")
    
    # TAB 2: Nova Fatura
    with tab2:
        st.subheader("Cadastrar Nova Fatura de Cartão")
        
        # Obtém grupos e subgrupos
        groups = db.query(Group).filter(Group.client_id == client_id).all()
        
        with st.form("new_invoice_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_date = st.date_input("Data da Transação *", value=date.today())
                new_description = st.text_area("Descrição *", placeholder="Ex: Compra no estabelecimento X")
                new_value = st.number_input("Valor *", min_value=0.0, step=10.0, value=0.0)
                new_establishment = st.text_input("Estabelecimento", placeholder="Ex: Loja ABC")
                new_card_brand = st.text_input("Bandeira do Cartão", placeholder="Ex: Visa, Mastercard")
            
            with col2:
                new_category = st.text_input("Categoria", placeholder="Ex: Alimentação")
                
                col_parcela1, col_parcela2 = st.columns(2)
                with col_parcela1:
                    new_installment = st.number_input("Parcela Nº", value=1, min_value=1, step=1)
                with col_parcela2:
                    new_total_installments = st.number_input("Total de Parcelas", value=1, min_value=1, step=1)
                
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
            
            submit = st.form_submit_button("➕ Cadastrar Fatura", use_container_width=True)
            
            if submit:
                if new_description and new_value > 0:
                    new_invoice = CreditCardInvoice(
                        client_id=client_id,
                        transaction_date=new_date,
                        description=new_description,
                        value=new_value,
                        establishment=new_establishment if new_establishment else None,
                        card_brand=new_card_brand if new_card_brand else None,
                        category=new_category if new_category else None,
                        installment_number=int(new_installment) if new_installment > 1 or new_total_installments > 1 else None,
                        total_installments=int(new_total_installments) if new_total_installments > 1 else None,
                        group_id=new_group.id if new_group else None,
                        subgroup_id=new_subgroup.id if new_subgroup else None
                    )
                    
                    db.add(new_invoice)
                    db.commit()
                    st.success("✅ Fatura cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Preencha os campos obrigatórios (*).")

finally:
    db.close()

