"""
Sistema Contábil - Aplicação Principal
"""
import streamlit as st
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import SessionLocal
from services.auth_service import AuthService
from models.client import Client

# Configuração da página
st.set_page_config(
    page_title="Início",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa estado da sessão
AuthService.init_session_state()


def login_page():
    """
    Página de login
    """
    st.title("🔐 Sistema Contábil")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Login")
        
        with st.form("login_form"):
            username = st.text_input("Usuário", placeholder="Digite seu usuário")
            password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            submit = st.form_submit_button("Entrar", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("❌ Por favor, preencha todos os campos.")
                else:
                    db = SessionLocal()
                    try:
                        user = AuthService.authenticate(db, username, password)
                        if user:
                            AuthService.login(user)
                            st.success(f"✅ Bem-vindo, {user.username}!")
                            st.rerun()
                        else:
                            st.error("❌ Usuário ou senha inválidos.")
                    finally:
                        db.close()
        
        st.markdown("---")
        st.info("""
        **Credenciais de Teste:**
        - Admin: `admin` / `admin123`
        - Gerente: `gerente1` / `gerente123`
        - Visualizador: `viewer1` / `viewer123`
        """)


def sidebar_navigation():
    """
    Navegação na sidebar com seleção de cliente
    """
    with st.sidebar:
        st.title("📊 Sistema Contábil")
        
        # Informações do usuário
        user = AuthService.get_current_user()
        st.markdown(f"**Usuário:** {user['username']}")
        st.markdown(f"**Perfil:** {user['role'].title()}")
        st.markdown("---")
        
        # Seleção de cliente com pesquisa
        st.subheader("🏢 Cliente")
        db = SessionLocal()
        try:
            clients = AuthService.get_user_clients(db, user['id'])
            
            if clients:
                # Cria dicionário com informações completas
                client_options = {}
                for c in clients:
                    tipo_info = f" [{c.tipo_empresa}]" if c.tipo_empresa else ""
                    client_options[c.id] = f"{c.name}{tipo_info}"
                
                # Valor padrão
                default_client = st.session_state.get('selected_client_id')
                if default_client not in client_options:
                    default_client = list(client_options.keys())[0]
                
                # Selectbox com pesquisa (nativo do Streamlit)
                selected_client_id = st.selectbox(
                    "Selecione o cliente:",
                    options=list(client_options.keys()),
                    format_func=lambda x: client_options[x],
                    index=list(client_options.keys()).index(default_client) if default_client in client_options else 0,
                    key="client_selector",
                    label_visibility="collapsed"
                )
                
                st.session_state.selected_client_id = selected_client_id
                
                # Exibe informações do cliente selecionado
                selected = next((c for c in clients if c.id == selected_client_id), None)
                if selected:
                    st.caption(f"📋 {selected.cpf_cnpj}")
            else:
                st.warning("⚠️ Nenhum cliente disponível.")
                st.session_state.selected_client_id = None
        finally:
            db.close()
        
        st.markdown("---")
        
        # Menu de navegação
        st.subheader("Menu")
        
        # Páginas disponíveis para todos
        st.page_link("app.py", label="Início", icon="🏠")
        
        st.markdown("**Dados**")
        st.page_link("pages/2_Importacao_Dados.py", label="Importação", icon="📥")
        st.page_link("pages/2_Transacoes.py", label="Transações", icon="💳")
        st.page_link("pages/4_Contratos.py", label="Contratos", icon="📝")
        st.page_link("pages/5_Contas.py", label="Contas", icon="💰")
        
        st.markdown("**Dashboards**")
        st.page_link("pages/6_DRE.py", label="DRE", icon="📊")
        st.page_link("pages/7_DFC.py", label="DFC", icon="💵")
        st.page_link("pages/8_Sazonalidade.py", label="Sazonalidade", icon="📈")
        st.page_link("pages/9_Relatorios.py", label="Relatórios", icon="📑")
        
        # Páginas administrativas
        if user['role'] in ['admin', 'manager']:
            st.markdown("---")
            st.markdown("**Administração**")
            st.page_link("pages/1_Gestao_Clientes.py", label="Gestão de Clientes", icon="👥")
        
        if user['role'] == 'admin':
            st.page_link("pages/10_Admin.py", label="Administração", icon="⚙️")
        
        st.markdown("---")
        
        # Botão de logout
        if st.button("🚪 Sair", use_container_width=True):
            AuthService.logout()
            st.rerun()


def main_page():
    """
    Página principal do sistema
    """
    sidebar_navigation()
    
    st.title("🏠 Bem-vindo ao Sistema Contábil")
    
    user = AuthService.get_current_user()
    
    # Informações do cliente selecionado - Card visual
    if st.session_state.selected_client_id:
        db = SessionLocal()
        try:
            client = db.query(Client).filter(Client.id == st.session_state.selected_client_id).first()
            if client:
                # Card visual do cliente
                st.markdown("""
                <style>
                .client-card {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px;
                    border-radius: 10px;
                    color: white;
                    margin-bottom: 20px;
                }
                .client-name {
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 5px;
                }
                .client-info {
                    font-size: 14px;
                    opacity: 0.9;
                }
                </style>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="client-card">
                    <div class="client-name">🏢 {client.name}</div>
                    <div class="client-info">📋 {client.cpf_cnpj}</div>
                </div>
                """, unsafe_allow_html=True)
        finally:
            db.close()
    else:
        st.warning("⚠️ Nenhum cliente selecionado. Selecione um cliente na barra lateral.")
    
    st.markdown("---")
    
    # Cards de informações
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Dashboards",
            value="3",
            help="DRE, DFC e Sazonalidade"
        )
    
    with col2:
        st.metric(
            label="📥 Importação",
            value="4 formatos",
            help="CSV, Excel, PDF, OFX"
        )
    
    with col3:
        st.metric(
            label="📝 Contratos",
            value="Gestão completa",
            help="Contratos e eventos"
        )
    
    with col4:
        st.metric(
            label="💰 Contas",
            value="Pagar/Receber",
            help="Controle financeiro"
        )
    
    st.markdown("---")
    
    # Guia rápido
    st.subheader("📖 Guia Rápido")
    
    with st.expander("🚀 Como começar"):
        st.markdown("""
        1. **Selecione um cliente** na barra lateral
        2. **Importe dados** através da página de Importação
        3. **Cadastre contratos** e contas a pagar/receber
        4. **Visualize dashboards** para análises
        5. **Gere relatórios** personalizados
        """)
    
    with st.expander("📥 Importação de Dados"):
        st.markdown("""
        O sistema suporta importação de:
        - **Extratos Bancários**: CSV, OFX
        - **Faturas de Cartão**: Excel, CSV
        - **Contratos**: Excel, CSV
        - **Contas**: Excel, CSV
        - **PDFs**: Extração automática de texto
        
        Você pode mapear as colunas do arquivo para os campos do sistema.
        """)
    
    with st.expander("📊 Dashboards Disponíveis"):
        st.markdown("""
        - **DRE (Demonstração do Resultado)**: Receitas vs Despesas, KPIs
        - **DFC (Fluxo de Caixa)**: Fluxo realizado e projetado
        - **Sazonalidade**: Análise de padrões sazonais
        """)
    
    with st.expander("👥 Permissões"):
        st.markdown(f"""
        **Seu perfil:** {user['role'].title()}
        
        - **Admin**: Acesso total ao sistema
        - **Manager**: Gerencia clientes específicos
        - **Viewer**: Apenas visualização
        """)
    
    st.markdown("---")
    
    # Rodapé
    st.caption("Sistema Contábil v1.0 | Desenvolvido com Streamlit")


def main():
    """
    Função principal
    """
    if not AuthService.is_authenticated():
        login_page()
    else:
        main_page()


if __name__ == "__main__":
    main()

