"""
Utilitário para esconder o menu automático do Streamlit
"""
import streamlit as st


def hide_streamlit_menu():
    """
    Esconde o menu automático de navegação do Streamlit usando CSS
    """
    st.markdown("""
    <style>
    /* Esconde o menu de navegação automático do Streamlit */
    [data-testid="stSidebarNav"] {
        opacity: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
        pointer-events: none !important;
    }
    
    /* Esconde o seletor de páginas automático */
    section[data-testid="stSidebar"] > div:first-child > div:first-child {
        display: none !important;
    }
    
    /* Esconde qualquer elemento de navegação automática na sidebar */
    section[data-testid="stSidebar"] nav {
        display: none !important;
    }
    
    /* Esconde o menu de navegação se estiver em outro lugar */
    .css-1d391kg,
    .css-1lcbmhc,
    .css-1y4p8pa {
        display: none !important;
    }
    
    /* Esconde o menu de navegação usando seletores mais específicos */
    section[data-testid="stSidebar"] > div > div:first-child > div:first-child {
        display: none !important;
    }
    
    /* Esconde qualquer lista de navegação */
    section[data-testid="stSidebar"] ul[data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* Remove o botão padrão de recolher/expandir */
    div[data-testid="collapsedControl"],
    button[title="Close sidebar"],
    button[title="Open sidebar"],
    button[data-testid="baseButton-toggleNav"] {
        display: none !important;
    }

    /* Garante que a sidebar personalizada ocupe todo o espaço */
    section[data-testid="stSidebar"] > div {
        padding-top: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)





