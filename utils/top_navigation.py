"""
Componente de navegação superior (menu na tela)
"""
import streamlit as st
from services.auth_service import AuthService
from config.database import SessionLocal
from models.client import Client


def show_top_navigation():
    """
    Exibe menu de navegação na parte superior da tela
    """
    user = AuthService.get_current_user()
    
    # Header com informações do usuário e logout
    col_header1, col_header2, col_header3 = st.columns([3, 2, 1])
    
    with col_header1:
        st.markdown("### 📊 Sistema Contábil")
    
    with col_header2:
        # Seleção de cliente
        db = SessionLocal()
        try:
            clients = AuthService.get_user_clients(db, user['id'])
            
            if clients:
                client_options = {}
                for c in clients:
                    tipo_info = f" [{c.tipo_empresa}]" if c.tipo_empresa else ""
                    client_options[c.id] = f"{c.name}{tipo_info}"
                
                default_client = st.session_state.get('selected_client_id')
                if default_client not in client_options:
                    default_client = list(client_options.keys())[0]
                    st.session_state.selected_client_id = default_client
                
                selected_client_id = st.selectbox(
                    "🏢 Cliente:",
                    options=list(client_options.keys()),
                    format_func=lambda x: client_options[x],
                    index=list(client_options.keys()).index(default_client) if default_client in client_options else 0,
                    key="top_nav_client_selector"
                )
                
                st.session_state.selected_client_id = selected_client_id
        finally:
            db.close()
    
    with col_header3:
        st.markdown(f"**{user['username']}** ({user['role'].title()})")
        if st.button("🚪 Sair", use_container_width=True, key="top_nav_logout"):
            AuthService.logout()
            st.rerun()
    
    st.markdown("---")
    
    # Menu de navegação principal
    # Agente IA em destaque primeiro
    st.markdown("#### 🤖 Inteligência Artificial")
    col_ai1, col_ai2 = st.columns([1, 4])
    with col_ai1:
        st.page_link("pages/11_Agente_IA.py", label="💬 Agente IA", icon="🤖", use_container_width=True)
    with col_ai2:
        st.caption("Faça perguntas em linguagem natural e receba análises inteligentes")
    
    st.markdown("---")
    
    # Menu principal em tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Início", "📥 Dados", "📊 Relatórios", "⚙️ Admin"])
    
    with tab1:
        st.page_link("app.py", label="🏠 Página Inicial", icon="🏠", use_container_width=True)
    
    with tab2:
        st.markdown("**Gestão de Dados**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.page_link("pages/2_Importacao_Dados.py", label="📤 Importar Dados", icon="📥", use_container_width=True)
            st.page_link("pages/2_Transacoes.py", label="💳 Transações", icon="💳", use_container_width=True)
        
        with col2:
            st.page_link("pages/4_Contratos.py", label="📝 Contratos", icon="📝", use_container_width=True)
            st.page_link("pages/5_Contas.py", label="💰 Contas", icon="💰", use_container_width=True)
    
    with tab3:
        st.markdown("**Dashboards e Relatórios**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.page_link("pages/6_DRE.py", label="📈 DRE", icon="📊", use_container_width=True)
            st.page_link("pages/7_DFC.py", label="💵 DFC", icon="💵", use_container_width=True)
        
        with col2:
            st.page_link("pages/8_Sazonalidade.py", label="📉 Sazonalidade", icon="📈", use_container_width=True)
            st.page_link("pages/9_Relatorios.py", label="📑 Relatórios", icon="📑", use_container_width=True)
    
    with tab4:
        if user['role'] in ['admin', 'manager']:
            st.page_link("pages/1_Gestao_Clientes.py", label="👥 Gestão de Clientes", icon="👥", use_container_width=True)
        
        if user['role'] == 'admin':
            st.page_link("pages/10_Admin.py", label="🔧 Configurações", icon="⚙️", use_container_width=True)
    
    st.markdown("---")

