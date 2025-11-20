"""
Fluxo de Caixa Gerencial
Realizado vs Previsto, projeções baseadas em contratos e alertas de liquidez
"""
import streamlit as st
import sys
import os
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from services.report_service import ReportService
from models.client import Client
from models.contract import Contract
from models.account import AccountPayable, AccountReceivable
from utils.formatters import format_currency, format_date

st.set_page_config(page_title="Fluxo de Caixa Gerencial", page_icon="💼", layout="wide")

from utils.hide_auto_menu import hide_streamlit_menu
hide_streamlit_menu()

AuthService.init_session_state()
AuthService.require_auth()

from utils.sidebar import show_sidebar
show_sidebar()

st.title("💼 Fluxo de Caixa Gerencial")
st.markdown("Realizado vs Previsto, projeções e alertas de liquidez")
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
st.subheader("📅 Período de Análise")
col1, col2 = st.columns(2)

with col1:
    meses_projecao = st.slider("Projeção (meses):", 1, 12, 3)

with col2:
    incluir_historico = st.checkbox("Incluir 3 meses histórico", value=True)

today = date.today()
start_date = today - relativedelta(months=3) if incluir_historico else today
end_date = today + relativedelta(months=meses_projecao)

st.markdown("---")

db = SessionLocal()
try:
    # Verifica tipos habilitados para DFC
    from services.report_config_service import ReportConfigService
    enabled_types = ReportConfigService.get_enabled_data_types(db, client_id, 'dfc')
    
    # Busca dados realizados
    dfc_realizado = ReportService.get_dfc_data(db, client_id, start_date, today)
    
    # Busca projeções
    dfc_projetado = ReportService.get_dfc_projection(db, client_id, today + timedelta(days=1), end_date)
    
    # Busca contratos futuros confirmados (APENAS se habilitado)
    contratos_futuros = []
    receita_contratos_futuros = 0
    
    if 'contracts' in enabled_types:
        contratos_futuros = db.query(Contract).filter(
            Contract.client_id == client_id,
            Contract.event_date > today,
            Contract.event_date <= end_date,
            Contract.status.in_(['em_andamento', 'concluido'])
        ).all()
        
        receita_contratos_futuros = sum(
            c.service_value + (c.displacement_value or 0) for c in contratos_futuros
        )
    
    # KPIs Principais
    st.subheader("📊 Indicadores de Liquidez")
    
    saldo_atual = dfc_realizado.get('saldo_final', 0) if dfc_realizado.get('fluxo_mensal') else 0
    projecao_30d = dfc_projetado.get('saldo_final_projetado', 0)
    
    # Contas a pagar/receber nos próximos 30 dias (APENAS se habilitado)
    hoje_30d = today + timedelta(days=30)
    
    contas_receber_30d = []
    contas_pagar_30d = []
    total_receber_30d = 0
    total_pagar_30d = 0
    
    if 'accounts_receivable' in enabled_types:
        contas_receber_30d = db.query(AccountReceivable).filter(
            AccountReceivable.client_id == client_id,
            AccountReceivable.received == False,
            AccountReceivable.due_date >= today,
            AccountReceivable.due_date <= hoje_30d
        ).all()
        total_receber_30d = sum(c.value for c in contas_receber_30d)
    
    if 'accounts_payable' in enabled_types:
        contas_pagar_30d = db.query(AccountPayable).filter(
            AccountPayable.client_id == client_id,
            AccountPayable.paid == False,
            AccountPayable.due_date >= today,
            AccountPayable.due_date <= hoje_30d
        ).all()
        total_pagar_30d = sum(c.value for c in contas_pagar_30d)
    
    # Calcula média de gastos diários
    if dfc_realizado.get('fluxo_mensal'):
        total_saidas_hist = sum(f['saidas'] for f in dfc_realizado['fluxo_mensal'])
        dias_hist = (today - start_date).days
        gasto_medio_diario = total_saidas_hist / dias_hist if dias_hist > 0 else 0
        dias_de_caixa = saldo_atual / gasto_medio_diario if gasto_medio_diario > 0 else 999
    else:
        gasto_medio_diario = 0
        dias_de_caixa = 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Disponível Hoje",
            format_currency(saldo_atual),
            help="Saldo acumulado até hoje"
        )
    
    with col2:
        delta_30d = total_receber_30d - total_pagar_30d
        st.metric(
            "📊 Projeção 30 dias",
            format_currency(saldo_atual + delta_30d),
            delta=format_currency(delta_30d),
            help=f"Receber: {format_currency(total_receber_30d)} | Pagar: {format_currency(total_pagar_30d)}"
        )
    
    with col3:
        comprometimento = (total_pagar_30d / total_receber_30d * 100) if total_receber_30d > 0 else 0
        st.metric(
            "⚖️ Comprometimento",
            f"{comprometimento:.1f}%",
            help="Contas a pagar / Contas a receber (próximos 30 dias)"
        )
    
    with col4:
        st.metric(
            "📅 Dias de Caixa",
            f"{dias_de_caixa:.0f} dias" if dias_de_caixa < 999 else "∞",
            help="Saldo atual / Gasto médio diário"
        )
    
    # Alertas
    if saldo_atual < gasto_medio_diario * 15:
        st.error(f"🔴 ALERTA: Saldo baixo! Menos de 15 dias de caixa ({format_currency(saldo_atual)})")
    elif saldo_atual < gasto_medio_diario * 30:
        st.warning(f"⚠️ Atenção: Saldo para menos de 30 dias ({format_currency(saldo_atual)})")
    
    if comprometimento > 80:
        st.error(f"🔴 ALERTA: Alto comprometimento ({comprometimento:.1f}%)!")
    
    st.markdown("---")
    
    # Gráfico Realizado vs Previsto
    st.subheader("📈 Fluxo Realizado vs Previsto")
    
    # Prepara dados
    meses_labels = []
    entradas_real = []
    saidas_real = []
    saldo_real = []
    
    entradas_prev = []
    saidas_prev = []
    saldo_prev = []
    
    # Realizado
    if dfc_realizado.get('fluxo_mensal'):
        for fluxo in dfc_realizado['fluxo_mensal']:
            meses_labels.append(fluxo['mes'] + ' (R)')
            entradas_real.append(fluxo['entradas'])
            saidas_real.append(fluxo['saidas'])
            saldo_real.append(fluxo['saldo_acumulado'])
    
    # Previsto
    saldo_acum_proj = saldo_atual
    if dfc_projetado.get('projecao_mensal'):
        for proj in dfc_projetado['projecao_mensal']:
            meses_labels.append(proj['mes'] + ' (P)')
            entradas_prev.append(proj['entradas_previstas'])
            saidas_prev.append(proj['saidas_previstas'])
            saldo_acum_proj += proj['saldo_mes']
            saldo_prev.append(saldo_acum_proj)
    
    # Preenche arrays para manter tamanho igual
    while len(entradas_prev) < len(entradas_real):
        entradas_prev.insert(0, None)
        saidas_prev.insert(0, None)
        saldo_prev.insert(0, None)
    
    while len(entradas_real) < len(entradas_prev):
        entradas_real.append(None)
        saidas_real.append(None)
        saldo_real.append(None)
    
    fig = go.Figure()
    
    # Entradas
    fig.add_trace(go.Bar(
        name='Entradas Realizadas',
        x=meses_labels,
        y=entradas_real,
        marker_color='#2ecc71',
        opacity=1.0
    ))
    
    fig.add_trace(go.Bar(
        name='Entradas Previstas',
        x=meses_labels,
        y=entradas_prev,
        marker_color='#a9dfbf',
        opacity=0.6
    ))
    
    # Saídas
    fig.add_trace(go.Bar(
        name='Saídas Realizadas',
        x=meses_labels,
        y=saidas_real,
        marker_color='#e74c3c',
        opacity=1.0
    ))
    
    fig.add_trace(go.Bar(
        name='Saídas Previstas',
        x=meses_labels,
        y=saidas_prev,
        marker_color='#f5b7b1',
        opacity=0.6
    ))
    
    # Saldo acumulado
    fig.add_trace(go.Scatter(
        name='Saldo Realizado',
        x=meses_labels,
        y=saldo_real,
        mode='lines+markers',
        line=dict(color='#3498db', width=3),
        yaxis='y2'
    ))
    
    fig.add_trace(go.Scatter(
        name='Saldo Projetado',
        x=meses_labels,
        y=saldo_prev,
        mode='lines+markers',
        line=dict(color='#9b59b6', width=3, dash='dash'),
        yaxis='y2'
    ))
    
    fig.update_layout(
        barmode='group',
        height=500,
        xaxis_title="Período (R=Realizado, P=Previsto)",
        yaxis_title="Entradas/Saídas (R$)",
        yaxis2=dict(
            title='Saldo Acumulado (R$)',
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Eventos Confirmados (impactam projeção)
    if contratos_futuros:
        st.subheader("📅 Eventos Confirmados (Receita Prevista)")
        
        st.info(f"🎉 {len(contratos_futuros)} evento(s) confirmado(s) nos próximos {meses_projecao} meses")
        st.metric("Receita Prevista de Eventos", format_currency(receita_contratos_futuros))
        
        eventos_data = []
        for c in contratos_futuros[:10]:  # Mostra até 10
            eventos_data.append({
                'Data': format_date(c.event_date),
                'Cliente': c.contractor_name,
                'Tipo': c.event_type or '-',
                'Valor': format_currency(c.service_value + (c.displacement_value or 0)),
                'Status': c.status
            })
        
        st.dataframe(pd.DataFrame(eventos_data), use_container_width=True, hide_index=True)
        
        if len(contratos_futuros) > 10:
            st.caption(f"Mostrando 10 de {len(contratos_futuros)} eventos")
    
    st.markdown("---")
    
    # Breakeven Mensal
    st.subheader("⚖️ Ponto de Equilíbrio (Breakeven)")
    
    # Calcula despesas fixas médias
    if dfc_realizado.get('fluxo_mensal'):
        total_saidas = sum(f['saidas'] for f in dfc_realizado['fluxo_mensal'])
        num_meses = len(dfc_realizado['fluxo_mensal'])
        despesa_fixa_mensal = total_saidas / num_meses if num_meses > 0 else 0
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "💸 Despesa Média Mensal",
                format_currency(despesa_fixa_mensal),
                help="Média dos últimos meses"
            )
            st.caption("💡 Este é o mínimo que precisa faturar/mês para não ter prejuízo")
        
        with col2:
            # Calcula receita média
            total_entradas = sum(f['entradas'] for f in dfc_realizado['fluxo_mensal'])
            receita_media_mensal = total_entradas / num_meses if num_meses > 0 else 0
            
            margem = ((receita_media_mensal - despesa_fixa_mensal) / receita_media_mensal * 100) if receita_media_mensal > 0 else 0
            
            st.metric(
                "💰 Receita Média Mensal",
                format_currency(receita_media_mensal),
                delta=f"{margem:+.1f}%"
            )
            
            if margem < 10:
                st.caption("⚠️ Margem baixa")
            else:
                st.caption("✅ Margem saudável")
    
    st.markdown("---")
    
    # Projeção Detalhada
    with st.expander("📋 Projeção Detalhada (Próximos Meses)"):
        if dfc_projetado.get('projecao_mensal'):
            proj_data = []
            saldo_acum = saldo_atual
            
            for proj in dfc_projetado['projecao_mensal']:
                saldo_acum += proj['saldo_mes']
                
                proj_data.append({
                    'Mês': proj['mes'],
                    'Entradas Previstas': format_currency(proj['entradas_previstas']),
                    'Saídas Previstas': format_currency(proj['saidas_previstas']),
                    'Saldo do Mês': format_currency(proj['saldo_mes']),
                    'Saldo Acumulado': format_currency(saldo_acum)
                })
            
            st.dataframe(pd.DataFrame(proj_data), use_container_width=True, hide_index=True)
            
            # Déficits previstos
            deficits = dfc_projetado.get('deficits', [])
            if deficits:
                st.error(f"🔴 ALERTA: {len(deficits)} mês(es) com projeção de déficit!")
                for deficit in deficits:
                    st.warning(f"⚠️ {deficit['mes']}: {format_currency(deficit['saldo_acumulado'])}")
        else:
            st.info("ℹ️ Sem projeções disponíveis (nenhuma conta a pagar/receber futura)")

finally:
    db.close()

