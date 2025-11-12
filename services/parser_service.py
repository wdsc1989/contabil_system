"""
Serviço de parsing de arquivos (CSV, Excel, PDF, OFX)
"""
import pandas as pd
import pdfplumber
from ofxparse import OfxParser
from typing import Dict, List, Optional, Any
from io import BytesIO, StringIO
import re


class ParserService:
    """
    Serviço para fazer parsing de diferentes formatos de arquivo
    """

    @staticmethod
    def parse_csv(file_content: bytes, encoding: str = 'utf-8', delimiter: str = ',') -> pd.DataFrame:
        """
        Faz parse de arquivo CSV
        """
        try:
            # Tenta diferentes encodings
            encodings = [encoding, 'utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            
            for enc in encodings:
                try:
                    df = pd.read_csv(BytesIO(file_content), encoding=enc, delimiter=delimiter)
                    return df
                except UnicodeDecodeError:
                    continue
            
            # Se nenhum encoding funcionou, tenta com errors='ignore'
            df = pd.read_csv(BytesIO(file_content), encoding='utf-8', delimiter=delimiter, errors='ignore')
            return df
        
        except Exception as e:
            raise Exception(f"Erro ao fazer parse do CSV: {str(e)}")

    @staticmethod
    def parse_excel(file_content: bytes, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Faz parse de arquivo Excel
        """
        try:
            if sheet_name:
                df = pd.read_excel(BytesIO(file_content), sheet_name=sheet_name)
            else:
                df = pd.read_excel(BytesIO(file_content))
            
            return df
        
        except Exception as e:
            raise Exception(f"Erro ao fazer parse do Excel: {str(e)}")

    @staticmethod
    def get_excel_sheets(file_content: bytes) -> List[str]:
        """
        Retorna lista de planilhas em um arquivo Excel
        """
        try:
            excel_file = pd.ExcelFile(BytesIO(file_content))
            return excel_file.sheet_names
        except Exception as e:
            raise Exception(f"Erro ao ler planilhas do Excel: {str(e)}")

    @staticmethod
    def parse_pdf(file_content: bytes) -> Dict[str, Any]:
        """
        Extrai texto de arquivo PDF
        """
        try:
            text_content = []
            tables = []
            
            with pdfplumber.open(BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    # Extrai texto
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                    
                    # Extrai tabelas
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
            
            return {
                'text': '\n\n'.join(text_content),
                'tables': tables,
                'num_pages': len(text_content)
            }
        
        except Exception as e:
            raise Exception(f"Erro ao fazer parse do PDF: {str(e)}")

    @staticmethod
    def parse_pdf_to_dataframe(file_content: bytes) -> Optional[pd.DataFrame]:
        """
        Tenta extrair tabela de PDF e converter para DataFrame
        """
        try:
            result = ParserService.parse_pdf(file_content)
            
            if result['tables']:
                # Pega a primeira tabela
                table = result['tables'][0]
                
                # Converte para DataFrame
                df = pd.DataFrame(table[1:], columns=table[0])
                return df
            
            return None
        
        except Exception as e:
            raise Exception(f"Erro ao extrair tabela do PDF: {str(e)}")

    @staticmethod
    def parse_ofx(file_content: bytes) -> Dict[str, Any]:
        """
        Faz parse de arquivo OFX (extratos bancários)
        """
        try:
            ofx = OfxParser.parse(BytesIO(file_content))
            
            transactions = []
            
            for account in ofx.accounts:
                for transaction in account.statement.transactions:
                    transactions.append({
                        'date': transaction.date,
                        'description': transaction.memo or transaction.payee or '',
                        'value': float(transaction.amount),
                        'type': transaction.type,
                        'id': transaction.id
                    })
            
            return {
                'bank_id': ofx.account.institution.fid if hasattr(ofx, 'account') else None,
                'account_id': ofx.account.account_id if hasattr(ofx, 'account') else None,
                'transactions': transactions,
                'balance': float(ofx.account.statement.balance) if hasattr(ofx, 'account') else None
            }
        
        except Exception as e:
            raise Exception(f"Erro ao fazer parse do OFX: {str(e)}")

    @staticmethod
    def ofx_to_dataframe(file_content: bytes) -> pd.DataFrame:
        """
        Converte OFX para DataFrame
        """
        try:
            result = ParserService.parse_ofx(file_content)
            df = pd.DataFrame(result['transactions'])
            return df
        
        except Exception as e:
            raise Exception(f"Erro ao converter OFX para DataFrame: {str(e)}")

    @staticmethod
    def detect_delimiter(file_content: bytes, sample_size: int = 1024) -> str:
        """
        Detecta o delimitador de um arquivo CSV
        """
        try:
            sample = file_content[:sample_size].decode('utf-8', errors='ignore')
            
            delimiters = [',', ';', '\t', '|']
            delimiter_counts = {}
            
            for delimiter in delimiters:
                count = sample.count(delimiter)
                delimiter_counts[delimiter] = count
            
            # Retorna o delimitador mais comum
            return max(delimiter_counts, key=delimiter_counts.get)
        
        except:
            return ','

    @staticmethod
    def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpa nomes de colunas (remove espaços, caracteres especiais)
        """
        df.columns = df.columns.str.strip()
        df.columns = df.columns.str.replace(r'[^\w\s]', '', regex=True)
        df.columns = df.columns.str.replace(r'\s+', '_', regex=True)
        return df

    @staticmethod
    def infer_column_types(df: pd.DataFrame) -> Dict[str, str]:
        """
        Infere tipos de colunas (data, moeda, texto, etc)
        """
        column_types = {}
        
        for col in df.columns:
            sample = df[col].dropna().head(10)
            
            if sample.empty:
                column_types[col] = 'text'
                continue
            
            # Tenta identificar datas
            date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
            if sample.astype(str).str.match(date_pattern).any():
                column_types[col] = 'date'
                continue
            
            # Tenta identificar valores monetários
            currency_pattern = r'R?\$?\s*-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?'
            if sample.astype(str).str.match(currency_pattern).any():
                column_types[col] = 'currency'
                continue
            
            # Tenta identificar números
            try:
                pd.to_numeric(sample)
                column_types[col] = 'numeric'
                continue
            except:
                pass
            
            # Default: texto
            column_types[col] = 'text'
        
        return column_types


