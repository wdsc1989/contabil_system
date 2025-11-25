"""
Validadores de dados
"""
import re
from datetime import datetime
from typing import Optional


def validate_cpf(cpf: str) -> bool:
    """
    Valida CPF brasileiro
    """
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    if len(cpf) != 11:
        return False
    
    if cpf == cpf[0] * 11:
        return False
    
    # Valida primeiro dígito
    sum_digits = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit1 = (sum_digits * 10 % 11) % 10
    
    if int(cpf[9]) != digit1:
        return False
    
    # Valida segundo dígito
    sum_digits = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit2 = (sum_digits * 10 % 11) % 10
    
    return int(cpf[10]) == digit2


def validate_cnpj(cnpj: str) -> bool:
    """
    Valida CNPJ brasileiro
    """
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    if len(cnpj) != 14:
        return False
    
    if cnpj == cnpj[0] * 14:
        return False
    
    # Valida primeiro dígito
    weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_digits = sum(int(cnpj[i]) * weights[i] for i in range(12))
    digit1 = (sum_digits % 11)
    digit1 = 0 if digit1 < 2 else 11 - digit1
    
    if int(cnpj[12]) != digit1:
        return False
    
    # Valida segundo dígito
    weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_digits = sum(int(cnpj[i]) * weights[i] for i in range(13))
    digit2 = (sum_digits % 11)
    digit2 = 0 if digit2 < 2 else 11 - digit2
    
    return int(cnpj[13]) == digit2


def validate_cpf_cnpj(value: str) -> bool:
    """
    Valida CPF ou CNPJ
    """
    clean_value = re.sub(r'[^0-9]', '', value)
    
    if len(clean_value) == 11:
        return validate_cpf(value)
    elif len(clean_value) == 14:
        return validate_cnpj(value)
    
    return False


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Tenta fazer parse de uma data em vários formatos
    """
    formats = [
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%Y-%m-%d',
        '%d/%m/%y',
        '%d-%m-%y',
        '%Y/%m/%d',
        '%d.%m.%Y',
        '%Y.%m.%d',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except:
            continue
    
    return None


def parse_currency(value: str) -> Optional[float]:
    """
    Converte string de moeda para float
    Extrai valores numéricos mesmo de strings complexas com texto e moeda
    """
    import re
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if not isinstance(value, str):
        return None
    
    # Primeiro, tenta extrair valor usando regex (para strings complexas)
    # Padrão: R$ seguido de número com ou sem separadores
    # Exemplos: "R$ 200,00", "R$ 6.901,09", "-R$ 200,00", "R$200.00"
    currency_patterns = [
        r'R\$\s*-?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',  # R$ com separadores
        r'R\$\s*-?\s*(\d+[.,]?\d*)',  # R$ simples
        r'-?\s*R\$\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',  # -R$ com separadores
        r'-?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*R\$',  # número antes de R$
    ]
    
    for pattern in currency_patterns:
        match = re.search(pattern, value, re.IGNORECASE)
        if match:
            extracted = match.group(1)
            # Verifica se é negativo (procura sinal de menos antes do padrão)
            is_negative = bool(re.search(r'-\s*R\$|R\$\s*-', value, re.IGNORECASE))
            
            # Limpa e converte
            clean_val = extracted.replace('.', '').replace(',', '.')
            try:
                result = float(clean_val)
                return -result if is_negative else result
            except:
                continue
    
    # Se não encontrou com regex, tenta método tradicional
    # Remove espaços e símbolos de moeda
    clean_value = value.strip().replace('R$', '').replace('$', '').strip()
    
    # Remove texto antes e depois do número (mantém apenas números, vírgulas e pontos)
    clean_value = re.sub(r'[^\d.,-]', '', clean_value)
    
    # Trata formato brasileiro (1.234,56)
    if ',' in clean_value and '.' in clean_value:
        try:
            if clean_value.rindex(',') > clean_value.rindex('.'):
                # Formato brasileiro
                clean_value = clean_value.replace('.', '').replace(',', '.')
            else:
                # Formato americano
                clean_value = clean_value.replace(',', '')
        except ValueError:
            # Se rindex falhar, tenta substituir vírgula
            clean_value = clean_value.replace(',', '.')
    elif ',' in clean_value:
        # Assume formato brasileiro se tiver apenas vírgula
        clean_value = clean_value.replace(',', '.')
    
    # Remove caracteres não numéricos exceto ponto e sinal de menos
    clean_value = re.sub(r'[^\d.-]', '', clean_value)
    
    try:
        return float(clean_value)
    except:
        return None











