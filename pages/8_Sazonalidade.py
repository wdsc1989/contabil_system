"""
Dashboard de Análise de Sazonalidade
"""
import streamlit as st
import sys
import os
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import calendar
from collections import defaultdict

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
        
        # Análise por Grupo/Subgrupo
        if seasonality_data.get('por_grupo_mes'):
            st.subheader("📊 Sazonalidade por Grupo/Subgrupo")
            
            # Agrupa dados por grupo
            grupos_data = defaultdict(lambda: defaultdict(float))
            for item in seasonality_data['por_grupo_mes']:
                grupo_label = item['grupo_subgrupo']
                mes = item['mes']
                valor = item['valor']
                grupos_data[grupo_label][(item['ano'], mes)] = valor
            
            # Cria gráfico comparativo
            fig = go.Figure()
            
            for grupo_label, data_points in list(grupos_data.items())[:5]:  # Top 5 grupos
                meses_labels = []
                valores = []
                for (year, month) in sorted(data_points.keys()):
                    meses_labels.append(f"{year}-{month:02d}")
                    valores.append(data_points[(year, month)])
                
                fig.add_trace(go.Scatter(
                    x=meses_labels,
                    y=valores,
                    mode='lines+markers',
                    name=grupo_label,
                    line=dict(width=2),
                    marker=dict(size=6)
                ))
            
            fig.update_layout(
                height=500,
                xaxis_title="Período",
                yaxis_title="Receita (R$)",
                hovermode='x unified',
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("---")
        
        # Análise de Eventos (Sazonalidade específica) - APENAS se habilitado
        if 'contracts' in enabled_types:
            st.subheader("🎉 Sazonalidade de Eventos")
            
            from models.contract import Contract
            
            # Busca eventos de todos os anos
            eventos = db.query(Contract).filter(
                Contract.client_id == client_id
            ).all()
        else:
            eventos = []
        
        if eventos:
            # Agrupa por mês
            eventos_por_mes = defaultdict(lambda: {'count': 0, 'revenue': 0})
            eventos_por_tipo_mes = defaultdict(lambda: defaultdict(int))
            
            for ev in eventos:
                mes = ev.event_date.month
                eventos_por_mes[mes]['count'] += 1
                eventos_por_mes[mes]['revenue'] += ev.service_value + (ev.displacement_value or 0)
                
                tipo = ev.event_type or 'Sem tipo'
                eventos_por_tipo_mes[mes][tipo] += 1
            
            # Gráfico de eventos por mês
            meses_nums = list(range(1, 13))
            meses_nomes = [calendar.month_name[m] for m in meses_nums]
            eventos_count = [eventos_por_mes[m]['count'] for m in meses_nums]
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=meses_nomes,
                y=eventos_count,
                marker_color='#9b59b6',
                text=eventos_count,
                textposition='auto'
            ))
            
            fig.update_layout(
                height=350,
                title="Número de Eventos por Mês (Histórico Completo)",
                xaxis_title="Mês",
                yaxis_title="Quantidade de Eventos",
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Insights de sazonalidade de eventos
            max_eventos_mes = max(eventos_count)
            mes_pico = eventos_count.index(max_eventos_mes) + 1
            mes_pico_nome = calendar.month_name[mes_pico]
            
            col_ev1, col_ev2 = st.columns(2)
            
            with col_ev1:
                st.success(f"📈 **Mês com mais eventos:** {mes_pico_nome}")
                st.caption(f"{max_eventos_mes} eventos em média")
            
            with col_ev2:
                # Eventos confirmados próximos 6 meses
                proximos_6m = db.query(Contract).filter(
                    Contract.client_id == client_id,
                    Contract.event_date >= today,
                    Contract.event_date <= today + relativedelta(months=6),
                    Contract.status.in_(['em_andamento', 'concluido'])
                ).count()
                
                st.info(f"📅 **Próximos 6 meses:** {proximos_6m} evento(s) confirmado(s)")
            
            st.markdown("---")
        
        # Análise por Fonte de Dados
        if seasonality_data.get('por_fonte'):
            st.subheader("📌 Receitas por Fonte de Dados")
            
            # Agrupa por fonte
            fontes_data = defaultdict(float)
            for item in seasonality_data['por_fonte']:
                fonte = item['fonte']
                valor = item['valor']
                fontes_data[fonte] += valor
            
            if fontes_data:
                # Gráfico de pizza
                labels = list(fontes_data.keys())
                values = list(fontes_data.values())
                
                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.4,
                    textinfo='label+percent+value',
                    hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>Percentual: %{percent}<extra></extra>'
                )])
                
                fig.update_layout(
                    height=400,
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela de fontes
                fonte_table = []
                for fonte, valor in sorted(fontes_data.items(), key=lambda x: x[1], reverse=True):
                    percentual = (valor / sum(values) * 100) if sum(values) > 0 else 0
                    fonte_table.append({
                        'Fonte': fonte,
                        'Valor Total': format_currency(valor),
                        'Percentual': f"{percentual:.1f}%"
                    })
                
                st.table(pd.DataFrame(fonte_table))
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

