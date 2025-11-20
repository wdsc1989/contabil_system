"""
Página de Gestão de Clientes
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from services.report_config_service import ReportConfigService, DATA_TYPES, REPORT_TYPES
from models.client import Client
from models.user import User, UserClientPermission
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Gestão de Clientes", page_icon="👥", layout="wide")

# Esconde o menu automático do Streamlit
from utils.hide_auto_menu import hide_streamlit_menu
hide_streamlit_menu()

# Verifica autenticação e permissão
AuthService.init_session_state()
AuthService.require_role(['admin', 'manager'])

# Importa a sidebar do app principal
if 'sidebar_loaded' not in st.session_state:
    st.session_state.sidebar_loaded = True


# Usa sidebar centralizada
from utils.sidebar import show_sidebar
show_sidebar()

st.title("👥 Gestão de Clientes")
st.markdown("---")

# Tabs para diferentes funcionalidades
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Lista de Clientes", "➕ Novo Cliente", "🔐 Permissões", "⚙️ Configuração de Relatórios", "🗺️ Mapa Visual de Dados"])

db = SessionLocal()

try:
    # TAB 1: Lista de Clientes
    with tab1:
        st.subheader("Clientes Cadastrados")
        
        # Busca
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("🔍 Buscar cliente", placeholder="Nome ou CPF/CNPJ")
        with col2:
            show_inactive = st.checkbox("Mostrar inativos", value=False)
        
        # Query de clientes
        query = db.query(Client)
        if not show_inactive:
            query = query.filter(Client.active == True)
        if search:
            query = query.filter(
                (Client.name.contains(search)) | (Client.cpf_cnpj.contains(search))
            )
        
        clients = query.order_by(Client.name).all()
        
        if clients:
            # Exibe em formato de tabela
            client_data = []
            for client in clients:
                client_data.append({
                    'ID': client.id,
                    'Nome': client.name,
                    'Tipo': client.tipo_empresa or '-',
                    'CPF/CNPJ': client.cpf_cnpj,
                    'Status': '✅ Ativo' if client.active else '❌ Inativo',
                    'Cadastro': client.created_at.strftime('%d/%m/%Y')
                })
            
            df = pd.DataFrame(client_data)
            # Traduz colunas para português (já estão em português, mas garante consistência)
            from utils.translations import translate_dataframe
            df = translate_dataframe(df, translate_columns=True, translate_values=True)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # Edição de cliente
            st.subheader("✏️ Editar Cliente")
            
            selected_client_id = st.selectbox(
                "Selecione um cliente para editar:",
                options=[c.id for c in clients],
                format_func=lambda x: next(c.name for c in clients if c.id == x)
            )
            
            if selected_client_id:
                client = db.query(Client).filter(Client.id == selected_client_id).first()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    new_name = st.text_input("Nome", value=client.name, key="edit_name")
                    new_cpf_cnpj = st.text_input("CPF/CNPJ", value=client.cpf_cnpj, key="edit_cpf_cnpj")
                    new_tipo = st.text_input("Tipo de Empresa", value=client.tipo_empresa or "", key="edit_tipo")
                
                with col2:
                    new_active = st.checkbox("Ativo", value=client.active, key="edit_active")
                
                if st.button("💾 Salvar Alterações", type="primary"):
                    try:
                        client.name = new_name
                        client.cpf_cnpj = new_cpf_cnpj
                        client.tipo_empresa = new_tipo if new_tipo else None
                        client.active = new_active
                        db.commit()
                        st.success("✅ Cliente atualizado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error(f"❌ Erro ao atualizar cliente: {str(e)}")
        else:
            st.info("ℹ️ Nenhum cliente encontrado.")
    
    # TAB 2: Novo Cliente
    with tab2:
        st.subheader("➕ Cadastrar Novo Cliente")
        
        with st.form("new_client_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Nome *", placeholder="Nome da empresa ou pessoa")
                cpf_cnpj = st.text_input("CPF/CNPJ *", placeholder="00.000.000/0000-00")
            
            with col2:
                tipo_empresa = st.text_input("Tipo de Empresa", placeholder="MEI, LTDA, EIRELI, etc.")
                active = st.checkbox("Ativo", value=True)
            
            submitted = st.form_submit_button("💾 Cadastrar Cliente", type="primary")
            
            if submitted:
                if not name or not cpf_cnpj:
                    st.error("❌ Nome e CPF/CNPJ são obrigatórios!")
                else:
                    try:
                        # Verifica se já existe
                        existing = db.query(Client).filter(Client.cpf_cnpj == cpf_cnpj).first()
                        if existing:
                            st.error(f"❌ Já existe um cliente com o CPF/CNPJ: {cpf_cnpj}")
                        else:
                            new_client = Client(
                                name=name,
                                cpf_cnpj=cpf_cnpj,
                                tipo_empresa=tipo_empresa if tipo_empresa else None,
                                active=active
                            )
                            db.add(new_client)
                            db.commit()
                            
                            # Cria configuração padrão de relatórios
                            ReportConfigService.ensure_default_config(db, new_client.id)
                            
                            st.success(f"✅ Cliente '{name}' cadastrado com sucesso!")
                            st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error(f"❌ Erro ao cadastrar cliente: {str(e)}")
    
    # TAB 3: Permissões
    with tab3:
        st.subheader("🔐 Permissões de Usuários por Cliente")
        
        # Seleciona cliente
        all_clients = db.query(Client).filter(Client.active == True).order_by(Client.name).all()
        
        if not all_clients:
            st.info("ℹ️ Nenhum cliente cadastrado.")
        else:
            selected_permission_client_id = st.selectbox(
                "Selecione um cliente:",
                options=[c.id for c in all_clients],
                format_func=lambda x: next(f"{c.name} ({c.cpf_cnpj})" for c in all_clients if c.id == x),
                key="permission_client_select"
            )
            
            if selected_permission_client_id:
                permission_client = db.query(Client).filter(Client.id == selected_permission_client_id).first()
                st.info(f"📌 Gerenciando permissões para: **{permission_client.name}**")
                
                # Lista usuários com permissões
                st.markdown("### Usuários com Acesso")
                
                permissions = db.query(UserClientPermission).filter(
                    UserClientPermission.client_id == selected_permission_client_id
                ).all()
                
                if permissions:
                    perm_data = []
                    for perm in permissions:
                        user = db.query(User).filter(User.id == perm.user_id).first()
                        perm_data.append({
                            'Usuário': user.username if user else 'N/A',
                            'Perfil': user.role if user else 'N/A',
                            'Ações': '🔐'
                        })
                    
                    perm_df = pd.DataFrame(perm_data)
                    st.dataframe(perm_df, use_container_width=True, hide_index=True)
                    
                    # Remover permissão
                    st.markdown("### Remover Permissão")
                    perm_to_remove = st.selectbox(
                        "Selecione uma permissão para remover:",
                        options=[p.id for p in permissions],
                        format_func=lambda x: next(
                            f"{db.query(User).filter(User.id == p.user_id).first().username if db.query(User).filter(User.id == p.user_id).first() else 'N/A'}"
                            for p in permissions if p.id == x
                        ),
                        key="remove_perm_select"
                    )
                    
                    if st.button("🗑️ Remover Permissão", type="secondary"):
                        try:
                            perm = db.query(UserClientPermission).filter(UserClientPermission.id == perm_to_remove).first()
                            if perm:
                                db.delete(perm)
                                db.commit()
                                st.success("✅ Permissão removida com sucesso!")
                                st.rerun()
                        except Exception as e:
                            db.rollback()
                            st.error(f"❌ Erro ao remover permissão: {str(e)}")
                else:
                    st.info("ℹ️ Nenhum usuário com acesso a este cliente.")
                
                st.markdown("---")
                
                # Adicionar permissão
                st.markdown("### Adicionar Permissão")
                
                all_users = db.query(User).all()
                if all_users:
                    # Filtra usuários que já têm permissão
                    users_with_permission = [p.user_id for p in permissions]
                    available_users = [u for u in all_users if u.id not in users_with_permission]
                    
                    if available_users:
                        user_to_add = st.selectbox(
                            "Selecione um usuário:",
                            options=[u.id for u in available_users],
                            format_func=lambda x: next(f"{u.username} ({u.role})" for u in available_users if u.id == x),
                            key="add_perm_user"
                        )
                        
                        if st.button("➕ Adicionar Permissão", type="primary"):
                            try:
                                new_perm = UserClientPermission(
                                    user_id=user_to_add,
                                    client_id=selected_permission_client_id
                                )
                                db.add(new_perm)
                                db.commit()
                                st.success("✅ Permissão adicionada com sucesso!")
                                st.rerun()
                            except Exception as e:
                                db.rollback()
                                st.error(f"❌ Erro ao adicionar permissão: {str(e)}")
                    else:
                        st.info("ℹ️ Todos os usuários já têm acesso a este cliente.")
                else:
                    st.info("ℹ️ Nenhum usuário cadastrado.")
    
    # TAB 4: Configuração de Relatórios
    with tab4:
        st.subheader("⚙️ Configuração de Relatórios por Cliente")
        st.markdown("Configure quais tipos de dados devem aparecer em cada relatório para cada cliente.")
        
        # Seleciona cliente
        all_clients = db.query(Client).filter(Client.active == True).order_by(Client.name).all()
        
        if not all_clients:
            st.info("ℹ️ Nenhum cliente cadastrado.")
        else:
            selected_config_client_id = st.selectbox(
                "Selecione um cliente:",
                options=[c.id for c in all_clients],
                format_func=lambda x: next(f"{c.name} ({c.cpf_cnpj})" for c in all_clients if c.id == x),
                key="config_client_select"
            )
            
            if selected_config_client_id:
                config_client = db.query(Client).filter(Client.id == selected_config_client_id).first()
                st.info(f"📌 Configurando relatórios para: **{config_client.name}**")
                
                # Garante que existe configuração padrão
                ReportConfigService.ensure_default_config(db, selected_config_client_id)
                
                # Obtém configurações atuais
                dre_config = ReportConfigService.get_client_report_config(db, selected_config_client_id, 'dre')
                dfc_config = ReportConfigService.get_client_report_config(db, selected_config_client_id, 'dfc')
                sazonalidade_config = ReportConfigService.get_client_report_config(db, selected_config_client_id, 'sazonalidade')
                
                # Se não houver configuração, cria com valores padrão (todos habilitados)
                data_types = DATA_TYPES
                
                if not dre_config:
                    dre_config = {dt: True for dt in data_types.keys()}
                if not dfc_config:
                    dfc_config = {dt: True for dt in data_types.keys()}
                if not sazonalidade_config:
                    sazonalidade_config = {dt: True for dt in data_types.keys()}
                
                # Formulário de configuração
                with st.form("report_config_form"):
                    st.markdown("### 📊 DRE - Demonstração do Resultado do Exercício")
                    dre_checkboxes = {}
                    for data_type, label in data_types.items():
                        dre_checkboxes[data_type] = st.checkbox(
                            label,
                            value=dre_config.get(data_type, True),
                            key=f"dre_{data_type}"
                        )
                    
                    st.markdown("---")
                    st.markdown("### 💵 DFC - Demonstração do Fluxo de Caixa")
                    dfc_checkboxes = {}
                    for data_type, label in data_types.items():
                        dfc_checkboxes[data_type] = st.checkbox(
                            label,
                            value=dfc_config.get(data_type, True),
                            key=f"dfc_{data_type}"
                        )
                    
                    st.markdown("---")
                    st.markdown("### 📉 Análise de Sazonalidade")
                    sazonalidade_checkboxes = {}
                    for data_type, label in data_types.items():
                        sazonalidade_checkboxes[data_type] = st.checkbox(
                            label,
                            value=sazonalidade_config.get(data_type, True),
                            key=f"saz_{data_type}"
                        )
                    
                    submitted = st.form_submit_button("💾 Salvar Configurações", type="primary")
                    
                    if submitted:
                        try:
                            # Valida que pelo menos um tipo está habilitado para cada relatório
                            if not any(dre_checkboxes.values()):
                                st.error("❌ Pelo menos um tipo de dado deve estar habilitado para DRE!")
                            elif not any(dfc_checkboxes.values()):
                                st.error("❌ Pelo menos um tipo de dado deve estar habilitado para DFC!")
                            elif not any(sazonalidade_checkboxes.values()):
                                st.error("❌ Pelo menos um tipo de dado deve estar habilitado para Sazonalidade!")
                            else:
                                # Atualiza configurações
                                ReportConfigService.update_client_report_config(
                                    db, selected_config_client_id, 'dre', dre_checkboxes
                                )
                                ReportConfigService.update_client_report_config(
                                    db, selected_config_client_id, 'dfc', dfc_checkboxes
                                )
                                ReportConfigService.update_client_report_config(
                                    db, selected_config_client_id, 'sazonalidade', sazonalidade_checkboxes
                                )
                                
                                st.success("✅ Configurações salvas com sucesso!")
                                st.rerun()
                        except Exception as e:
                            db.rollback()
                            st.error(f"❌ Erro ao salvar configurações: {str(e)}")
    
    # TAB 5: Mapa Visual de Dados
    with tab5:
        st.subheader("🗺️ Mapa Visual de Dados e Relatórios")
        st.markdown("Visualize como os tipos de dados importados se conectam aos relatórios baseado na configuração do cliente.")
        
        # Seleciona cliente
        all_clients = db.query(Client).filter(Client.active == True).order_by(Client.name).all()
        
        if not all_clients:
            st.info("ℹ️ Nenhum cliente cadastrado.")
        else:
            selected_map_client_id = st.selectbox(
                "Selecione um cliente:",
                options=[c.id for c in all_clients],
                format_func=lambda x: next(f"{c.name} ({c.cpf_cnpj})" for c in all_clients if c.id == x),
                key="map_client_select"
            )
            
            if selected_map_client_id:
                map_client = db.query(Client).filter(Client.id == selected_map_client_id).first()
                st.info(f"📌 Visualizando mapa para: **{map_client.name}**")
                
                # Garante que existe configuração padrão
                ReportConfigService.ensure_default_config(db, selected_map_client_id)
                
                # Obtém todas as configurações
                all_configs = ReportConfigService.get_all_configs(db, selected_map_client_id)
                
                # Verifica quais tipos de dados realmente existem no banco para este cliente
                from models.transaction import Transaction, BankStatement
                from models.contract import Contract
                from models.account import AccountPayable, AccountReceivable
                from models.financial_investment import FinancialInvestment
                from models.credit_card import CreditCardInvoice
                from models.card_machine import CardMachineStatement
                from models.inventory import Inventory
                
                # Conta registros por tipo de dado
                data_type_counts = {
                    'transactions': db.query(Transaction).filter(Transaction.client_id == selected_map_client_id).count(),
                    'bank_statements': db.query(BankStatement).filter(BankStatement.client_id == selected_map_client_id).count(),
                    'contracts': db.query(Contract).filter(Contract.client_id == selected_map_client_id).count(),
                    'accounts_payable': db.query(AccountPayable).filter(AccountPayable.client_id == selected_map_client_id).count(),
                    'accounts_receivable': db.query(AccountReceivable).filter(AccountReceivable.client_id == selected_map_client_id).count(),
                    'financial_investments': db.query(FinancialInvestment).filter(FinancialInvestment.client_id == selected_map_client_id).count(),
                    'credit_card_invoices': db.query(CreditCardInvoice).filter(CreditCardInvoice.client_id == selected_map_client_id).count(),
                    'card_machine_statements': db.query(CardMachineStatement).filter(CardMachineStatement.client_id == selected_map_client_id).count(),
                }
                
                # Filtra apenas tipos de dados que existem OU estão configurados para algum relatório
                available_data_types = []
                for data_type in DATA_TYPES.keys():
                    # Inclui se tem dados OU se está habilitado em pelo menos um relatório
                    has_data = data_type_counts.get(data_type, 0) > 0
                    is_configured = any(
                        all_configs.get(report_type, {}).get(data_type, False)
                        for report_type in REPORT_TYPES
                    )
                    if has_data or is_configured:
                        available_data_types.append(data_type)
                
                # Se não houver nenhum tipo disponível, mostra todos (para configuração inicial)
                if not available_data_types:
                    available_data_types = list(DATA_TYPES.keys())
                
                # Cria o mapa visual usando Plotly
                st.markdown("### 📊 Mapa de Conexões: Tipos de Dados → Relatórios")
                
                # Mostra informações sobre dados existentes
                if any(data_type_counts.values()):
                    st.info(f"📊 **Dados encontrados:** {sum(1 for count in data_type_counts.values() if count > 0)} tipo(s) com dados importados")
                
                # Define mapeamento de tipos de dados para tipos intermediários
                # Alguns tipos de dados geram transações automaticamente
                data_to_intermediate = {
                    'bank_statements': 'transactions',  # Extratos bancários geram transações
                    'credit_card_invoices': 'transactions',  # Faturas de cartão podem gerar transações
                    'card_machine_statements': 'transactions',  # Máquina de cartão pode gerar transações
                    'accounts_payable': 'transactions',  # Contas a pagar podem gerar transações
                    'accounts_receivable': 'transactions',  # Contas a receber podem gerar transações
                }
                
                # Tipos de dados (lado esquerdo) - apenas os disponíveis
                data_type_labels = [DATA_TYPES[dt] for dt in available_data_types]
                data_type_keys = available_data_types
                
                # Tipos intermediários (centro) - apenas "Transações" por enquanto
                intermediate_types = {
                    'transactions': '💳 Transações'
                }
                
                # Relatórios (lado direito)
                report_labels = {
                    'dre': '📈 DRE',
                    'dfc': '💵 DFC',
                    'sazonalidade': '📉 Sazonalidade'
                }
                
                # Criar posições dos nós
                # Dados à esquerda (x=0), intermediários no centro (x=5), relatórios à direita (x=10)
                node_x = []
                node_y = []
                node_text = []
                node_colors = []
                node_types = []  # 'data', 'intermediate', 'report'
                
                # Posições dos tipos de dados (lado esquerdo)
                for i, label in enumerate(data_type_labels):
                    node_x.append(0)
                    node_y.append(i * 2)
                    node_text.append(label)
                    node_colors.append('#3498db')  # Azul para dados
                    node_types.append('data')
                
                # Posições dos tipos intermediários (centro)
                intermediate_start_idx = len(data_type_labels)
                for i, (key, label) in enumerate(intermediate_types.items()):
                    node_x.append(5)
                    node_y.append(i * 6)
                    node_text.append(label)
                    node_colors.append('#f39c12')  # Laranja para intermediários
                    node_types.append('intermediate')
                
                # Posições dos relatórios (lado direito)
                report_start_idx = len(data_type_labels) + len(intermediate_types)
                for i, (report_type, label) in enumerate(report_labels.items()):
                    node_x.append(10)
                    node_y.append(i * 4)
                    node_text.append(label)
                    node_colors.append('#2ecc71')  # Verde para relatórios
                    node_types.append('report')
                
                # Criar conexões (edges) com caminhos completos
                connections = []
                connection_labels = []  # Para tooltips
                
                for data_idx, data_type in enumerate(data_type_keys):
                    # Verifica se este tipo gera um tipo intermediário
                    intermediate_type = data_to_intermediate.get(data_type)
                    
                    if intermediate_type and intermediate_type in intermediate_types:
                        # Caminho: Dado → Intermediário → Relatório
                        intermediate_idx = intermediate_start_idx + list(intermediate_types.keys()).index(intermediate_type)
                        
                        # Conexão: Dado → Intermediário
                        connections.append({
                            'from': data_idx,
                            'to': intermediate_idx,
                            'type': 'data_to_intermediate'
                        })
                        connection_labels.append(f"{data_type_labels[data_idx]} → {intermediate_types[intermediate_type]}")
                        
                        # Conexão: Intermediário → Relatórios
                        for report_type, report_label in report_labels.items():
                            # Verifica se o tipo intermediário está habilitado para o relatório
                            # Para transações, verifica se 'transactions' está habilitado
                            if all_configs.get(report_type, {}).get(intermediate_type, True):
                                report_idx = report_start_idx + list(report_labels.keys()).index(report_type)
                                connections.append({
                                    'from': intermediate_idx,
                                    'to': report_idx,
                                    'type': 'intermediate_to_report'
                                })
                                connection_labels.append(f"{intermediate_types[intermediate_type]} → {report_label}")
                    else:
                        # Caminho direto: Dado → Relatório
                        for report_type, report_label in report_labels.items():
                            if all_configs.get(report_type, {}).get(data_type, True):
                                report_idx = report_start_idx + list(report_labels.keys()).index(report_type)
                                connections.append({
                                    'from': data_idx,
                                    'to': report_idx,
                                    'type': 'direct'
                                })
                                connection_labels.append(f"{data_type_labels[data_idx]} → {report_label}")
                
                # Criar arestas (conexões) com cores diferentes por tipo
                edge_x = []
                edge_y = []
                edge_colors = []
                
                for conn in connections:
                    x0, y0 = node_x[conn['from']], node_y[conn['from']]
                    x1, y1 = node_x[conn['to']], node_y[conn['to']]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                    
                    # Cores diferentes para diferentes tipos de conexão
                    if conn['type'] == 'data_to_intermediate':
                        edge_colors.extend(['#3498db', '#f39c12', None])  # Azul → Laranja
                    elif conn['type'] == 'intermediate_to_report':
                        edge_colors.extend(['#f39c12', '#2ecc71', None])  # Laranja → Verde
                    else:  # direct
                        edge_colors.extend(['#3498db', '#2ecc71', None])  # Azul → Verde
                
                # Criar gráfico
                fig = go.Figure()
                
                # Adicionar arestas agrupadas por tipo para melhor visualização
                # Conexões diretas (dados → relatórios)
                direct_edges_x = []
                direct_edges_y = []
                for i, conn in enumerate(connections):
                    if conn['type'] == 'direct':
                        x0, y0 = node_x[conn['from']], node_y[conn['from']]
                        x1, y1 = node_x[conn['to']], node_y[conn['to']]
                        direct_edges_x.extend([x0, x1, None])
                        direct_edges_y.extend([y0, y1, None])
                
                if direct_edges_x:
                    fig.add_trace(go.Scatter(
                        x=direct_edges_x, y=direct_edges_y,
                        line=dict(width=2, color='#3498db', dash='dash'),
                        hoverinfo='none',
                        mode='lines',
                        showlegend=True,
                        name='Conexão Direta'
                    ))
                
                # Conexões via intermediário (dados → intermediário → relatórios)
                intermediate_edges_x = []
                intermediate_edges_y = []
                for i, conn in enumerate(connections):
                    if conn['type'] in ['data_to_intermediate', 'intermediate_to_report']:
                        x0, y0 = node_x[conn['from']], node_y[conn['from']]
                        x1, y1 = node_x[conn['to']], node_y[conn['to']]
                        intermediate_edges_x.extend([x0, x1, None])
                        intermediate_edges_y.extend([y0, y1, None])
                
                if intermediate_edges_x:
                    fig.add_trace(go.Scatter(
                        x=intermediate_edges_x, y=intermediate_edges_y,
                        line=dict(width=2.5, color='#f39c12'),
                        hoverinfo='none',
                        mode='lines',
                        showlegend=True,
                        name='Via Transações'
                    ))
                
                # Adicionar nós de dados
                data_nodes_x = [node_x[i] for i in range(len(data_type_labels))]
                data_nodes_y = [node_y[i] for i in range(len(data_type_labels))]
                fig.add_trace(go.Scatter(
                    x=data_nodes_x,
                    y=data_nodes_y,
                    mode='markers+text',
                    marker=dict(size=35, color='#3498db', line=dict(width=2, color='white')),
                    text=[label.split(' ')[-1] if len(label.split(' ')) > 1 else label for label in data_type_labels],
                    textposition="middle center",
                    textfont=dict(size=9, color='white'),
                    name='Tipos de Dados',
                    hovertemplate='<b>%{text}</b><extra></extra>',
                    showlegend=True
                ))
                
                # Adicionar nós intermediários (se houver)
                if intermediate_start_idx < report_start_idx:
                    intermediate_nodes_x = [node_x[i] for i in range(intermediate_start_idx, report_start_idx)]
                    intermediate_nodes_y = [node_y[i] for i in range(intermediate_start_idx, report_start_idx)]
                    intermediate_node_text = [node_text[i] for i in range(intermediate_start_idx, report_start_idx)]
                    fig.add_trace(go.Scatter(
                        x=intermediate_nodes_x,
                        y=intermediate_nodes_y,
                        mode='markers+text',
                        marker=dict(size=40, color='#f39c12', line=dict(width=2, color='white')),
                        text=intermediate_node_text,
                        textposition="middle center",
                        textfont=dict(size=11, color='white', weight='bold'),
                        name='Tipos Intermediários',
                        hovertemplate='<b>%{text}</b><extra></extra>',
                        showlegend=True
                    ))
                
                # Adicionar nós de relatórios
                report_nodes_x = [node_x[i] for i in range(report_start_idx, len(node_x))]
                report_nodes_y = [node_y[i] for i in range(report_start_idx, len(node_y))]
                report_node_text = [node_text[i] for i in range(report_start_idx, len(node_text))]
                fig.add_trace(go.Scatter(
                    x=report_nodes_x,
                    y=report_nodes_y,
                    mode='markers+text',
                    marker=dict(size=45, color='#2ecc71', line=dict(width=2, color='white')),
                    text=report_node_text,
                    textposition="middle center",
                    textfont=dict(size=12, color='white', weight='bold'),
                    name='Relatórios',
                    hovertemplate='<b>%{text}</b><extra></extra>',
                    showlegend=True
                ))
                
                # Layout
                fig.update_layout(
                    title=dict(
                        text=f"Mapa de Conexões: {map_client.name}",
                        x=0.5,
                        font=dict(size=20)
                    ),
                    showlegend=True,
                    hovermode='closest',
                    margin=dict(b=20, l=50, r=50, t=80),
                    annotations=[
                        dict(
                            text="Tipos de Dados Importados",
                            xref="paper", yref="paper",
                            x=0.05, y=1.05,
                            showarrow=False,
                            font=dict(size=14, color='#3498db')
                        ),
                        dict(
                            text="Tipos Intermediários",
                            xref="paper", yref="paper",
                            x=0.5, y=1.05,
                            showarrow=False,
                            font=dict(size=14, color='#f39c12')
                        ),
                        dict(
                            text="Relatórios",
                            xref="paper", yref="paper",
                            x=0.95, y=1.05,
                            showarrow=False,
                            font=dict(size=14, color='#2ecc71')
                        )
                    ],
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    plot_bgcolor='white',
                    height=600
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela resumo
                st.markdown("### 📋 Resumo da Configuração")
                
                summary_data = []
                for data_type in available_data_types:
                    label = DATA_TYPES[data_type]
                    count = data_type_counts.get(data_type, 0)
                    row = {'Tipo de Dado': f"{label} ({count} registros)" if count > 0 else label}
                    for report_type, report_label in report_labels.items():
                        enabled = all_configs.get(report_type, {}).get(data_type, True)
                        row[report_label] = '✅ Sim' if enabled else '❌ Não'
                    summary_data.append(row)
                
                summary_df = pd.DataFrame(summary_data)
                # Traduz colunas para português
                from utils.translations import translate_dataframe
                summary_df = translate_dataframe(summary_df, translate_columns=True, translate_values=True)
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
                # Estatísticas
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    dre_count = sum(1 for dt in available_data_types if all_configs.get('dre', {}).get(dt, True))
                    st.metric("DRE", f"{dre_count}/{len(available_data_types)} tipos habilitados")
                
                with col2:
                    dfc_count = sum(1 for dt in available_data_types if all_configs.get('dfc', {}).get(dt, True))
                    st.metric("DFC", f"{dfc_count}/{len(available_data_types)} tipos habilitados")
                
                with col3:
                    saz_count = sum(1 for dt in available_data_types if all_configs.get('sazonalidade', {}).get(dt, True))
                    st.metric("Sazonalidade", f"{saz_count}/{len(available_data_types)} tipos habilitados")

finally:
    db.close()
