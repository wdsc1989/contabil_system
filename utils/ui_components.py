"""
Componentes visuais reutilizáveis para a interface
"""
import streamlit as st
from config.database import SessionLocal
from models.client import Client


def show_client_header(client_id: int, compact: bool = True):
    """
    Exibe um header visual com informações do cliente selecionado
    
    Args:
        client_id: ID do cliente
        compact: Se True, exibe versão compacta. Se False, exibe versão completa
    """
    db = SessionLocal()
    try:
        client = db.query(Client).filter(Client.id == client_id).first()
        if client:
            if compact:
                # Versão compacta (para páginas internas)
                st.markdown(f"""
                <div style="
                    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                    padding: 12px 20px;
                    border-radius: 8px;
                    color: white;
                    margin-bottom: 15px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                ">
                    <div>
                        <span style="font-size: 18px; font-weight: bold;">🏢 {client.name}</span>
                        <span style="font-size: 12px; margin-left: 15px; opacity: 0.9;">📋 {client.cpf_cnpj}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Versão completa (para página principal)
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px;
                    border-radius: 10px;
                    color: white;
                    margin-bottom: 20px;
                ">
                    <div style="font-size: 24px; font-weight: bold; margin-bottom: 5px;">
                        🏢 {client.name}
                    </div>
                    <div style="font-size: 14px; opacity: 0.9;">
                        📋 {client.cpf_cnpj}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    finally:
        db.close()


def show_client_selector():
    """
    Exibe seletor de cliente com pesquisa (reutilizável)
    Retorna o client_id selecionado
    """
    from services.auth_service import AuthService
    
    user = AuthService.get_current_user()
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
                st.session_state.selected_client_id = default_client
            
            # Selectbox com pesquisa (permite digitar para buscar)
            selected_client_id = st.selectbox(
                "🏢 Selecione o cliente:",
                options=list(client_options.keys()),
                format_func=lambda x: client_options[x],
                index=list(client_options.keys()).index(default_client) if default_client in client_options else 0,
                key="client_selector_global",
                help="Digite para pesquisar pelo nome do cliente"
            )
            
            # Atualiza session state se mudou
            if selected_client_id != st.session_state.get('selected_client_id'):
                st.session_state.selected_client_id = selected_client_id
                st.rerun()
            
            # Exibe informações do cliente selecionado
            selected = next((c for c in clients if c.id == selected_client_id), None)
            if selected:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption(f"📋 {selected.cpf_cnpj}")
                with col2:
                    if selected.tipo_empresa:
                        st.caption(f"🏷️ {selected.tipo_empresa}")
            
            return selected_client_id
        else:
            st.warning("⚠️ Nenhum cliente disponível.")
            st.session_state.selected_client_id = None
            return None
    finally:
        db.close()


def show_sidebar_navigation():
    """
    Exibe a sidebar padrão com navegação
    """
    from services.auth_service import AuthService
    
    with st.sidebar:
        st.title("📊 Sistema Contábil")
        user = AuthService.get_current_user()
        st.markdown(f"**Usuário:** {user['username']}")
        st.markdown(f"**Perfil:** {user['role'].title()}")
        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True):
            AuthService.logout()
            st.rerun()


def show_metric_card(label: str, value: str, icon: str = "📊", delta: str = None, help_text: str = None):
    """
    Exibe um card de métrica estilizado
    
    Args:
        label: Rótulo da métrica
        value: Valor da métrica
        icon: Ícone emoji
        delta: Variação (opcional)
        help_text: Texto de ajuda (opcional)
    """
    st.metric(
        label=f"{icon} {label}",
        value=value,
        delta=delta,
        help=help_text
    )


def show_info_box(title: str, content: str, box_type: str = "info"):
    """
    Exibe uma caixa de informação estilizada
    
    Args:
        title: Título da caixa
        content: Conteúdo
        box_type: Tipo (info, success, warning, error)
    """
    colors = {
        "info": "#3498db",
        "success": "#2ecc71",
        "warning": "#f39c12",
        "error": "#e74c3c"
    }
    
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    
    color = colors.get(box_type, colors["info"])
    icon = icons.get(box_type, icons["info"])
    
    st.markdown(f"""
    <div style="
        background-color: {color}15;
        border-left: 4px solid {color};
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    ">
        <div style="font-weight: bold; margin-bottom: 5px;">
            {icon} {title}
        </div>
        <div style="font-size: 14px;">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_stat_cards(stats: list):
    """
    Exibe cards de estatísticas em colunas
    
    Args:
        stats: Lista de dicionários com 'label', 'value', 'icon', 'delta' (opcional)
    """
    cols = st.columns(len(stats))
    
    for idx, stat in enumerate(stats):
        with cols[idx]:
            show_metric_card(
                label=stat.get('label', ''),
                value=stat.get('value', ''),
                icon=stat.get('icon', '📊'),
                delta=stat.get('delta'),
                help_text=stat.get('help')
            )

