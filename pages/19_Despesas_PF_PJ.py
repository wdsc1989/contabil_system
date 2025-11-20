"""
Relatório de Despesas CPF vs CNPJ
Separa despesas pessoais (CPF) de empresariais (CNPJ) e classifica em fixas/variáveis
"""
import streamlit as st
import sys
import os
import pandas as pd
import plotly.graph_objects as go
from datetime import date
from dateutil.relativedelta import relativedelta
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from models.client import Client
from models.account import AccountPayable
from models.transaction import Transaction
from utils.formatters import format_currency, format_date

st.set_page_config(page_title="Despesas PF vs PJ", page_icon="💼", layout="wide")

from utils.hide_auto_menu import hide_streamlit_menu
hide_streamlit_menu()

AuthService.init_session_state()
AuthService.require_auth()

from utils.sidebar import show_sidebar
show_sidebar()

st.title("💼 Despesas Pessoa Física vs Pessoa Jurídica")
st.markdown("Controle de despesas pessoais (CPF) e empresariais (CNPJ) com alertas MEI")
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

# Período
st.subheader("📅 Período")
col1, col2, col3 = st.columns(3)

with col1:
    period_type = st.selectbox(
        "Tipo:",
        options=['Mês Atual', 'Últimos 3 meses', 'Últimos 6 meses', 'Último ano', 'Personalizado']
    )

today = date.today()

if period_type == 'Mês Atual':
    start_date = date(today.year, today.month, 1)
    end_date = today
elif period_type == 'Últimos 3 meses':
    start_date = today - relativedelta(months=3)
    end_date = today
elif period_type == 'Últimos 6 meses':
    start_date = today - relativedelta(months=6)
    end_date = today
elif period_type == 'Último ano':
    start_date = today - relativedelta(years=1)
    end_date = today
else:
    with col2:
        start_date = st.date_input("Data inicial:", value=today - relativedelta(months=3))
    with col3:
        end_date = st.date_input("Data final:", value=today)

st.markdown("---")

