"""
Página de Visualização e Gestão de Extratos Bancários
"""
import streamlit as st
import sys
import os
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from models.client import Client
from models.transaction import BankStatement, Transaction
from utils.formatters import format_currency, format_date
from utils.ui_components import show_client_selector, show_sidebar_navigation

st.set_page_config(page_title="Extratos Bancários", page_icon="🏦", layout="wide")

AuthService.init_session_state()
AuthService.require_auth()

show_sidebar_navigation()

st.title("🏦 Extratos Bancários")

# Seletor de cliente no topo da página
client_id = show_client_selector()

if not client_id:
    st.warning("⚠️ Nenhum cliente disponível.")
    st.stop()

st.markdown("---")

db = SessionLocal()
try:
    client = db.query(Client).filter(Client.id == client_id).first()
finally:
    db.close()

# Tabs
tab1, tab2, tab3 = st.tabs(["📋 Lista de Extratos", "➕ Novo Extrato", "📊 Análise e Estatísticas"])

db = SessionLocal()

try:
    # TAB 1: Lista de Extratos
    with tab1:
        st.subheader("Extratos Bancários Importados")
        
        # Filtros
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Lista de bancos únicos (busca de transactions)
            banks = db.query(Transaction.bank_name).filter(
                Transaction.client_id == client_id,
                Transaction.document_type == 'extrato_bancario',
                Transaction.bank_name.isnot(None)
            ).distinct().all()
            bank_options = [None] + [b[0] for b in banks if b[0]]
            selected_bank = st.selectbox(
                "Banco:",
                options=bank_options,
                format_func=lambda x: "Todos" if x is None else x
            )
        
        with col2:
            # Lista de contas únicas (busca de transactions)
            accounts = db.query(Transaction.account).filter(
                Transaction.client_id == client_id,
                Transaction.document_type == 'extrato_bancario',
                Transaction.account.isnot(None)
            ).distinct().all()
            account_options = [None] + [a[0] for a in accounts if a[0]]
            selected_account = st.selectbox(
                "Conta:",
                options=account_options,
                format_func=lambda x: "Todas" if x is None else x
            )
        
        with col3:
            date_from = st.date_input("Data de:", value=None, key="extrato_from")
        
        with col4:
            date_to = st.date_input("Data até:", value=None, key="extrato_to")
        
        # Busca por descrição
        search = st.text_input("🔍 Buscar na descrição:", placeholder="Digite para buscar...")
        
        # Query de extratos (busca de transactions onde document_type == 'extrato_bancario')
        query = db.query(Transaction).filter(
            Transaction.client_id == client_id,
            Transaction.document_type == 'extrato_bancario'
        )
        
        if selected_bank:
            query = query.filter(Transaction.bank_name == selected_bank)
        
        if selected_account:
            query = query.filter(Transaction.account == selected_account)
        
        if date_from:
            query = query.filter(Transaction.date >= date_from)
        
        if date_to:
            query = query.filter(Transaction.date <= date_to)
        
        if search:
            query = query.filter(Transaction.description.contains(search))
        
        statements = query.order_by(Transaction.date.desc()).all()
        
        if statements:
            # Estatísticas
            col1, col2, col3, col4 = st.columns(4)
            
            # Calcula usando type (entrada/saida) ao invés de valor positivo/negativo
            total_creditos = sum(s.value for s in statements if s.type == 'entrada')
            total_debitos = sum(s.value for s in statements if s.type == 'saida')
            saldo_final = total_creditos - total_debitos
            
            with col1:
                st.metric("💰 Total Créditos", format_currency(total_creditos))
            
            with col2:
                st.metric("💸 Total Débitos", format_currency(total_debitos))
            
            with col3:
                st.metric("📊 Saldo Final", format_currency(saldo_final))
            
            with col4:
                st.metric("📝 Total de Registros", len(statements))
            
            st.markdown("---")
            
            # Tabela de extratos
            st.subheader("Extratos")
            
            # Busca saldos de bank_statements para exibição (join opcional)
            # Cria mapeamento de saldos por data/descrição/valor para join rápido
            statement_ids = [s.id for s in statements]
            bank_statements_map = {}
            if statement_ids:
                # Busca bank_statements correspondentes para obter saldo
                bank_stmts = db.query(BankStatement).filter(
                    BankStatement.client_id == client_id
                ).all()
                # Mapeia por data, descrição e valor para encontrar correspondência
                for bs in bank_stmts:
                    key = (bs.date, bs.description, abs(bs.value))
                    bank_statements_map[key] = bs.balance
            
            # Preparar dados para tabela
            statements_data = []
            for stmt in statements:
                tipo_icon = '💰' if stmt.type == 'entrada' else '💸'
                # Identifica origem: manual ou importado (baseado em imported_from)
                origem = "📝 Manual"
                if stmt.imported_from and stmt.imported_from != 'manual':
                    origem = "📥 Importado"
                
                # Busca saldo correspondente (se existir)
                balance = None
                key = (stmt.date, stmt.description, stmt.value)
                if key in bank_statements_map:
                    balance = bank_statements_map[key]
                
                statements_data.append({
                    'ID': stmt.id,
                    'Data': format_date(stmt.date),
                    'Banco': stmt.bank_name or '-',
                    'Conta': stmt.account or '-',
                    'Descrição': stmt.description[:60] + '...' if len(stmt.description) > 60 else stmt.description,
                    'Valor': format_currency(stmt.value),
                    'Saldo': format_currency(balance) if balance is not None else '-',
                    'Tipo': f"{tipo_icon} {'Crédito' if stmt.type == 'entrada' else 'Débito'}",
                    'Origem': origem,
                    'Importado em': format_date(stmt.created_at.date()) if stmt.created_at else '-'
                })
            
            df = pd.DataFrame(statements_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.caption(f"Mostrando {len(statements)} extrato(s) no filtro selecionado.")
            
            st.markdown("---")
            
            # Ações
            st.subheader("✏️ Editar/Excluir Extrato")
            
            selected_stmt_id = st.selectbox(
                "Selecione um extrato para editar/excluir:",
                options=[s.id for s in statements],
                format_func=lambda x: f"ID {x} - {format_date([s.date for s in statements if s.id == x][0])} - {format_currency([s.value for s in statements if s.id == x][0])}"
            )
            
            if selected_stmt_id:
                selected_stmt = db.query(Transaction).filter(Transaction.id == selected_stmt_id).first()
                
                if selected_stmt:
                    # Busca saldo correspondente em bank_statements (se existir)
                    balance = None
                    bank_stmt = db.query(BankStatement).filter(
                        BankStatement.client_id == client_id,
                        BankStatement.date == selected_stmt.date,
                        BankStatement.description == selected_stmt.description,
                        BankStatement.value == (selected_stmt.value if selected_stmt.type == 'entrada' else -selected_stmt.value)
                    ).first()
                    if bank_stmt:
                        balance = bank_stmt.balance
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Dados atuais:**")
                        st.write(f"**Data:** {format_date(selected_stmt.date)}")
                        st.write(f"**Banco:** {selected_stmt.bank_name or '-'}")
                        st.write(f"**Conta:** {selected_stmt.account or '-'}")
                        st.write(f"**Descrição:** {selected_stmt.description}")
                        st.write(f"**Valor:** {format_currency(selected_stmt.value)}")
                        st.write(f"**Tipo:** {'Entrada' if selected_stmt.type == 'entrada' else 'Saída'}")
                        st.write(f"**Saldo:** {format_currency(balance) if balance is not None else '-'}")
                    
                    with col2:
                        st.markdown("**Editar:**")
                        
                        new_date = st.date_input("Data:", value=selected_stmt.date, key="edit_date")
                        new_bank = st.text_input("Banco:", value=selected_stmt.bank_name or "", key="edit_bank")
                        new_account = st.text_input("Conta:", value=selected_stmt.account or "", key="edit_account")
                        new_description = st.text_area("Descrição:", value=selected_stmt.description, key="edit_desc")
                        new_value = st.number_input("Valor:", value=float(selected_stmt.value), key="edit_value")
                        new_type = st.selectbox("Tipo:", options=['entrada', 'saida'], index=0 if selected_stmt.type == 'entrada' else 1, key="edit_type")
                        new_balance = st.number_input("Saldo (referência):", value=float(balance) if balance is not None else None, key="edit_balance")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        
                        with col_btn1:
                            if st.button("💾 Salvar Alterações", use_container_width=True, type="primary"):
                                selected_stmt.date = new_date
                                selected_stmt.bank_name = new_bank if new_bank else None
                                selected_stmt.account = new_account if new_account else None
                                selected_stmt.description = new_description
                                selected_stmt.value = new_value
                                selected_stmt.type = new_type
                                
                                # Atualiza saldo em bank_statements se existir
                                if bank_stmt and new_balance is not None:
                                    bank_stmt.balance = new_balance
                                
                                db.commit()
                                st.success("✅ Extrato atualizado com sucesso!")
                                st.rerun()
                        
                        with col_btn2:
                            if st.button("🗑️ Excluir Extrato", use_container_width=True):
                                # Remove também o bank_statement correspondente se existir
                                if bank_stmt:
                                    db.delete(bank_stmt)
                                db.delete(selected_stmt)
                                db.commit()
                                st.success("✅ Extrato excluído com sucesso!")
                                st.rerun()
            
            st.markdown("---")
            
            # Nota sobre conversão automática
            st.subheader("ℹ️ Sobre Extratos Bancários")
            st.info("""
            **💡 Informação Importante:**
            - Os extratos bancários são automaticamente convertidos em transações ao serem importados
            - Esta página mostra as transações que foram criadas a partir de extratos bancários
            - Todas essas transações já aparecem nos relatórios DRE e DFC
            - A tabela `bank_statements` é mantida apenas para referência histórica e conciliação bancária
            """)
            
            st.markdown("---")
            
            # Exportar para Excel
            st.subheader("📥 Exportar Dados")
            
            col_exp1, col_exp2 = st.columns(2)
            
            with col_exp1:
                if st.button("📊 Exportar para Excel", use_container_width=True):
                    # Busca saldos para exportação
                    export_bank_statements_map = {}
                    bank_stmts_export = db.query(BankStatement).filter(
                        BankStatement.client_id == client_id
                    ).all()
                    for bs in bank_stmts_export:
                        key = (bs.date, bs.description, abs(bs.value))
                        export_bank_statements_map[key] = bs.balance
                    
                    # Prepara dados para exportação
                    export_data = []
                    for s in statements:
                        balance = None
                        key = (s.date, s.description, s.value)
                        if key in export_bank_statements_map:
                            balance = export_bank_statements_map[key]
                        
                        export_data.append({
                            'Data': s.date.strftime('%Y-%m-%d'),
                            'Banco': s.bank_name or '',
                            'Conta': s.account or '',
                            'Descrição': s.description,
                            'Valor': s.value,
                            'Tipo': 'Crédito' if s.type == 'entrada' else 'Débito',
                            'Saldo': balance if balance is not None else None,
                            'Importado em': s.created_at.strftime('%Y-%m-%d %H:%M:%S') if s.created_at else ''
                        })
                    
                    export_df = pd.DataFrame(export_data)
                    
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        export_df.to_excel(writer, sheet_name='Extratos Bancários', index=False)
                    
                    output.seek(0)
                    st.download_button(
                        label="⬇️ Baixar arquivo Excel",
                        data=output.getvalue(),
                        file_name=f"extratos_bancarios_{client.name}_{date.today().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openpyxl-officedocument.spreadsheetml.sheet"
                    )
            
            with col_exp2:
                if st.button("📄 Exportar para CSV", use_container_width=True):
                    # Prepara dados para exportação
                    export_df = pd.DataFrame([
                        {
                            'Data': s.date.strftime('%Y-%m-%d'),
                            'Banco': s.bank_name or '',
                            'Conta': s.account or '',
                            'Descrição': s.description,
                            'Valor': s.value,
                            'Saldo': s.balance if s.balance else None,
                            'Tipo': 'Crédito' if s.value > 0 else 'Débito',
                            'Importado em': s.imported_at.strftime('%Y-%m-%d %H:%M:%S') if s.imported_at else ''
                        }
                        for s in statements
                    ])
                    
                    csv = export_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="⬇️ Baixar arquivo CSV",
                        data=csv,
                        file_name=f"extratos_bancarios_{client.name}_{date.today().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
        
        else:
            st.info("ℹ️ Nenhum extrato bancário encontrado com os filtros selecionados.")
            st.markdown("""
            **Dica:** Importe extratos bancários na página de **Importação de Dados** ou crie manualmente na aba "➕ Novo Extrato".
            """)
    
    # TAB 2: Novo Extrato Manual
    with tab2:
        st.subheader("➕ Criar Novo Extrato Bancário")
        st.info("💡 Crie extratos bancários manualmente. Eles serão salvos como transações e aparecerão nos relatórios.")
        
        with st.form("novo_extrato_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                extrato_date = st.date_input("📅 Data *", value=date.today(), key="new_extrato_date")
                extrato_bank = st.text_input("🏦 Banco", placeholder="Ex: Banco do Brasil", key="new_extrato_bank")
                extrato_account = st.text_input("💳 Conta", placeholder="Ex: 12345-6", key="new_extrato_account")
            
            with col2:
                extrato_value = st.number_input("💰 Valor *", value=0.0, step=0.01, format="%.2f", key="new_extrato_value")
                extrato_type = st.selectbox("Tipo:", options=['entrada', 'saida'], index=0, key="new_extrato_type")
                extrato_balance = st.number_input("📊 Saldo (opcional, referência)", value=None, step=0.01, format="%.2f", key="new_extrato_balance")
            
            extrato_description = st.text_area("📝 Descrição *", placeholder="Descrição da transação...", key="new_extrato_description", height=100)
            
            # Seleção de grupo/subgrupo
            from models.group import Group, Subgroup
            groups = db.query(Group).filter(Group.client_id == client_id).all()
            selected_group_id = None
            selected_subgroup_id = None
            
            if groups:
                col_grp1, col_grp2 = st.columns(2)
                with col_grp1:
                    selected_group = st.selectbox(
                        "Grupo (opcional):",
                        options=[None] + groups,
                        format_func=lambda x: "Nenhum" if x is None else x.name,
                        key="new_extrato_group"
                    )
                    if selected_group:
                        selected_group_id = selected_group.id
                
                with col_grp2:
                    if selected_group:
                        subgroups = db.query(Subgroup).filter(Subgroup.group_id == selected_group_id).all()
                        if subgroups:
                            selected_subgroup = st.selectbox(
                                "Subgrupo (opcional):",
                                options=[None] + subgroups,
                                format_func=lambda x: "Nenhum" if x is None else x.name,
                                key="new_extrato_subgroup"
                            )
                            if selected_subgroup:
                                selected_subgroup_id = selected_subgroup.id
            
            submitted = st.form_submit_button("💾 Salvar Extrato", use_container_width=True, type="primary")
            
            if submitted:
                # Validações
                if not extrato_description or not extrato_description.strip():
                    st.error("❌ Descrição é obrigatória!")
                elif extrato_value == 0.0:
                    st.error("❌ Valor deve ser diferente de zero!")
                else:
                    try:
                        # Cria transação (fonte única de verdade)
                        new_transaction = Transaction(
                            client_id=client_id,
                            date=extrato_date,
                            description=extrato_description.strip(),
                            value=extrato_value,
                            type=extrato_type,
                            bank_name=extrato_bank.strip() if extrato_bank and extrato_bank.strip() else None,
                            account=extrato_account.strip() if extrato_account and extrato_account.strip() else None,
                            group_id=selected_group_id,
                            subgroup_id=selected_subgroup_id,
                            document_type='extrato_bancario',
                            imported_from='manual'
                        )
                        db.add(new_transaction)
                        
                        # Opcionalmente, salva também em bank_statements para referência (com saldo)
                        if extrato_balance is not None:
                            new_statement = BankStatement(
                                client_id=client_id,
                                date=extrato_date,
                                bank_name=extrato_bank.strip() if extrato_bank and extrato_bank.strip() else None,
                                account=extrato_account.strip() if extrato_account and extrato_account.strip() else None,
                                description=extrato_description.strip(),
                                value=extrato_value if extrato_type == 'entrada' else -extrato_value,
                                balance=extrato_balance,
                                imported_at=None  # Manual
                            )
                            db.add(new_statement)
                        
                        db.commit()
                        st.success("✅ Extrato criado com sucesso!")
                        st.rerun()
                    
                    except Exception as e:
                        db.rollback()
                        st.error(f"❌ Erro ao criar extrato: {str(e)}")
    
    # TAB 3: Análise e Estatísticas
    with tab3:
        st.subheader("📊 Análise e Estatísticas dos Extratos")
        
        # Filtros de período
        col1, col2 = st.columns(2)
        
        with col1:
            period_type = st.selectbox(
                "Período:",
                options=['Últimos 6 meses', 'Último ano', '2 anos', 'Personalizado'],
                key="stats_period"
            )
        
        today = date.today()
        
        if period_type == 'Últimos 6 meses':
            stats_start = today - relativedelta(months=6)
            stats_end = today
        elif period_type == 'Último ano':
            stats_start = today - relativedelta(years=1)
            stats_end = today
        elif period_type == '2 anos':
            stats_start = today - relativedelta(years=2)
            stats_end = today
        else:  # Personalizado
            with col2:
                stats_start = st.date_input("Data inicial:", value=today - relativedelta(months=6), key="stats_from")
                stats_end = st.date_input("Data final:", value=today, key="stats_to")
        
        # Busca extratos no período (de transactions)
        stats_query = db.query(Transaction).filter(
            Transaction.client_id == client_id,
            Transaction.document_type == 'extrato_bancario',
            Transaction.date >= stats_start,
            Transaction.date <= stats_end
        )
        
        stats_statements = stats_query.order_by(Transaction.date).all()
        
        if stats_statements:
            # Estatísticas gerais
            st.markdown("### 📈 Resumo do Período")
            
            col1, col2, col3, col4 = st.columns(4)
            
            period_creditos = sum(s.value for s in stats_statements if s.type == 'entrada')
            period_debitos = sum(s.value for s in stats_statements if s.type == 'saida')
            period_saldo = period_creditos - period_debitos
            period_count = len(stats_statements)
            
            with col1:
                st.metric("💰 Créditos", format_currency(period_creditos))
            
            with col2:
                st.metric("💸 Débitos", format_currency(period_debitos))
            
            with col3:
                st.metric("📊 Saldo", format_currency(period_saldo))
            
            with col4:
                st.metric("📝 Transações", period_count)
            
            st.markdown("---")
            
            # Análise por banco
            st.markdown("### 🏦 Análise por Banco")
            
            bank_stats = {}
            for stmt in stats_statements:
                bank = stmt.bank_name or 'Sem banco'
                if bank not in bank_stats:
                    bank_stats[bank] = {'creditos': 0, 'debitos': 0, 'count': 0}
                
                if stmt.type == 'entrada':
                    bank_stats[bank]['creditos'] += stmt.value
                else:
                    bank_stats[bank]['debitos'] += stmt.value
                bank_stats[bank]['count'] += 1
            
            if bank_stats:
                bank_df = pd.DataFrame([
                    {
                        'Banco': bank,
                        'Créditos': format_currency(stats['creditos']),
                        'Débitos': format_currency(stats['debitos']),
                        'Saldo': format_currency(stats['creditos'] - stats['debitos']),
                        'Transações': stats['count']
                    }
                    for bank, stats in bank_stats.items()
                ])
                
                st.dataframe(bank_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # Análise mensal
            st.markdown("### 📅 Análise Mensal")
            
            monthly_stats = {}
            for stmt in stats_statements:
                month_key = stmt.date.strftime('%Y-%m')
                if month_key not in monthly_stats:
                    monthly_stats[month_key] = {'creditos': 0, 'debitos': 0, 'count': 0}
                
                if stmt.type == 'entrada':
                    monthly_stats[month_key]['creditos'] += stmt.value
                else:
                    monthly_stats[month_key]['debitos'] += stmt.value
                monthly_stats[month_key]['count'] += 1
            
            if monthly_stats:
                monthly_df = pd.DataFrame([
                    {
                        'Mês': month,
                        'Créditos': format_currency(stats['creditos']),
                        'Débitos': format_currency(stats['debitos']),
                        'Saldo': format_currency(stats['creditos'] - stats['debitos']),
                        'Transações': stats['count']
                    }
                    for month, stats in sorted(monthly_stats.items())
                ])
                
                st.dataframe(monthly_df, use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ Nenhum extrato encontrado no período selecionado.")

finally:
    db.close()

