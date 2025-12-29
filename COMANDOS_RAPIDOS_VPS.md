# 🚀 Comandos Rápidos para VPS

## ⚡ Solução Rápida para "Permission denied"

Se você receber `Permission denied` ao executar o script:

```bash
# 1. Dar permissão de execução
chmod +x deploy/deploy.sh
chmod +x deploy/*.sh

# 2. Executar o deploy
./deploy/deploy.sh
```

## 📋 Sequência Completa (Copy & Paste)

```bash
cd /opt/contabil && \
chmod +x deploy/deploy.sh deploy/*.sh && \
./deploy/deploy.sh
```

## 🔧 Se Ainda Der Erro

```bash
# Executar com bash explicitamente
bash deploy/deploy.sh

# Ou com sh
sh deploy/deploy.sh
```

## ✅ Verificação Rápida

Após o deploy:

```bash
# Ver status
systemctl status contabil.service

# Ver logs
journalctl -u contabil.service -n 20
```









