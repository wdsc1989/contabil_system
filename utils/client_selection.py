"""
Funções utilitárias para sincronizar seleção de cliente entre componentes
"""
import streamlit as st


def sync_selected_client(selected_client_id: int, source: str | None = None):
    """
    Atualiza o estado global do cliente selecionado e mantém os widgets sincronizados.

    Args:
        selected_client_id: ID do cliente selecionado.
        source: Identificador opcional de onde veio a seleção
                (ex.: 'sidebar', 'top_nav'). Usado para evitar loops.
    """
    if selected_client_id is None:
        return

    st.session_state.selected_client_id = selected_client_id

    # Widgets pegam o valor direto de selected_client_id como default,
    # evitando atualizar manualmente st.session_state de cada selectbox.









