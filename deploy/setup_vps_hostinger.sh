#!/bin/bash
# Script de setup inicial da VPS Hostinger
# Configura o ambiente completo para deploy do sistema contábil
# Uso: ./setup_vps_hostinger.sh

set -e  # Para na primeira erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   SETUP VPS HOSTINGER - Sistema Contábil                ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verifica se está rodando como root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Este script precisa ser executado como root (use sudo)${NC}"
    exit 1
fi

# Atualiza sistema
echo -e "${YELLOW}📦 Atualizando sistema...${NC}"
apt update && apt upgrade -y

# Instala ferramentas básicas
echo -e "${YELLOW}🔧 Instalando ferramentas básicas...${NC}"
apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    ufw \
    fail2ban \
    unattended-upgrades \
    software-properties-common

# Instala Python 3.12 e pip
echo -e "${YELLOW}🐍 Instalando Python 3.12...${NC}"
apt install -y python3.12 python3.12-venv python3.12-dev python3-pip

# Verifica versão do Python
PYTHON_VERSION=$(python3.12 --version)
echo -e "${GREEN}✅ $PYTHON_VERSION instalado${NC}"

# Instala PostgreSQL 16
echo -e "${YELLOW}🗄️  Instalando PostgreSQL 16...${NC}"
apt install -y postgresql-16 postgresql-contrib-16 postgresql-client-16

# Inicia e habilita PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# Verifica status do PostgreSQL
if systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✅ PostgreSQL instalado e rodando${NC}"
else
    echo -e "${RED}❌ Erro ao iniciar PostgreSQL${NC}"
    exit 1
fi

# Instala Nginx
echo -e "${YELLOW}🌐 Instalando Nginx...${NC}"
apt install -y nginx

# Inicia e habilita Nginx
systemctl start nginx
systemctl enable nginx

# Verifica status do Nginx
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx instalado e rodando${NC}"
else
    echo -e "${RED}❌ Erro ao iniciar Nginx${NC}"
    exit 1
fi

# Instala Certbot (Let's Encrypt)
echo -e "${YELLOW}🔒 Instalando Certbot (Let's Encrypt)...${NC}"
apt install -y certbot python3-certbot-nginx

# Configura firewall (UFW)
echo -e "${YELLOW}🔥 Configurando firewall...${NC}"
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw status

echo -e "${GREEN}✅ Firewall configurado${NC}"

# Cria usuário para a aplicação
echo -e "${YELLOW}👤 Criando usuário da aplicação...${NC}"
APP_USER="contabil"
if id "$APP_USER" &>/dev/null; then
    echo -e "${YELLOW}⚠️  Usuário $APP_USER já existe${NC}"
else
    useradd -m -s /bin/bash "$APP_USER"
    usermod -aG sudo "$APP_USER"
    echo -e "${GREEN}✅ Usuário $APP_USER criado${NC}"
fi

# Cria diretórios necessários
echo -e "${YELLOW}📁 Criando diretórios...${NC}"
mkdir -p /var/log/contabil
mkdir -p /var/backups/contabil/postgresql/{daily,weekly,monthly}
mkdir -p /opt/contabil
chown -R "$APP_USER:$APP_USER" /var/log/contabil
chown -R "$APP_USER:$APP_USER" /var/backups/contabil
chown -R "$APP_USER:$APP_USER" /opt/contabil

echo -e "${GREEN}✅ Diretórios criados${NC}"

# Configura PostgreSQL
echo -e "${YELLOW}🗄️  Configurando PostgreSQL...${NC}"
DB_NAME="contabil_db"
DB_USER="contabil_user"
DB_PASSWORD=$(openssl rand -base64 32)

# Cria banco de dados e usuário
sudo -u postgres psql <<EOF
-- Cria usuário
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';

-- Cria banco de dados
CREATE DATABASE $DB_NAME OWNER $DB_USER;

-- Concede permissões
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- Habilita extensões úteis
\c $DB_NAME
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOF

echo -e "${GREEN}✅ PostgreSQL configurado${NC}"
echo -e "${YELLOW}💡 Credenciais do banco de dados:${NC}"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo "   Password: $DB_PASSWORD"
echo ""
echo -e "${RED}⚠️  IMPORTANTE: Salve essas credenciais em local seguro!${NC}"
echo ""

# Configura atualizações automáticas de segurança
echo -e "${YELLOW}🛡️  Configurando atualizações automáticas de segurança...${NC}"
cat > /etc/apt/apt.conf.d/50unattended-upgrades <<EOF
Unattended-Upgrade::Allowed-Origins {
    "\${distro_id}:\${distro_codename}-security";
    "\${distro_id}ESMApps:\${distro_codename}-apps-security";
    "\${distro_id}ESM:\${distro_codename}-infra-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF

echo "APT::Periodic::Update-Package-Lists \"1\";" > /etc/apt/apt.conf.d/20auto-upgrades
echo "APT::Periodic::Unattended-Upgrade \"1\";" >> /etc/apt/apt.conf.d/20auto-upgrades

echo -e "${GREEN}✅ Atualizações automáticas configuradas${NC}"

# Configura Fail2ban
echo -e "${YELLOW}🛡️  Configurando Fail2ban...${NC}"
systemctl enable fail2ban
systemctl start fail2ban
echo -e "${GREEN}✅ Fail2ban configurado${NC}"

# Resumo final
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   SETUP CONCLUÍDO COM SUCESSO!                          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✅ Componentes instalados:${NC}"
echo "   - Python 3.12"
echo "   - PostgreSQL 16"
echo "   - Nginx"
echo "   - Certbot (Let's Encrypt)"
echo "   - Firewall (UFW)"
echo "   - Fail2ban"
echo ""
echo -e "${YELLOW}📋 Próximos passos:${NC}"
echo "   1. Configure as variáveis de ambiente em /opt/contabil/.env"
echo "   2. Use as credenciais do banco acima para DATABASE_URL"
echo "   3. Clone o repositório em /opt/contabil"
echo "   4. Execute o script de deploy: ./deploy/deploy.sh"
echo ""
echo -e "${RED}⚠️  IMPORTANTE: Salve as credenciais do banco de dados!${NC}"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo "   Password: $DB_PASSWORD"
echo ""

