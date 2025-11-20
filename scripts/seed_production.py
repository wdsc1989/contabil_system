#!/usr/bin/env python3
"""
Script para criar dados de exemplo em produção após reset
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from services.group_template_service import GroupTemplateService
from models.client import Client
from models.user import User

def criar_cliente_exemplo():
    """Cria um cliente de exemplo"""
    db = SessionLocal()
    try:
        # Verificar se já existe
        cliente = db.query(Client).filter(Client.name == 'Cliente Exemplo').first()
        if cliente:
            print("   ⚠️  Cliente exemplo já existe")
            return cliente.id
        
        # Criar cliente
        cliente = Client(
            name='Cliente Exemplo',
            cpf_cnpj='12.345.678/0001-90',
            tipo_empresa='Eventos',
            active=True
        )
        db.add(cliente)
        db.commit()
        db.refresh(cliente)
        
        print(f"   ✅ Cliente exemplo criado (ID: {cliente.id})")
        
        # Criar grupos padrão
        GroupTemplateService.ensure_default_groups(db, cliente.id)
        print("   ✅ Grupos padrão criados")
        
        return cliente.id
    finally:
        db.close()

def main():
    print("=" * 70)
    print("🌱 CRIANDO DADOS DE EXEMPLO")
    print("=" * 70)
    print()
    
    cliente_id = criar_cliente_exemplo()
    
    print()
    print("=" * 70)
    print("✅ DADOS DE EXEMPLO CRIADOS")
    print("=" * 70)
    print()
    print(f"Cliente ID: {cliente_id}")
    print("Você pode agora:")
    print("  - Importar dados através da interface")
    print("  - Ou usar scripts de seed para criar dados de teste")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

