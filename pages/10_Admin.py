"""
Página de Administração do Sistema
"""
import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime
from sqlalchemy import func

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from services.ai_service import AIService
from config.ai_config import AIConfigManager
from models.user import User
from models.client import Client
from models.group import Group, Subgroup

st.set_page_config(page_title="Administração", page_icon="⚙️", layout="wide")

# Esconde o menu automático do Streamlit
from utils.hide_auto_menu import hide_streamlit_menu
hide_streamlit_menu()

AuthService.init_session_state()
AuthService.require_role(['admin'])


# Usa sidebar centralizada
from utils.sidebar import show_sidebar
show_sidebar()

st.title("⚙️ Administração do Sistema")
st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["👥 Usuários", "🏷️ Grupos e Subgrupos", "🤖 Configuração de IA", "📊 Estatísticas"])

db = SessionLocal()

try:
    # TAB 1: Gestão de Usuários
    with tab1:
        st.subheader("Gestão de Usuários")
        
        subtab1, subtab2 = st.tabs(["📋 Lista", "➕ Novo Usuário"])
        
        with subtab1:
            users = db.query(User).order_by(User.username).all()
            
            if users:
                user_data = []
                for user in users:
                    user_data.append({
                        'ID': user.id,
                        'Usuário': user.username,
                        'Email': user.email,
                        'Perfil': user.role.title(),
                        'Status': '✅ Ativo' if user.active else '❌ Inativo',
                        'Cadastro': user.created_at.strftime('%d/%m/%Y')
                    })
                
                df = pd.DataFrame(user_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                st.subheader("✏️ Editar Usuário")
                
                selected_user_id = st.selectbox(
                    "Selecione um usuário:",
                    options=[u.id for u in users],
                    format_func=lambda x: next(f"{u.username} ({u.email})" for u in users if u.id == x)
                )
                
                if selected_user_id:
                    user = db.query(User).filter(User.id == selected_user_id).first()
                    
                    with st.form("edit_user_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            new_username = st.text_input("Usuário", value=user.username)
                            new_email = st.text_input("Email", value=user.email)
                        
                        with col2:
                            new_role = st.selectbox(
                                "Perfil",
                                options=['admin', 'manager', 'viewer'],
                                index=['admin', 'manager', 'viewer'].index(user.role)
                            )
                            new_active = st.checkbox("Ativo", value=user.active)
                        
                        new_password = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password")
                        
                        col1, col2 = st.columns([1, 3])
                        
                        with col1:
                            submit = st.form_submit_button("💾 Salvar", use_container_width=True)
                        
                        with col2:
                            delete = st.form_submit_button("🗑️ Excluir", use_container_width=True)
                        
                        if submit:
                            if new_username and new_email:
                                user.username = new_username
                                user.email = new_email
                                user.role = new_role
                                user.active = new_active
                                
                                if new_password:
                                    user.password_hash = AuthService.hash_password(new_password)
                                
                                db.commit()
                                st.success("✅ Usuário atualizado!")
                                st.rerun()
                            else:
                                st.error("❌ Preencha todos os campos.")
                        
                        if delete:
                            # Não permite excluir o próprio usuário
                            current_user = AuthService.get_current_user()
                            if user.id == current_user['id']:
                                st.error("❌ Você não pode excluir seu próprio usuário!")
                            else:
                                db.delete(user)
                                db.commit()
                                st.success("✅ Usuário excluído!")
                                st.rerun()
            else:
                st.info("ℹ️ Nenhum usuário cadastrado.")
        
        with subtab2:
            st.subheader("Cadastrar Novo Usuário")
            
            with st.form("new_user_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    username = st.text_input("Usuário *")
                    email = st.text_input("Email *")
                
                with col2:
                    role = st.selectbox("Perfil *", options=['admin', 'manager', 'viewer'])
                    password = st.text_input("Senha *", type="password")
                
                submit = st.form_submit_button("➕ Cadastrar", use_container_width=True)
                
                if submit:
                    if username and email and password:
                        # Verifica se já existe
                        existing = db.query(User).filter(
                            (User.username == username) | (User.email == email)
                        ).first()
                        
                        if existing:
                            st.error("❌ Usuário ou email já cadastrado.")
                        else:
                            new_user = AuthService.create_user(db, username, password, email, role)
                            st.success(f"✅ Usuário '{username}' cadastrado com sucesso!")
                            st.rerun()
                    else:
                        st.error("❌ Preencha todos os campos obrigatórios.")
    
    # TAB 2: Grupos e Subgrupos
    with tab2:
        st.subheader("Gestão de Grupos e Subgrupos")
        
        # Seleção de cliente
        if not st.session_state.get('selected_client_id'):
            st.warning("⚠️ Selecione um cliente na página inicial.")
        else:
            client_id = st.session_state.selected_client_id
            client = db.query(Client).filter(Client.id == client_id).first()
            
            st.info(f"📌 Cliente: **{client.name}**")
            
            subtab1, subtab2 = st.tabs(["🏷️ Grupos", "🔖 Subgrupos"])
            
            with subtab1:
                st.markdown("### Grupos")
                
                groups = db.query(Group).filter(Group.client_id == client_id).all()
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    if groups:
                        for group in groups:
                            with st.expander(f"📁 {group.name}"):
                                st.markdown(f"**Descrição:** {group.description or '-'}")
                                
                                # Subgrupos deste grupo
                                subgroups = db.query(Subgroup).filter(Subgroup.group_id == group.id).all()
                                if subgroups:
                                    st.markdown("**Subgrupos:**")
                                    for sg in subgroups:
                                        st.markdown(f"- {sg.name}")
                                
                                if st.button(f"🗑️ Excluir Grupo", key=f"del_group_{group.id}"):
                                    db.delete(group)
                                    db.commit()
                                    st.success("✅ Grupo excluído!")
                                    st.rerun()
                    else:
                        st.info("ℹ️ Nenhum grupo cadastrado.")
                
                with col2:
                    st.markdown("**Novo Grupo**")
                    
                    with st.form("new_group_form"):
                        group_name = st.text_input("Nome *")
                        group_desc = st.text_area("Descrição")
                        
                        submit = st.form_submit_button("➕ Criar", use_container_width=True)
                        
                        if submit:
                            if group_name:
                                new_group = Group(
                                    client_id=client_id,
                                    name=group_name,
                                    description=group_desc if group_desc else None
                                )
                                db.add(new_group)
                                db.commit()
                                st.success("✅ Grupo criado!")
                                st.rerun()
                            else:
                                st.error("❌ Preencha o nome do grupo.")
            
            with subtab2:
                st.markdown("### Subgrupos")
                
                groups = db.query(Group).filter(Group.client_id == client_id).all()
                
                if groups:
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Lista subgrupos
                        for group in groups:
                            subgroups = db.query(Subgroup).filter(Subgroup.group_id == group.id).all()
                            
                            if subgroups:
                                st.markdown(f"**Grupo: {group.name}**")
                                
                                for sg in subgroups:
                                    with st.expander(f"🔖 {sg.name}"):
                                        st.markdown(f"**Descrição:** {sg.description or '-'}")
                                        
                                        if st.button(f"🗑️ Excluir", key=f"del_sg_{sg.id}"):
                                            db.delete(sg)
                                            db.commit()
                                            st.success("✅ Subgrupo excluído!")
                                            st.rerun()
                    
                    with col2:
                        st.markdown("**Novo Subgrupo**")
                        
                        with st.form("new_subgroup_form"):
                            parent_group = st.selectbox(
                                "Grupo *",
                                options=[g.id for g in groups],
                                format_func=lambda x: next(g.name for g in groups if g.id == x)
                            )
                            
                            sg_name = st.text_input("Nome *")
                            sg_desc = st.text_area("Descrição")
                            
                            submit = st.form_submit_button("➕ Criar", use_container_width=True)
                            
                            if submit:
                                if sg_name:
                                    new_sg = Subgroup(
                                        group_id=parent_group,
                                        name=sg_name,
                                        description=sg_desc if sg_desc else None
                                    )
                                    db.add(new_sg)
                                    db.commit()
                                    st.success("✅ Subgrupo criado!")
                                    st.rerun()
                                else:
                                    st.error("❌ Preencha o nome do subgrupo.")
                else:
                    st.info("ℹ️ Crie grupos primeiro para poder adicionar subgrupos.")
    
    # TAB 3: Configuração de IA
    with tab3:
        st.subheader("🤖 Configuração de Inteligência Artificial")
        st.markdown("Configure a IA para análise inteligente de arquivos importados.")
        
        # Verifica configuração atual
        current_config = AIConfigManager.get_config(db)
        
        if current_config:
            st.info(f"✅ **IA Ativa:** {current_config.provider.upper()} - {current_config.model or 'Modelo padrão'}")
        else:
            st.warning("⚠️ Nenhuma configuração de IA ativa. Configure abaixo para habilitar análise inteligente.")
        
        st.markdown("---")
        
        # Formulário de configuração
        with st.form("ai_config_form"):
            st.markdown("### Nova Configuração")
            
            provider = st.selectbox(
                "Provedor de IA:",
                options=['openai', 'gemini', 'ollama', 'groq'],
                format_func=lambda x: {
                    'openai': 'OpenAI (GPT-4, GPT-3.5)',
                    'gemini': 'Google Gemini',
                    'ollama': 'Ollama (Local)',
                    'groq': 'Groq (Llama, Mixtral)'
                }[x]
            )
            
            api_key = st.text_input(
                "Chave de API:",
                type="password",
                help="Para Ollama, deixe em branco ou digite 'ollama'. Para Groq, obtenha em https://console.groq.com"
            )
            
            # Modelos por provedor - todos permitem entrada manual
            if provider == 'openai':
                model = st.text_input(
                    "Modelo:",
                    value='gpt-4o-mini',
                    help="Ex: gpt-4o-mini, gpt-4o, gpt-4-turbo, gpt-3.5-turbo, etc"
                )
                base_url = None
            elif provider == 'gemini':
                model = st.text_input(
                    "Modelo:",
                    value='gemini-1.5-flash',
                    help="Ex: gemini-1.5-flash, gemini-1.5-pro, gemini-pro, etc"
                )
                base_url = None
            elif provider == 'groq':
                model = st.text_input(
                    "Modelo:",
                    value='llama-3.3-70b-versatile',
                    help="Ex: llama-3.3-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768, gemma2-9b-it, etc"
                )
                base_url = None
            else:  # ollama
                model = st.text_input(
                    "Modelo:",
                    value='llama3.2',
                    help="Ex: llama3.2, mistral, codellama, etc"
                )
                base_url = st.text_input(
                    "URL Base (opcional):",
                    value='http://localhost:11434/v1',
                    help="URL do servidor Ollama"
                )
            
            enabled = st.checkbox("Ativar esta configuração", value=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                submit = st.form_submit_button("💾 Salvar Configuração", use_container_width=True)
            
            with col2:
                test_btn = st.form_submit_button("🧪 Testar Conexão", use_container_width=True)
            
            if submit:
                if provider == 'ollama' or api_key:
                    try:
                        config = AIConfigManager.save_config(
                            db=db,
                            provider=provider,
                            api_key=api_key if api_key else 'ollama',
                            model=model,
                            base_url=base_url if provider == 'ollama' else None,
                            enabled=enabled
                        )
                        st.success(f"✅ Configuração salva com sucesso! ({config.provider.upper()})")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar configuração: {str(e)}")
                else:
                    st.error("❌ Por favor, informe a chave de API.")
            
            if test_btn:
                if provider == 'ollama' or api_key:
                    try:
                        # Salva temporariamente para teste
                        test_config = AIConfigManager.save_config(
                            db=db,
                            provider=provider,
                            api_key=api_key if api_key else 'ollama',
                            model=model,
                            base_url=base_url if provider == 'ollama' else None,
                            enabled=True  # Ativa temporariamente para teste
                        )
                        
                        # Recarrega configuração
                        db.refresh(test_config)
                        
                        # Testa conexão
                        ai_service = AIService(db)
                        ai_service._reload_config()  # Recarrega configuração atualizada
                        success, message = ai_service.test_connection()
                        
                        # Remove configuração de teste se não estava ativa antes
                        if not current_config or current_config.provider != provider:
                            AIConfigManager.delete_config(db, provider)
                            # Restaura configuração anterior se existia
                            if current_config:
                                AIConfigManager.save_config(
                                    db=db,
                                    provider=current_config.provider,
                                    api_key=current_config.api_key,
                                    model=current_config.model,
                                    base_url=current_config.base_url,
                                    enabled=True
                                )
                        
                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                    except Exception as e:
                        st.error(f"❌ Erro ao testar conexão: {str(e)}")
                        # Limpa configuração de teste em caso de erro
                        try:
                            AIConfigManager.delete_config(db, provider)
                        except:
                            pass
                else:
                    st.error("❌ Por favor, informe a chave de API para testar.")
        
        st.markdown("---")
        
        # Lista configurações existentes
        st.markdown("### Configurações Existentes")
        all_configs = AIConfigManager.get_all_configs(db)
        
        if all_configs:
            for config in all_configs:
                with st.expander(f"{'✅' if config.enabled else '❌'} {config.provider.upper()} - {config.model or 'Modelo padrão'}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"""
                        - **Provedor:** {config.provider}
                        - **Modelo:** {config.model or 'Modelo padrão'}
                        - **Status:** {'✅ Ativo' if config.enabled else '❌ Inativo'}
                        - **URL Base:** {config.base_url or 'Padrão'}
                        """)
                    
                    with col2:
                        if st.button("🗑️ Excluir", key=f"del_ai_{config.id}"):
                            AIConfigManager.delete_config(db, config.provider)
                            st.success("✅ Configuração excluída!")
                            st.rerun()
        else:
            st.info("ℹ️ Nenhuma configuração cadastrada.")
        
        st.markdown("---")
        
        # Informações
        with st.expander("ℹ️ Informações sobre Provedores"):
            st.markdown("""
            **OpenAI**
            - Requer chave de API: https://platform.openai.com/api-keys
            - Modelos recomendados: gpt-4o-mini (mais barato), gpt-4o (mais preciso)
            
            **Google Gemini**
            - Requer chave de API: https://makersuite.google.com/app/apikey
            - Modelos recomendados: gemini-1.5-flash (rápido), gemini-1.5-pro (preciso)
            
            **Groq**
            - Requer chave de API: https://console.groq.com
            - Modelos recomendados: llama-3.3-70b-versatile (preciso), llama-3.1-8b-instant (rápido), mixtral-8x7b-32768
            - Muito rápido, ideal para processamento em tempo real
            - Consulte modelos disponíveis: https://console.groq.com/docs/models
            
            **Ollama (Local)**
            - Não requer chave de API
            - Requer instalação local do Ollama: https://ollama.ai
            - Modelos recomendados: llama3.2, mistral, codellama
            - Funciona offline, sem custos
            """)
    
    # TAB 4: Estatísticas
    with tab4:
        st.subheader("Estatísticas do Sistema")
        
        # Contadores
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.active == True).count()
        total_clients = db.query(Client).count()
        active_clients = db.query(Client).filter(Client.active == True).count()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Usuários", total_users, delta=f"{active_users} ativos")
        
        with col2:
            st.metric("🏢 Clientes", total_clients, delta=f"{active_clients} ativos")
        
        with col3:
            from models.transaction import Transaction
            total_transactions = db.query(Transaction).count()
            st.metric("💳 Transações", total_transactions)
        
        with col4:
            from models.contract import Contract
            total_contracts = db.query(Contract).count()
            st.metric("📝 Contratos", total_contracts)
        
        st.markdown("---")
        
        # Distribuição de usuários por perfil
        st.subheader("📊 Distribuição de Usuários por Perfil")
        
        import plotly.graph_objects as go
        
        roles = db.query(User.role, func.count(User.id)).group_by(User.role).all()
        
        if roles:
            labels = [r[0].title() for r in roles]
            values = [r[1] for r in roles]
            
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.3)])
            fig.update_layout(height=400)
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Informações do sistema
        st.subheader("ℹ️ Informações do Sistema")
        
        st.markdown(f"""
        - **Versão:** 1.0.0
        - **Banco de Dados:** SQLite
        - **Framework:** Streamlit
        - **Data/Hora:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        """)

finally:
    db.close()

