"""
Relatório de Performance de Vendedores
Ranking, faturamento, conversão e metas
"""
import streamlit as st
import sys
import os
import pandas as pd
import plotly.graph_objects as go
from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy import func

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from services.contract_service import ContractService
from models.client import Client
from models.contract import Contract
from utils.formatters import format_currency

st.set_page_config(page_title="Performance Vendedores", page_icon="🏆", layout="wide")

from utils.hide_auto_menu import hide_streamlit_menu
hide_streamlit_menu()

AuthService.init_session_state()
AuthService.require_auth()

from utils.sidebar import show_sidebar
show_sidebar()

st.title("🏆 Performance de Vendedores")
st.markdown("Ranking, faturamento e análise individual")
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
col1, col2, col3 = st.columns(3)

with col1:
    period_type = st.selectbox(
        "Período:",
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
    # Busca performance
    performance = ContractService.get_seller_performance(db, client_id, start_date, end_date)
    
    if performance:
        # Ranking
        st.subheader("🥇 Ranking de Vendedores")
        
        for i, perf in enumerate(performance[:5], 1):
            medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(i, f'{i}º')
            
            col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
            
            with col1:
                st.markdown(f"### {medal}")
            
            with col2:
                st.markdown(f"### {perf['seller']}")
            
            with col3:
                st.metric("Eventos", perf['num_events'])
            
            with col4:
                st.metric("Receita", format_currency(perf['total_revenue']))
            
            # Barra de progresso visual
            max_revenue = performance[0]['total_revenue']
            progress = perf['total_revenue'] / max_revenue if max_revenue > 0 else 0
            st.progress(progress)
            
            st.markdown("---")
        
        st.markdown("---")
        
        # Gráficos Comparativos
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Faturamento por Vendedor")
            
            sellers = [p['seller'] for p in performance]
            revenues = [p['total_revenue'] for p in performance]
            
            fig = go.Figure(data=[go.Bar(
                y=sellers,
                x=revenues,
                orientation='h',
                marker_color='#3498db',
                text=[format_currency(r) for r in revenues],
                textposition='auto'
            )])
            
            fig.update_layout(
                height=max(300, len(sellers) * 50),
                xaxis_title="Receita (R$)",
                yaxis_title="",
                showlegend=False,
                yaxis={'categoryorder': 'total ascending'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Ticket Médio")
            
            avg_tickets = [p['avg_ticket'] for p in performance]
            
            fig = go.Figure(data=[go.Bar(
                y=sellers,
                x=avg_tickets,
                orientation='h',
                marker_color='#2ecc71',
                text=[format_currency(t) for t in avg_tickets],
                textposition='auto'
            )])
            
            fig.update_layout(
                height=max(300, len(sellers) * 50),
                xaxis_title="Ticket Médio (R$)",
                yaxis_title="",
                showlegend=False,
                yaxis={'categoryorder': 'total ascending'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Tabela Detalhada
        st.subheader("📋 Detalhamento por Vendedor")
        
        perf_data = []
        for perf in performance:
            perf_data.append({
                'Vendedor': perf['seller'],
                'Nº Eventos': perf['num_events'],
                'Receita Total': format_currency(perf['total_revenue']),
                'Ticket Médio': format_currency(perf['avg_ticket']),
                'Total Convidados': perf['total_guests'],
                'Média Convidados/Evento': f"{perf['total_guests'] / perf['num_events']:.0f}" if perf['num_events'] > 0 else '0'
            })
        
        st.dataframe(pd.DataFrame(perf_data), use_container_width=True, hide_index=True)
    
    else:
        st.info("ℹ️ Nenhum vendedor informado nos contratos do período")
        st.markdown("💡 Adicione vendedores aos contratos para visualizar performance")

finally:
    db.close()

