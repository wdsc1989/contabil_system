"""
Página de Diário de Gastos - Controle Diário de Despesas
"""
import streamlit as st
import sys
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import calendar
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from sqlalchemy.orm import joinedload

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from models.client import Client
from models.transaction import Transaction
from models.group import Group, Subgroup
from utils.formatters import format_currency, format_date, format_data_source
from io import BytesIO

st.set_page_config(page_title="Diário de Gastos", page_icon="📓", layout="wide")

# Esconde o menu automático do Streamlit
from utils.hide_auto_menu import hide_streamlit_menu
hide_streamlit_menu()

AuthService.init_session_state()
AuthService.require_auth()

# Usa sidebar centralizada
from utils.sidebar import show_sidebar
show_sidebar()

st.title("📓 Diário de Gastos")
st.markdown("Controle visual e detalhado de suas despesas diárias")
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
st.subheader("📅 Período e Filtros")

col1, col2, col3, col4 = st.columns(4)

with col1:
    period_type = st.selectbox(
        "Período:",
        options=['Mês Atual', 'Semana Atual', 'Últimos 7 dias', 'Últimos 30 dias', 'Personalizado']
    )

today = date.today()

if period_type == 'Mês Atual':
    start_date = date(today.year, today.month, 1)
    end_date = today
elif period_type == 'Semana Atual':
    start_date = today - timedelta(days=today.weekday())
    end_date = today
elif period_type == 'Últimos 7 dias':
    start_date = today - timedelta(days=7)
    end_date = today
elif period_type == 'Últimos 30 dias':
    start_date = today - timedelta(days=30)
    end_date = today
else:  # Personalizado
    with col2:
        start_date = st.date_input("Data inicial:", value=today - timedelta(days=30))
    with col3:
        end_date = st.date_input("Data final:", value=today)

# Filtros adicionais
with col4:
    show_entradas = st.checkbox("Incluir Entradas", value=False, help="Por padrão mostra apenas saídas (gastos)")

st.markdown("---")

