"""
Sidebar centralizada para todas as páginas
"""
import streamlit as st
from services.auth_service import AuthService
from config.database import SessionLocal
from models.client import Client
from utils.hide_auto_menu import hide_streamlit_menu
from utils.client_selection import sync_selected_client


def show_sidebar():
    """
    Sidebar de navegação centralizada - usada por todas as páginas
    """
    # Esconde o menu automático do Streamlit
    hide_streamlit_menu()
    
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
                
                # Mantém o estado do widget alinhado ao cliente selecionado globalmente
                current_value = st.session_state.get("sidebar_client_selector")
                if current_value != default_client:
                    st.session_state["sidebar_client_selector"] = default_client

                options_list = list(client_options.keys())
                default_index = options_list.index(default_client) if default_client in options_list else 0

                selected_client_id = st.selectbox(
                    "Selecione o cliente:",
                    options=options_list,
                    format_func=lambda x: client_options[x],
                    index=default_index,
                    label_visibility="collapsed"
                )
                
                sync_selected_client(selected_client_id, source="sidebar")
                
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
        
        st.page_link("pages/16_Diario_Gastos.py", label="📓 Diário de Gastos", icon="📓")
        st.caption("Controle visual diário de despesas")
        
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
        
        st.page_link("pages/4_Contratos.py", label="📝 Contratos e Eventos", icon="📝")
        st.caption("Gerencie contratos e eventos")
        
        st.page_link("pages/5_Contas.py", label="💰 Contas a Pagar/Receber", icon="💰")
        st.caption("Controle de contas a pagar e receber")
        
        st.markdown("---")
        
        # Seção Dashboards e Relatórios
        st.markdown("#### 📊 Dashboards e Relatórios")
        
        st.page_link("pages/22_Painel_Controle.py", label="🎯 Painel de Controle", icon="🎯")
        st.caption("Visão executiva unificada")
        
        st.markdown("**📊 Relatórios Financeiros:**")
        st.page_link("pages/6_DRE.py", label="📈 DRE", icon="📊")
        st.page_link("pages/7_DFC.py", label="💵 DFC", icon="💵")
        st.page_link("pages/18_Fluxo_Caixa_Gerencial.py", label="💼 Fluxo Gerencial", icon="💼")
        
        st.markdown("**🎯 Relatórios Operacionais:**")
        st.page_link("pages/17_Relatorio_Eventos.py", label="🎉 Eventos/Contratos", icon="🎉")
        st.page_link("pages/20_Contas_Dashboard.py", label="💰 Contas Dashboard", icon="💰")
        st.page_link("pages/19_Despesas_PF_PJ.py", label="💼 Despesas PF/PJ", icon="💼")
        st.page_link("pages/21_Performance_Vendedores.py", label="🏆 Vendedores", icon="🏆")
        
        st.markdown("**📈 Análises:**")
        st.page_link("pages/8_Sazonalidade.py", label="📉 Sazonalidade", icon="📈")
        st.page_link("pages/9_Relatorios.py", label="📑 Exportação", icon="📑")
        
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












