"""
Relatório de Eventos e Contratos
Calendário, pipeline de vendas, análise por vendedor e tipo de evento
"""
import streamlit as st
import sys
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import calendar
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from sqlalchemy.orm import joinedload
from sqlalchemy import func

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from services.contract_service import ContractService
from models.client import Client
from models.contract import Contract
from utils.formatters import format_currency, format_date

st.set_page_config(page_title="Relatório de Eventos", page_icon="🎉", layout="wide")

from utils.hide_auto_menu import hide_streamlit_menu
hide_streamlit_menu()

AuthService.init_session_state()
AuthService.require_auth()

from utils.sidebar import show_sidebar
show_sidebar()

st.title("🎉 Relatório de Eventos e Contratos")
st.markdown("Análise completa de eventos, vendedores e pipeline de vendas")
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

# Filtros
st.subheader("📅 Período de Análise")

col1, col2, col3 = st.columns(3)

with col1:
    period_type = st.selectbox(
        "Período:",
        options=['Próximos 3 meses', 'Próximos 6 meses', 'Próximo ano', 'Últimos 6 meses', 'Personalizado']
    )

today = date.today()

if period_type == 'Próximos 3 meses':
    start_date = today
    end_date = today + relativedelta(months=3)
elif period_type == 'Próximos 6 meses':
    start_date = today
    end_date = today + relativedelta(months=6)
elif period_type == 'Próximo ano':
    start_date = today
    end_date = today + relativedelta(years=1)
elif period_type == 'Últimos 6 meses':
    start_date = today - relativedelta(months=6)
    end_date = today
else:
    with col2:
        start_date = st.date_input("Data inicial:", value=today)
    with col3:
        end_date = st.date_input("Data final:", value=today + relativedelta(months=6))

st.markdown("---")

