"""
Dashboard de Contas a Pagar e Receber
Aging, inadimplência, projeções e gestão unificada
"""
import streamlit as st
import sys
import os
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from models.client import Client
from models.account import AccountPayable, AccountReceivable
from utils.formatters import format_currency, format_date

st.set_page_config(page_title="Dashboard Contas", page_icon="💰", layout="wide")

from utils.hide_auto_menu import hide_streamlit_menu
hide_streamlit_menu()

AuthService.init_session_state()
AuthService.require_auth()

from utils.sidebar import show_sidebar
show_sidebar()

st.title("💰 Dashboard de Contas a Pagar e Receber")
st.markdown("Visão unificada de contas, aging e projeções")
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

today = date.today()

db = SessionLocal()
try:
    # Busca todas as contas
    contas_receber = db.query(AccountReceivable).filter(
        AccountReceivable.client_id == client_id
    ).all()
    
    contas_pagar = db.query(AccountPayable).filter(
        AccountPayable.client_id == client_id
    ).all()
    
    # Classifica por aging
    def classify_aging(due_date, is_paid_or_received):
        if is_paid_or_received:
            return 'Concluído'
        
        diff = (due_date - today).days
        
        if diff < 0:
            return 'Vencido'
        elif diff <= 7:
            return '0-7 dias'
        elif diff <= 15:
            return '8-15 dias'
        elif diff <= 30:
            return '16-30 dias'
        elif diff <= 60:
            return '31-60 dias'
        else:
            return '60+ dias'
    
    # Contas a Receber por aging
    receber_aging = {'Vencido': [], '0-7 dias': [], '8-15 dias': [], '16-30 dias': [], '31-60 dias': [], '60+ dias': [], 'Concluído': []}
    for c in contas_receber:
        aging = classify_aging(c.due_date, c.received)
        receber_aging[aging].append(c)
    
    # Contas a Pagar por aging
    pagar_aging = {'Vencido': [], '0-7 dias': [], '8-15 dias': [], '16-30 dias': [], '31-60 dias': [], '60+ dias': [], 'Concluído': []}
    for c in contas_pagar:
        aging = classify_aging(c.due_date, c.paid)
        pagar_aging[aging].append(c)
    
    # KPIs
    st.subheader("📊 Indicadores Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_receber = sum(c.value for c in contas_receber if not c.received)
    total_receber_vencido = sum(c.value for c in receber_aging['Vencido'])
    
    total_pagar = sum(c.value for c in contas_pagar if not c.paid)
    total_pagar_vencido = sum(c.value for c in pagar_aging['Vencido'])
    
    with col1:
        st.metric(
            "💵 A Receber",
            format_currency(total_receber),
            help=f"{len([c for c in contas_receber if not c.received])} conta(s)"
        )
        if total_receber_vencido > 0:
            st.caption(f"🔴 Vencido: {format_currency(total_receber_vencido)}")
    
    with col2:
        st.metric(
            "💸 A Pagar",
            format_currency(total_pagar),
            help=f"{len([c for c in contas_pagar if not c.paid])} conta(s)"
        )
        if total_pagar_vencido > 0:
            st.caption(f"🔴 Vencido: {format_currency(total_pagar_vencido)}")
    
    with col3:
        saldo_projetado = total_receber - total_pagar
        st.metric(
            "⚖️ Saldo Projetado",
            format_currency(saldo_projetado),
            delta=format_currency(saldo_projetado)
        )
    
    with col4:
        inadimplencia = (total_receber_vencido / total_receber * 100) if total_receber > 0 else 0
        st.metric(
            "📊 Inadimplência",
            f"{inadimplencia:.1f}%",
            help="Contas vencidas / Total a receber"
        )
    
    st.markdown("---")
    
    # Aging Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💵 Aging - Contas a Receber")
        
        aging_labels = ['Vencido', '0-7 dias', '8-15 dias', '16-30 dias', '31-60 dias', '60+ dias']
        aging_values = [sum(c.value for c in receber_aging[label]) for label in aging_labels]
        aging_colors = ['#e74c3c', '#f39c12', '#f1c40f', '#3498db', '#9b59b6', '#95a5a6']
        
        fig = go.Figure(data=[go.Bar(
            x=aging_labels,
            y=aging_values,
            marker_color=aging_colors,
            text=[format_currency(v) if v > 0 else '' for v in aging_values],
            textposition='auto'
        )])
        
        fig.update_layout(
            height=350,
            xaxis_title="Vencimento",
            yaxis_title="Valor (R$)",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True, key="aging_receber")
    
    with col2:
        st.subheader("💸 Aging - Contas a Pagar")
        
        aging_values_pagar = [sum(c.value for c in pagar_aging[label]) for label in aging_labels]
        
        fig = go.Figure(data=[go.Bar(
            x=aging_labels,
            y=aging_values_pagar,
            marker_color=aging_colors,
            text=[format_currency(v) if v > 0 else '' for v in aging_values_pagar],
            textposition='auto'
        )])
        
        fig.update_layout(
            height=350,
            xaxis_title="Vencimento",
            yaxis_title="Valor (R$)",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True, key="aging_pagar")
    
    st.markdown("---")
    
    # Projeção 90 dias
    st.subheader("📅 Projeção 90 Dias")
    
    hoje_90d = today + timedelta(days=90)
    
    receber_90d = db.query(AccountReceivable).filter(
        AccountReceivable.client_id == client_id,
        AccountReceivable.received == False,
        AccountReceivable.due_date >= today,
        AccountReceivable.due_date <= hoje_90d
    ).order_by(AccountReceivable.due_date).all()
    
    pagar_90d = db.query(AccountPayable).filter(
        AccountPayable.client_id == client_id,
        AccountPayable.paid == False,
        AccountPayable.due_date >= today,
        AccountPayable.due_date <= hoje_90d
    ).order_by(AccountPayable.due_date).all()
    
    # Agrupa por mês
    receber_por_mes = {}
    pagar_por_mes = {}
    
    for c in receber_90d:
        mes_key = c.due_date.strftime('%Y-%m')
        receber_por_mes[mes_key] = receber_por_mes.get(mes_key, 0) + c.value
    
    for c in pagar_90d:
        mes_key = c.due_date.strftime('%Y-%m')
        pagar_por_mes[mes_key] = pagar_por_mes.get(mes_key, 0) + c.value
    
    all_months_90d = sorted(set(list(receber_por_mes.keys()) + list(pagar_por_mes.keys())))
    
    if all_months_90d:
        receber_values = [receber_por_mes.get(m, 0) for m in all_months_90d]
        pagar_values = [pagar_por_mes.get(m, 0) for m in all_months_90d]
        saldo_values = [r - p for r, p in zip(receber_values, pagar_values)]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='A Receber',
            x=all_months_90d,
            y=receber_values,
            marker_color='#2ecc71'
        ))
        
        fig.add_trace(go.Bar(
            name='A Pagar',
            x=all_months_90d,
            y=pagar_values,
            marker_color='#e74c3c'
        ))
        
        fig.add_trace(go.Scatter(
            name='Saldo Mensal',
            x=all_months_90d,
            y=saldo_values,
            mode='lines+markers',
            line=dict(color='#3498db', width=3),
            yaxis='y2'
        ))
        
        fig.update_layout(
            barmode='group',
            height=400,
            xaxis_title="Mês",
            yaxis_title="Valor (R$)",
            yaxis2=dict(
                title='Saldo (R$)',
                overlaying='y',
                side='right'
            ),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True, key="projecao_90d")

finally:
    db.close()