# Busca dados
db = SessionLocal()
try:
    # Query base com eager loading
    query = db.query(Transaction).options(
        joinedload(Transaction.group),
        joinedload(Transaction.subgroup)
    ).filter(
        Transaction.client_id == client_id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    )
    
    # Filtro por tipo (padrão: apenas saídas)
    if not show_entradas:
        query = query.filter(Transaction.type == 'saida')
    
    transactions = query.order_by(Transaction.date.desc()).all()
    
    # Filtros avançados na sidebar
    with st.sidebar:
        st.markdown("### 🔍 Filtros Avançados")
        
        # Filtro por categoria
        categorias_disponiveis = list(set([t.category for t in transactions if t.category]))
        if categorias_disponiveis:
            categorias_selecionadas = st.multiselect(
                "Categorias:",
                options=sorted(categorias_disponiveis),
                default=[]
            )
            
            if categorias_selecionadas:
                transactions = [t for t in transactions if t.category in categorias_selecionadas]
        
        # Filtro por grupo
        grupos_disponiveis = list(set([t.group.name for t in transactions if t.group]))
        if grupos_disponiveis:
            grupos_selecionados = st.multiselect(
                "Grupos:",
                options=sorted(grupos_disponiveis),
                default=[]
            )
            
            if grupos_selecionados:
                transactions = [t for t in transactions if t.group and t.group.name in grupos_selecionados]
        
        # Filtro por valor
        if transactions:
            valores = [t.value for t in transactions]
            valor_min = min(valores)
            valor_max = max(valores)
            
            valor_range = st.slider(
                "Faixa de valor:",
                min_value=float(valor_min),
                max_value=float(valor_max),
                value=(float(valor_min), float(valor_max)),
                format="R$ %.2f"
            )
            
            transactions = [t for t in transactions if valor_range[0] <= t.value <= valor_range[1]]
        
        if st.button("🔄 Limpar Filtros", use_container_width=True):
            st.rerun()
    
    if transactions:
        # KPIs
        st.subheader("📊 Indicadores do Período")
        
        total = sum(t.value for t in transactions)
        dias_periodo = (end_date - start_date).days + 1
        media_diaria = total / dias_periodo if dias_periodo > 0 else 0
        maior_gasto = max(t.value for t in transactions)
        menor_gasto = min(t.value for t in transactions)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💰 Total do Período",
                format_currency(total),
                help=f"{len(transactions)} lançamentos"
            )
        
        with col2:
            st.metric(
                "📊 Média Diária",
                format_currency(media_diaria),
                help=f"Total / {dias_periodo} dias"
            )
        
        with col3:
            maior_trans = max(transactions, key=lambda t: t.value)
            st.metric(
                "📈 Maior Gasto",
                format_currency(maior_gasto),
                help=f"{maior_trans.description[:30]}..."
            )
        
        with col4:
            menor_trans = min(transactions, key=lambda t: t.value)
            st.metric(
                "📉 Menor Gasto",
                format_currency(menor_gasto),
                help=f"{menor_trans.description[:30]}..."
            )
        
        st.markdown("---")
        
        # Calendário Heatmap
        st.subheader("📅 Calendário de Gastos")
        
        # Agrupa por dia
        gastos_por_dia = defaultdict(float)
        for t in transactions:
            gastos_por_dia[t.date] += t.value
        
        # Cria matriz para heatmap (semanas x dias da semana)
        # Pega todas as datas do período
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Organiza em semanas
        semanas = defaultdict(lambda: {i: 0 for i in range(7)})  # 0=Segunda, 6=Domingo
        
        for dt in date_range:
            dia_semana = dt.weekday()
            semana_num = dt.isocalendar()[1]  # Número da semana no ano
            valor = gastos_por_dia.get(dt.date(), 0)
            semanas[semana_num][dia_semana] = valor
        
        # Cria heatmap
        if semanas:
            semanas_ordenadas = sorted(semanas.keys())
            dias_semana_labels = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
            
            z_values = []
            hover_text = []
            
            for semana in semanas_ordenadas:
                row = []
                hover_row = []
                for dia in range(7):
                    valor = semanas[semana][dia]
                    row.append(valor)
                    hover_row.append(f"Semana {semana}<br>{dias_semana_labels[dia]}<br>{format_currency(valor)}")
                z_values.append(row)
                hover_text.append(hover_row)
            
            fig = go.Figure(data=go.Heatmap(
                z=z_values,
                x=dias_semana_labels,
                y=[f"S{s}" for s in semanas_ordenadas],
                colorscale='RdYlGn_r',  # Vermelho = alto, Verde = baixo
                text=[[format_currency(v) if v > 0 else '' for v in row] for row in z_values],
                texttemplate='%{text}',
                textfont={"size": 9},
                hovertext=hover_text,
                hovertemplate='%{hovertext}<extra></extra>',
                colorbar=dict(title="Gastos (R$)")
            ))
            
            fig.update_layout(
                height=min(400, len(semanas_ordenadas) * 60),
                xaxis_title="Dia da Semana",
                yaxis_title="Semana",
                title="Heatmap de Gastos por Dia"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Gráficos de Análise
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Evolução Diária")
            
            # Agrupa por dia para gráfico de linha
            df_diario = pd.DataFrame([
                {'data': dt, 'valor': gastos_por_dia.get(dt, 0)}
                for dt in date_range
            ])
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df_diario['data'],
                y=df_diario['valor'],
                mode='lines+markers',
                fill='tozeroy',
                line=dict(color='#e74c3c', width=2),
                marker=dict(size=6),
                text=[format_currency(v) for v in df_diario['valor']],
                hovertemplate='%{x|%d/%m/%Y}<br>%{text}<extra></extra>'
            ))
            
            # Linha de média
            fig.add_hline(
                y=media_diaria,
                line_dash="dash",
                line_color="blue",
                annotation_text=f"Média: {format_currency(media_diaria)}",
                annotation_position="right"
            )
            
            fig.update_layout(
                height=400,
                xaxis_title="Data",
                yaxis_title="Gastos (R$)",
                showlegend=False,
                hovermode='x'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🥧 Distribuição por Categoria")
            
            # Agrupa por categoria
            gastos_por_categoria = defaultdict(float)
            for t in transactions:
                cat = t.category or 'Sem categoria'
                gastos_por_categoria[cat] += t.value
            
            if gastos_por_categoria:
                labels = list(gastos_por_categoria.keys())
                values = list(gastos_por_categoria.values())
                
                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.4,
                    textinfo='label+percent',
                    textposition='inside',
                    hovertemplate='<b>%{label}</b><br>%{value:,.2f} R$<br>%{percent}<extra></extra>'
                )])
                
                fig.update_layout(
                    height=400,
                    showlegend=True,
                    legend=dict(orientation="v", yanchor="middle", y=0.5)
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Top 10 Grupos/Subgrupos
        st.subheader("📊 Top 10 Categorias de Gastos")
        
        gastos_por_grupo_subgrupo = defaultdict(float)
        for t in transactions:
            if t.group and t.subgroup:
                label = f"{t.group.name} > {t.subgroup.name}"
            elif t.group:
                label = t.group.name
            elif t.category:
                label = t.category
            else:
                label = 'Sem classificação'
            
            gastos_por_grupo_subgrupo[label] += t.value
        
        if gastos_por_grupo_subgrupo:
            # Ordena e pega top 10
            top_10 = sorted(gastos_por_grupo_subgrupo.items(), key=lambda x: x[1], reverse=True)[:10]
            
            labels = [item[0] for item in top_10]
            valores = [item[1] for item in top_10]
            percentuais = [(v / total * 100) if total > 0 else 0 for v in valores]
            
            fig = go.Figure(data=[go.Bar(
                y=labels,
                x=valores,
                orientation='h',
                marker_color='#e74c3c',
                text=[f"{format_currency(v)} ({p:.1f}%)" for v, p in zip(valores, percentuais)],
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>%{x:,.2f} R$<extra></extra>'
            )])
            
            fig.update_layout(
                height=max(400, len(top_10) * 40),
                xaxis_title="Valor (R$)",
                yaxis_title="",
                showlegend=False,
                yaxis={'categoryorder': 'total ascending'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Análises e Insights
        st.subheader("💡 Análises e Insights")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 📊 Comparativo")
            
            # Período anterior
            dias = (end_date - start_date).days
            start_anterior = start_date - timedelta(days=dias + 1)
            end_anterior = start_date - timedelta(days=1)
            
            query_anterior = db.query(Transaction).filter(
                Transaction.client_id == client_id,
                Transaction.date >= start_anterior,
                Transaction.date <= end_anterior
            )
            
            if not show_entradas:
                query_anterior = query_anterior.filter(Transaction.type == 'saida')
            
            trans_anterior = query_anterior.all()
            total_anterior = sum(t.value for t in trans_anterior)
            
            variacao = total - total_anterior
            variacao_perc = (variacao / total_anterior * 100) if total_anterior > 0 else 0
            
            st.metric(
                "vs Período Anterior",
                format_currency(total),
                delta=f"{variacao_perc:+.1f}%",
                delta_color="inverse"
            )
            
            st.caption(f"Anterior: {format_currency(total_anterior)}")
        
        with col2:
            st.markdown("#### 🎯 Tendência")
            
            # Calcula tendência dos últimos 7 dias
            if len(transactions) >= 7:
                ultimos_7_dias = sorted([t.date for t in transactions if t.date >= today - timedelta(days=7)])
                if len(ultimos_7_dias) >= 2:
                    gastos_inicio = sum(t.value for t in transactions if t.date == ultimos_7_dias[0])
                    gastos_fim = sum(t.value for t in transactions if t.date >= ultimos_7_dias[-1])
                    
                    if gastos_fim > gastos_inicio:
                        st.error("📈 Gastos crescentes")
                        st.caption("Últimos 7 dias mostram aumento")
                    elif gastos_fim < gastos_inicio:
                        st.success("📉 Gastos decrescentes")
                        st.caption("Últimos 7 dias mostram redução")
                    else:
                        st.info("➡️ Gastos estáveis")
                        st.caption("Sem variação significativa")
        
        with col3:
            st.markdown("#### ⚠️ Alertas")
            
            # Identifica outliers (gastos muito acima da média)
            if len(transactions) > 3:
                outliers = [t for t in transactions if t.value > media_diaria * 3]
                
                if outliers:
                    st.warning(f"{len(outliers)} gasto(s) anormais")
                    st.caption(f"Acima de {format_currency(media_diaria * 3)}")
                    
                    # Mostra maior outlier
                    maior_outlier = max(outliers, key=lambda t: t.value)
                    st.caption(f"Ex: {maior_outlier.description[:25]}... - {format_currency(maior_outlier.value)}")
                else:
                    st.success("✅ Gastos regulares")
                    st.caption("Nenhum outlier detectado")
        
        st.markdown("---")
        
        # Tabela de Lançamentos
        st.subheader("📋 Lançamentos Detalhados")
        
        # Opções de visualização
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            ordenacao = st.selectbox(
                "Ordenar por:",
                options=['Data (recente)', 'Data (antiga)', 'Valor (maior)', 'Valor (menor)', 'Descrição'],
                index=0
            )
        
        with col2:
            limite = st.selectbox(
                "Exibir:",
                options=[50, 100, 200, 'Todos'],
                index=0
            )
        
        with col3:
            formato_exibicao = st.selectbox(
                "Formato:",
                options=['Tabela', 'Lista Detalhada'],
                index=0
            )
        
        # Aplica ordenação
        if ordenacao == 'Data (recente)':
            transactions_sorted = sorted(transactions, key=lambda t: t.date, reverse=True)
        elif ordenacao == 'Data (antiga)':
            transactions_sorted = sorted(transactions, key=lambda t: t.date)
        elif ordenacao == 'Valor (maior)':
            transactions_sorted = sorted(transactions, key=lambda t: t.value, reverse=True)
        elif ordenacao == 'Valor (menor)':
            transactions_sorted = sorted(transactions, key=lambda t: t.value)
        else:  # Descrição
            transactions_sorted = sorted(transactions, key=lambda t: t.description.lower())
        
        # Aplica limite
        if limite != 'Todos':
            transactions_display = transactions_sorted[:limite]
        else:
            transactions_display = transactions_sorted
        
        # Exibe conforme formato
        if formato_exibicao == 'Tabela':
            # Prepara dados para tabela
            tabela_data = []
            for t in transactions_display:
                grupo = t.group.name if t.group else '-'
                subgrupo = t.subgroup.name if t.subgroup else '-'
                origem = format_data_source(t.document_type, t.imported_from)
                
                tabela_data.append({
                    'Data': format_date(t.date),
                    'Descrição': t.description,
                    'Valor': format_currency(t.value),
                    'Tipo': '💰 Entrada' if t.type == 'entrada' else '💸 Saída',
                    'Categoria': t.category or '-',
                    'Grupo': grupo,
                    'Subgrupo': subgrupo,
                    'Origem': origem,
                    'ID': t.id
                })
            
            df_tabela = pd.DataFrame(tabela_data)
            
            # Remove coluna ID se não for admin
            user = AuthService.get_current_user()
            if user['role'] not in ['admin', 'manager']:
                df_tabela = df_tabela.drop(columns=['ID'])
            
            st.dataframe(
                df_tabela,
                use_container_width=True,
                height=min(600, len(df_tabela) * 35 + 38),
                hide_index=True
            )
            
            st.caption(f"Exibindo {len(transactions_display)} de {len(transactions)} lançamentos")
            
        else:  # Lista Detalhada
            # Agrupa por dia
            trans_por_dia = defaultdict(list)
            for t in transactions_display:
                trans_por_dia[t.date].append(t)
            
            for dia in sorted(trans_por_dia.keys(), reverse=True):
                trans_dia = trans_por_dia[dia]
                total_dia = sum(t.value for t in trans_dia)
                
                dia_semana = calendar.day_name[dia.weekday()]
                
                with st.expander(f"📅 {format_date(dia)} ({dia_semana}) - {format_currency(total_dia)} ({len(trans_dia)} lançamentos)"):
                    for t in trans_dia:
                        col_det1, col_det2, col_det3 = st.columns([2, 1, 1])
                        
                        with col_det1:
                            tipo_icon = '💰' if t.type == 'entrada' else '💸'
                            st.markdown(f"{tipo_icon} **{t.description}**")
                            grupo = t.group.name if t.group else 'Sem grupo'
                            subgrupo = t.subgroup.name if t.subgroup else 'Sem subgrupo'
                            st.caption(f"{grupo} > {subgrupo}")
                        
                        with col_det2:
                            st.markdown(f"**{format_currency(t.value)}**")
                            if t.category:
                                st.caption(f"🏷️ {t.category}")
                        
                        with col_det3:
                            origem = format_data_source(t.document_type, t.imported_from)
                            st.caption(f"📄 {origem}")
                        
                        st.markdown("---")
        
        st.markdown("---")
        
        # Botões de Ação
        st.subheader("⚡ Ações")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export para Excel
            if st.button("📥 Exportar para Excel", use_container_width=True):
                # Prepara dados
                export_data = []
                for t in transactions:
                    grupo = t.group.name if t.group else ''
                    subgrupo = t.subgroup.name if t.subgroup else ''
                    origem = format_data_source(t.document_type, t.imported_from)
                    
                    export_data.append({
                        'Data': t.date.strftime('%d/%m/%Y'),
                        'Descrição': t.description,
                        'Valor': t.value,
                        'Tipo': t.type,
                        'Categoria': t.category or '',
                        'Grupo': grupo,
                        'Subgrupo': subgrupo,
                        'Conta': t.account or '',
                        'Origem': origem
                    })
                
                df_export = pd.DataFrame(export_data)
                
                # Cria Excel em memória
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_export.to_excel(writer, sheet_name='Diário de Gastos', index=False)
                
                output.seek(0)
                
                st.download_button(
                    label="⬇️ Download Excel",
                    data=output.getvalue(),
                    file_name=f"diario_gastos_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        with col2:
            # Análise detalhada
            if st.button("📊 Ver Análise Detalhada", use_container_width=True):
                st.info("💡 Use os relatórios DRE, DFC e Sazonalidade para análises aprofundadas")
                st.page_link("pages/6_DRE.py", label="📈 Ir para DRE", icon="📊")
                st.page_link("pages/7_DFC.py", label="💵 Ir para DFC", icon="💵")
        
        with col3:
            # Nova transação
            if st.button("➕ Adicionar Lançamento", use_container_width=True):
                st.info("Use a página de Transações para adicionar manualmente")
                st.page_link("pages/2_Transacoes.py", label="💳 Ir para Transações", icon="💳")
        
        st.markdown("---")
        
        # Estatísticas Avançadas
        with st.expander("📈 Estatísticas Avançadas"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Distribuição Temporal")
                
                # Gastos por dia da semana
                gastos_por_dia_semana = defaultdict(float)
                for t in transactions:
                    dia_semana = calendar.day_name[t.date.weekday()]
                    gastos_por_dia_semana[dia_semana] += t.value
                
                dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
                
                valores_semana = [gastos_por_dia_semana[dia] for dia in dias_ordem]
                
                fig = go.Figure(data=[go.Bar(
                    x=dias_pt,
                    y=valores_semana,
                    marker_color='#3498db',
                    text=[format_currency(v) if v > 0 else '' for v in valores_semana],
                    textposition='auto'
                )])
                
                fig.update_layout(
                    height=300,
                    xaxis_title="Dia da Semana",
                    yaxis_title="Total (R$)",
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### 🏷️ Top 5 Descrições")
                
                # Conta ocorrências de descrições
                desc_count = defaultdict(lambda: {'count': 0, 'total': 0})
                for t in transactions:
                    desc = t.description[:50]  # Limita tamanho
                    desc_count[desc]['count'] += 1
                    desc_count[desc]['total'] += t.value
                
                top_desc = sorted(desc_count.items(), key=lambda x: x[1]['total'], reverse=True)[:5]
                
                desc_data = []
                for desc, info in top_desc:
                    desc_data.append({
                        'Descrição': desc,
                        'Qtd': info['count'],
                        'Total': format_currency(info['total']),
                        'Média': format_currency(info['total'] / info['count'])
                    })
                
                if desc_data:
                    st.dataframe(pd.DataFrame(desc_data), use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Alertas Automáticos
        if len(transactions) > 0:
            st.subheader("🚨 Alertas e Recomendações")
            
            alertas = []
            
            # Dias sem lançamentos
            dias_com_lancamento = set(t.date for t in transactions)
            dias_sem_lancamento = [dt for dt in date_range if dt not in dias_com_lancamento]
            
            if len(dias_sem_lancamento) > dias_periodo * 0.3:  # Mais de 30% sem lançamento
                alertas.append({
                    'tipo': 'warning',
                    'mensagem': f"⚠️ {len(dias_sem_lancamento)} dia(s) sem lançamentos. Verifique se há gastos não registrados."
                })
            
            # Gastos muito acima da média
            outliers_criticos = [t for t in transactions if t.value > media_diaria * 5]
            if outliers_criticos:
                alertas.append({
                    'tipo': 'info',
                    'mensagem': f"📌 {len(outliers_criticos)} gasto(s) muito acima da média. Revise se são despesas excepcionais."
                })
            
            # Crescimento acelerado
            if variacao_perc > 20:
                alertas.append({
                    'tipo': 'error',
                    'mensagem': f"🔴 Gastos aumentaram {variacao_perc:.1f}% em relação ao período anterior. Atenção ao controle!"
                })
            elif variacao_perc < -20:
                alertas.append({
                    'tipo': 'success',
                    'mensagem': f"🟢 Gastos reduziram {abs(variacao_perc):.1f}% em relação ao período anterior. Ótimo controle!"
                })
            
            # Exibe alertas
            if alertas:
                for alerta in alertas:
                    if alerta['tipo'] == 'error':
                        st.error(alerta['mensagem'])
                    elif alerta['tipo'] == 'warning':
                        st.warning(alerta['mensagem'])
                    elif alerta['tipo'] == 'success':
                        st.success(alerta['mensagem'])
                    else:
                        st.info(alerta['mensagem'])
            else:
                st.success("✅ Nenhum alerta. Gastos sob controle!")
    
    else:
        st.info("ℹ️ Nenhuma transação encontrada no período selecionado.")
        st.markdown("---")
        st.markdown("### 💡 Como começar?")
        st.markdown("1. Importe seu diário de gastos (Excel ou CSV) em **Importação de Dados**")
        st.markdown("2. Ou adicione lançamentos manualmente em **Transações**")
        st.page_link("pages/2_Importacao_Dados.py", label="📥 Ir para Importação", icon="📥")
        st.page_link("pages/2_Transacoes.py", label="💳 Ir para Transações", icon="💳")

finally:
    db.close()

