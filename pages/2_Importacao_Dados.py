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
from services.import_service import ImportService
from services.ai_service import AIService
from services.vision_processor import VisionProcessor
from utils.translations import translate_dataframe
from models.client import Client
from models.group import Group, Subgroup
from config.ai_config import AIConfigManager

# Constantes
CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.70  # 70% de confiança mínima para classificação

# Helpers
def _ensure_classification_confidence(record: dict) -> dict:
    """
    Normaliza o campo classification_confidence nos registros retornados pela IA.
    """
    if (
        "classification_confidence" not in record
        and "confidence" in record
        and record["confidence"] is not None
    ):
        record["classification_confidence"] = record.pop("confidence")
    else:
        record.pop("confidence", None)
    return record


def _get_group_subgroup_names_mapping(db, client_id: int) -> tuple:
    """
    Cria mapeamento de IDs para nomes de grupos e subgrupos.
    Retorna: (group_mapping, subgroup_mapping)
    """
    from models.group import Group, Subgroup
    
    groups = db.query(Group).filter(Group.client_id == client_id).all()
    group_mapping = {g.id: g.name for g in groups}
    
    subgroups = db.query(Subgroup).join(Group).filter(Group.client_id == client_id).all()
    subgroup_mapping = {sg.id: sg.name for sg in subgroups}
    
    return group_mapping, subgroup_mapping


def _add_group_subgroup_names_to_data(data: list, group_mapping: dict, subgroup_mapping: dict) -> list:
    """
    Adiciona colunas group_name e subgroup_name aos dados baseado nos IDs.
    """
    result = []
    for record in data:
        record_copy = dict(record)
        
        # Adiciona nomes de grupo e subgrupo
        group_id = record_copy.get('group_id')
        subgroup_id = record_copy.get('subgroup_id')
        
        if group_id is not None and not pd.isna(group_id):
            try:
                group_id_int = int(group_id)
                record_copy['group_name'] = group_mapping.get(group_id_int, f'ID: {group_id_int}')
            except (ValueError, TypeError):
                record_copy['group_name'] = '-'
        else:
            record_copy['group_name'] = '-'
        
        if subgroup_id is not None and not pd.isna(subgroup_id):
            try:
                subgroup_id_int = int(subgroup_id)
                record_copy['subgroup_name'] = subgroup_mapping.get(subgroup_id_int, f'ID: {subgroup_id_int}')
            except (ValueError, TypeError):
                record_copy['subgroup_name'] = '-'
        else:
            record_copy['subgroup_name'] = '-'
        
        result.append(record_copy)
    
    return result


st.set_page_config(page_title="Importação de Dados", page_icon="📥", layout="wide")

# Esconde o menu automático do Streamlit
from utils.hide_auto_menu import hide_streamlit_menu
hide_streamlit_menu()

# Verifica autenticação
AuthService.init_session_state()
AuthService.require_auth()

# Verifica se há resultado de importação concluída
if 'import_result' in st.session_state and st.session_state.import_result:
    result = st.session_state.import_result
    # Mostra notificação se a importação foi concluída recentemente (últimos 5 minutos)
    from datetime import datetime, timedelta
    try:
        timestamp = datetime.fromisoformat(result.get('timestamp', ''))
        if datetime.now() - timestamp < timedelta(minutes=5):
            if result.get('status') == 'success':
                st.success(f"✅ **Importação Concluída:** {result.get('message', '')}")
            elif result.get('status') == 'warning':
                st.warning(f"⚠️ **Importação:** {result.get('message', '')}")
            
            # Botão para limpar notificação
            if st.button("✖️ Fechar notificação", key="clear_import_notification"):
                del st.session_state.import_result
                st.rerun()
    except:
        pass


# Usa sidebar centralizada
from utils.sidebar import show_sidebar
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

# Upload de arquivo
st.subheader("1️⃣ Faça Upload do Arquivo")

