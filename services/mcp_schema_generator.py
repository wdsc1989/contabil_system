"""
Gerador de schemas JSON a partir de modelos SQLAlchemy para uso com MCP Tools
"""
from typing import Dict, Any, List, Optional
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeMeta
from sqlalchemy.types import Integer, String, Float, Date, DateTime, Boolean, Text
from datetime import datetime

from models.transaction import Transaction, BankStatement
from models.contract import Contract
from models.account import AccountPayable, AccountReceivable
from models.financial_investment import FinancialInvestment
from models.credit_card import CreditCardInvoice
from models.card_machine import CardMachineStatement
from models.inventory import Inventory


class MCPSchemaGenerator:
    """
    Gera schemas JSON a partir de modelos SQLAlchemy para uso com MCP Tools
    """
    
    # Mapeamento de tipos SQLAlchemy para JSON Schema
    TYPE_MAPPING = {
        Integer: {"type": "integer"},
        Float: {"type": "number"},
        String: {"type": "string"},
        Text: {"type": "string"},
        Date: {"type": "string", "format": "date"},
        DateTime: {"type": "string", "format": "date-time"},
        Boolean: {"type": "boolean"},
    }
    
    # Mapeamento de tipos de dados para modelos
    DATA_TYPE_MODELS = {
        'transactions': Transaction,
        'bank_statements': BankStatement,
        'contracts': Contract,
        'accounts_payable': AccountPayable,
        'accounts_receivable': AccountReceivable,
        'financial_investments': FinancialInvestment,
        'credit_card_invoices': CreditCardInvoice,
        'card_machine_statements': CardMachineStatement,
        'inventory': Inventory,
    }
    
    # Campos que devem ser ignorados (gerados automaticamente ou não relevantes para importação)
    IGNORED_FIELDS = {'id', 'created_at', 'client_id'}
    
    @classmethod
    def _sqlalchemy_type_to_json_schema(cls, column_type) -> Dict[str, Any]:
        """
        Converte tipo SQLAlchemy para JSON Schema
        """
        # Verifica o tipo base
        for sql_type, json_schema in cls.TYPE_MAPPING.items():
            if isinstance(column_type, sql_type):
                result = json_schema.copy()
                
                # Adiciona constraints específicos
                if isinstance(column_type, String):
                    if hasattr(column_type, 'length'):
                        result['maxLength'] = column_type.length
                
                return result
        
        # Fallback para string se não reconhecer
        return {"type": "string"}
    
    @classmethod
    def _get_column_info(cls, column) -> Dict[str, Any]:
        """
        Extrai informações de uma coluna SQLAlchemy
        """
        column_type = column.type
        json_schema = cls._sqlalchemy_type_to_json_schema(column_type)
        
        # Adiciona nullable
        if column.nullable:
            json_schema['nullable'] = True
        else:
            json_schema['required'] = True
        
        # Adiciona descrição se houver
        if column.doc:
            json_schema['description'] = column.doc
        
        return json_schema
    
    @classmethod
    def generate_schema(cls, model_class: DeclarativeMeta, include_relationships: bool = False) -> Dict[str, Any]:
        """
        Gera schema JSON para um modelo SQLAlchemy
        
        Args:
            model_class: Classe do modelo SQLAlchemy
            include_relationships: Se deve incluir informações de relacionamentos
        
        Returns:
            Dict com schema JSON Schema
        """
        inspector = inspect(model_class)
        table_name = model_class.__tablename__
        
        schema = {
            "type": "object",
            "title": model_class.__name__,
            "description": f"Schema para {table_name}",
            "properties": {},
            "required": []
        }
        
        # Itera sobre todas as colunas
        for column in inspector.columns:
            column_name = column.name
            
            # Ignora campos especiais
            if column_name in cls.IGNORED_FIELDS:
                continue
            
            # Obtém informações da coluna
            column_info = cls._get_column_info(column)
            
            # Adiciona ao schema
            schema["properties"][column_name] = column_info
            
            # Adiciona à lista de required se não for nullable
            if not column.nullable and column_name not in cls.IGNORED_FIELDS:
                if column_name not in schema["required"]:
                    schema["required"].append(column_name)
        
        return schema
    
    @classmethod
    def get_schema_for_data_type(cls, data_type: str) -> Dict[str, Any]:
        """
        Obtém schema para um tipo de dado específico
        
        Args:
            data_type: Tipo de dado (transactions, bank_statements, etc.)
        
        Returns:
            Dict com schema JSON Schema
        """
        if data_type not in cls.DATA_TYPE_MODELS:
            raise ValueError(f"Tipo de dado desconhecido: {data_type}")
        
        model_class = cls.DATA_TYPE_MODELS[data_type]
        return cls.generate_schema(model_class)
    
    @classmethod
    def get_all_schemas(cls) -> Dict[str, Dict[str, Any]]:
        """
        Obtém todos os schemas disponíveis
        
        Returns:
            Dict mapeando tipo de dado para seu schema
        """
        schemas = {}
        for data_type, model_class in cls.DATA_TYPE_MODELS.items():
            schemas[data_type] = cls.generate_schema(model_class)
        return schemas
    
    @classmethod
    def get_column_specifications(cls, data_type: str) -> Dict[str, Dict[str, Any]]:
        """
        Obtém especificações detalhadas de colunas para um tipo de dado
        
        Args:
            data_type: Tipo de dado
        
        Returns:
            Dict mapeando nome da coluna para suas especificações
        """
        if data_type not in cls.DATA_TYPE_MODELS:
            raise ValueError(f"Tipo de dado desconhecido: {data_type}")
        
        model_class = cls.DATA_TYPE_MODELS[data_type]
        inspector = inspect(model_class)
        
        specifications = {}
        
        for column in inspector.columns:
            column_name = column.name
            
            if column_name in cls.IGNORED_FIELDS:
                continue
            
            column_info = cls._get_column_info(column)
            
            specifications[column_name] = {
                "type": column_info.get("type"),
                "format": column_info.get("format"),
                "nullable": column.nullable,
                "required": not column.nullable,
                "description": column_info.get("description", ""),
                "max_length": column_info.get("maxLength"),
                "sql_type": str(column.type),
            }
        
        return specifications
    
    @classmethod
    def get_target_columns(cls, data_type: str) -> List[str]:
        """
        Obtém lista de colunas de destino para um tipo de dado
        
        Args:
            data_type: Tipo de dado
        
        Returns:
            Lista de nomes de colunas
        """
        if data_type not in cls.DATA_TYPE_MODELS:
            raise ValueError(f"Tipo de dado desconhecido: {data_type}")
        
        model_class = cls.DATA_TYPE_MODELS[data_type]
        inspector = inspect(model_class)
        
        columns = []
        for column in inspector.columns:
            if column.name not in cls.IGNORED_FIELDS:
                columns.append(column.name)
        
        return columns
    
    @classmethod
    def get_table_structure_description(cls, data_type: str) -> str:
        """
        Obtém descrição textual da estrutura da tabela
        
        Args:
            data_type: Tipo de dado
        
        Returns:
            String com descrição da estrutura
        """
        if data_type not in cls.DATA_TYPE_MODELS:
            raise ValueError(f"Tipo de dado desconhecido: {data_type}")
        
        model_class = cls.DATA_TYPE_MODELS[data_type]
        inspector = inspect(model_class)
        table_name = model_class.__tablename__
        
        description = f"Tabela: {table_name}\n"
        description += f"Modelo: {model_class.__name__}\n\n"
        description += "Colunas:\n"
        
        for column in inspector.columns:
            if column.name in cls.IGNORED_FIELDS:
                continue
            
            nullable = "NULL" if column.nullable else "NOT NULL"
            description += f"  - {column.name}: {column.type} ({nullable})\n"
        
        return description



