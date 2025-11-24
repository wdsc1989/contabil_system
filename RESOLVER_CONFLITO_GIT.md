# 🔧 Resolver Conflito Git na VPS

## ❌ Problema

Ao executar `git pull`, aparece o erro:
```
error: Your local changes to the following files would be overwritten by merge:
        deploy/deploy.sh
        deploy/setup_vps_hostinger.sh
Please commit your changes or stash them before you merge.
```

## ✅ Solução Rápida

Execute na VPS:

```bash
cd /opt/contabil

# Opção 1: Fazer stash (salva mudanças locais)
git stash push -m "Mudanças locais antes do pull"
git pull origin main

# Opção 2: Descartar mudanças locais (se não forem importantes)
git checkout -- deploy/deploy.sh deploy/setup_vps_hostinger.sh
git pull origin main

# Opção 3: Usar script automático
bash deploy/resolve_git_conflict.sh
```

## 🔍 Verificar o que foi alterado localmente

```bash
cd /opt/contabil
git diff deploy/deploy.sh
git diff deploy/setup_vps_hostinger.sh
```

## 💡 Recomendação

**Use a Opção 1 (stash)** se quiser preservar as mudanças locais, ou **Opção 2** se as mudanças locais não forem importantes (geralmente são apenas ajustes manuais que já estão no repositório).

## 🚀 Após Resolver

Continue com o deploy normal:

```bash
./deploy/deploy.sh
```

