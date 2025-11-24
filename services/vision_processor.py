"""
Processador de arquivos usando GPT-4o Vision API
Processa todos os tipos de arquivo (CSV, Excel, PDF, Imagens) diretamente via Vision API
"""
import base64
import io
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
import json
import pandas as pd
from PIL import Image
from datetime import datetime

from config.ai_config import AIConfigManager


class VisionProcessor:
    """
    Processador de arquivos usando Vision API
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o processador com configuração do banco
        """
        self.db = db
        self.config = AIConfigManager.get_config_dict(db)
        self._client = None
    
    def _get_client(self):
        """
        Obtém cliente OpenAI para Vision API
        """
        if not self.config:
            return None, "Configuração de IA não encontrada"
        
        if self._client is not None:
            return self._client, None
        
        provider = self.config['provider']
        api_key = self.config.get('api_key', '').strip()
        model = self.config.get('model', 'gpt-4o')
        
        # Verifica se suporta Vision API
        if not AIConfigManager.supports_vision(provider, model):
            return None, f"Modelo {model} do provedor {provider} não suporta Vision API"
        
        if provider != 'openai':
            return None, f"Vision API atualmente suporta apenas OpenAI. Provedor configurado: {provider}"
        
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key)
            return self._client, None
        except ImportError:
            return None, "Biblioteca 'openai' não instalada. Execute: pip install openai"
        except Exception as e:
            return None, f"Erro ao inicializar cliente OpenAI: {str(e)}"
    
    def _pdf_to_images(self, pdf_bytes: bytes) -> List[bytes]:
        """
        Converte PDF para lista de imagens (uma por página)
        Tenta PyMuPDF primeiro, depois pdf2image como fallback
        """
        # Tenta PyMuPDF primeiro (funciona melhor no Linux, não precisa de poppler)
        try:
            import fitz  # PyMuPDF
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            image_bytes_list = []
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                # Renderiza página como imagem (zoom=2.0 = 200 DPI)
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                # Converte para bytes PNG
                img_bytes = pix.tobytes("png")
                image_bytes_list.append(img_bytes)
            
            pdf_document.close()
            return image_bytes_list
        except ImportError:
            # PyMuPDF não instalado, tenta pdf2image
            pass
        except Exception as e:
            error_msg = str(e).lower()
            import platform
            
            # Detecta erro de DLL (comum no Windows/Python 3.13)
            if "dll" in error_msg or ("module" in error_msg and platform.system() == "Windows"):
                # Tenta pdf2image como fallback
                try:
                    from pdf2image import convert_from_bytes
                    images = convert_from_bytes(pdf_bytes, dpi=200)
                    image_bytes_list = []
                    for img in images:
                        buf = io.BytesIO()
                        img.save(buf, format='PNG')
                        buf.seek(0)
                        image_bytes_list.append(buf.read())
                    return image_bytes_list
                except ImportError:
                    raise Exception(
                        f"PyMuPDF não está funcionando (erro de DLL) e pdf2image não está instalado.\n"
                        f"Erro PyMuPDF: {str(e)}\n\n"
                        "Soluções:\n"
                        "1. Use Python 3.11 ou 3.12 (PyMuPDF funciona melhor)\n"
                        "2. Ou instale pdf2image: pip install pdf2image\n"
                        "   (Em Linux: sudo apt-get install poppler-utils)"
                    )
                except Exception as pdf2img_error:
                    if "poppler" in str(pdf2img_error).lower():
                        raise Exception(
                            f"PyMuPDF não está funcionando e pdf2image precisa de poppler.\n"
                            f"Erro PyMuPDF: {str(e)}\n"
                            f"Erro pdf2image: {str(pdf2img_error)}\n\n"
                            "Soluções:\n"
                            "1. Use Python 3.11 ou 3.12 (PyMuPDF funciona melhor)\n"
                            "2. Ou instale poppler:\n"
                            "   - Linux: sudo apt-get install poppler-utils\n"
                            "   - Windows: Baixe de https://github.com/oschwartz10612/poppler-windows/releases"
                        )
                    raise Exception(f"Erro ao converter PDF: {str(e)} (PyMuPDF) e {str(pdf2img_error)} (pdf2image)")
            # Outros erros do PyMuPDF, tenta pdf2image como fallback
            try:
                from pdf2image import convert_from_bytes
                images = convert_from_bytes(pdf_bytes, dpi=200)
                image_bytes_list = []
                for img in images:
                    buf = io.BytesIO()
                    img.save(buf, format='PNG')
                    buf.seek(0)
                    image_bytes_list.append(buf.read())
                return image_bytes_list
            except:
                raise Exception(f"Erro ao converter PDF para imagens: {str(e)}")
        
        # Se PyMuPDF não foi instalado, tenta pdf2image
        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(pdf_bytes, dpi=200)
            image_bytes_list = []
            for img in images:
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                buf.seek(0)
                image_bytes_list.append(buf.read())
            return image_bytes_list
        except ImportError:
            raise Exception(
                "Nenhuma biblioteca de PDF disponível.\n"
                "Instale uma das opções:\n"
                "- pip install PyMuPDF (recomendado, funciona no Linux sem poppler)\n"
                "- pip install pdf2image (requer poppler instalado no sistema)"
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "poppler" in error_msg:
                raise Exception(
                    f"pdf2image precisa de poppler instalado.\n"
                    f"Erro: {str(e)}\n\n"
                    "Instale poppler:\n"
                    "- Linux: sudo apt-get install poppler-utils\n"
                    "- Windows: Baixe de https://github.com/oschwartz10612/poppler-windows/releases\n\n"
                    "Ou use PyMuPDF (não precisa de poppler): pip install PyMuPDF"
                )
            raise Exception(f"Erro ao converter PDF para imagens: {str(e)}")
    
    def _prepare_file_for_vision(self, file_content: bytes, filename: str) -> Tuple[Optional[str], List[Dict], str]:
        """
        Prepara arquivo para processamento via Vision API
        Retorna (texto_do_arquivo, lista_de_imagens_base64, tipo_de_arquivo)
        - Se o arquivo for texto (CSV/Excel), retorna o texto e None para imagens
        - Se o arquivo for imagem/PDF, retorna None para texto e lista de imagens
        """
        filename_lower = filename.lower()
        
        # CSV/Excel/TXT: lê como texto e envia diretamente (mais direto, como ChatGPT)
        if filename_lower.endswith(('.csv', '.txt')):
            try:
                # Tenta diferentes encodings
                for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        text_content = file_content.decode(encoding)
                        return text_content, [], 'text'
                    except UnicodeDecodeError:
                        continue
                raise Exception("Não foi possível decodificar o arquivo com nenhum encoding conhecido")
            except Exception as e:
                raise Exception(f"Erro ao ler arquivo CSV/TXT: {str(e)}")
        
        elif filename_lower.endswith(('.xlsx', '.xls')):
            try:
                # Lê Excel e converte para texto estruturado (CSV-like)
                df = pd.read_excel(io.BytesIO(file_content))
                # Converte para string CSV
                csv_string = df.to_csv(index=False)
                return csv_string, [], 'spreadsheet'
            except Exception as e:
                raise Exception(f"Erro ao ler arquivo Excel: {str(e)}")
        
        # Imagens: envia diretamente como imagem
        elif filename_lower.endswith(('.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp')):
            image_base64 = base64.b64encode(file_content).decode('utf-8')
            mime_type = 'image/jpeg' if filename_lower.endswith(('.jpg', '.jpeg')) else 'image/png'
            return None, [{'type': 'image_url', 'image_url': {'url': f'data:{mime_type};base64,{image_base64}'}}], 'image'
        
        # PDFs: SEMPRE converte para imagens (Vision API não aceita PDFs diretamente)
        elif filename_lower.endswith('.pdf'):
            # A Vision API só aceita imagens, então sempre convertemos PDF para imagens
            try:
                images = self._pdf_to_images(file_content)
                image_list = []
                for img_bytes in images:
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    image_list.append({
                        'type': 'image_url',
                        'image_url': {'url': f'data:image/png;base64,{img_base64}'}
                    })
                return None, image_list, 'pdf'
            except Exception as e:
                # Erro já tem mensagem clara do _pdf_to_images
                raise Exception(f"Erro ao processar PDF: {str(e)}")
        
        # Outros: tenta abrir como imagem
        else:
            try:
                img = Image.open(io.BytesIO(file_content))
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                buf.seek(0)
                image_bytes = buf.read()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                return None, [{'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{image_base64}'}}], 'image'
            except:
                raise Exception(f"Tipo de arquivo não suportado: {filename}")
    
    def _build_prompt(self, file_type: str, groups_subgroups: Optional[List[Dict]] = None, import_type: Optional[str] = None) -> str:
        """
        Constrói prompt para Vision API
        """
        groups_info = ""
        if groups_subgroups:
            groups_list = []
            for group in groups_subgroups:
                group_name = group.get('name', '')
                subgroups = group.get('subgroups', [])
                subgroup_names = [sg.get('name', '') for sg in subgroups]
                groups_list.append(f"- {group_name} (ID: {group.get('id')}): {', '.join(subgroup_names) if subgroup_names else 'sem subgrupos'}")
            groups_info = "\n".join(groups_list)
        
        # Define regras claras para cada tipo de dado
        type_rules = {
            "transactions": "Transações financeiras gerais (entradas e saídas de dinheiro). Campos obrigatórios: date, description, value, type (entrada/saida).",
            "bank_statements": "Extratos bancários com movimentações de conta. Campos obrigatórios: date, description, value, balance. Deve incluir bank_name e account se disponíveis.",
            "contracts": "Contratos e eventos (festas, casamentos, etc.). Campos obrigatórios: contract_start, event_date, service_value, contractor_name.",
            "accounts_payable": "Contas a pagar. Campos obrigatórios: account_name, due_date, value. Pode incluir cpf_cnpj, monthly_installments.",
            "accounts_receivable": "Contas a receber. Campos obrigatórios: account_name, due_date, value. Pode incluir cpf_cnpj, contract_value.",
            "financial_investments": "Investimentos financeiros. Campos obrigatórios: date. Pode incluir applied_value, redeemed_value, yield_value, balance.",
            "credit_card_invoices": "Faturas de cartão de crédito. Campos obrigatórios: transaction_date, value, description.",
            "card_machine_statements": "Extratos de máquina de cartão. Campos obrigatórios: date, value, description.",
            "inventory": "Controle de estoque. Campos obrigatórios: product_name, quantity, value."
        }
        
        prompt = f"""Você é um especialista em extração e classificação de dados financeiros. Sua tarefa é analisar este arquivo e extrair TODOS os dados estruturados com classificação precisa.

Tipo de arquivo: {file_type}
"""
        
        if import_type:
            prompt += f"""
TIPO DE DADO ESPERADO: {import_type}
{type_rules.get(import_type, '')}

Você DEVE classificar todos os registros como {import_type} e usar os campos apropriados para este tipo.
"""
        else:
            prompt += """
DETECÇÃO AUTOMÁTICA DO TIPO DE DADO:
Analise cuidadosamente o conteúdo e identifique o tipo de dado. Escolha APENAS UM dos seguintes tipos:

"""
            for dtype, rule in type_rules.items():
                prompt += f"- {dtype}: {rule}\n"
            
            prompt += """
IMPORTANTE: Você DEVE escolher o tipo mais apropriado baseado no conteúdo real do arquivo.
"""
        
        if groups_info:
            prompt += f"""
CLASSIFICAÇÃO OBRIGATÓRIA DE GRUPOS E SUBGRUPOS:
Você DEVE classificar CADA registro com group_id e subgroup_id apropriados baseado na descrição e contexto.

Grupos e Subgrupos disponíveis:
{groups_info}

REGRAS DE CLASSIFICAÇÃO:
1. Analise a descrição de cada transação/registro
2. Identifique a natureza financeira (receita, despesa, investimento, etc.)
3. Escolha o grupo mais apropriado baseado no contexto
4. Escolha o subgrupo mais específico dentro do grupo selecionado
5. Se nenhum grupo/subgrupo se encaixar perfeitamente, escolha o mais próximo possível
6. NUNCA deixe group_id ou subgroup_id como null - SEMPRE atribua valores válidos

EXEMPLOS DE CLASSIFICAÇÃO:
- "Pagamento de fornecedor" → grupo de Despesas → subgrupo de Fornecedores
- "Recebimento de cliente" → grupo de Receitas → subgrupo de Vendas
- "Taxa bancária" → grupo de Despesas → subgrupo de Taxas/Bancárias
- "Investimento em aplicação" → grupo de Investimentos → subgrupo apropriado
"""
        else:
            prompt += """
ATENÇÃO: Nenhum grupo/subgrupo foi fornecido. Use group_id e subgroup_id como null, mas tente inferir quando possível.
"""
        
        prompt += """
INSTRUÇÕES DETALHADAS:
1. Extraia TODOS os registros do arquivo - não pule nenhum
2. Para cada registro:
   a. Identifique e extraia todos os campos relevantes
   b. Normalize datas para formato YYYY-MM-DD (obrigatório)
   c. Normalize valores monetários para números decimais (ex: 1234.56, não "R$ 1.234,56")
   d. Determine se é entrada (valor positivo) ou saída (valor negativo) para o campo "type"
   e. Classifique com group_id e subgroup_id apropriados (OBRIGATÓRIO se grupos foram fornecidos)
   f. Extraia informações adicionais (banco, conta, CPF/CNPJ, etc.) quando disponíveis

3. Validação obrigatória:
   - Todas as datas devem estar no formato YYYY-MM-DD
   - Todos os valores devem ser números (float)
   - Todos os registros devem ter group_id e subgroup_id (se grupos foram fornecidos)
   - Campos obrigatórios não podem estar vazios ou null

FORMATO DE RESPOSTA (JSON válido e completo):
{
    "detected_type": "bank_statements",
    "records": [
        {
            "date": "2024-01-15",
            "description": "Descrição completa da transação",
            "value": 1000.00,
            "type": "entrada",
            "group_id": 1,
            "subgroup_id": 2,
            "bank_name": "Banco do Brasil",
            "account": "12345-6",
            "balance": 5000.00
        }
    ],
    "summary": {
        "total_records": 50,
        "bank_name": "Banco do Brasil",
        "account_info": "12345-6",
        "date_range": {
            "start": "2024-01-01",
            "end": "2024-01-31"
        }
    }
}

REGRAS CRÍTICAS:
1. Retorne APENAS JSON válido - sem texto adicional, sem markdown, sem explicações
2. Extraia TODOS os registros - não limite a quantidade
3. Classifique CADA registro com group_id e subgroup_id (obrigatório se grupos foram fornecidos)
4. Seja preciso e consistente na classificação
5. Mantenha todas as informações relevantes de cada registro
6. Valide que todos os campos obrigatórios estão presentes
7. Use valores numéricos reais (não strings) para valores monetários
"""
        
        return prompt
    
    def process_file(
        self,
        file_content: bytes,
        filename: str,
        import_type: Optional[str] = None,
        groups_subgroups: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Processa arquivo usando Vision API
        
        Args:
            file_content: Conteúdo do arquivo em bytes
            filename: Nome do arquivo
            import_type: Tipo de importação esperado (opcional, será detectado automaticamente)
            groups_subgroups: Lista de grupos e subgrupos para classificação
            
        Returns:
            {
                'success': bool,
                'processed_data': List[Dict],
                'summary': Dict,
                'detected_type': str,
                'issues': List[str]
            }
        """
        # Verifica se Vision API está disponível
        client, error = self._get_client()
        if not client:
            return {
                'success': False,
                'error': error,
                'processed_data': [],
                'summary': {},
                'detected_type': None,
                'issues': [error]
            }
        
        try:
            # Prepara arquivo para Vision API
            file_text, images, file_type = self._prepare_file_for_vision(file_content, filename)
            
            # Constrói prompt
            prompt = self._build_prompt(file_type, groups_subgroups, import_type)
            
            # Se temos texto (CSV/Excel), envia como texto na mensagem (mais direto)
            if file_text:
                messages = [
                    {
                        'role': 'user',
                        'content': [
                            {'type': 'text', 'text': f"{prompt}\n\nConteúdo do arquivo:\n{file_text}"}
                        ]
                    }
                ]
                
                response = client.chat.completions.create(
                    model=self.config.get('model', 'gpt-4o'),
                    messages=messages,
                    max_tokens=8000,  # Mais tokens para arquivos grandes
                    temperature=0.1
                )
                
                content = response.choices[0].message.content
                json_data = self._extract_json_from_response(content)
                
                if not json_data:
                    return {
                        'success': False,
                        'error': 'Não foi possível extrair dados estruturados da resposta da IA',
                        'processed_data': [],
                        'summary': {},
                        'detected_type': import_type,
                        'issues': ['Resposta da IA não contém JSON válido']
                    }
                
                # Valida e corrige dados
                records = json_data.get('records', [])
                issues = []
                validated_records = self._validate_and_fix_records(records, groups_subgroups, issues)
                
                return {
                    'success': True,
                    'processed_data': validated_records,
                    'summary': json_data.get('summary', {}),
                    'detected_type': json_data.get('detected_type', import_type),
                    'issues': issues
                }
            
            # Para imagens/PDFs: usa Vision API
            # Verifica se temos imagens para processar
            if not images or len(images) == 0:
                return {
                    'success': False,
                    'error': 'Nenhuma imagem ou conteúdo de texto encontrado para processar',
                    'processed_data': [],
                    'summary': {},
                    'detected_type': import_type,
                    'issues': ['Arquivo não pôde ser preparado para processamento']
                }
            
            # Para múltiplas imagens (PDF), processa página por página ou envia todas
            if len(images) > 1:
                # Para PDFs com múltiplas páginas, processa cada página e combina resultados
                all_records = []
                all_summaries = []
                detected_type = None
                
                for i, image in enumerate(images):
                    page_prompt = f"{prompt}\n\nEsta é a página {i+1} de {len(images)} do documento. Extraia os dados desta página."
                    
                    response = client.chat.completions.create(
                        model=self.config.get('model', 'gpt-4o'),
                        messages=[
                            {
                                'role': 'user',
                                'content': [
                                    {'type': 'text', 'text': page_prompt},
                                    image
                                ]
                            }
                        ],
                        max_tokens=4000,
                        temperature=0.1
                    )
                    
                    content = response.choices[0].message.content
                    
                    # Extrai JSON da resposta
                    json_data = self._extract_json_from_response(content)
                    if json_data:
                        if 'records' in json_data:
                            all_records.extend(json_data['records'])
                        if 'summary' in json_data:
                            all_summaries.append(json_data['summary'])
                        if not detected_type and 'detected_type' in json_data:
                            detected_type = json_data['detected_type']
                
                # Combina summaries
                combined_summary = self._combine_summaries(all_summaries)
                combined_summary['total_records'] = len(all_records)
                
                # Valida e corrige dados
                issues = []
                validated_records = self._validate_and_fix_records(all_records, groups_subgroups, issues)
                
                return {
                    'success': True,
                    'processed_data': validated_records,
                    'summary': combined_summary,
                    'detected_type': detected_type or import_type,
                    'issues': issues
                }
            else:
                # Arquivo único (imagem, CSV, Excel)
                response = client.chat.completions.create(
                    model=self.config.get('model', 'gpt-4o'),
                    messages=[
                        {
                            'role': 'user',
                            'content': [
                                {'type': 'text', 'text': prompt},
                                images[0]
                            ]
                        }
                    ],
                    max_tokens=4000,
                    temperature=0.1
                )
                
                content = response.choices[0].message.content
                
                # Extrai JSON da resposta
                json_data = self._extract_json_from_response(content)
                
                if not json_data:
                    return {
                        'success': False,
                        'error': 'Não foi possível extrair dados estruturados da resposta da IA',
                        'processed_data': [],
                        'summary': {},
                        'detected_type': None,
                        'issues': ['Resposta da IA não contém JSON válido']
                    }
                
                # Valida e corrige dados
                records = json_data.get('records', [])
                issues = []
                validated_records = self._validate_and_fix_records(records, groups_subgroups, issues)
                
                return {
                    'success': True,
                    'processed_data': validated_records,
                    'summary': json_data.get('summary', {}),
                    'detected_type': json_data.get('detected_type', import_type),
                    'issues': issues
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processed_data': [],
                'summary': {},
                'detected_type': None,
                'issues': [str(e)]
            }
    
    def _extract_json_from_response(self, content: str) -> Optional[Dict]:
        """
        Extrai JSON da resposta da IA
        """
        # Tenta encontrar JSON no conteúdo
        # Procura por { ... } ou [ ... ]
        import re
        
        # Remove markdown code blocks se existirem
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        content = content.strip()
        
        # Procura por JSON válido
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Tenta parse direto
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _validate_and_fix_records(self, records: List[Dict], groups_subgroups: Optional[List[Dict]] = None, issues: List[str] = None) -> List[Dict]:
        """
        Valida e corrige registros retornados pela IA
        """
        if issues is None:
            issues = []
        
        validated = []
        missing_group_count = 0
        missing_subgroup_count = 0
        invalid_date_count = 0
        invalid_value_count = 0
        
        # Cria mapeamento de IDs válidos se grupos foram fornecidos
        valid_group_ids = set()
        valid_subgroup_ids = {}
        if groups_subgroups:
            for group in groups_subgroups:
                group_id = group.get('id')
                if group_id:
                    valid_group_ids.add(group_id)
                    subgroups = group.get('subgroups', [])
                    for sg in subgroups:
                        sg_id = sg.get('id')
                        if sg_id:
                            if group_id not in valid_subgroup_ids:
                                valid_subgroup_ids[group_id] = set()
                            valid_subgroup_ids[group_id].add(sg_id)
        
        for idx, record in enumerate(records):
            try:
                # Valida e corrige data
                if 'date' in record:
                    date_val = record['date']
                    if isinstance(date_val, str):
                        # Tenta parsear data
                        try:
                            # Tenta vários formatos
                            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']:
                                try:
                                    dt = datetime.strptime(date_val.strip(), fmt)
                                    record['date'] = dt.strftime('%Y-%m-%d')
                                    break
                                except:
                                    continue
                            else:
                                invalid_date_count += 1
                        except:
                            invalid_date_count += 1
                    elif isinstance(date_val, (datetime, pd.Timestamp)):
                        record['date'] = date_val.strftime('%Y-%m-%d')
                
                # Valida e corrige valor
                if 'value' in record:
                    value_val = record['value']
                    if isinstance(value_val, str):
                        # Tenta converter string para float
                        try:
                            # Remove símbolos de moeda
                            clean_val = value_val.replace('R$', '').replace('$', '').strip()
                            # Trata formato brasileiro
                            if ',' in clean_val and '.' in clean_val:
                                if clean_val.rindex(',') > clean_val.rindex('.'):
                                    clean_val = clean_val.replace('.', '').replace(',', '.')
                                else:
                                    clean_val = clean_val.replace(',', '')
                            elif ',' in clean_val:
                                clean_val = clean_val.replace(',', '.')
                            record['value'] = float(clean_val)
                        except:
                            invalid_value_count += 1
                    elif not isinstance(value_val, (int, float)):
                        try:
                            record['value'] = float(value_val)
                        except:
                            invalid_value_count += 1
                
                # Valida group_id e subgroup_id
                if groups_subgroups and valid_group_ids:
                    group_id = record.get('group_id')
                    subgroup_id = record.get('subgroup_id')
                    
                    # Se group_id não está presente ou é inválido
                    if not group_id or group_id not in valid_group_ids:
                        missing_group_count += 1
                        # Tenta usar o primeiro grupo disponível como fallback
                        if valid_group_ids:
                            record['group_id'] = list(valid_group_ids)[0]
                            # Se tinha subgroup_id, remove pois pode não pertencer ao novo grupo
                            if 'subgroup_id' in record:
                                record['subgroup_id'] = None
                    
                    # Se subgroup_id não está presente ou é inválido para o group_id
                    if group_id and group_id in valid_group_ids:
                        if not subgroup_id or group_id not in valid_subgroup_ids or subgroup_id not in valid_subgroup_ids.get(group_id, set()):
                            missing_subgroup_count += 1
                            # Remove subgroup_id inválido (será None)
                            record['subgroup_id'] = None
                
                # Garante que type está correto
                if 'value' in record and 'type' not in record:
                    value = record.get('value', 0)
                    if isinstance(value, (int, float)):
                        record['type'] = 'entrada' if value >= 0 else 'saida'
                
                validated.append(record)
                
            except Exception as e:
                issues.append(f"Erro ao validar registro {idx + 1}: {str(e)}")
                continue
        
        # Adiciona avisos aos issues
        if missing_group_count > 0:
            issues.append(f"{missing_group_count} registro(s) sem group_id válido - foram atribuídos ao primeiro grupo disponível")
        if missing_subgroup_count > 0:
            issues.append(f"{missing_subgroup_count} registro(s) sem subgroup_id válido - foram deixados como None")
        if invalid_date_count > 0:
            issues.append(f"{invalid_date_count} registro(s) com data inválida")
        if invalid_value_count > 0:
            issues.append(f"{invalid_value_count} registro(s) com valor inválido")
        
        return validated
    
    def _combine_summaries(self, summaries: List[Dict]) -> Dict:
        """
        Combina múltiplos summaries em um único
        """
        if not summaries:
            return {}
        
        combined = {}
        
        # Combina informações
        bank_names = set()
        account_infos = set()
        date_ranges = []
        
        for summary in summaries:
            if 'bank_name' in summary and summary['bank_name']:
                bank_names.add(summary['bank_name'])
            if 'account_info' in summary and summary['account_info']:
                account_infos.add(summary['account_info'])
            if 'date_range' in summary:
                date_ranges.append(summary['date_range'])
        
        if bank_names:
            combined['bank_name'] = list(bank_names)[0] if len(bank_names) == 1 else ', '.join(bank_names)
        if account_infos:
            combined['account_info'] = list(account_infos)[0] if len(account_infos) == 1 else ', '.join(account_infos)
        
        # Combina ranges de data
        if date_ranges:
            all_dates = []
            for dr in date_ranges:
                if 'start' in dr:
                    all_dates.append(dr['start'])
                if 'end' in dr:
                    all_dates.append(dr['end'])
            
            if all_dates:
                combined['date_range'] = {
                    'start': min(all_dates),
                    'end': max(all_dates)
                }
        
        return combined

