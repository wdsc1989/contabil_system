#!/bin/bash
# Script para verificar status do serviço e diagnosticar problemas
# Uso: bash deploy/check_service.sh

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   DIAGNÓSTICO DO SERVIÇO                                 ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. Verifica status do serviço Streamlit
echo -e "${YELLOW}1. Verificando serviço Streamlit...${NC}"
if systemctl is-active --quiet contabil.service; then
    echo -e "${GREEN}✅ Serviço está rodando${NC}"
    systemctl status contabil.service --no-pager -l | head -20
else
    echo -e "${RED}❌ Serviço NÃO está rodando${NC}"
    echo -e "${YELLOW}Tentando iniciar...${NC}"
    systemctl start contabil.service
    sleep 3
    if systemctl is-active --quiet contabil.service; then
        echo -e "${GREEN}✅ Serviço iniciado${NC}"
    else
        echo -e "${RED}❌ Erro ao iniciar serviço${NC}"
    fi
fi
echo ""

# 2. Verifica se Streamlit está respondendo na porta 8501
echo -e "${YELLOW}2. Verificando se Streamlit responde na porta 8501...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8501 | grep -q "200\|302"; then
    echo -e "${GREEN}✅ Streamlit está respondendo${NC}"
else
    echo -e "${RED}❌ Streamlit NÃO está respondendo na porta 8501${NC}"
    echo -e "${YELLOW}Verificando se a porta está em uso...${NC}"
    netstat -tlnp | grep 8501 || echo "Porta 8501 não está em uso"
fi
echo ""

# 3. Verifica logs recentes
echo -e "${YELLOW}3. Últimas 30 linhas dos logs do serviço:${NC}"
journalctl -u contabil.service -n 30 --no-pager
echo ""

# 4. Verifica nginx
echo -e "${YELLOW}4. Verificando Nginx...${NC}"
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx está rodando${NC}"
    nginx -t && echo -e "${GREEN}✅ Configuração do Nginx está OK${NC}" || echo -e "${RED}❌ Erro na configuração do Nginx${NC}"
else
    echo -e "${RED}❌ Nginx NÃO está rodando${NC}"
fi
echo ""

# 5. Verifica logs do nginx
echo -e "${YELLOW}5. Últimas 20 linhas dos logs de erro do Nginx:${NC}"
tail -20 /var/log/nginx/contabil_error.log 2>/dev/null || echo "Arquivo de log não encontrado"
echo ""

# 6. Verifica memória e CPU
echo -e "${YELLOW}6. Uso de recursos:${NC}"
ps aux | grep streamlit | grep -v grep || echo "Nenhum processo Streamlit encontrado"
echo ""

# 7. Verifica se PyMuPDF está instalado
echo -e "${YELLOW}7. Verificando dependências Python...${NC}"
source /opt/contabil/venv/bin/activate 2>/dev/null || echo "Venv não encontrado"
python -c "import fitz; print('✅ PyMuPDF OK')" 2>/dev/null || echo "❌ PyMuPDF não encontrado"
python -c "import openai; print('✅ OpenAI OK')" 2>/dev/null || echo "❌ OpenAI não encontrado"
echo ""

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   DIAGNÓSTICO CONCLUÍDO                                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}💡 Comandos úteis:${NC}"
echo "   Ver logs em tempo real: journalctl -u contabil.service -f"
echo "   Reiniciar serviço: systemctl restart contabil.service"
echo "   Recarregar Nginx: systemctl reload nginx"
echo ""

