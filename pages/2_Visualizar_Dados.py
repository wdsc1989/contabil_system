"""
Página unificada para visualizar todos os tipos de dados importados
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import AuthService
from utils.ui_components import show_client_selector, show_sidebar_navigation

st.set_page_config(page_title="Visualizar Dados", page_icon="📊", layout="wide")

AuthService.init_session_state()
AuthService.require_auth()

show_sidebar_navigation()

st.title("📊 Visualizar Dados Importados")

# Seletor de cliente no topo da página
client_id = show_client_selector()

if not client_id:
    st.warning("⚠️ Nenhum cliente disponível.")
    st.stop()

st.markdown("---")

# Lista suspensa para selecionar o tipo de dado
st.subheader("Selecione o tipo de dado para visualizar:")

data_types = {
    "💳 Faturas de Cartão de Crédito": "12_Faturas_Cartao",
    "📈 Aplicações Financeiras": "13_Aplicacoes_Financeiras",
    "🏪 Extratos de Máquina de Cartão": "14_Maquina_Cartao",
    "📦 Controle de Estoque": "15_Estoque"
}

selected_type = st.selectbox(
    "Tipo de dado:",
    options=list(data_types.keys()),
    index=0,
    key="data_type_selector"
)

st.markdown("---")

# Redireciona para a página selecionada usando st.switch_page
if selected_type:
    page_name = data_types[selected_type]
    st.info(f"📌 Redirecionando para: **{selected_type}**")
    
    # Usa JavaScript para redirecionar (alternativa ao st.switch_page que pode não funcionar em todos os contextos)
    # Ou podemos usar st.rerun com session_state
    if 'redirect_to_page' not in st.session_state or st.session_state.redirect_to_page != page_name:
        st.session_state.redirect_to_page = page_name
        st.rerun()
    
    # Tenta usar st.switch_page se disponível
    try:
        st.switch_page(f"pages/{page_name}.py")
    except:
        # Fallback: mostra mensagem e link
        st.markdown(f"""
        <div style="padding: 20px; background-color: #f0f2f6; border-radius: 10px; text-align: center;">
            <h3>Clique no botão abaixo para acessar:</h3>
            <p style="font-size: 18px; margin: 20px 0;">{selected_type}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Cria um link direto
        page_path = f"pages/{page_name}.py"
        st.page_link(page_path, label=f"➡️ Abrir {selected_type}", icon="📊", use_container_width=True)

