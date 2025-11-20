"""
Sistema Contábil - Aplicação Principal
"""
import streamlit as st
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import SessionLocal, init_db
from services.auth_service import AuthService
from models.client import Client
from models.user import User

# Configuração da página
st.set_page_config(
    page_title="Início",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",  # Sidebar expandida para mostrar nosso menu customizado
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Esconde o menu automático do Streamlit
from utils.hide_auto_menu import hide_streamlit_menu
hide_streamlit_menu()

# Inicializa estado da sessão
AuthService.init_session_state()


@st.cache_resource
def initialize_database():
    """
    Inicializa o banco de dados e cria usuário admin se não existir
    """
    try:
        # Cria todas as tabelas
        init_db()
        
        # Verifica se existe algum usuário, se não, cria admin padrão
        db = SessionLocal()
        try:
            user_count = db.query(User).count()
            if user_count == 0:
                # Cria usuário admin padrão
                AuthService.create_user(
                    db=db,
                    username="admin",
                    password="admin123",
                    email="admin@contabil.com",
                    role="admin"
                )
                db.commit()
                print("✅ Usuário admin criado: admin / admin123")
        except Exception as e:
            print(f"⚠️ Erro ao verificar/criar usuário admin: {e}")
            db.rollback()
        finally:
            db.close()
    except Exception as e:
        print(f"⚠️ Erro ao inicializar banco de dados: {e}")


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


def sidebar_navigation():
    """
    Navegação na sidebar com seleção de cliente
    DEPRECATED: Use utils.sidebar.show_sidebar() ao invés desta função
    """
    from utils.sidebar import show_sidebar
    show_sidebar()

def _old_sidebar_navigation():
    """
    Função antiga - mantida para referência
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
        
        # Menu de navegação - Organizado por seções
        st.markdown("### 🧭 Navegação")
        
        # Seção Início
        st.markdown("#### 🏠 Início")
        st.page_link("app.py", label="Página Inicial", icon="🏠")
        
        st.markdown("---")
        
        # Seção Administração (primeiro para admin/manager)
        if user['role'] in ['admin', 'manager']:
            st.markdown("#### ⚙️ Administração")
            st.page_link("pages/1_Gestao_Clientes.py", label="👥 Gestão de Clientes", icon="👥")
            st.caption("Cadastre e gerencie clientes")
            st.markdown("---")
        
        # Seção Dados
        st.markdown("#### 📥 Gestão de Dados")
        st.page_link("pages/2_Importacao_Dados.py", label="📤 Importar Dados", icon="📥")
        st.caption("Importe arquivos CSV, Excel, PDF ou OFX")
        
        # Seção Visualizar Dados Importados
        st.markdown("**📊 Visualizar Dados Importados:**")
        st.page_link("pages/12_Faturas_Cartao.py", label="💳 Faturas de Cartão", icon="💳")
        st.page_link("pages/13_Aplicacoes_Financeiras.py", label="📈 Aplicações Financeiras", icon="📈")
        st.page_link("pages/14_Maquina_Cartao.py", label="🏪 Máquina de Cartão", icon="🏪")
        st.page_link("pages/15_Estoque.py", label="📦 Controle de Estoque", icon="📦")
        
        st.markdown("---")
        
        # Outros dados
        st.page_link("pages/2_Transacoes.py", label="💳 Transações Financeiras", icon="💳")
        st.caption("Visualize e gerencie transações")
        
        # Verificar se existe página de Extratos Bancários
        # st.page_link("pages/X_Extratos_Bancarios.py", label="🏦 Extratos Bancários", icon="🏦")
        
        st.page_link("pages/4_Contratos.py", label="📝 Contratos e Eventos", icon="📝")
        st.caption("Gerencie contratos e eventos")
        
        st.page_link("pages/5_Contas.py", label="💰 Contas a Pagar/Receber", icon="💰")
        st.caption("Controle de contas a pagar e receber")
        
        st.markdown("---")
        
        # Seção Dashboards e Relatórios
        st.markdown("#### 📊 Dashboards e Relatórios")
        st.page_link("pages/6_DRE.py", label="📈 DRE - Demonstração do Resultado", icon="📊")
        st.caption("Receitas vs Despesas e resultado")
        
        st.page_link("pages/7_DFC.py", label="💵 DFC - Fluxo de Caixa", icon="💵")
        st.caption("Análise de fluxo de caixa")
        
        st.page_link("pages/8_Sazonalidade.py", label="📉 Análise de Sazonalidade", icon="📈")
        st.caption("Padrões sazonais e tendências")
        
        st.page_link("pages/9_Relatorios.py", label="📑 Relatórios e Exportação", icon="📑")
        st.caption("Gere e exporte relatórios completos")
        
        st.markdown("---")
        
        # Seção Inteligência Artificial
        st.markdown("#### 🤖 Inteligência Artificial")
        st.page_link("pages/11_Agente_IA.py", label="💬 Agente IA", icon="🤖")
        st.caption("Faça perguntas sobre seus dados")
        
        st.markdown("---")
        
        # Configurações (apenas admin)
        if user['role'] == 'admin':
            st.markdown("#### 🔧 Configurações")
            st.page_link("pages/10_Admin.py", label="⚙️ Configurações do Sistema", icon="⚙️")
            st.caption("Configurações avançadas e IA")
        
        st.markdown("---")
        
        # Botão de logout
        if st.button("🚪 Sair", use_container_width=True):
            AuthService.logout()
            st.rerun()


def main_page():
    """
    Página principal do sistema
    """
    # Menu na tela principal ao invés de sidebar
    from utils.top_navigation import show_top_navigation
    show_top_navigation()
    
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
            label="📊 Relatórios",
            value="12+",
            help="DRE, DFC, Sazonalidade, Eventos, Performance, e mais"
        )
    
    with col2:
        st.metric(
            label="📥 Importação",
            value="7+ formatos",
            help="CSV, Excel, PDF, OFX, JPG, PNG, TIFF e mais"
        )
    
    with col3:
        st.metric(
            label="🤖 IA + OCR",
            value="Ativo",
            help="Processamento inteligente e OCR para imagens"
        )
    
    with col4:
        st.metric(
            label="📝 Dados",
            value="9 tipos",
            help="Transações, Contratos, Contas, Estoque, e mais"
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
        O sistema suporta importação de múltiplos formatos com processamento inteligente:
        
        **Formatos Suportados:**
        - **CSV/TXT**: Extratos bancários, transações, contas
        - **Excel (XLSX/XLS)**: Planilhas complexas, múltiplas abas
        - **PDF**: Extração automática de texto e tabelas
        - **OFX**: Extratos bancários no formato OFX
        - **Imagens**: JPG, PNG, TIFF, BMP, WEBP (com OCR automático)
        
        **Tipos de Dados:**
        - Extratos Bancários
        - Transações Financeiras
        - Contratos e Eventos
        - Contas a Pagar/Receber
        - Faturas de Cartão de Crédito
        - Extratos de Máquina de Cartão
        - Aplicações Financeiras
        - Controle de Estoque
        
        **Recursos:**
        - 🤖 **IA para classificação automática** por grupo/subgrupo
        - 🖼️ **OCR para PDFs e imagens** (processamento de documentos escaneados)
        - ✅ **Validação completa** garantindo que todas as linhas sejam processadas
        - 📊 **Mapeamento inteligente** de colunas
        """)
    
    with st.expander("📊 Relatórios e Dashboards Disponíveis"):
        st.markdown("""
        **Relatórios Principais:**
        - **DRE (Demonstração do Resultado)**: Receitas vs Despesas, KPIs, análise por grupo/subgrupo
        - **DFC (Fluxo de Caixa)**: Fluxo realizado e projetado, análise por fonte de dados
        - **Sazonalidade**: Análise de padrões sazonais, tendências e comparações mensais
        
        **Relatórios Especializados:**
        - **📅 Diário de Gastos**: Acompanhamento diário de despesas com heatmap e gráficos
        - **🎯 Painel de Controle Unificado**: Visão executiva consolidada
        - **💵 Fluxo de Caixa Gerencial**: Análise gerencial de fluxo de caixa
        - **👤 Despesas CPF vs CNPJ**: Separação de despesas pessoais e empresariais
        - **💰 Dashboard de Contas**: Aging, inadimplência e projeções de contas
        - **📝 Relatório de Eventos**: Análise de contratos e eventos
        - **📈 Performance de Vendedores**: Análise de vendas por vendedor
        
        **Visualização de Dados:**
        - Transações Financeiras
        - Extratos Bancários
        - Contratos e Eventos
        - Contas a Pagar/Receber
        - Faturas de Cartão
        - Máquina de Cartão
        - Aplicações Financeiras
        - Controle de Estoque
        """)
    
    with st.expander("👥 Permissões"):
        st.markdown(f"""
        **Seu perfil:** {user['role'].title()}
        
        - **Admin**: Acesso total ao sistema, configurações, gestão de usuários e clientes
        - **Manager**: Gerencia clientes específicos, importa dados, visualiza relatórios
        - **Viewer**: Apenas visualização de dados e relatórios
        """)
    
    with st.expander("🤖 Agente Conversacional IA"):
        st.markdown("""
        **O que é o Agente IA?**
        Seu assistente contábil inteligente que responde perguntas em linguagem natural e gera análises profissionais com visualizações interativas.
        
        **Como usar:**
        1. Acesse a página **"🤖 Agente IA"** no menu lateral
        2. Selecione o cliente que deseja analisar
        3. Faça perguntas em português natural sobre seus dados financeiros
        4. Receba respostas com análises, gráficos e recomendações
        
        **Exemplos de perguntas:**
        - "Gerar relatório gerencial de Outubro 2025"
        - "Quais são as receitas do último mês?"
        - "Mostre as despesas por grupo"
        - "Qual é o saldo atual?"
        - "Analise a performance de vendedores"
        - "Mostre o dashboard de contas a pagar e receber"
        - "Qual é a margem operacional atual?"
        - "Compare as receitas deste ano com o ano passado"
        
        **Recursos do Agente:**
        - 📊 **Análise em tempo real** de dados do PostgreSQL
        - 📈 **Relatórios gerenciais completos** com visualizações interativas
        - 🖼️ **Suporte a OCR** para processamento de imagens e PDFs escaneados
        - 🤖 **Processamento inteligente** garantindo análise completa de todos os dados
        - 📑 **Exportação de relatórios** em Markdown e HTML
        - 💡 **Sugestões proativas** baseadas nos dados do cliente
        
        **Relatórios Gerenciais:**
        O agente pode gerar relatórios gerenciais completos incluindo:
        - Disponíveis financeiros vs obrigações
        - Análise de receitas e despesas por grupo/subgrupo
        - Fluxo de caixa mensal
        - Projeções futuras
        - KPIs e indicadores principais
        - Recomendações estratégicas
        
        **Visualizações:**
        Os relatórios incluem gráficos interativos (Plotly) que podem ser explorados diretamente na tela.
        """)
    
    with st.expander("🤖 Inteligência Artificial (Importação)"):
        st.markdown("""
        O sistema utiliza IA para:
        - **Classificação automática** de transações por grupo/subgrupo
        - **Processamento completo** garantindo que todas as linhas sejam analisadas
        - **OCR inteligente** para extrair dados de PDFs e imagens
        - **Detecção automática** de quando usar IA para melhor processamento
        
        **Recomendações automáticas** aparecem durante a importação quando:
        - Arquivo de imagem é detectado
        - PDF baseado em imagens é identificado
        - Arquivo grande (>100 linhas) é importado
        - Formato complexo ou não estruturado é detectado
        """)
    
    with st.expander("📚 Documentação e Tutoriais"):
        st.markdown("""
        - **Tutorial Completo**: Consulte `docs/TUTORIAL_COMPLETO.md` para guia detalhado
        - **Deploy em Produção**: Consulte `docs/TUTORIAL_DEPLOY_PRODUCAO.md` para instruções de deploy
        - **README**: Consulte `README.md` para visão geral e funcionalidades
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
        # Renderiza a sidebar de navegação
        sidebar_navigation()
        main_page()


if __name__ == "__main__":
    # Inicializa banco de dados e cria admin se necessário
    initialize_database()
    main()


