"""
Página de Importação de Dados
"""
import streamlit as st
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from services.parser_service import ParserService
from services.import_service import ImportService
from utils.column_mapper import ColumnMapper
from models.client import Client
from models.group import Group, Subgroup

st.set_page_config(page_title="Importação de Dados", page_icon="📥", layout="wide")

# Verifica autenticação
AuthService.init_session_state()
AuthService.require_auth()


def show_sidebar():
    """Mostra a sidebar de navegação"""
    with st.sidebar:
        st.title("📊 Sistema Contábil")
        user = AuthService.get_current_user()
        st.markdown(f"**Usuário:** {user['username']}")
        st.markdown(f"**Perfil:** {user['role'].title()}")
        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True):
            AuthService.logout()
            st.rerun()


show_sidebar()

st.title("📥 Importação de Dados")
st.markdown("---")

# Verifica se há cliente selecionado
if not st.session_state.get('selected_client_id'):
    st.warning("⚠️ Selecione um cliente na página inicial para importar dados.")
    st.stop()

client_id = st.session_state.selected_client_id

# Informações do cliente
db = SessionLocal()
try:
    client = db.query(Client).filter(Client.id == client_id).first()
    if client:
        st.info(f"📌 Importando dados para: **{client.name}**")
finally:
    db.close()

# Tipo de importação
st.subheader("1️⃣ Selecione o Tipo de Importação")

import_type = st.selectbox(
    "Tipo de dado:",
    options=['transactions', 'bank_statements', 'contracts', 'accounts_payable', 'accounts_receivable'],
    format_func=lambda x: {
        'transactions': '💳 Transações Financeiras',
        'bank_statements': '🏦 Extratos Bancários',
        'contracts': '📝 Contratos/Eventos',
        'accounts_payable': '💸 Contas a Pagar',
        'accounts_receivable': '💰 Contas a Receber'
    }[x]
)

st.markdown("---")

# Upload de arquivo
st.subheader("2️⃣ Faça Upload do Arquivo")

file_type = st.radio(
    "Formato do arquivo:",
    options=['CSV', 'Excel', 'PDF', 'OFX'],
    horizontal=True
)

uploaded_file = st.file_uploader(
    f"Selecione um arquivo {file_type}",
    type={
        'CSV': ['csv', 'txt'],
        'Excel': ['xlsx', 'xls'],
        'PDF': ['pdf'],
        'OFX': ['ofx']
    }[file_type]
)