db = SessionLocal()
try:
    # Busca contas a pagar
    contas = db.query(AccountPayable).filter(
        AccountPayable.client_id == client_id,
        AccountPayable.payment_date >= start_date if AccountPayable.paid else AccountPayable.due_date >= start_date,
        AccountPayable.payment_date <= end_date if AccountPayable.paid else AccountPayable.due_date <= end_date
    ).all()
    
    # Classifica CPF vs CNPJ
    despesas_cpf = []
    despesas_cnpj = []
    despesas_sem_classificacao = []
    
    for conta in contas:
        if conta.cpf_cnpj:
            # Remove formatação
            doc_limpo = ''.join(filter(str.isdigit, conta.cpf_cnpj))
            
            if len(doc_limpo) == 11:  # CPF
                despesas_cpf.append(conta)
            elif len(doc_limpo) == 14:  # CNPJ
                despesas_cnpj.append(conta)
            else:
                despesas_sem_classificacao.append(conta)
        else:
            despesas_sem_classificacao.append(conta)
    
    total_cpf = sum(c.value for c in despesas_cpf)
    total_cnpj = sum(c.value for c in despesas_cnpj)
    total_sem = sum(c.value for c in despesas_sem_classificacao)
    total_geral = total_cpf + total_cnpj + total_sem
    
    # KPIs
    st.subheader("📊 Resumo de Despesas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        perc_cpf = (total_cpf / total_geral * 100) if total_geral > 0 else 0
        st.metric(
            "👤 Despesas CPF",
            format_currency(total_cpf),
            delta=f"{perc_cpf:.1f}%"
        )
        st.caption(f"{len(despesas_cpf)} conta(s)")
    
    with col2:
        perc_cnpj = (total_cnpj / total_geral * 100) if total_geral > 0 else 0
        st.metric(
            "🏢 Despesas CNPJ",
            format_currency(total_cnpj),
            delta=f"{perc_cnpj:.1f}%"
        )
        st.caption(f"{len(despesas_cnpj)} conta(s)")
    
    with col3:
        st.metric(
            "❓ Sem Classificação",
            format_currency(total_sem),
            help="Contas sem CPF/CNPJ informado"
        )
        st.caption(f"{len(despesas_sem_classificacao)} conta(s)")
    
    with col4:
        st.metric("💵 Total Geral", format_currency(total_geral))
    
    st.markdown("---")
    
    # Gráfico CPF vs CNPJ
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Distribuição CPF vs CNPJ")
        
        labels = []
        values = []
        colors = []
        
        if total_cpf > 0:
            labels.append('Despesas CPF (Pessoais)')
            values.append(total_cpf)
            colors.append('#e74c3c')
        
        if total_cnpj > 0:
            labels.append('Despesas CNPJ (Empresariais)')
            values.append(total_cnpj)
            colors.append('#3498db')
        
        if total_sem > 0:
            labels.append('Sem Classificação')
            values.append(total_sem)
            colors.append('#95a5a6')
        
        if labels:
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors,
                hole=0.4,
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>%{value:,.2f} R$<br>%{percent}<extra></extra>'
            )])
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("💡 Alertas e Recomendações")
        
        # Alerta MEI
        if client.tipo_empresa and 'MEI' in client.tipo_empresa.upper():
            limite_mei_anual = 81000  # Limite MEI 2024/2025
            meses_periodo = ((end_date.year - start_date.year) * 12 + end_date.month - start_date.month)
            
            if meses_periodo > 0:
                faturamento_projetado_anual = (total_cnpj / meses_periodo) * 12
                
                if faturamento_projetado_anual > limite_mei_anual:
                    st.error(f"🔴 RISCO DE DESENQUADRAMENTO MEI!")
                    st.markdown(f"Projeção anual: **{format_currency(faturamento_projetado_anual)}**")
                    st.markdown(f"Limite MEI: **{format_currency(limite_mei_anual)}**")
                    st.markdown("**Ação:** Considerar migrar para ME ou EIRELI")
                elif faturamento_projetado_anual > limite_mei_anual * 0.8:
                    st.warning(f"⚠️ Atenção: Próximo do limite MEI")
                    st.markdown(f"Projeção: {format_currency(faturamento_projetado_anual)}")
                    st.markdown(f"Uso: {(faturamento_projetado_anual/limite_mei_anual*100):.1f}% do limite")
                else:
                    st.success(f"✅ MEI dentro do limite")
                    margem = limite_mei_anual - faturamento_projetado_anual
                    st.markdown(f"Margem: {format_currency(margem)}")
        
        # Otimização fiscal
        if total_cpf > total_cnpj * 0.3:
            st.info("💡 Otimização Fiscal")
            st.markdown("Despesas pessoais representam >30% das empresariais")
            st.markdown("**Sugestão:** Revisar se algumas despesas PF podem ser reclassificadas como PJ")
    
    st.markdown("---")
    
    # Evolução Mensal
    st.subheader("📈 Evolução Mensal CPF vs CNPJ")
    
    # Agrupa por mês
    cpf_por_mes = defaultdict(float)
    cnpj_por_mes = defaultdict(float)
    
    for conta in despesas_cpf:
        mes_key = (conta.payment_date if conta.paid else conta.due_date).strftime('%Y-%m')
        cpf_por_mes[mes_key] += conta.value
    
    for conta in despesas_cnpj:
        mes_key = (conta.payment_date if conta.paid else conta.due_date).strftime('%Y-%m')
        cnpj_por_mes[mes_key] += conta.value
    
    # Cria gráfico
    all_months = sorted(set(list(cpf_por_mes.keys()) + list(cnpj_por_mes.keys())))
    
    if all_months:
        cpf_values = [cpf_por_mes.get(m, 0) for m in all_months]
        cnpj_values = [cnpj_por_mes.get(m, 0) for m in all_months]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='CPF (Pessoal)',
            x=all_months,
            y=cpf_values,
            marker_color='#e74c3c',
            text=[format_currency(v) if v > 0 else '' for v in cpf_values],
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            name='CNPJ (Empresarial)',
            x=all_months,
            y=cnpj_values,
            marker_color='#3498db',
            text=[format_currency(v) if v > 0 else '' for v in cnpj_values],
            textposition='auto'
        ))
        
        fig.update_layout(
            barmode='stack',
            height=400,
            xaxis_title="Mês",
            yaxis_title="Despesas (R$)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Detalhamento
    tab1, tab2, tab3 = st.tabs(["👤 Despesas CPF", "🏢 Despesas CNPJ", "❓ Sem Classificação"])
    
    with tab1:
        if despesas_cpf:
            cpf_data = []
            for c in despesas_cpf:
                cpf_data.append({
                    'Vencimento': format_date(c.due_date),
                    'Conta': c.account_name,
                    'CPF': c.cpf_cnpj,
                    'Valor': format_currency(c.value),
                    'Pago': '✅' if c.paid else '❌',
                    'Pagamento': format_date(c.payment_date) if c.payment_date else '-'
                })
            
            st.dataframe(pd.DataFrame(cpf_data), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma despesa CPF no período")
    
    with tab2:
        if despesas_cnpj:
            cnpj_data = []
            for c in despesas_cnpj:
                cnpj_data.append({
                    'Vencimento': format_date(c.due_date),
                    'Conta': c.account_name,
                    'CNPJ': c.cpf_cnpj,
                    'Valor': format_currency(c.value),
                    'Pago': '✅' if c.paid else '❌',
                    'Pagamento': format_date(c.payment_date) if c.payment_date else '-'
                })
            
            st.dataframe(pd.DataFrame(cnpj_data), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma despesa CNPJ no período")
    
    with tab3:
        if despesas_sem_classificacao:
            sem_data = []
            for c in despesas_sem_classificacao:
                sem_data.append({
                    'Vencimento': format_date(c.due_date),
                    'Conta': c.account_name,
                    'Valor': format_currency(c.value),
                    'Pago': '✅' if c.paid else '❌'
                })
            
            st.dataframe(pd.DataFrame(sem_data), use_container_width=True, hide_index=True)
            st.warning("⚠️ Recomendação: Adicione CPF/CNPJ para melhor classificação")
        else:
            st.success("✅ Todas as despesas classificadas!")

finally:
    db.close()

