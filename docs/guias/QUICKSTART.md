# 🚀 Quick Start - Sistema Contábil

## Início Rápido em 5 Minutos

### 1️⃣ Instale as Dependências

```bash
cd C:\Users\DELL\Documents\Projetos\Contabil\contabil_system
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2️⃣ Inicialize o Sistema

```bash
python init_db.py
python tests/seed_data.py --reset
```

### 3️⃣ Execute a Aplicação

```bash
streamlit run app.py
```

### 4️⃣ Faça Login

Acesse: `http://localhost:8501`

**Credenciais:**
- Admin: `admin` / `admin123`

### 5️⃣ Explore!

1. Selecione um cliente na sidebar
2. Veja os dashboards (DRE, DFC, Sazonalidade)
3. Explore os dados de 2 anos já carregados

## 📊 O Que Você Vai Encontrar

- **3 clientes** com dados completos
- **2 anos** de histórico financeiro
- **1.200+ transações** por cliente
- **150+ contratos** por cliente
- **Dashboards** interativos prontos
- **Análises** de sazonalidade

## 🎯 Principais Funcionalidades

| Funcionalidade | Onde Encontrar |
|----------------|----------------|
| Importar dados | 📥 Importação de Dados |
| **Gerenciar transações** | **💳 Transações (NOVO!)** |
| Gerenciar contratos | 📝 Contratos |
| Controlar contas | 💰 Contas |
| Ver receitas/despesas | 📊 DRE |
| Analisar fluxo de caixa | 💵 DFC |
| Identificar sazonalidade | 📈 Sazonalidade |
| Gerar relatórios | 📑 Relatórios |

### ✨ CRUD Completo
- ✅ **Criar** dados manualmente
- ✅ **Editar** dados (importados ou manuais)
- ✅ **Excluir** dados
- ✅ Disponível em **todos os módulos**

## 💡 Dicas

- Use **Ctrl+R** para recarregar a página
- Todos os dashboards têm **filtros de período**
- Os dados de teste têm **sazonalidade realista**
- Experimente **importar seus próprios arquivos**

## 📚 Documentação Completa

- `README.md` - Visão geral
- `INSTALL.md` - Instalação detalhada
- `tests/TESTING_GUIDE.md` - Guia de testes
- `IMPLEMENTATION_SUMMARY.md` - Resumo técnico

## ❓ Problemas?

```bash
# Reiniciar tudo do zero
python tests/seed_data.py --reset
streamlit run app.py
```

## 🎉 Pronto!

Agora você tem um sistema contábil completo funcionando!