if uploaded_file:
    st.success(f"✅ Arquivo carregado: {uploaded_file.name}")
    
    try:
        # Parse do arquivo
        df = None
        
        if file_type == 'CSV':
            file_content = uploaded_file.read()
            delimiter = ParserService.detect_delimiter(file_content)
            
            col1, col2 = st.columns(2)
            with col1:
                encoding = st.selectbox("Encoding:", ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252'])
            with col2:
                delimiter = st.selectbox("Delimitador:", [',', ';', '\t', '|'], 
                                        index=[',', ';', '\t', '|'].index(delimiter))
            
            df = ParserService.parse_csv(file_content, encoding, delimiter)
        
        elif file_type == 'Excel':
            file_content = uploaded_file.read()
            sheets = ParserService.get_excel_sheets(file_content)
            
            if len(sheets) > 1:
                selected_sheet = st.selectbox("Selecione a planilha:", sheets)
                df = ParserService.parse_excel(file_content, selected_sheet)
            else:
                df = ParserService.parse_excel(file_content)
        
        elif file_type == 'PDF':
            file_content = uploaded_file.read()
            df = ParserService.parse_pdf_to_dataframe(file_content)
            
            if df is None:
                st.error("❌ Não foi possível extrair tabela do PDF. Tente converter para CSV ou Excel.")
                st.stop()
        
        elif file_type == 'OFX':
            file_content = uploaded_file.read()
            df = ParserService.ofx_to_dataframe(file_content)
        
        if df is not None and not df.empty:
            st.markdown("---")
            st.subheader("3️⃣ Preview dos Dados")
            st.dataframe(df.head(10), use_container_width=True)
            st.caption(f"Total de linhas: {len(df)}")
            
            st.markdown("---")
            st.subheader("4️⃣ Mapeamento de Colunas")
            
            # Obtém colunas alvo
            target_columns = ImportService.get_target_columns(import_type)
            required_fields = ColumnMapper.get_required_fields(import_type)
            
            # Tenta carregar mapeamento salvo
            db = SessionLocal()
            try:
                saved_mapping = ImportService.load_mapping(db, client_id, import_type)
                
                if saved_mapping:
                    use_saved = st.checkbox("📋 Usar mapeamento salvo anteriormente", value=True)
                else:
                    use_saved = False
                
                # Sugere mapeamento automático
                if use_saved and saved_mapping:
                    mapping = saved_mapping
                else:
                    mapping = ColumnMapper.suggest_mapping(list(df.columns), target_columns)
                
                st.markdown("**Mapeie as colunas do arquivo para os campos do sistema:**")
                st.caption("Campos obrigatórios marcados com *")
                
                # Interface de mapeamento
                mapping_form = {}
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Coluna do Arquivo**")
                with col2:
                    st.markdown("**Campo do Sistema**")
                
                st.markdown("---")
                
                for source_col in df.columns:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.text(source_col)
                    
                    with col2:
                        options = ['ignore'] + target_columns
                        default_value = mapping.get(source_col, 'ignore')
                        
                        if default_value not in options:
                            default_value = 'ignore'
                        
                        selected = st.selectbox(
                            f"Mapear para:",
                            options=options,
                            index=options.index(default_value),
                            key=f"map_{source_col}",
                            format_func=lambda x: f"⚠️ {x} *" if x in required_fields else x,
                            label_visibility="collapsed"
                        )
                        
                        mapping_form[source_col] = selected
                
                # Validação do mapeamento
                is_valid, missing_fields = ColumnMapper.validate_mapping(mapping_form, required_fields)
                
                if not is_valid:
                    st.error(f"❌ Campos obrigatórios não mapeados: {', '.join(missing_fields)}")
                else:
                    st.success("✅ Todos os campos obrigatórios foram mapeados!")
                
                st.markdown("---")
                
                # Opções adicionais para transações
                group_id = None
                subgroup_id = None
                
                if import_type == 'transactions':
                    st.subheader("5️⃣ Classificação (Opcional)")
                    
                    groups = db.query(Group).filter(Group.client_id == client_id).all()
                    
                    if groups:
                        selected_group = st.selectbox(
                            "Grupo:",
                            options=[None] + groups,
                            format_func=lambda x: "Nenhum" if x is None else x.name
                        )
                        
                        if selected_group:
                            group_id = selected_group.id
                            
                            subgroups = db.query(Subgroup).filter(Subgroup.group_id == group_id).all()
                            
                            if subgroups:
                                selected_subgroup = st.selectbox(
                                    "Subgrupo:",
                                    options=[None] + subgroups,
                                    format_func=lambda x: "Nenhum" if x is None else x.name
                                )
                                
                                if selected_subgroup:
                                    subgroup_id = selected_subgroup.id
                    else:
                        st.info("ℹ️ Nenhum grupo cadastrado. Você pode criar grupos na página de administração.")
                    
                    st.markdown("---")
                
                # Botões de ação
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    save_mapping_btn = st.button("💾 Salvar Mapeamento", use_container_width=True)
                
                with col2:
                    import_btn = st.button("📥 Importar Dados", use_container_width=True, 
                                          disabled=not is_valid, type="primary")
                
                if save_mapping_btn:
                    ImportService.save_mapping(db, client_id, import_type, mapping_form)
                    st.success("✅ Mapeamento salvo com sucesso!")
                
                if import_btn and is_valid:
                    with st.spinner("Importando dados..."):
                        # Aplica mapeamento
                        mapped_df = ImportService.apply_mapping(df, mapping_form)
                        
                        # Importa dados
                        imported_count = 0
                        
                        if import_type == 'transactions':
                            imported_count = ImportService.import_transactions(
                                db, client_id, mapped_df, 'imported', uploaded_file.name,
                                group_id, subgroup_id
                            )
                        
                        elif import_type == 'bank_statements':
                            bank_name = st.text_input("Nome do banco:", value="Banco")
                            imported_count = ImportService.import_bank_statements(
                                db, client_id, mapped_df, bank_name, uploaded_file.name
                            )
                        
                        elif import_type == 'contracts':
                            imported_count = ImportService.import_contracts(
                                db, client_id, mapped_df
                            )
                        
                        elif import_type == 'accounts_payable':
                            imported_count = ImportService.import_accounts_payable(
                                db, client_id, mapped_df
                            )
                        
                        elif import_type == 'accounts_receivable':
                            imported_count = ImportService.import_accounts_receivable(
                                db, client_id, mapped_df
                            )
                        
                        if imported_count > 0:
                            st.success(f"✅ {imported_count} registro(s) importado(s) com sucesso!")
                            st.balloons()
                        else:
                            st.warning("⚠️ Nenhum registro foi importado. Verifique os dados.")
            
            finally:
                db.close()
        
        else:
            st.error("❌ Não foi possível ler o arquivo. Verifique o formato.")
    
    except Exception as e:
        st.error(f"❌ Erro ao processar arquivo: {str(e)}")
        st.exception(e)

else:
    st.info("ℹ️ Faça upload de um arquivo para começar.")

# Informações sobre formatos
with st.expander("ℹ️ Informações sobre Formatos"):
    st.markdown("""
    ### Formatos Suportados
    
    **CSV (Comma-Separated Values)**
    - Formato texto com valores separados por vírgula, ponto-e-vírgula ou tabulação
    - Suporta diferentes encodings (UTF-8, Latin-1, etc)
    
    **Excel (XLSX/XLS)**
    - Planilhas do Microsoft Excel
    - Suporta múltiplas abas
    
    **PDF**
    - Extração automática de tabelas
    - Funciona melhor com PDFs que contêm tabelas estruturadas
    
    **OFX (Open Financial Exchange)**
    - Formato padrão de extratos bancários
    - Usado por bancos brasileiros (BB, Itaú, Bradesco, etc)
    """)

with st.expander("✏️ Edição de Dados Importados"):
    st.markdown("""
    ### Como Editar Dados Importados
    
    Após importar seus dados, você pode editá-los nas páginas específicas:
    
    - **💳 Transações** → Edite, exclua ou adicione transações manualmente
    - **📝 Contratos** → Gerencie contratos importados ou manuais
    - **💰 Contas** → Edite contas a pagar e receber
    
    **Dica:** Todos os dados importados podem ser editados ou excluídos individualmente!
    """)