uploaded_file = st.file_uploader(
    "Selecione um arquivo (CSV, Excel, PDF, OFX, ou Imagens: JPG, PNG, TIFF, etc)",
    type=['csv', 'txt', 'xlsx', 'xls', 'pdf', 'ofx', 'jpg', 'jpeg', 'png', 'tiff', 'tif', 'bmp', 'webp'],
    help="O sistema processará o arquivo automaticamente usando IA Vision."
)

if uploaded_file:
    st.success(f"✅ Arquivo carregado: {uploaded_file.name}")
    
    # Verifica se Vision API está disponível
    db = SessionLocal()
    try:
        ai_service = AIService(db)
        
        if not ai_service.is_available():
            st.error("❌ IA não configurada. Configure a IA na página de Administração antes de importar.")
            st.stop()
        
        # Verifica se suporta Vision API
        config = AIConfigManager.get_config_dict(db)
        provider = config.get('provider', '')
        model = config.get('model', '')
        
        if not AIConfigManager.supports_vision(provider, model):
            st.error(f"❌ O modelo {model} do provedor {provider} não suporta Vision API. Configure um modelo compatível (gpt-4o, gpt-4o-mini, etc).")
            st.stop()
        
        # Busca grupos e subgrupos
        groups = db.query(Group).filter(Group.client_id == client_id).all()
        groups_subgroups = []
        for group in groups:
            subgroups = db.query(Subgroup).filter(Subgroup.group_id == group.id).all()
            groups_subgroups.append({
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'subgroups': [
                    {
                        'id': sg.id,
                        'name': sg.name,
                        'description': sg.description
                    }
                    for sg in subgroups
                ]
            })
    finally:
        db.close()
    
    # Processamento direto com Vision API
    st.markdown("---")
    st.subheader("2️⃣ Processamento Automático com IA Vision")
    
    file_content = uploaded_file.read()
    
    # Verifica se já foi processado
    file_hash = f"{uploaded_file.name}_{len(file_content)}"
    if 'processed_file_hash' not in st.session_state or st.session_state.processed_file_hash != file_hash:
        # Processa arquivo
        with st.spinner("🤖 Processando arquivo com IA Vision (isso pode levar alguns segundos)..."):
            db = SessionLocal()
            try:
                processor = VisionProcessor(db)
                result = processor.process_file(
                    file_content=file_content,
                    filename=uploaded_file.name,
                    import_type=None,  # Detecta automaticamente
                    groups_subgroups=groups_subgroups if groups_subgroups else None
                )
                
                if not result.get('success'):
                    error_msg = result.get('error', 'Erro desconhecido')
                    st.error(f"❌ Erro no processamento: {error_msg}")
                    
                    # Mensagens de ajuda específicas
                    if 'pdf' in error_msg.lower() and ('poppler' in error_msg.lower() or 'pdf2image' in error_msg.lower()):
                        st.warning("📦 **Dependência faltando:** É necessária uma biblioteca para processar PDFs.")
                        st.info("💡 **Solução recomendada (Windows):** Execute no terminal:\n```bash\npip install PyMuPDF\n```")
                        st.caption("💡 PyMuPDF funciona no Windows sem precisar instalar poppler separadamente.")
                        st.info("💡 **Alternativa:** Se preferir usar pdf2image:\n```bash\npip install pdf2image\n```")
                        st.caption("⚠️ pdf2image requer poppler instalado no sistema (mais complexo no Windows).")
                    elif 'matplotlib' in error_msg.lower():
                        st.warning("📦 **Dependência faltando:** A biblioteca `matplotlib` é necessária para processar CSV/Excel.")
                        st.info("💡 **Solução:** Execute no terminal:\n```bash\npip install matplotlib\n```")
                    
                    if result.get('issues'):
                        with st.expander("⚠️ Detalhes dos problemas"):
                            for issue in result.get('issues', []):
                                st.warning(f"⚠️ {issue}")
                    st.stop()
                
                # Salva resultado no session state
                st.session_state.processed_data = result.get('processed_data', [])
                st.session_state.processed_summary = result.get('summary', {})
                st.session_state.detected_type = result.get('detected_type', 'transactions')
                st.session_state.processed_file_hash = file_hash
                
            finally:
                db.close()
    
    # Dados processados
    processed_data = st.session_state.get('processed_data', [])
    summary = st.session_state.get('processed_summary', {})
    detected_type = st.session_state.get('detected_type', 'transactions')
    
    if not processed_data:
        st.warning("⚠️ Nenhum dado foi extraído do arquivo.")
        st.stop()
    
    # Exibe estatísticas
    st.success(f"✅ Processamento concluído! {len(processed_data)} registro(s) extraído(s).")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Registros", len(processed_data))
    with col2:
        type_names = {
            'transactions': '💳 Transações',
            'bank_statements': '🏦 Extratos',
            'contracts': '📝 Contratos',
            'accounts_payable': '💸 Contas a Pagar',
            'accounts_receivable': '💰 Contas a Receber',
            'financial_investments': '📈 Investimentos',
            'credit_card_invoices': '💳 Faturas',
            'card_machine_statements': '🏪 Máquina Cartão',
            'inventory': '📦 Estoque'
        }
        st.metric("Tipo Detectado", type_names.get(detected_type, detected_type))
    with col3:
        if 'bank_name' in summary:
            st.metric("Banco", summary.get('bank_name', '-'))
    
    # Normaliza dados
    processed_data = [_ensure_classification_confidence(dict(record)) for record in processed_data]
    
    # Inicializa seleção
    if 'selected_rows' not in st.session_state:
        st.session_state.selected_rows = set(range(len(processed_data)))
    
    st.markdown("---")
    st.subheader("3️⃣ Revisão e Edição dos Dados")
    
    # Controles de seleção
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("✅ Selecionar Todas", use_container_width=True):
            st.session_state.selected_rows = set(range(len(processed_data)))
            st.rerun()
    
    with col2:
        if st.button("❌ Desselecionar Todas", use_container_width=True):
            st.session_state.selected_rows = set()
            st.rerun()
        
    with col3:
        total_selected = len(st.session_state.selected_rows)
        st.metric("Selecionadas", f"{total_selected} / {len(processed_data)}")
    
    with col4:
        if st.button("🔄 Reprocessar", use_container_width=True):
            del st.session_state.processed_file_hash
            st.rerun()
    
    # Prepara dados para edição
    db_edit = SessionLocal()
    try:
        group_mapping, subgroup_mapping = _get_group_subgroup_names_mapping(db_edit, client_id)
    finally:
        db_edit.close()
    
    edit_data = []
    for idx, row in enumerate(processed_data):
        row_copy = row.copy()
        row_copy['_select'] = idx in st.session_state.selected_rows
        row_copy['_row_num'] = idx + 1
        edit_data.append(row_copy)
    
    # Adiciona nomes de grupos e subgrupos
    edit_data = _add_group_subgroup_names_to_data(edit_data, group_mapping, subgroup_mapping)
    edit_df = pd.DataFrame(edit_data)
    
    # Configura colunas para edição
    display_cols = ['_row_num', '_select']
    if 'group_name' in edit_df.columns:
        display_cols.append('group_name')
    if 'subgroup_name' in edit_df.columns:
        display_cols.append('subgroup_name')
    
    # Adiciona outras colunas
    for col in edit_df.columns:
        if col not in ['_row_num', '_select', 'group_id', 'subgroup_id', 'group_name', 'subgroup_name']:
            display_cols.append(col)
    
    # Adiciona colunas ocultas (group_id, subgroup_id)
    all_cols = display_cols + ['group_id', 'subgroup_id'] if 'group_id' in edit_df.columns else display_cols
    edit_df = edit_df[[c for c in all_cols if c in edit_df.columns]]
    
    # Configura colunas editáveis
    column_config = {
        "_row_num": st.column_config.NumberColumn("Linha", width="small", disabled=True),
        "_select": st.column_config.CheckboxColumn("Importar", width="small"),
    }
    
    if 'group_name' in edit_df.columns:
        column_config['group_name'] = st.column_config.TextColumn("Grupo", width="medium", disabled=True)
    if 'subgroup_name' in edit_df.columns:
        column_config['subgroup_name'] = st.column_config.TextColumn("Subgrupo", width="medium", disabled=True)
    if 'group_id' in edit_df.columns:
        column_config['group_id'] = st.column_config.NumberColumn("group_id", width=0, disabled=True)
    if 'subgroup_id' in edit_df.columns:
        column_config['subgroup_id'] = st.column_config.NumberColumn("subgroup_id", width=0, disabled=True)
    
    # Adiciona configuração para campos comuns
    if 'date' in edit_df.columns:
        try:
            edit_df['date'] = pd.to_datetime(edit_df['date'], errors='coerce')
            column_config["date"] = st.column_config.DateColumn("Data", format="YYYY-MM-DD")
        except:
            column_config["date"] = st.column_config.TextColumn("Data")
    
    if 'value' in edit_df.columns:
        try:
            edit_df['value'] = pd.to_numeric(edit_df['value'], errors='coerce')
            column_config["value"] = st.column_config.NumberColumn("Valor", format="%.2f")
        except:
            column_config["value"] = st.column_config.TextColumn("Valor")
    
    if 'description' in edit_df.columns:
        column_config["description"] = st.column_config.TextColumn("Descrição", width="large")
    
    if 'bank_name' in edit_df.columns:
        column_config["bank_name"] = st.column_config.TextColumn("Banco", width="medium")
    
    # Exibe tabela editável
    edited_df = st.data_editor(
        edit_df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        height=min(500, max(300, len(edit_df) * 35))
    )
    
    # Atualiza seleção e dados
    new_selection = set()
    updated_data = []
    
    for idx, row in edited_df.iterrows():
        row_num = int(row.get('_row_num', idx + 1)) - 1
        if row.get('_select', False):
            new_selection.add(row_num)
        
        # Atualiza dados (remove colunas internas e nomes, mantém apenas IDs)
        row_dict = row.to_dict()
        row_dict.pop('_row_num', None)
        row_dict.pop('_select', None)
        row_dict.pop('group_name', None)
        row_dict.pop('subgroup_name', None)
        
        # Converte datas
        if 'date' in row_dict and pd.notna(row_dict.get('date')):
            if isinstance(row_dict['date'], pd.Timestamp):
                row_dict['date'] = row_dict['date'].strftime('%Y-%m-%d')
        
        # Converte valores
        for col in ['value', 'balance']:
            if col in row_dict and pd.notna(row_dict.get(col)):
                try:
                    row_dict[col] = float(row_dict[col])
                except:
                    pass
        
        updated_data.append(row_dict)
    
    st.session_state.selected_rows = new_selection
    st.session_state.processed_data = updated_data
    
    st.markdown("---")
    st.subheader("4️⃣ Importação Final")
    
    # Configurações específicas por tipo
    bank_name = "Banco"
    if detected_type == 'bank_statements':
        bank_name = summary.get('bank_name', 'Banco')
        if 'bank_name_override' not in st.session_state:
            st.session_state.bank_name_override = bank_name
        
        edited_bank_name = st.text_input(
            "Nome do banco:",
            value=st.session_state.get('bank_name_override', bank_name),
            key="bank_name_input"
        )
        st.session_state.bank_name_override = edited_bank_name
        bank_name = edited_bank_name
    
    # Botão de importar
    import_btn = st.button(
        "📥 Importar Dados Selecionados",
        use_container_width=True,
        disabled=len(st.session_state.selected_rows) == 0,
        type="primary"
    )
    
    if import_btn and len(st.session_state.selected_rows) > 0:
        # Filtra apenas linhas selecionadas
        selected_indices = sorted(list(st.session_state.selected_rows))
        data_to_import = [st.session_state.processed_data[i] for i in selected_indices if 0 <= i < len(st.session_state.processed_data)]
        import_df = pd.DataFrame(data_to_import)
        
        # Container para progresso
        import_progress_container = st.empty()
        
        def update_import_progress(message):
            import_progress_container.info(f"💾 **Importando:** {message}")
        
        # Importa dados
        db = SessionLocal()
        try:
            with st.spinner("💾 Preparando importação..."):
                imported_count = 0
                import_result = None
                
                if detected_type == 'transactions':
                    imported_count = ImportService.import_transactions(
                        db, client_id, import_df, 'imported', uploaded_file.name,
                        None, None, progress_callback=update_import_progress
                    )
                
                elif detected_type == 'bank_statements':
                    import_result = ImportService.import_bank_statements(
                        db, client_id, import_df, bank_name, uploaded_file.name,
                        None, None, progress_callback=update_import_progress
                    )
                    imported_count = import_result.get('statements', 0)
                    transactions_created = import_result.get('transactions', 0)
                
                elif detected_type == 'contracts':
                    imported_count = ImportService.import_contracts(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
                
                elif detected_type == 'accounts_payable':
                    imported_count = ImportService.import_accounts_payable(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
                
                elif detected_type == 'accounts_receivable':
                    imported_count = ImportService.import_accounts_receivable(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
                
                elif detected_type == 'financial_investments':
                    imported_count = ImportService.import_financial_investments(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
                
                elif detected_type == 'credit_card_invoices':
                    imported_count = ImportService.import_credit_card_invoices(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
                
                elif detected_type == 'card_machine_statements':
                    imported_count = ImportService.import_card_machine_statements(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
                
                elif detected_type == 'inventory':
                    imported_count = ImportService.import_inventory(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
            
            import_progress_container.empty()
            
            # Armazena resultado
            from datetime import datetime
            if detected_type == 'bank_statements' and imported_count > 0:
                transactions_created = import_result.get('transactions', 0)
                st.session_state.import_result = {
                    'status': 'success',
                    'import_type': detected_type,
                    'count': imported_count,
                    'transactions_created': transactions_created,
                    'message': f"{imported_count} extrato(s) importado(s) e {transactions_created} transação(ões) criada(s)!",
                    'timestamp': datetime.now().isoformat()
                }
                st.success(f"✅ {imported_count} extrato(s) importado(s) e {transactions_created} transação(ões) criada(s)!")
            elif imported_count > 0:
                st.session_state.import_result = {
                    'status': 'success',
                    'import_type': detected_type,
                    'count': imported_count,
                    'message': f"{imported_count} registro(s) importado(s) com sucesso!",
                    'timestamp': datetime.now().isoformat()
                }
                st.success(f"✅ {imported_count} registro(s) importado(s) com sucesso!")
                st.balloons()
            else:
                st.warning("⚠️ Nenhum registro foi importado. Verifique os dados.")
            
            # Limpa estado após importação
            if imported_count > 0:
                if 'processed_data' in st.session_state:
                    del st.session_state.processed_data
                if 'selected_rows' in st.session_state:
                    del st.session_state.selected_rows
                if 'processed_file_hash' in st.session_state:
                    del st.session_state.processed_file_hash
                if 'bank_name_override' in st.session_state:
                    del st.session_state.bank_name_override
                st.rerun()
            
        except Exception as e:
            st.error(f"❌ Erro ao importar: {str(e)}")
            st.exception(e)
        finally:
            db.close()

else:
    st.info("ℹ️ Faça upload de um arquivo para começar.")

# Informações sobre formatos
with st.expander("ℹ️ Informações sobre Formatos"):
    st.markdown("""
    ### Formatos Suportados
    
    **CSV, Excel, PDF, OFX, Imagens**
    - Todos os formatos são processados automaticamente usando IA Vision
    - O sistema detecta e extrai dados de qualquer tipo de arquivo
    - Não é necessário configurar encoding, delimitadores ou outras opções
    
    **Processamento Automático**
    - Upload → Processamento com IA → Edição → Importação
    - Detecção automática do tipo de dado
    - Classificação automática por grupos e subgrupos
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








