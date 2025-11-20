"""
Dashboard de Análise de Sazonalidade
"""
import streamlit as st
import sys
import os
import plotly.graph_objects as go
import plotly.express as px
import calendar

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from services.report_service import ReportService
from services.report_config_service import ReportConfigService, DATA_TYPES
from models.client import Client
from utils.formatters import format_currency

st.set_page_config(page_title="Sazonalidade", page_icon="📈", layout="wide")

# Esconde o menu automático do Streamlit
from utils.hide_auto_menu import hide_streamlit_menu
hide_streamlit_menu()

AuthService.init_session_state()
AuthService.require_auth()


# Usa sidebar centralizada
from utils.sidebar import show_sidebar
show_sidebar()

st.title("📈 Análise de Sazonalidade")
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

st.markdown("""
Esta análise identifica padrões sazonais nas receitas ao longo dos meses e anos,
ajudando no planejamento comercial e financeiro.
""")

st.markdown("---")

# Busca dados
db = SessionLocal()
try:
    seasonality_data = ReportService.get_seasonality_data(db, client_id)
    
    # Mostra tipos de dados incluídos no relatório
    enabled_types = seasonality_data.get('enabled_data_types', [])
    if enabled_types:
        st.info(f"📊 **Tipos de dados incluídos na Sazonalidade:** {', '.join([DATA_TYPES.get(dt, dt) for dt in enabled_types])}")
    
    if seasonality_data['por_ano']:
        # Média mensal
        st.subheader("📊 Média de Receitas por Mês")
        
        month_names = [calendar.month_name[m['mes']] for m in seasonality_data['media_mensal']]
        month_values = [m['media'] for m in seasonality_data['media_mensal']]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=month_names,
            y=month_values,
            marker_color='#3498db',
            text=[format_currency(v) for v in month_values],
            textposition='auto'
        ))
        
        # Linha de média geral
        media_geral = sum(month_values) / len(month_values) if month_values else 0
        fig.add_hline(
            y=media_geral,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Média: {format_currency(media_geral)}",
            annotation_position="right"
        )
        
        fig.update_layout(
            height=500,
            xaxis_title="Mês",
            yaxis_title="Receita Média (R$)",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Heatmap por ano
        st.subheader("🔥 Heatmap de Receitas por Ano e Mês")
        
        # Prepara dados para heatmap
        anos = sorted(seasonality_data['por_ano'].keys())
        meses = list(range(1, 13))
        
        # Matriz de valores
        z_values = []
        for ano in anos:
            row = []
            for mes in meses:
                valor = seasonality_data['por_ano'][ano].get(mes, 0)
                row.append(valor)
            z_values.append(row)
        
        fig = go.Figure(data=go.Heatmap(
            z=z_values,
            x=[calendar.month_abbr[m] for m in meses],
            y=[str(ano) for ano in anos],
            colorscale='RdYlGn',
            text=[[format_currency(v) for v in row] for row in z_values],
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(title="Receita (R$)")
        ))
        
        fig.update_layout(
            height=400,
            xaxis_title="Mês",
            yaxis_title="Ano"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Comparação ano a ano
        st.subheader("📊 Comparação Ano a Ano")
        
        fig = go.Figure()
        
        for ano in anos:
            valores_ano = [seasonality_data['por_ano'][ano].get(mes, 0) for mes in meses]
            
            fig.add_trace(go.Scatter(
                x=[calendar.month_abbr[m] for m in meses],
                y=valores_ano,
                mode='lines+markers',
                name=str(ano),
                line=dict(width=3),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            height=500,
            xaxis_title="Mês",
            yaxis_title="Receita (R$)",
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
        
        # Insights
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💡 Insights de Sazonalidade")
            
            # Mês com maior média
            max_month_idx = month_values.index(max(month_values))
            max_month_name = month_names[max_month_idx]
            
            st.success(f"**Melhor mês (média):** {max_month_name}")
            st.markdown(f"Receita média: {format_currency(month_values[max_month_idx])}")
            
            # Mês com menor média
            min_month_idx = month_values.index(min(month_values))
            min_month_name = month_names[min_month_idx]
            
            st.error(f"**Pior mês (média):** {min_month_name}")
            st.markdown(f"Receita média: {format_currency(month_values[min_month_idx])}")
            
            # Variação
            variacao = ((month_values[max_month_idx] - month_values[min_month_idx]) / month_values[min_month_idx] * 100) if month_values[min_month_idx] > 0 else 0
            st.info(f"**Variação sazonal:** {variacao:.1f}%")
        
        with col2:
            st.subheader("📋 Recomendações")
            
            # Identifica meses fortes e fracos
            meses_fortes = [month_names[i] for i, v in enumerate(month_values) if v > media_geral]
            meses_fracos = [month_names[i] for i, v in enumerate(month_values) if v < media_geral]
            
            if meses_fortes:
                st.markdown("**Meses fortes (acima da média):**")
                st.markdown(", ".join(meses_fortes))
                st.markdown("💡 *Aproveite para investir em marketing e expansão*")
            
            st.markdown("---")
            
            if meses_fracos:
                st.markdown("**Meses fracos (abaixo da média):**")
                st.markdown(", ".join(meses_fracos))
                st.markdown("💡 *Planeje promoções e ações para aumentar vendas*")
        
        st.markdown("---")
        
        # Análise de crescimento ano a ano
        if len(anos) >= 2:
            st.subheader("📈 Crescimento Ano a Ano")
            
            crescimento_data = []
            for i in range(1, len(anos)):
                ano_anterior = anos[i-1]
                ano_atual = anos[i]
                
                total_anterior = sum(seasonality_data['por_ano'][ano_anterior].values())
                total_atual = sum(seasonality_data['por_ano'][ano_atual].values())
                
                crescimento = ((total_atual - total_anterior) / total_anterior * 100) if total_anterior > 0 else 0
                
                crescimento_data.append({
                    'periodo': f"{ano_anterior} → {ano_atual}",
                    'ano_anterior': total_anterior,
                    'ano_atual': total_atual,
                    'crescimento': crescimento
                })
            
            col1, col2, col3 = st.columns(3)
            
            for i, data in enumerate(crescimento_data):
                with [col1, col2, col3][i % 3]:
                    st.metric(
                        data['periodo'],
                        format_currency(data['ano_atual']),
                        delta=f"{data['crescimento']:+.1f}%"
                    )
        
        st.markdown("---")
        
        # Tabela detalhada
        with st.expander("📋 Dados Detalhados"):
            import pandas as pd
            
            # Cria DataFrame
            df_data = []
            for ano in anos:
                for mes in meses:
                    valor = seasonality_data['por_ano'][ano].get(mes, 0)
                    if valor > 0:
                        df_data.append({
                            'Ano': ano,
                            'Mês': calendar.month_name[mes],
                            'Receita': format_currency(valor)
                        })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    else:
        st.info("ℹ️ Não há dados suficientes para análise de sazonalidade. Importe transações de pelo menos 2 anos.")

finally:
    db.close()

