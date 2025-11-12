"""
Dashboard DRE (Demonstração do Resultado do Exercício)
"""
import streamlit as st
import sys
import os
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from services.report_service import ReportService
from models.client import Client
from models.transaction import Transaction
from utils.formatters import format_currency, format_date

st.set_page_config(page_title="DRE", page_icon="📊", layout="wide")

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

st.title("📊 DRE - Demonstração do Resultado do Exercício")
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

# Filtros de período
st.subheader("📅 Período de Análise")

col1, col2, col3 = st.columns(3)

with col1:
    period_type = st.selectbox(
        "Tipo de período:",
        options=['Mês Atual', 'Últimos 3 meses', 'Últimos 6 meses', 'Último ano', 'Personalizado']
    )

# Calcula datas baseado no tipo de período
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
else:  # Personalizado
    with col2:
        start_date = st.date_input("Data inicial:", value=today - relativedelta(months=1))
    with col3:
        end_date = st.date_input("Data final:", value=today)

st.markdown("---")

# Busca dados
db = SessionLocal()
try:
    dre_data = ReportService.get_dre_data(db, client_id, start_date, end_date)
    
    # KPIs principais
    st.subheader("📈 Indicadores Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Receitas",
            format_currency(dre_data['receitas']),
            help="Total de receitas no período"
        )
    
    with col2:
        st.metric(
            "💸 Despesas",
            format_currency(dre_data['despesas']),
            help="Total de despesas no período"
        )
    
    with col3:
        resultado = dre_data['resultado']
        delta_color = "normal" if resultado >= 0 else "inverse"
        st.metric(
            "📊 Resultado",
            format_currency(resultado),
            delta=f"{dre_data['margem']:.1f}%",
            help="Resultado líquido (Receitas - Despesas)"
        )
    
    with col4:
        margem = dre_data['margem']
        st.metric(
            "📉 Margem",
            f"{margem:.1f}%",
            help="Margem de lucro líquido"
        )
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Receitas vs Despesas")
        
        # Gráfico de barras
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Receitas',
            x=['Receitas'],
            y=[dre_data['receitas']],
            marker_color='#2ecc71',
            text=[format_currency(dre_data['receitas'])],
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            name='Despesas',
            x=['Despesas'],
            y=[dre_data['despesas']],
            marker_color='#e74c3c',
            text=[format_currency(dre_data['despesas'])],
            textposition='auto'
        ))
        
        fig.update_layout(
            showlegend=True,
            height=400,
            xaxis_title="",
            yaxis_title="Valor (R$)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Resultado")
        
        # Gráfico de pizza
        labels = ['Receitas', 'Despesas']
        values = [dre_data['receitas'], dre_data['despesas']]
        colors = ['#2ecc71', '#e74c3c']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            hole=0.4,
            textinfo='label+percent',
            textposition='inside'
        )])
        
        fig.update_layout(
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Receitas por categoria
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💵 Receitas por Categoria")
        
        if dre_data['receitas_por_categoria']:
            categorias = [r['categoria'] for r in dre_data['receitas_por_categoria']]
            valores = [r['valor'] for r in dre_data['receitas_por_categoria']]
            
            fig = go.Figure(data=[go.Bar(
                x=categorias,
                y=valores,
                marker_color='#3498db',
                text=[format_currency(v) for v in valores],
                textposition='auto'
            )])
            
            fig.update_layout(
                height=400,
                xaxis_title="Categoria",
                yaxis_title="Valor (R$)",
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ℹ️ Nenhuma receita registrada no período.")
    
    with col2:
        st.subheader("💳 Despesas por Categoria")
        
        if dre_data['despesas_por_categoria']:
            categorias = [d['categoria'] for d in dre_data['despesas_por_categoria']]
            valores = [d['valor'] for d in dre_data['despesas_por_categoria']]
            
            fig = go.Figure(data=[go.Bar(
                x=categorias,
                y=valores,
                marker_color='#e67e22',
                text=[format_currency(v) for v in valores],
                textposition='auto'
            )])
            
            fig.update_layout(
                height=400,
                xaxis_title="Categoria",
                yaxis_title="Valor (R$)",
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ℹ️ Nenhuma despesa registrada no período.")
    
    st.markdown("---")
    
    # Detalhamento DRE Completo
    with st.expander("📋 Detalhamento Completo da DRE", expanded=False):
        st.markdown("### 📊 Demonstração do Resultado do Exercício")
        st.markdown(f"**Cliente:** {client.name}")
        st.markdown(f"**Período:** {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
        st.markdown("---")
        
        # RECEITAS DETALHADAS
        st.markdown("### (+) RECEITAS OPERACIONAIS")
        
        if dre_data['receitas_por_categoria']:
            # Agrupa receitas por categoria com detalhes
            for idx, rec in enumerate(dre_data['receitas_por_categoria'], 1):
                categoria = rec['categoria']
                valor = rec['valor']
                percentual = (valor / dre_data['receitas'] * 100) if dre_data['receitas'] > 0 else 0
                
                with st.expander(f"💰 {categoria} - {format_currency(valor)} ({percentual:.1f}%)"):
                    # Busca transações desta categoria
                    trans_receitas = db.query(Transaction).filter(
                        Transaction.client_id == client_id,
                        Transaction.type == 'entrada',
                        Transaction.category == categoria,
                        Transaction.date >= start_date,
                        Transaction.date <= end_date
                    ).order_by(Transaction.date.desc()).all()
                    
                    if trans_receitas:
                        st.markdown(f"**Total de transações:** {len(trans_receitas)}")
                        st.markdown(f"**Valor médio:** {format_currency(valor / len(trans_receitas))}")
                        
                        # Tabela de transações
                        trans_data = []
                        for t in trans_receitas[:10]:  # Mostra até 10
                            trans_data.append({
                                'Data': format_date(t.date),
                                'Descrição': t.description[:40] + '...' if len(t.description) > 40 else t.description,
                                'Valor': format_currency(t.value),
                                'Grupo': t.group.name if t.group else '-',
                                'Conta': t.account or '-'
                            })
                        
                        df_trans = pd.DataFrame(trans_data)
                        st.dataframe(df_trans, use_container_width=True, hide_index=True)
                        
                        if len(trans_receitas) > 10:
                            st.caption(f"Mostrando 10 de {len(trans_receitas)} transações")
        
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### **TOTAL DE RECEITAS**")
        with col2:
            st.markdown(f"### **{format_currency(dre_data['receitas'])}**")
        
        st.markdown("---")
        
        # DESPESAS DETALHADAS
        st.markdown("### (-) DESPESAS OPERACIONAIS")
        
        if dre_data['despesas_por_categoria']:
            # Agrupa despesas por categoria com detalhes
            for idx, desp in enumerate(dre_data['despesas_por_categoria'], 1):
                categoria = desp['categoria']
                valor = desp['valor']
                percentual = (valor / dre_data['despesas'] * 100) if dre_data['despesas'] > 0 else 0
                
                with st.expander(f"💸 {categoria} - {format_currency(valor)} ({percentual:.1f}%)"):
                    # Busca transações desta categoria
                    trans_despesas = db.query(Transaction).filter(
                        Transaction.client_id == client_id,
                        Transaction.type == 'saida',
                        Transaction.category == categoria,
                        Transaction.date >= start_date,
                        Transaction.date <= end_date
                    ).order_by(Transaction.date.desc()).all()
                    
                    if trans_despesas:
                        st.markdown(f"**Total de transações:** {len(trans_despesas)}")
                        st.markdown(f"**Valor médio:** {format_currency(valor / len(trans_despesas))}")
                        
                        # Tabela de transações
                        trans_data = []
                        for t in trans_despesas[:10]:  # Mostra até 10
                            trans_data.append({
                                'Data': format_date(t.date),
                                'Descrição': t.description[:40] + '...' if len(t.description) > 40 else t.description,
                                'Valor': format_currency(t.value),
                                'Grupo': t.group.name if t.group else '-',
                                'Conta': t.account or '-'
                            })
                        
                        df_trans = pd.DataFrame(trans_data)
                        st.dataframe(df_trans, use_container_width=True, hide_index=True)
                        
                        if len(trans_despesas) > 10:
                            st.caption(f"Mostrando 10 de {len(trans_despesas)} transações")
        
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### **TOTAL DE DESPESAS**")
        with col2:
            st.markdown(f"### **{format_currency(dre_data['despesas'])}**")
        
        st.markdown("---")
        st.markdown("---")
        
        # RESULTADO FINAL
        resultado = dre_data['resultado']
        margem = dre_data['margem']
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if resultado >= 0:
                st.markdown("### **✅ LUCRO LÍQUIDO DO PERÍODO**")
            else:
                st.markdown("### **❌ PREJUÍZO DO PERÍODO**")
        with col2:
            if resultado >= 0:
                st.markdown(f"### **{format_currency(resultado)}**")
            else:
                st.markdown(f"### **{format_currency(resultado)}**")
        
        st.markdown("---")
        
        # Análise detalhada
        st.markdown("### 📊 Análise Detalhada")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Margem Líquida", f"{margem:.2f}%")
            st.caption("Lucro / Receitas")
        
        with col2:
            if dre_data['receitas'] > 0:
                desp_sobre_rec = (dre_data['despesas'] / dre_data['receitas'] * 100)
                st.metric("Despesas / Receitas", f"{desp_sobre_rec:.1f}%")
                st.caption("Quanto das receitas vira despesa")
        
        with col3:
            # Maior categoria de receita
            if dre_data['receitas_por_categoria']:
                maior_rec = max(dre_data['receitas_por_categoria'], key=lambda x: x['valor'])
                st.metric("Maior Receita", maior_rec['categoria'])
                st.caption(format_currency(maior_rec['valor']))
        
        st.markdown("---")
        
        # Comparativo com período anterior
        st.markdown("### 📈 Comparativo com Período Anterior")
        
        # Calcula período anterior
        dias_periodo = (end_date - start_date).days
        start_date_anterior = start_date - timedelta(days=dias_periodo)
        end_date_anterior = start_date - timedelta(days=1)
        
        dre_anterior = ReportService.get_dre_data(db, client_id, start_date_anterior, end_date_anterior)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            var_receitas = dre_data['receitas'] - dre_anterior['receitas']
            var_perc_rec = (var_receitas / dre_anterior['receitas'] * 100) if dre_anterior['receitas'] > 0 else 0
            st.metric(
                "Receitas",
                format_currency(dre_data['receitas']),
                delta=f"{var_perc_rec:+.1f}%",
                help=f"Período anterior: {format_currency(dre_anterior['receitas'])}"
            )
        
        with col2:
            var_despesas = dre_data['despesas'] - dre_anterior['despesas']
            var_perc_desp = (var_despesas / dre_anterior['despesas'] * 100) if dre_anterior['despesas'] > 0 else 0
            st.metric(
                "Despesas",
                format_currency(dre_data['despesas']),
                delta=f"{var_perc_desp:+.1f}%",
                delta_color="inverse",
                help=f"Período anterior: {format_currency(dre_anterior['despesas'])}"
            )
        
        with col3:
            var_resultado = dre_data['resultado'] - dre_anterior['resultado']
            var_perc_res = (var_resultado / abs(dre_anterior['resultado']) * 100) if dre_anterior['resultado'] != 0 else 0
            st.metric(
                "Resultado",
                format_currency(dre_data['resultado']),
                delta=f"{var_perc_res:+.1f}%",
                help=f"Período anterior: {format_currency(dre_anterior['resultado'])}"
            )
        
        st.markdown("---")
        
        # Insights e Recomendações
        st.markdown("### 💡 Insights e Recomendações")
        
        if resultado >= 0:
            st.success("✅ **Situação Positiva:** Empresa apresenta lucro no período")
            
            if margem >= 20:
                st.info("📈 **Margem Saudável:** Margem líquida acima de 20%")
            elif margem >= 10:
                st.warning("⚠️ **Margem Moderada:** Considere otimizar custos")
            else:
                st.error("❌ **Margem Baixa:** Atenção! Margem abaixo de 10%")
        else:
            st.error("❌ **Situação Crítica:** Empresa apresenta prejuízo")
            st.markdown("**Ações Recomendadas:**")
            st.markdown("- 🔍 Revisar despesas operacionais")
            st.markdown("- 📈 Buscar aumentar receitas")
            st.markdown("- 💰 Analisar precificação")
            st.markdown("- 🔄 Reavaliar estratégia comercial")

finally:
    db.close()

