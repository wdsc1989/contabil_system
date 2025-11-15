"""
Formatadores de dados
"""
import re
from datetime import datetime
from typing import Union


def format_cpf(cpf: str) -> str:
    """
    Formata CPF: 000.000.000-00
    """
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) == 11:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return cpf


def format_cnpj(cnpj: str) -> str:
    """
    Formata CNPJ: 00.000.000/0000-00
    """
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj) == 14:
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    return cnpj


def format_cpf_cnpj(value: str) -> str:
    """
    Formata CPF ou CNPJ automaticamente
    """
    clean_value = re.sub(r'[^0-9]', '', value)
    
    if len(clean_value) == 11:
        return format_cpf(value)
    elif len(clean_value) == 14:
        return format_cnpj(value)
    
    return value


def format_currency(value: Union[int, float], symbol: str = 'R$') -> str:
    """
    Formata valor monetário
    """
    if value is None:
        return f"{symbol} 0,00"
    
    formatted = f"{abs(value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    if value < 0:
        return f"-{symbol} {formatted}"
    
    return f"{symbol} {formatted}"


def format_date(date: datetime, format_str: str = '%d/%m/%Y') -> str:
    """
    Formata data
    """
    if isinstance(date, datetime):
        return date.strftime(format_str)
    return str(date)


def format_month_year(date: datetime) -> str:
    """
    Formata mês/ano: MM/YYYY
    """
    if isinstance(date, datetime):
        return date.strftime('%m/%Y')
    return str(date)





