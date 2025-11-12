"""
Dashboard DFC (Demonstração do Fluxo de Caixa)
"""
import streamlit as st
import sys
import os
import plotly.graph_objects as go
import pandas as pd
import calendar
from datetime import date
from dateutil.relativedelta import relativedelta
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from services.report_service import ReportService
from models.client import Client
from models.transaction import Transaction
from utils.formatters import format_currency, format_date

st.set_page_config(page_title="DFC", page_icon="💵", layout="wide")

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

st.title("💵 DFC - Demonstração do Fluxo de Caixa")
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
        options=['Últimos 6 meses', 'Último ano', '2 anos', 'Personalizado']
    )

today = date.today()

if period_type == 'Últimos 6 meses':
    start_date = today - relativedelta(months=6)
    end_date = today
elif period_type == 'Último ano':
    start_date = today - relativedelta(years=1)
    end_date = today
elif period_type == '2 anos':
    start_date = today - relativedelta(years=2)
    end_date = today
else:  # Personalizado
    with col2:
        start_date = st.date_input("Data inicial:", value=today - relativedelta(months=6))
    with col3:
        end_date = st.date_input("Data final:", value=today)

st.markdown("---")

# Busca dados
db = SessionLocal()
try:
    dfc_data = ReportService.get_dfc_data(db, client_id, start_date, end_date)
    
    if dfc_data['fluxo_mensal']:
        # KPIs
        st.subheader("📈 Indicadores do Fluxo de Caixa")
        
        total_entradas = sum(f['entradas'] for f in dfc_data['fluxo_mensal'])
        total_saidas = sum(f['saidas'] for f in dfc_data['fluxo_mensal'])
        saldo_final = dfc_data['saldo_final']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💰 Total Entradas",
                format_currency(total_entradas),
                help="Total de entradas no período"
            )
        
        with col2:
            st.metric(
                "💸 Total Saídas",
                format_currency(total_saidas),
                help="Total de saídas no período"
            )
        
        with col3:
            st.metric(
                "📊 Saldo Final",
                format_currency(saldo_final),
                delta=format_currency(saldo_final),
                help="Saldo acumulado no período"
            )
        
        with col4:
            media_mensal = saldo_final / len(dfc_data['fluxo_mensal']) if dfc_data['fluxo_mensal'] else 0
            st.metric(
                "📉 Média Mensal",
                format_currency(media_mensal),
                help="Média de saldo mensal"
            )
        
        st.markdown("---")
        
        # Gráfico de fluxo de caixa
        st.subheader("📊 Fluxo de Caixa Mensal")
        
        meses = [f['mes'] for f in dfc_data['fluxo_mensal']]
        entradas = [f['entradas'] for f in dfc_data['fluxo_mensal']]
        saidas = [f['saidas'] for f in dfc_data['fluxo_mensal']]
        saldo_mes = [f['saldo_mes'] for f in dfc_data['fluxo_mensal']]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Entradas',
            x=meses,
            y=entradas,
            marker_color='#2ecc71',
            text=[format_currency(v) for v in entradas],
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            name='Saídas',
            x=meses,
            y=saidas,
            marker_color='#e74c3c',
            text=[format_currency(v) for v in saidas],
            textposition='auto'
        ))
        
        fig.add_trace(go.Scatter(
            name='Saldo do Mês',
            x=meses,
            y=saldo_mes,
            mode='lines+markers',
            line=dict(color='#3498db', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            barmode='group',
            height=500,
            xaxis_title="Mês",
            yaxis_title="Valor (R$)",
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Gráfico de saldo acumulado
        st.subheader("💰 Saldo Acumulado")
        
        saldo_acumulado = [f['saldo_acumulado'] for f in dfc_data['fluxo_mensal']]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=meses,
            y=saldo_acumulado,
            mode='lines+markers',
            fill='tozeroy',
            line=dict(color='#9b59b6', width=3),
            marker=dict(size=10),
            text=[format_currency(v) for v in saldo_acumulado],
            textposition='top center'
        ))
        
        # Linha zero
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            height=400,
            xaxis_title="Mês",
            yaxis_title="Saldo Acumulado (R$)",
            hovermode='x unified',
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Análise de tendência
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Análise de Tendência")
            
            # Verifica se há tendência de crescimento ou queda
            if len(saldo_acumulado) >= 3:
                ultimos_3 = saldo_acumulado[-3:]
                if ultimos_3[-1] > ultimos_3[0]:
                    st.success("✅ Tendência de **crescimento** no saldo!")
                    variacao = ((ultimos_3[-1] - ultimos_3[0]) / abs(ultimos_3[0]) * 100) if ultimos_3[0] != 0 else 0
                    st.metric("Variação (últimos 3 meses)", f"{variacao:.1f}%")
                elif ultimos_3[-1] < ultimos_3[0]:
                    st.error("⚠️ Tendência de **queda** no saldo!")
                    variacao = ((ultimos_3[-1] - ultimos_3[0]) / abs(ultimos_3[0]) * 100) if ultimos_3[0] != 0 else 0
                    st.metric("Variação (últimos 3 meses)", f"{variacao:.1f}%")
                else:
                    st.info("➡️ Saldo **estável**")
            
            # Previsão simples
            if saldo_final < 0:
                st.warning("⚠️ **Atenção:** Saldo negativo detectado!")
                st.markdown("Recomendações:")
                st.markdown("- Revisar despesas fixas")
                st.markdown("- Buscar aumentar receitas")
                st.markdown("- Considerar renegociação de dívidas")
        
        with col2:
            st.subheader("💡 Insights")
            
            # Mês com maior entrada
            max_entrada_idx = entradas.index(max(entradas))
            st.success(f"**Melhor mês (entradas):** {meses[max_entrada_idx]}")
            st.markdown(f"Valor: {format_currency(entradas[max_entrada_idx])}")
            
            # Mês com maior saída
            max_saida_idx = saidas.index(max(saidas))
            st.error(f"**Maior gasto:** {meses[max_saida_idx]}")
            st.markdown(f"Valor: {format_currency(saidas[max_saida_idx])}")
            
            # Média de entradas vs saídas
            media_entradas = sum(entradas) / len(entradas)
            media_saidas = sum(saidas) / len(saidas)
            
            if media_entradas > media_saidas:
                diferenca = media_entradas - media_saidas
                st.info(f"**Superávit médio mensal:** {format_currency(diferenca)}")
            else:
                diferenca = media_saidas - media_entradas
                st.warning(f"**Déficit médio mensal:** {format_currency(diferenca)}")
        
        st.markdown("---")
        
        # Detalhamento Completo do DFC
        with st.expander("📋 Detalhamento Completo do DFC", expanded=False):
            st.markdown("### 💵 Demonstração do Fluxo de Caixa")
            st.markdown(f"**Cliente:** {client.name}")
            st.markdown(f"**Período:** {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
            st.markdown("---")
            
            # Detalhamento mês a mês
            for fluxo in dfc_data['fluxo_mensal']:
                mes = fluxo['mes']
                entradas_mes = fluxo['entradas']
                saidas_mes = fluxo['saidas']
                saldo_do_mes = fluxo['saldo_mes']
                saldo_acum = fluxo['saldo_acumulado']
                
                # Determina cor do saldo
                saldo_color = "🟢" if saldo_do_mes >= 0 else "🔴"
                
                with st.expander(f"📅 {mes} - Saldo: {saldo_color} {format_currency(saldo_do_mes)}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("💰 Entradas", format_currency(entradas_mes))
                    
                    with col2:
                        st.metric("💸 Saídas", format_currency(saidas_mes))
                    
                    with col3:
                        st.metric("📊 Saldo Acumulado", format_currency(saldo_acum))
                    
                    st.markdown("---")
                    
                    # Busca transações do mês
                    ano, mes_num = mes.split('-')
                    from datetime import date
                    import calendar
                    
                    primeiro_dia = date(int(ano), int(mes_num), 1)
                    ultimo_dia = date(int(ano), int(mes_num), calendar.monthrange(int(ano), int(mes_num))[1])
                    
                    # Entradas do mês
                    st.markdown("#### 💰 Entradas do Mês")
                    trans_entradas = db.query(Transaction).filter(
                        Transaction.client_id == client_id,
                        Transaction.type == 'entrada',
                        Transaction.date >= primeiro_dia,
                        Transaction.date <= ultimo_dia
                    ).order_by(Transaction.date).all()
                    
                    if trans_entradas:
                        # Agrupa por categoria
                        from collections import defaultdict
                        entradas_por_cat = defaultdict(list)
                        for t in trans_entradas:
                            entradas_por_cat[t.category or 'Sem categoria'].append(t)
                        
                        for cat, trans_list in entradas_por_cat.items():
                            total_cat = sum(t.value for t in trans_list)
                            
                            with st.expander(f"📂 {cat} - {format_currency(total_cat)} ({len(trans_list)} transações)"):
                                trans_data = []
                                for t in trans_list[:5]:  # Mostra até 5
                                    trans_data.append({
                                        'Data': format_date(t.date),
                                        'Descrição': t.description[:35] + '...' if len(t.description) > 35 else t.description,
                                        'Valor': format_currency(t.value)
                                    })
                                
                                df_trans = pd.DataFrame(trans_data)
                                st.dataframe(df_trans, use_container_width=True, hide_index=True)
                                
                                if len(trans_list) > 5:
                                    st.caption(f"Mostrando 5 de {len(trans_list)} transações")
                    else:
                        st.info("Nenhuma entrada neste mês")
                    
                    st.markdown("---")
                    
                    # Saídas do mês
                    st.markdown("#### 💸 Saídas do Mês")
                    trans_saidas = db.query(Transaction).filter(
                        Transaction.client_id == client_id,
                        Transaction.type == 'saida',
                        Transaction.date >= primeiro_dia,
                        Transaction.date <= ultimo_dia
                    ).order_by(Transaction.date).all()
                    
                    if trans_saidas:
                        # Agrupa por categoria
                        saidas_por_cat = defaultdict(list)
                        for t in trans_saidas:
                            saidas_por_cat[t.category or 'Sem categoria'].append(t)
                        
                        for cat, trans_list in saidas_por_cat.items():
                            total_cat = sum(t.value for t in trans_list)
                            
                            with st.expander(f"📂 {cat} - {format_currency(total_cat)} ({len(trans_list)} transações)"):
                                trans_data = []
                                for t in trans_list[:5]:  # Mostra até 5
                                    trans_data.append({
                                        'Data': format_date(t.date),
                                        'Descrição': t.description[:35] + '...' if len(t.description) > 35 else t.description,
                                        'Valor': format_currency(t.value)
                                    })
                                
                                df_trans = pd.DataFrame(trans_data)
                                st.dataframe(df_trans, use_container_width=True, hide_index=True)
                                
                                if len(trans_list) > 5:
                                    st.caption(f"Mostrando 5 de {len(trans_list)} transações")
                    else:
                        st.info("Nenhuma saída neste mês")
            
            st.markdown("---")
            st.markdown("---")
            
            # Resumo consolidado
            st.markdown("### 📊 Resumo Consolidado do Período")
            
            df_resumo = pd.DataFrame([
                {
                    'Mês': f['mes'],
                    'Entradas': format_currency(f['entradas']),
                    'Saídas': format_currency(f['saidas']),
                    'Saldo do Mês': format_currency(f['saldo_mes']),
                    'Saldo Acumulado': format_currency(f['saldo_acumulado'])
                }
                for f in dfc_data['fluxo_mensal']
            ])
            
            st.dataframe(df_resumo, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # Estatísticas do período
            st.markdown("### 📈 Estatísticas do Período")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                media_entradas = sum(entradas) / len(entradas) if entradas else 0
                st.metric("Média Entradas/Mês", format_currency(media_entradas))
            
            with col2:
                media_saidas = sum(saidas) / len(saidas) if saidas else 0
                st.metric("Média Saídas/Mês", format_currency(media_saidas))
            
            with col3:
                melhor_mes_idx = saldo_mes.index(max(saldo_mes))
                st.metric("Melhor Mês", meses[melhor_mes_idx])
                st.caption(format_currency(saldo_mes[melhor_mes_idx]))
            
            with col4:
                pior_mes_idx = saldo_mes.index(min(saldo_mes))
                st.metric("Pior Mês", meses[pior_mes_idx])
                st.caption(format_currency(saldo_mes[pior_mes_idx]))
            
            st.markdown("---")
            
            # Projeção simples
            st.markdown("### 🔮 Projeção Simples (próximo mês)")
            
            if len(saldo_mes) >= 3:
                # Média dos últimos 3 meses
                media_saldo_3m = sum(saldo_mes[-3:]) / 3
                projecao_saldo = saldo_acumulado[-1] + media_saldo_3m
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.info(f"**Saldo projetado:** {format_currency(projecao_saldo)}")
                    st.caption(f"Baseado na média dos últimos 3 meses: {format_currency(media_saldo_3m)}")
                
                with col2:
                    if projecao_saldo < 0:
                        st.error("⚠️ **Alerta:** Projeção indica saldo negativo!")
                        st.markdown("**Ações sugeridas:**")
                        st.markdown("- Reduzir despesas não essenciais")
                        st.markdown("- Acelerar recebimentos")
                        st.markdown("- Buscar capital de giro")
                    elif projecao_saldo < saldo_acumulado[-1] * 0.5:
                        st.warning("⚠️ **Atenção:** Projeção indica queda significativa")
                    else:
                        st.success("✅ Projeção positiva para o próximo mês")
    
    else:
        st.info("ℹ️ Nenhuma transação encontrada no período selecionado.")

finally:
    db.close()

