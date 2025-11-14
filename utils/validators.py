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
    """
    if isinstance(value, (int, float)):
        return float(value)
    
    if not isinstance(value, str):
        return None
    
    # Remove espaços e símbolos de moeda
    value = value.strip().replace('R$', '').replace('$', '').strip()
    
    # Trata formato brasileiro (1.234,56)
    if ',' in value and '.' in value:
        if value.rindex(',') > value.rindex('.'):
            # Formato brasileiro
            value = value.replace('.', '').replace(',', '.')
        else:
            # Formato americano
            value = value.replace(',', '')
    elif ',' in value:
        # Assume formato brasileiro se tiver apenas vírgula
        value = value.replace(',', '.')
    
    try:
        return float(value)
    except:
        return None




