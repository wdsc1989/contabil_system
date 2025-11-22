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
        
        prompt = f"""Você é um especialista em extração de dados financeiros. Analise este arquivo e extraia todos os dados estruturados.

Tipo de arquivo detectado: {file_type}
"""
        
        if import_type:
            prompt += f"Tipo de dado esperado: {import_type}\n"
        else:
            prompt += "Detecte automaticamente o tipo de dado (transactions, bank_statements, contracts, accounts_payable, accounts_receivable, financial_investments, credit_card_invoices, card_machine_statements, inventory).\n"
        
        if groups_info:
            prompt += f"\nGrupos e Subgrupos disponíveis para classificação:\n{groups_info}\n"
        
        prompt += """
INSTRUÇÕES:
1. Extraia TODOS os dados estruturados do arquivo
2. Identifique o tipo de dado automaticamente se não foi especificado
3. Para cada registro, classifique com group_id e subgroup_id apropriados baseado no contexto
4. Normalize datas para formato YYYY-MM-DD
5. Normalize valores monetários para números (sem símbolos de moeda)
6. Extraia informações adicionais relevantes (nome do banco, conta, etc.)

FORMATO DE RESPOSTA (JSON válido):
{
    "detected_type": "bank_statements",
    "records": [
        {
            "date": "2024-01-15",
            "description": "Descrição da transação",
            "value": 1000.00,
            "type": "entrada" ou "saida",
            "group_id": 1,
            "subgroup_id": 2,
            "bank_name": "Banco do Brasil" (se aplicável),
            "account": "12345-6" (se aplicável),
            "balance": 5000.00 (se aplicável),
            ... (outros campos relevantes)
        }
    ],
    "summary": {
        "total_records": 50,
        "bank_name": "Banco do Brasil" (se detectado),
        "account_info": "12345-6" (se detectado),
        "date_range": {
            "start": "2024-01-01",
            "end": "2024-01-31"
        }
    }
}

IMPORTANTE:
- Retorne APENAS JSON válido, sem texto adicional antes ou depois
- Se houver muitos registros, extraia TODOS (não limite)
- Seja preciso na classificação de grupos/subgrupos
- Mantenha todas as informações relevantes
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
                
                return {
                    'success': True,
                    'processed_data': json_data.get('records', []),
                    'summary': json_data.get('summary', {}),
                    'detected_type': json_data.get('detected_type', import_type),
                    'issues': []
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
                
                return {
                    'success': True,
                    'processed_data': all_records,
                    'summary': combined_summary,
                    'detected_type': detected_type or import_type,
                    'issues': []
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
                
                return {
                    'success': True,
                    'processed_data': json_data.get('records', []),
                    'summary': json_data.get('summary', {}),
                    'detected_type': json_data.get('detected_type', import_type),
                    'issues': []
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

