#!/bin/bash
# Script rápido para corrigir permissões
# Uso: bash deploy/fix_permissions.sh

cd /opt/contabil || exit 1

echo "🔧 Corrigindo permissões dos scripts..."

chmod +x deploy/deploy.sh
chmod +x deploy/setup_vps_hostinger.sh
chmod +x deploy/fix_production.sh
chmod +x deploy/check_service.sh
chmod +x deploy/resolve_git_conflict.sh
chmod +x deploy/fix_permissions.sh 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true

echo "✅ Permissões corrigidas!"
echo ""
echo "Agora você pode executar:"
echo "  ./deploy/deploy.sh"
echo ""




