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
    
    with st.expander("📚 Tutorial Completo - Sistema de Ponta a Ponta"):
        st.markdown("""
        ## 1️⃣ Administração do Sistema
        
        ### 1.1 Login e Primeiro Acesso
        
        1. **Acesse o sistema** através do navegador
        2. **Faça login** com suas credenciais:
           - **Admin**: Usuário com acesso total ao sistema
           - **Manager**: Gerencia clientes específicos
           - **Viewer**: Apenas visualização de dados
        3. Após o login, você será direcionado para a **página inicial**
        
        ### 1.2 Gestão de Usuários (Apenas Admin)
        
        Para administradores:
        - Acesse **"👥 Gestão de Clientes"** → Aba **"🔐 Permissões"**
        - **Criar usuário**: Adicione novos usuários ao sistema
        - **Editar permissões**: Defina quais clientes cada usuário pode acessar
        - **Alterar roles**: Modifique o nível de acesso (admin, manager, viewer)
        
        ### 1.3 Permissões e Roles
        
        O sistema possui três níveis de acesso:
        
        - **👑 Admin**: 
          - Acesso total ao sistema
          - Cria e gerencia usuários
          - Cria e gerencia clientes
          - Configura relatórios
          - Acessa todos os dados e relatórios
        
        - **👔 Manager**: 
          - Gerencia clientes específicos (atribuídos pelo admin)
          - Importa e edita dados
          - Visualiza relatórios dos clientes atribuídos
          - Não pode criar usuários ou alterar configurações globais
        
        - **👁️ Viewer**: 
          - Apenas visualização de dados e relatórios
          - Não pode importar ou editar dados
          - Acesso somente aos clientes atribuídos
        
        ---
        
        ## 2️⃣ Gestão de Clientes
        
        ### 2.1 Criar Novo Cliente
        
        1. Acesse **"👥 Gestão de Clientes"** no menu
        2. Vá para a aba **"➕ Novo Cliente"**
        3. Preencha os campos obrigatórios:
           - **Nome**: Nome completo da empresa/cliente
           - **CPF/CNPJ**: Documento (será validado automaticamente)
           - **Tipo de Empresa**: Selecione o tipo (Eventos, Consultoria, etc.)
        4. Clique em **"Criar Cliente"**
        5. O sistema criará automaticamente:
           - Grupos e subgrupos padrão (DRE, DFC, Sazonalidade)
           - Configuração padrão de relatórios (todos os tipos habilitados)
        
        ### 2.2 Editar Informações do Cliente
        
        1. Na aba **"📋 Lista de Clientes"**
        2. Selecione o cliente que deseja editar
        3. Modifique os campos necessários
        4. Clique em **"Salvar Alterações"**
        
        ### 2.3 Configuração de Relatórios (⚠️ FUNDAMENTAL)
        
        **O que são Configurações de Relatórios?**
        
        As configurações de relatórios permitem que você **personalize quais tipos de dados** aparecem em cada relatório para cada cliente. Isso é essencial porque diferentes clientes podem ter necessidades diferentes.
        
        **Como funciona:**
        
        1. Acesse **"👥 Gestão de Clientes"** → Aba **"⚙️ Configuração de Relatórios"**
        2. Selecione o cliente que deseja configurar
        3. Para cada relatório (DRE, DFC, Sazonalidade), você pode habilitar/desabilitar tipos de dados:
           - ✅ **Transações Financeiras**
           - ✅ **Extratos Bancários**
           - ✅ **Contratos/Eventos**
           - ✅ **Contas a Pagar**
           - ✅ **Contas a Receber**
           - ✅ **Aplicações Financeiras**
           - ✅ **Faturas de Cartão**
           - ✅ **Extratos de Máquina de Cartão**
           - ✅ **Controle de Estoque**
        
        4. Clique em **"Salvar Configuração"**
        
        **Impacto nas Visualizações:**
        
        - ✅ **Tipos habilitados**: Aparecem nos relatórios correspondentes
        - ❌ **Tipos desabilitados**: São **completamente ignorados** nos relatórios
        - O sistema **respeita rigorosamente** essas configurações
        - O **Mapa Visual de Dados** reflete essas configurações em tempo real
        
        **Exemplo prático:**
        
        Se você desabilitar "Contratos/Eventos" no DRE:
        - Os contratos **não aparecerão** no relatório DRE
        - Mas ainda podem aparecer no DFC se estiverem habilitados lá
        - O mapa visual mostrará que contratos não estão conectados ao DRE
        
        ### 2.4 Mapa Visual de Dados (🗺️ Entendendo o Fluxo)
        
        **O que é o Mapa Visual?**
        
        O mapa visual é uma representação gráfica que mostra **como os tipos de dados importados se conectam aos relatórios** baseado nas configurações do cliente.
        
        **Como acessar:**
        
        1. Acesse **"👥 Gestão de Clientes"** → Aba **"🗺️ Mapa Visual de Dados"**
        2. Selecione o cliente que deseja visualizar
        
        **Como interpretar o mapa:**
        
        O mapa possui três seções principais:
        
        - **🔵 Tipos de Dados Importados** (lado esquerdo):
          - Mostra todos os tipos de dados que podem ser importados
          - Tipos com dados existentes aparecem destacados
          - Tipos sem dados aparecem mais transparentes
        
        - **🟡 Tipos Intermediários** (centro):
          - **Transações**: Geradas automaticamente a partir de extratos bancários
          - Outros tipos vão direto aos relatórios
        
        - **🟢 Relatórios** (lado direito):
          - **DRE**: Demonstração do Resultado
          - **DFC**: Fluxo de Caixa
          - **Sazonalidade**: Análise de padrões sazonais
        
        **Conexões visuais:**
        
        - **Linhas conectando tipos → relatórios**: Mostram quais dados alimentam quais relatórios
        - **Linhas verdes**: Tipos habilitados na configuração
        - **Sem linhas**: Tipos desabilitados (não aparecem no relatório)
        - **Tabela de configuração**: Mostra exatamente o que está habilitado/desabilitado
        
        **Como o mapa reflete as configurações:**
        
        - O mapa é **gerado dinamicamente** baseado nas configurações de relatórios
        - Se você desabilitar um tipo em um relatório, a conexão desaparece do mapa
        - Se você habilitar um tipo, a conexão aparece automaticamente
        - O mapa ajuda a **visualizar o impacto** das configurações antes de gerar relatórios
        
        **Exemplo prático:**
        
        Se você configurar:
        - DRE: Apenas "Transações" e "Contratos" habilitados
        - DFC: Todos os tipos habilitados
        
        O mapa mostrará:
        - Transações e Contratos conectados ao DRE
        - Todos os tipos conectados ao DFC
        - Outros tipos (Contas a Pagar, etc.) conectados apenas ao DFC
        
        ---
        
        ## 3️⃣ Cadastro de Dados
        
        ### 3.1 Importação Automática
        
        **Passo 1: Upload do Arquivo**
        
        1. Acesse **"📥 Importar Dados"** no menu
        2. Certifique-se de que um cliente está selecionado
        3. Clique em **"Escolher arquivo"**
        4. Selecione o arquivo que deseja importar
        
        **Formatos suportados:**
        - **CSV/TXT**: Extratos bancários, transações, contas
        - **Excel (XLSX/XLS)**: Planilhas complexas, múltiplas abas
        - **PDF**: Extração automática de texto e tabelas
        - **OFX**: Extratos bancários no formato OFX
        - **Imagens**: JPG, PNG, TIFF, BMP, WEBP (com OCR automático)
        
        **Passo 2: Detecção e Recomendações**
        
        O sistema automaticamente:
        - **Detecta o tipo de arquivo** (CSV, Excel, PDF, etc.)
        - **Recomenda uso de IA** quando apropriado:
          - Arquivos de imagem (requer OCR)
          - PDFs baseados em imagens
          - Arquivos grandes (>100 linhas)
          - Formatos não estruturados
        
        **Passo 3: Processamento com IA**
        
        O sistema processa o arquivo:
        
        1. **Extração de dados**:
           - PDFs: Extrai texto completo e tabelas
           - Imagens: Usa OCR para extrair texto
           - Excel/CSV: Lê todas as planilhas/linhas
        
        2. **Classificação automática**:
           - Detecta o tipo de dado (extrato, transação, contrato, etc.)
           - Mapeia colunas automaticamente
           - Classifica por grupo/subgrupo usando IA
           - Calcula confiança da classificação
        
        3. **Validação completa**:
           - Compara número de linhas processadas vs. original
           - Alerta se houver diferença
           - Permite usar IA como "avaliador completo" para garantir processamento total
        
        **Opção: Usar IA como Avaliador Completo**
        
        - Marque a opção **"Usar IA como avaliador completo do arquivo"**
        - Garante que **todas as linhas** sejam processadas
        - Recomendado para:
          - PDFs com mais de 200 linhas
          - Arquivos não estruturados
          - Quando o processamento automático não capturou tudo
        
        **Passo 4: Revisão e Edição**
        
        1. Visualize os dados processados na tabela
        2. **Edite diretamente** se necessário:
           - Clique em uma célula para editar
           - Pressione Enter para salvar
        3. **Revise classificações**:
           - Verifique grupo/subgrupo atribuídos
           - Alerte para confiança < 70%
           - Corrija manualmente se necessário
        
        4. **Selecione linhas** para importar:
           - Use checkboxes à esquerda
           - Ou selecione todas com o checkbox do cabeçalho
        
        **Passo 5: Importação Final**
        
        1. Revise os dados uma última vez
        2. Clique em **"Importar Dados Selecionados"**
        3. Aguarde a confirmação
        4. Os dados serão salvos no banco de dados
        5. Aparecerão automaticamente nos relatórios (se habilitados na configuração)
        
        ### 3.2 Cadastro Manual
        
        Você pode cadastrar dados manualmente quando não tiver arquivos para importar:
        
        **Transações Financeiras:**
        
        1. Acesse **"💳 Transações Financeiras"**
        2. Aba **"➕ Nova Transação"**
        3. Preencha: Data, Descrição, Valor, Tipo (entrada/saída)
        4. Selecione Grupo e Subgrupo
        5. Clique em **"Cadastrar Transação"**
        
        **Extratos Bancários:**
        
        1. Acesse **"🏦 Extratos Bancários"**
        2. Aba **"➕ Novo Extrato"**
        3. Preencha: Data, Banco, Conta, Valor, Descrição
        4. Selecione Grupo e Subgrupo
        5. Clique em **"Criar Extrato"**
        
        **Contratos/Eventos:**
        
        1. Acesse **"📝 Contratos"**
        2. Aba **"➕ Novo Contrato"**
        3. Preencha campos:
           - Datas (início, evento)
           - Valores (serviço, deslocamento)
           - Tipo de evento, Serviço vendido
           - Vendedor, Local, Horas, NF
           - Cliente/Contratante
        4. Clique em **"Criar Contrato"**
        
        **Contas a Pagar:**
        
        1. Acesse **"💰 Contas"** → Aba **"Contas a Pagar"**
        2. Clique em **"➕ Nova Conta a Pagar"**
        3. Preencha: Credor, CPF/CNPJ, Data de vencimento, Valor
        4. Selecione Grupo e Subgrupo
        5. Clique em **"Cadastrar"**
        
        **Contas a Receber:**
        
        1. Acesse **"💰 Contas"** → Aba **"Contas a Receber"**
        2. Clique em **"➕ Nova Conta a Receber"**
        3. Preencha: Devedor, CPF/CNPJ, Data de vencimento, Valor
        4. Opcional: Vincule a um contrato existente
        5. Selecione Grupo e Subgrupo
        6. Clique em **"Cadastrar"**
        
        ---
        
        ## 4️⃣ Relacionamento entre Dados e Relatórios
        
        ### 4.1 Como os Dados Alimentam os Relatórios
        
        **Fluxo de dados:**
        
        ```
        Importação/Cadastro → Banco de Dados → Filtragem por Configuração → Agrupamento → Relatórios
        ```
        
        1. **Dados são importados ou cadastrados manualmente**
           - Salvos no banco de dados PostgreSQL
           - Classificados por grupo/subgrupo
           - Vinculados ao cliente
        
        2. **Sistema verifica configurações de relatórios**
           - Para cada relatório (DRE, DFC, Sazonalidade)
           - Verifica quais tipos de dados estão habilitados
           - **Ignora completamente** tipos desabilitados
        
        3. **Agrupamento por grupo/subgrupo**
           - Dados são agrupados conforme o plano de contas
           - Permite análise hierárquica (grupo → subgrupo → transações)
        
        4. **Consolidação de múltiplas fontes**
           - DRE: Consolida receitas e despesas de todas as fontes habilitadas
           - DFC: Consolida fluxo de caixa de todas as fontes habilitadas
           - Sazonalidade: Analisa padrões de todas as fontes habilitadas
        
        ### 4.2 Filtragem por Configuração de Relatórios
        
        **Exemplo prático:**
        
        Cliente tem:
        - 100 transações financeiras
        - 50 contratos
        - 30 contas a pagar
        
        Configuração do DRE:
        - ✅ Transações: Habilitado
        - ✅ Contratos: Habilitado
        - ❌ Contas a Pagar: Desabilitado
        
        Resultado no DRE:
        - ✅ Transações aparecem (100 registros)
        - ✅ Contratos aparecem (50 registros)
        - ❌ Contas a Pagar **não aparecem** (0 registros, mesmo tendo 30 no banco)
        
        ### 4.3 Agrupamento por Grupo/Subgrupo
        
        Todos os dados são classificados por:
        
        - **Grupo**: Categoria principal (ex: "Receitas Operacionais", "Despesas Administrativas")
        - **Subgrupo**: Categoria específica (ex: "Vendas de Serviços", "Aluguel")
        
        Nos relatórios:
        - DRE: Agrupa receitas e despesas por grupo/subgrupo
        - DFC: Agrupa fluxo por grupo/subgrupo
        - Sazonalidade: Analisa padrões por grupo/subgrupo
        
        ### 4.4 Consolidação de Múltiplas Fontes
        
        O sistema consolida dados de diferentes fontes:
        
        **DRE (Demonstração do Resultado):**
        - Receitas: Transações (entrada) + Contratos + Contas a Receber
        - Despesas: Transações (saída) + Contas a Pagar + Faturas de Cartão
        
        **DFC (Fluxo de Caixa):**
        - Entradas: Extratos bancários (créditos) + Contas a Receber (recebidas)
        - Saídas: Extratos bancários (débitos) + Contas a Pagar (pagas)
        
        **Sazonalidade:**
        - Analisa padrões de todas as fontes habilitadas
        - Identifica tendências mensais, trimestrais, anuais
        
        ---
        
        ## 5️⃣ Relatórios e Dashboards
        
        ### 5.1 DRE (Demonstração do Resultado)
        
        **O que é:**
        Relatório que mostra receitas, despesas e resultado líquido em um período.
        
        **Como acessar:**
        Menu → **"📊 DRE"**
        
        **O que você verá:**
        - **KPIs principais**: Receitas totais, Despesas totais, Resultado, Margem
        - **Gráfico de barras**: Receitas vs Despesas por mês
        - **Tabela detalhada**: Receitas e despesas agrupadas por grupo/subgrupo
        - **Origem dos dados**: Indica de onde vieram (extrato, contrato, etc.)
        
        **Como interpretar:**
        - **Receitas > Despesas**: Resultado positivo (lucro)
        - **Receitas < Despesas**: Resultado negativo (prejuízo)
        - **Margem**: Percentual de lucro sobre receitas
        - **Grupos/Subgrupos**: Mostram onde estão concentradas receitas/despesas
        
        **Filtros disponíveis:**
        - Período (mês, 3 meses, 6 meses, ano, personalizado)
        - Tipo (receitas, despesas, ambos)
        
        ### 5.2 DFC (Fluxo de Caixa)
        
        **O que é:**
        Relatório que mostra entradas e saídas de dinheiro em um período.
        
        **Como acessar:**
        Menu → **"💵 DFC"**
        
        **O que você verá:**
        - **KPIs principais**: Saldo inicial, Entradas, Saídas, Saldo final
        - **Gráfico de fluxo**: Entradas e saídas por mês
        - **Tabela detalhada**: Transações agrupadas por grupo/subgrupo
        - **Fontes dos dados**: Tabela mostrando origem (extrato, conta, etc.)
        
        **Como interpretar:**
        - **Saldo positivo**: Mais dinheiro entrando do que saindo
        - **Saldo negativo**: Mais dinheiro saindo do que entrando
        - **Projeções**: Mostra fluxo futuro baseado em contas a pagar/receber
        
        **Filtros disponíveis:**
        - Período (mês, 3 meses, 6 meses, ano, personalizado)
        
        ### 5.3 Sazonalidade
        
        **O que é:**
        Análise de padrões sazonais e tendências ao longo do tempo.
        
        **Como acessar:**
        Menu → **"📈 Sazonalidade"**
        
        **O que você verá:**
        - **Gráfico de tendências**: Receitas e despesas ao longo dos meses
        - **Comparação mensal**: Mês atual vs mesmo mês do ano anterior
        - **Análise por grupo/subgrupo**: Padrões específicos por categoria
        - **Análise de eventos**: Sazonalidade de contratos/eventos
        
        **Como interpretar:**
        - **Picos**: Meses com maior movimento
        - **Vales**: Meses com menor movimento
        - **Tendências**: Crescimento ou declínio ao longo do tempo
        - **Sazonalidade**: Padrões que se repetem (ex: dezembro sempre alto)
        
        ### 5.4 Relatórios Especializados
        
        **📅 Diário de Gastos:**
        - Acompanhamento diário de despesas
        - Heatmap de gastos por dia
        - Gráficos de tendências diárias
        
        **🎯 Painel de Controle Unificado:**
        - Visão executiva consolidada
        - KPIs principais de todos os relatórios
        - Gráficos interativos
        
        **💵 Fluxo de Caixa Gerencial:**
        - Análise gerencial de fluxo de caixa
        - Projeções futuras
        - Análise de cenários
        
        **👤 Despesas CPF vs CNPJ:**
        - Separação de despesas pessoais e empresariais
        - Análise de distribuição
        - Conformidade fiscal
        
        **💰 Dashboard de Contas:**
        - Aging de contas a pagar e receber
        - Inadimplência
        - Projeções de 90 dias
        
        **📝 Relatório de Eventos:**
        - Análise de contratos e eventos
        - Calendário de eventos
        - Performance de vendedores
        
        **📈 Performance de Vendedores:**
        - Análise de vendas por vendedor
        - Comissões
        - Metas e resultados
        
        ---
        
        ## 🔄 Fluxo Completo do Sistema
        
        **Resumo do processo de ponta a ponta:**
        
        1. **👑 Admin cria usuários e clientes**
           - Define permissões e roles
           - Cria clientes no sistema
        
        2. **⚙️ Admin configura relatórios por cliente**
           - Define quais tipos de dados aparecem em cada relatório
           - Visualiza o mapa de conexões
        
        3. **📥 Usuário importa/cadastra dados**
           - Importa arquivos (CSV, Excel, PDF, imagens)
           - Ou cadastra manualmente
           - Sistema classifica automaticamente
        
        4. **🤖 Sistema processa e organiza**
           - Classifica por grupo/subgrupo
           - Valida e armazena no banco
        
        5. **📊 Relatórios são gerados automaticamente**
           - Respeitando configurações de relatórios
           - Agrupando por grupo/subgrupo
           - Consolidando múltiplas fontes
        
        6. **🗺️ Mapa visual mostra conexões**
           - Tipos de dados → Relatórios
           - Reflete configurações em tempo real
        
        **Dica importante:**
        
        Sempre configure os relatórios **antes** de importar muitos dados. Isso garante que os relatórios mostrem exatamente o que você precisa desde o início.
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






