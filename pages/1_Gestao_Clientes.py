"""
Página de Gestão de Clientes
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from services.report_config_service import ReportConfigService
from models.client import Client
from models.user import User, UserClientPermission
import pandas as pd

st.set_page_config(page_title="Gestão de Clientes", page_icon="👥", layout="wide")

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
tab1, tab2, tab3, tab4 = st.tabs(["📋 Lista de Clientes", "➕ Novo Cliente", "🔐 Permissões", "⚙️ Configuração de Relatórios"])

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
                    new_cpf_cnpj = st.text_input("CPF/CNPJ", value=client.cpf_cnpj, key="edit_cpf")
                
                with col2:
                    new_tipo = st.selectbox(
                        "Tipo de Empresa",
                        options=['', 'Eventos', 'Consultoria', 'Comércio', 'Serviços', 'Indústria', 'Outro'],
                        index=['', 'Eventos', 'Consultoria', 'Comércio', 'Serviços', 'Indústria', 'Outro'].index(client.tipo_empresa or ''),
                        key="edit_tipo"
                    )
                    new_active = st.checkbox("Ativo", value=client.active, key="edit_active")
                
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    if st.button("💾 Salvar Alterações", use_container_width=True):
                        if new_name and new_cpf_cnpj:
                            client.name = new_name
                            client.cpf_cnpj = new_cpf_cnpj
                            client.tipo_empresa = new_tipo if new_tipo else None
                            client.active = new_active
                            db.commit()
                            st.success("✅ Cliente atualizado com sucesso!")
                            st.rerun()
                        else:
                            st.error("❌ Preencha todos os campos obrigatórios.")
                
                with col2:
                    if st.button("🗑️ Excluir Cliente", use_container_width=True):
                        if AuthService.get_current_user()['role'] == 'admin':
                            db.delete(client)
                            db.commit()
                            st.success("✅ Cliente excluído com sucesso!")
                            st.rerun()
                        else:
                            st.error("❌ Apenas administradores podem excluir clientes.")
        else:
            st.info("ℹ️ Nenhum cliente encontrado.")
    
    # TAB 2: Novo Cliente
    with tab2:
        st.subheader("Cadastrar Novo Cliente")
        
        with st.form("new_client_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Nome *", placeholder="Nome do cliente")
                cpf_cnpj = st.text_input("CPF/CNPJ *", placeholder="000.000.000-00 ou 00.000.000/0000-00")
            
            with col2:
                tipo_empresa = st.selectbox(
                    "Tipo de Empresa",
                    options=['', 'Eventos', 'Consultoria', 'Comércio', 'Serviços', 'Indústria', 'Outro']
                )
            
            submit = st.form_submit_button("➕ Cadastrar Cliente", use_container_width=True)
            
            if submit:
                if not name or not cpf_cnpj:
                    st.error("❌ Preencha todos os campos obrigatórios.")
                else:
                    # Verifica se já existe
                    existing = db.query(Client).filter(Client.cpf_cnpj == cpf_cnpj).first()
                    if existing:
                        st.error("❌ Já existe um cliente com este CPF/CNPJ.")
                    else:
                        new_client = Client(
                            name=name,
                            cpf_cnpj=cpf_cnpj,
                            tipo_empresa=tipo_empresa if tipo_empresa else None,
                            active=True
                        )
                        db.add(new_client)
                        db.commit()
                        # Cria configuração padrão de relatórios para o novo cliente
                        ReportConfigService.ensure_default_config(db, new_client.id)
                        st.success(f"✅ Cliente '{name}' cadastrado com sucesso!")
                        st.rerun()
    
    # TAB 3: Permissões
    with tab3:
        st.subheader("Gerenciar Permissões de Acesso")
        
        # Apenas admin pode gerenciar permissões
        if AuthService.get_current_user()['role'] != 'admin':
            st.warning("⚠️ Apenas administradores podem gerenciar permissões.")
        else:
            # Seleciona usuário
            users = db.query(User).filter(User.active == True).all()
            
            if not users:
                st.info("ℹ️ Nenhum usuário cadastrado.")
            else:
                selected_user_id = st.selectbox(
                    "Selecione um usuário:",
                    options=[u.id for u in users],
                    format_func=lambda x: next(f"{u.username} ({u.role})" for u in users if u.id == x)
                )
                
                if selected_user_id:
                    user = db.query(User).filter(User.id == selected_user_id).first()
                    
                    st.markdown(f"**Usuário:** {user.username}")
                    st.markdown(f"**Perfil:** {user.role}")
                    
                    if user.role == 'admin':
                        st.info("ℹ️ Administradores têm acesso total a todos os clientes.")
                    else:
                        st.markdown("---")
                        st.markdown("**Permissões por Cliente:**")
                        
                        # Lista todos os clientes
                        all_clients = db.query(Client).filter(Client.active == True).all()
                        
                        if all_clients:
                            # Obtém permissões atuais
                            current_perms = db.query(UserClientPermission).filter(
                                UserClientPermission.user_id == selected_user_id
                            ).all()
                            
                            perm_dict = {p.client_id: p for p in current_perms}
                            
                            # Formulário de permissões
                            with st.form("permissions_form"):
                                perm_changes = {}
                                
                                for client in all_clients:
                                    st.markdown(f"**{client.name}** ({client.cpf_cnpj})")
                                    
                                    col1, col2, col3 = st.columns(3)
                                    
                                    current_perm = perm_dict.get(client.id)
                                    
                                    with col1:
                                        can_view = st.checkbox(
                                            "👁️ Visualizar",
                                            value=current_perm.can_view if current_perm else False,
                                            key=f"view_{client.id}"
                                        )
                                    
                                    with col2:
                                        can_edit = st.checkbox(
                                            "✏️ Editar",
                                            value=current_perm.can_edit if current_perm else False,
                                            key=f"edit_{client.id}"
                                        )
                                    
                                    with col3:
                                        can_delete = st.checkbox(
                                            "🗑️ Excluir",
                                            value=current_perm.can_delete if current_perm else False,
                                            key=f"delete_{client.id}"
                                        )
                                    
                                    perm_changes[client.id] = {
                                        'can_view': can_view,
                                        'can_edit': can_edit,
                                        'can_delete': can_delete
                                    }
                                    
                                    st.markdown("---")
                                
                                submit_perms = st.form_submit_button("💾 Salvar Permissões", use_container_width=True)
                                
                                if submit_perms:
                                    # Atualiza permissões
                                    for client_id, perms in perm_changes.items():
                                        if any(perms.values()):  # Se alguma permissão está marcada
                                            AuthService.grant_permission(
                                                db, selected_user_id, client_id,
                                                perms['can_view'], perms['can_edit'], perms['can_delete']
                                            )
                                        else:
                                            # Remove permissão se todas estão desmarcadas
                                            perm = db.query(UserClientPermission).filter(
                                                UserClientPermission.user_id == selected_user_id,
                                                UserClientPermission.client_id == client_id
                                            ).first()
                                            if perm:
                                                db.delete(perm)
                                    
                                    db.commit()
                                    st.success("✅ Permissões atualizadas com sucesso!")
                                    st.rerun()
                        else:
                            st.info("ℹ️ Nenhum cliente cadastrado.")
    
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
                from services.report_config_service import DATA_TYPES
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
                    dre_enabled = {}
                    for data_type, label in data_types.items():
                        dre_enabled[data_type] = st.checkbox(
                            label,
                            value=dre_config.get(data_type, True),
                            key=f"dre_{data_type}"
                        )
                    
                    st.markdown("---")
                    st.markdown("### 💵 DFC - Demonstração do Fluxo de Caixa")
                    dfc_enabled = {}
                    for data_type, label in data_types.items():
                        dfc_enabled[data_type] = st.checkbox(
                            label,
                            value=dfc_config.get(data_type, True),
                            key=f"dfc_{data_type}"
                        )
                    
                    st.markdown("---")
                    st.markdown("### 📈 Sazonalidade")
                    sazonalidade_enabled = {}
                    for data_type, label in data_types.items():
                        sazonalidade_enabled[data_type] = st.checkbox(
                            label,
                            value=sazonalidade_config.get(data_type, True),
                            key=f"sazonalidade_{data_type}"
                        )
                    
                    st.markdown("---")
                    
                    submit_config = st.form_submit_button("💾 Salvar Configurações", use_container_width=True)
                    
                    if submit_config:
                        # Validação: não permitir desabilitar todos os tipos
                        if not any(dre_enabled.values()):
                            st.error("❌ Pelo menos um tipo de dado deve estar habilitado para DRE.")
                        elif not any(dfc_enabled.values()):
                            st.error("❌ Pelo menos um tipo de dado deve estar habilitado para DFC.")
                        elif not any(sazonalidade_enabled.values()):
                            st.error("❌ Pelo menos um tipo de dado deve estar habilitado para Sazonalidade.")
                        else:
                            # Atualiza configurações
                            ReportConfigService.update_client_report_config(db, selected_config_client_id, 'dre', dre_enabled)
                            ReportConfigService.update_client_report_config(db, selected_config_client_id, 'dfc', dfc_enabled)
                            ReportConfigService.update_client_report_config(db, selected_config_client_id, 'sazonalidade', sazonalidade_enabled)
                            
                            st.success("✅ Configurações de relatórios atualizadas com sucesso!")
                            st.rerun()

finally:
    db.close()

