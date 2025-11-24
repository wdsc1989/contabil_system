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
st.markdown("**Processamento automático com IA Vision - Suporta CSV, Excel, PDF, OFX e Imagens**")
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
        st.info(f"📌 **Cliente:** {client.name}")
finally:
    db.close()

# Upload de arquivo
st.subheader("📤 Upload do Arquivo")

uploaded_file = st.file_uploader(
    "Selecione um arquivo para importar",
    type=['csv', 'txt', 'xlsx', 'xls', 'pdf', 'ofx', 'jpg', 'jpeg', 'png', 'tiff', 'tif', 'bmp', 'webp'],
    help="Formatos suportados: CSV, Excel, PDF, OFX, Imagens (JPG, PNG, etc). O sistema detecta e processa automaticamente."
)

if uploaded_file:
    file_size = len(uploaded_file.read())
    uploaded_file.seek(0)  # Reset para ler novamente depois
    file_size_kb = file_size / 1024
    st.success(f"✅ **{uploaded_file.name}** ({file_size_kb:.1f} KB)")
    
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
    
    file_content = uploaded_file.read()
    
    # Verifica se já foi processado
    file_hash = f"{uploaded_file.name}_{len(file_content)}"
    if 'processed_file_hash' not in st.session_state or st.session_state.processed_file_hash != file_hash:
        # Processa arquivo
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_status(message):
            status_text.info(f"🤖 {message}")
        
        with st.spinner("Processando com IA Vision..."):
            update_status("Analisando arquivo...")
            progress_bar.progress(20)
            db = SessionLocal()
            try:
                update_status("Extraindo dados com IA...")
                progress_bar.progress(50)
                
                processor = VisionProcessor(db)
                result = processor.process_file(
                    file_content=file_content,
                    filename=uploaded_file.name,
                    import_type=None,  # Detecta automaticamente
                    groups_subgroups=groups_subgroups if groups_subgroups else None
                )
                
                update_status("Classificando dados...")
                progress_bar.progress(80)
                
                if not result.get('success'):
                    progress_bar.empty()
                    status_text.empty()
                    error_msg = result.get('error', 'Erro desconhecido')
                    st.error(f"❌ **Erro no processamento:** {error_msg}")
                    
                    # Mensagens de ajuda específicas
                    if 'pdf' in error_msg.lower() and ('poppler' in error_msg.lower() or 'pdf2image' in error_msg.lower()):
                        st.warning("📦 **Dependência faltando:** É necessária uma biblioteca para processar PDFs.")
                        st.info("💡 **Solução:** Execute no terminal: `pip install PyMuPDF`")
                    elif 'matplotlib' in error_msg.lower():
                        st.warning("📦 **Dependência faltando:** Execute: `pip install matplotlib`")
                    
                    if result.get('issues'):
                        with st.expander("⚠️ Detalhes dos problemas"):
                            for issue in result.get('issues', []):
                                st.warning(f"⚠️ {issue}")
                    st.stop()
                
                update_status("Finalizando...")
                progress_bar.progress(100)
                
                # Salva resultado no session state
                st.session_state.processed_data = result.get('processed_data', [])
                st.session_state.processed_summary = result.get('summary', {})
                st.session_state.detected_type = result.get('detected_type', 'transactions')
                st.session_state.processed_file_hash = file_hash
                
                progress_bar.empty()
                status_text.empty()
                
            finally:
                db.close()
    
    # Dados processados
    processed_data = st.session_state.get('processed_data', [])
    summary = st.session_state.get('processed_summary', {})
    detected_type = st.session_state.get('detected_type', 'transactions')
    
    if not processed_data:
        st.warning("⚠️ Nenhum dado foi extraído do arquivo.")
        st.stop()
    
    # Exibe estatísticas de forma mais limpa
    st.markdown("---")
    st.subheader("✅ Dados Processados")
    
    type_names = {
        'transactions': '💳 Transações Financeiras',
        'bank_statements': '🏦 Extratos Bancários',
        'contracts': '📝 Contratos/Eventos',
        'accounts_payable': '💸 Contas a Pagar',
        'accounts_receivable': '💰 Contas a Receber',
        'financial_investments': '📈 Investimentos Financeiros',
        'credit_card_invoices': '💳 Faturas de Cartão',
        'card_machine_statements': '🏪 Extratos de Máquina de Cartão',
        'inventory': '📦 Controle de Estoque'
    }
    
    # Normaliza dados
    processed_data = [_ensure_classification_confidence(dict(record)) for record in processed_data]
    
    # Inicializa seleção
    if 'selected_rows' not in st.session_state:
        st.session_state.selected_rows = set(range(len(processed_data)))
    
    # Calcula valor total apenas dos registros selecionados
    selected_data = [processed_data[i] for i in st.session_state.selected_rows if 0 <= i < len(processed_data)]
    total_value_selected = sum(float(r.get('value', 0)) for r in selected_data if r.get('value') and pd.notna(r.get('value')))
    
    # Métricas em cards mais limpos
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Registros", f"{len(processed_data):,}".replace(',', '.'))
    with col2:
        type_display = type_names.get(detected_type, detected_type)
        type_short = type_display.split(' ')[-1] if ' ' in type_display else type_display
        st.metric("📋 Tipo", type_short)
    with col3:
        if 'bank_name' in summary and summary.get('bank_name'):
            st.metric("🏦 Banco", summary.get('bank_name', '-'))
        else:
            st.metric("✓ Status", "Pronto")
    with col4:
        if total_value_selected != 0:
            from utils.formatters import format_currency
            st.metric("💰 Valor Total (Selecionados)", format_currency(total_value_selected))
        else:
            st.metric("✓ Classificado", "Sim")
    
    st.markdown("---")
    st.subheader("✏️ Revisão e Edição")
    
    # Controles de seleção simplificados
    col1, col2, col3 = st.columns([2, 2, 3])
    
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
        st.info(f"📌 **{total_selected} de {len(processed_data)}** registros selecionados para importação")
    
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
    
    # Dica de uso
    if len(edit_df) > 10:
        st.caption(f"💡 **{len(edit_df)} registros encontrados.** Edite os dados diretamente na tabela e use as checkboxes para selecionar quais importar.")
    else:
        st.caption("💡 Edite os dados diretamente na tabela e selecione quais registros importar.")
    
    # Exibe tabela editável
    edited_df = st.data_editor(
        edit_df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        height=min(600, max(400, len(edit_df) * 40)),
        key="data_editor_import"
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
    
    # Recalcula valor total dos selecionados após edição e mostra atualização
    if new_selection != st.session_state.get('last_selection', set()):
        selected_data_updated = [updated_data[i] for i in new_selection if 0 <= i < len(updated_data)]
        total_value_selected_updated = sum(float(r.get('value', 0)) for r in selected_data_updated if r.get('value') and pd.notna(r.get('value')))
        if total_value_selected_updated != 0:
            from utils.formatters import format_currency
            st.info(f"💰 **Valor total atualizado:** {format_currency(total_value_selected_updated)} ({len(new_selection)} registro(s) selecionado(s))")
        st.session_state.last_selection = new_selection
    
    st.markdown("---")
    st.subheader("📥 Importação")
    
    # Configurações específicas por tipo (apenas se necessário)
    bank_name = "Banco"
    if detected_type == 'bank_statements':
        bank_name = summary.get('bank_name', 'Banco')
        if 'bank_name_override' not in st.session_state:
            st.session_state.bank_name_override = bank_name
        
        bank_name = st.text_input(
            "Nome do banco:",
            value=st.session_state.get('bank_name_override', bank_name),
            key="bank_name_input"
        )
        st.session_state.bank_name_override = bank_name
    
    # Botão de importar (mais destacado)
    col1, col2 = st.columns([1, 2])
    with col1:
        import_btn = st.button(
            "📥 **Importar Dados**",
            use_container_width=True,
            disabled=len(st.session_state.selected_rows) == 0,
            type="primary"
        )
    with col2:
        if len(st.session_state.selected_rows) == 0:
            st.warning("⚠️ Selecione pelo menos um registro para importar")
    
    if import_btn and len(st.session_state.selected_rows) > 0:
        # Filtra apenas linhas selecionadas
        selected_indices = sorted(list(st.session_state.selected_rows))
        data_to_import = [st.session_state.processed_data[i] for i in selected_indices if 0 <= i < len(st.session_state.processed_data)]
        import_df = pd.DataFrame(data_to_import)
        
        # Valida se há dados para importar
        if import_df.empty:
            st.error("❌ **Nenhum dado válido para importar.** Verifique se os registros selecionados contêm dados válidos.")
            st.stop()
        
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
                st.error("❌ **Nenhum registro foi importado.**")
                st.info("""
                **Possíveis causas:**
                - Nenhum registro foi selecionado para importação
                - Os dados não atendem aos requisitos do tipo de importação
                - Erro na validação dos dados (datas, valores, grupos/subgrupos)
                - Dados duplicados que foram ignorados
                
                **Soluções:**
                - Verifique se há registros selecionados (checkboxes marcadas)
                - Revise os dados na tabela e corrija campos obrigatórios
                - Verifique se os grupos/subgrupos estão corretos
                - Tente importar novamente após fazer as correções
                """)
            
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
    st.info("💡 **Como funciona:** Faça upload do arquivo e o sistema processará automaticamente com IA Vision, detectando o tipo de dado e classificando por grupos/subgrupos.")
    
    st.markdown("---")
    with st.expander("ℹ️ Sobre o Processamento Automático"):
        st.markdown("""
        **Formatos Suportados:**
        - 📄 CSV, Excel, TXT
        - 📑 PDF (incluindo PDFs escaneados/imagens)
        - 🖼️ Imagens (JPG, PNG, TIFF, etc)
        - 💳 OFX (extratos bancários)
        
        **O que a IA faz automaticamente:**
        - ✅ Detecta o tipo de dado (transações, extratos, contratos, etc)
        - ✅ Extrai todos os dados estruturados
        - ✅ Classifica por grupos e subgrupos
        - ✅ Normaliza datas e valores
        - ✅ Identifica tipo de transação (entrada/saída)
        
        **Você só precisa:**
        1. Fazer upload do arquivo
        2. Revisar e editar se necessário
        3. Importar!
        """)