db = SessionLocal()
try:
    # Busca contratos do período
    contracts = db.query(Contract).options(
        joinedload(Contract.group),
        joinedload(Contract.subgroup)
    ).filter(
        Contract.client_id == client_id,
        Contract.event_date >= start_date,
        Contract.event_date <= end_date
    ).order_by(Contract.event_date).all()
    
    if contracts:
        # KPIs Principais
        st.subheader("📊 Indicadores Principais")
        
        total_events = len(contracts)
        total_revenue = sum(c.service_value + (c.displacement_value or 0) for c in contracts)
        avg_ticket = total_revenue / total_events if total_events > 0 else 0
        total_guests = sum(c.guests_count or 0 for c in contracts)
        
        concluidos = [c for c in contracts if c.status == 'concluido']
        em_andamento = [c for c in contracts if c.status == 'em_andamento']
        pendentes = [c for c in contracts if c.status == 'pendente']
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("🎉 Total de Eventos", total_events)
        
        with col2:
            st.metric("💰 Receita Total", format_currency(total_revenue))
        
        with col3:
            st.metric("🎯 Ticket Médio", format_currency(avg_ticket))
        
        with col4:
            st.metric("👥 Total Convidados", f"{total_guests:,}")
        
        with col5:
            media_convidados = total_guests / total_events if total_events > 0 else 0
            st.metric("📊 Média Convidados", f"{media_convidados:.0f}")
        
        st.markdown("---")
        
        # Pipeline de Vendas
        st.subheader("📈 Pipeline de Vendas")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "⏳ Pendentes",
                len(pendentes),
                help=f"Valor: {format_currency(sum(c.service_value for c in pendentes))}"
            )
            if pendentes:
                st.caption(f"Valor: {format_currency(sum(c.service_value + (c.displacement_value or 0) for c in pendentes))}")
        
        with col2:
            st.metric(
                "🔄 Em Andamento",
                len(em_andamento),
                help=f"Valor: {format_currency(sum(c.service_value for c in em_andamento))}"
            )
            if em_andamento:
                st.caption(f"Valor: {format_currency(sum(c.service_value + (c.displacement_value or 0) for c in em_andamento))}")
        
        with col3:
            st.metric(
                "✅ Concluídos",
                len(concluidos),
                help=f"Valor: {format_currency(sum(c.service_value for c in concluidos))}"
            )
            if concluidos:
                st.caption(f"Valor: {format_currency(sum(c.service_value + (c.displacement_value or 0) for c in concluidos))}")
        
        # Gráfico Funil
        fig = go.Figure(data=[go.Funnel(
            y=['Pendentes', 'Em Andamento', 'Concluídos'],
            x=[len(pendentes), len(em_andamento), len(concluidos)],
            textinfo="value+percent initial",
            marker=dict(color=['#f39c12', '#3498db', '#2ecc71'])
        )])
        
        fig.update_layout(height=350, title="Funil de Conversão")
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Calendário de Eventos
        st.subheader("📅 Calendário de Eventos")
        
        events_calendar = ContractService.get_events_calendar(db, client_id, start_date, end_date)
        
        if events_calendar:
            # Agrupa por mês
            events_by_month = defaultdict(list)
            for event in events_calendar:
                month_key = event['date'].strftime('%Y-%m')
                events_by_month[month_key].append(event)
            
            for month_key in sorted(events_by_month.keys()):
                events_month = events_by_month[month_key]
                mes_nome = date.fromisoformat(f"{month_key}-01").strftime('%B %Y').title()
                total_mes = sum(e['value'] for e in events_month)
                
                with st.expander(f"📅 {mes_nome} - {len(events_month)} evento(s) - {format_currency(total_mes)}"):
                    for event in events_month:
                        col_ev1, col_ev2, col_ev3 = st.columns([2, 1, 1])
                        
                        with col_ev1:
                            status_icon = {'pendente': '⏳', 'em_andamento': '🔄', 'concluido': '✅'}.get(event['status'], '❓')
                            st.markdown(f"{status_icon} **{event['title']}**")
                            st.caption(f"📍 {event['location'] or 'Local não informado'}")
                        
                        with col_ev2:
                            st.markdown(f"**{format_date(event['date'])}**")
                            st.caption(f"👥 {event['guests'] or 0} convidados")
                        
                        with col_ev3:
                            st.markdown(f"**{format_currency(event['value'])}**")
                            if event['seller']:
                                st.caption(f"👤 {event['seller']}")
                            if event['invoice']:
                                st.caption(f"📄 NF: {event['invoice']}")
                        
                        st.markdown("---")
        
        st.markdown("---")
        
        # Análise por Vendedor
        st.subheader("👤 Performance por Vendedor")
        
        seller_performance = ContractService.get_seller_performance(db, client_id, start_date, end_date)
        
        if seller_performance:
            # Tabela
            perf_data = []
            for perf in seller_performance:
                perf_data.append({
                    'Vendedor': perf['seller'],
                    'Eventos': perf['num_events'],
                    'Receita Total': format_currency(perf['total_revenue']),
                    'Ticket Médio': format_currency(perf['avg_ticket']),
                    'Total Convidados': perf['total_guests']
                })
            
            st.dataframe(pd.DataFrame(perf_data), use_container_width=True, hide_index=True)
            
            # Gráfico
            if len(seller_performance) > 1:
                fig = go.Figure(data=[go.Bar(
                    y=[p['seller'] for p in seller_performance],
                    x=[p['total_revenue'] for p in seller_performance],
                    orientation='h',
                    marker_color='#3498db',
                    text=[format_currency(p['total_revenue']) for p in seller_performance],
                    textposition='auto'
                )])
                
                fig.update_layout(
                    height=max(300, len(seller_performance) * 50),
                    xaxis_title="Receita Total (R$)",
                    yaxis_title="",
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ℹ️ Nenhum vendedor informado nos contratos")
        
        st.markdown("---")
        
        # Análise por Tipo de Evento
        st.subheader("🎊 Análise por Tipo de Evento")
        
        events_by_type = defaultdict(lambda: {'count': 0, 'revenue': 0, 'guests': 0})
        for c in contracts:
            tipo = c.event_type or 'Sem tipo'
            events_by_type[tipo]['count'] += 1
            events_by_type[tipo]['revenue'] += c.service_value + (c.displacement_value or 0)
            events_by_type[tipo]['guests'] += c.guests_count or 0
        
        if events_by_type:
            col1, col2 = st.columns(2)
            
            with col1:
                # Pizza de eventos por tipo
                labels = list(events_by_type.keys())
                values = [events_by_type[k]['count'] for k in labels]
                
                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.4,
                    textinfo='label+percent+value'
                )])
                
                fig.update_layout(height=400, title="Distribuição de Eventos por Tipo")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Receita por tipo
                revenues = [events_by_type[k]['revenue'] for k in labels]
                
                fig = go.Figure(data=[go.Bar(
                    x=labels,
                    y=revenues,
                    marker_color='#2ecc71',
                    text=[format_currency(v) for v in revenues],
                    textposition='auto'
                )])
                
                fig.update_layout(
                    height=400,
                    title="Receita por Tipo de Evento",
                    xaxis_title="",
                    yaxis_title="Receita (R$)"
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # NFs Pendentes
        st.subheader("📄 Notas Fiscais Pendentes")
        
        nf_pendentes = ContractService.get_pending_invoices(db, client_id)
        
        if nf_pendentes:
            st.warning(f"⚠️ {len(nf_pendentes)} evento(s) concluído(s) sem NF emitida!")
            
            nf_data = []
            for c in nf_pendentes:
                nf_data.append({
                    'Data Evento': format_date(c.event_date),
                    'Cliente': c.contractor_name,
                    'Tipo': c.event_type or '-',
                    'Valor': format_currency(c.service_value + (c.displacement_value or 0)),
                    'Status': c.status,
                    'ID': c.id
                })
            
            st.dataframe(pd.DataFrame(nf_data), use_container_width=True, hide_index=True)
        else:
            st.success("✅ Todas as NFs emitidas!")
        
        st.markdown("---")
        
        # Detalhamento Completo
        with st.expander("📋 Lista Completa de Eventos"):
            full_data = []
            for c in contracts:
                status_map = {
                    'pendente': '⏳ Pendente',
                    'em_andamento': '🔄 Em Andamento',
                    'concluido': '✅ Concluído',
                    'cancelado': '❌ Cancelado'
                }
                
                full_data.append({
                    'Data': format_date(c.event_date),
                    'Cliente': c.contractor_name,
                    'Tipo': c.event_type or '-',
                    'Local': c.event_location or '-',
                    'Convidados': c.guests_count or 0,
                    'Valor Serviço': format_currency(c.service_value),
                    'Deslocamento': format_currency(c.displacement_value or 0),
                    'Total': format_currency(c.service_value + (c.displacement_value or 0)),
                    'Vendedor': c.seller_name or '-',
                    'NF': c.invoice_number or 'Pendente',
                    'Status': status_map.get(c.status, c.status)
                })
            
            st.dataframe(pd.DataFrame(full_data), use_container_width=True, hide_index=True)
    
    else:
        st.info("ℹ️ Nenhum evento encontrado no período selecionado.")

finally:
    db.close()

