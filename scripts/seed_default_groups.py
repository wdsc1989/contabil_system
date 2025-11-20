"""
Script utilitario para aplicar grupos/subgrupos padronizados em todos os clientes.
Uso: python scripts/seed_default_groups.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from models.client import Client
from services.group_template_service import GroupTemplateService


def main() -> int:
    db = SessionLocal()
    try:
        clients = db.query(Client).all()
        if not clients:
            print("Nenhum cliente encontrado.")
            return 0

        total_groups = 0
        total_subgroups = 0

        for client in clients:
            result = GroupTemplateService.ensure_default_groups(db, client.id)
            if result["groups_created"] or result["subgroups_created"]:
                print(
                    f"Cliente {client.id} - {client.name}: "
                    f"{result['groups_created']} grupos, "
                    f"{result['subgroups_created']} subgrupos criados."
                )
            total_groups += result["groups_created"]
            total_subgroups += result["subgroups_created"]

        print(
            f"\nResumo: {total_groups} novos grupos e {total_subgroups} novos subgrupos."
        )
        return 0
    except Exception as exc:
        print(f"Erro ao aplicar template de grupos: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())

