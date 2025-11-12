# 🚀 Instalação Fácil - Sistema Contábil

## Para Usuários Sem Conhecimento Técnico

---

## 📋 Pré-requisito: Python

### Verificar se Python está instalado:

1. Abra o **Prompt de Comando** (CMD)
2. Digite: `python --version`
3. Se aparecer algo como "Python 3.x.x" → **Já tem Python!**
4. Se aparecer erro → **Precisa instalar**

### Instalar Python (se necessário):

1. Acesse: https://www.python.org/downloads/
2. Baixe a versão mais recente (3.8 ou superior)
3. **IMPORTANTE:** Marque a opção **"Add Python to PATH"**
4. Clique em "Install Now"
5. Aguarde a instalação

---

## 🎯 Instalação do Sistema (3 Cliques!)

### Passo 1: Baixar o Sistema
- Copie a pasta `contabil_system` para seu computador
- Exemplo: `C:\Sistemas\contabil_system`

### Passo 2: Instalar
1. Entre na pasta `contabil_system`
2. **Clique duas vezes** em: `install.bat`
3. Aguarde a instalação (2-5 minutos)
4. Pronto!

### Passo 3: Executar
1. **Clique duas vezes** em: `run.bat`
2. O sistema abrirá automaticamente no navegador
3. Use as credenciais fornecidas

---

## 📁 Arquivos Importantes

### Para Usuário Final:

| Arquivo | Para que serve | Quando usar |
|---------|---------------|-------------|
| **install.bat** | Instala o sistema | Primeira vez apenas |
| **run.bat** | Executa o sistema | Sempre que quiser usar |
| **reset_data.bat** | Reseta dados de teste | Se quiser recomeçar |

### Não Mexer:
- `venv/` - Ambiente Python (criado automaticamente)
- `data/` - Banco de dados (criado automaticamente)
- Outros arquivos `.py` - Código do sistema

---

## 🎮 Como Usar

### Primeira Vez:

```
1. Clique em: install.bat
   ↓
2. Aguarde instalação
   ↓
3. Clique em: run.bat
   ↓
4. Sistema abre no navegador
   ↓
5. Login: admin / admin123
```

### Próximas Vezes:

```
1. Clique em: run.bat
   ↓
2. Sistema abre no navegador
   ↓
3. Use normalmente
```

### Para Resetar Dados:

```
1. Clique em: reset_data.bat
   ↓
2. Confirme (digite S)
   ↓
3. Dados resetados
```

---

## 🔑 Credenciais Padrão

Após instalar, use:

- **Administrador:** `admin` / `admin123`
- **Gerente:** `gerente1` / `gerente123`
- **Visualizador:** `viewer1` / `viewer123`

**Dica:** Altere as senhas na página de Administração!

---

## ❓ Perguntas Frequentes

### O sistema precisa de internet?
**Não!** Funciona 100% offline no seu computador.

### Posso usar em vários computadores?
**Sim!** Basta copiar a pasta e executar `install.bat` em cada um.

### Os dados ficam salvos?
**Sim!** Tudo fica salvo no arquivo `data/contabil.db`

### Como fazer backup?
Copie a pasta `data/` para um local seguro.

### Como atualizar o sistema?
Substitua os arquivos, mas **mantenha a pasta `data/`** para não perder dados.

### O sistema fecha quando fecho o navegador?
**Não!** O sistema continua rodando. Para parar, feche a janela preta (CMD).

### Posso acessar de outro computador na rede?
**Sim!** O sistema mostrará um endereço de rede (ex: http://192.168.1.10:8501)

---

## 🆘 Problemas Comuns

### "Python não encontrado"
**Solução:** Instale o Python (veja seção acima)

### "Erro ao instalar dependências"
**Solução:** 
1. Abra CMD como Administrador
2. Execute: `install.bat` novamente

### "Porta 8501 já em uso"
**Solução:** 
1. Feche outras instâncias do sistema
2. Ou reinicie o computador

### Sistema não abre no navegador
**Solução:** Abra manualmente: http://localhost:8501

---

## 📦 Para Distribuir

### Opção 1: Pasta Completa (Recomendado)
1. Copie toda a pasta `contabil_system`
2. Envie para o usuário (pen drive, email, rede)
3. Usuário executa `install.bat` uma vez
4. Depois usa `run.bat` sempre

### Opção 2: Executável (Em breve)
- Arquivo único `.exe`
- Não precisa instalar Python
- Mais fácil ainda

---

## 📞 Suporte

**Problemas?**
1. Leia este guia
2. Veja o arquivo `README.md`
3. Execute `install.bat` novamente

---

## ✅ Checklist de Instalação

- [ ] Python instalado (3.8+)
- [ ] Pasta `contabil_system` copiada
- [ ] Executado `install.bat`
- [ ] Aguardado instalação completa
- [ ] Executado `run.bat`
- [ ] Sistema abriu no navegador
- [ ] Login funcionou
- [ ] Dados de teste carregados

**Se todos os itens estão marcados, está pronto!** 🎉


