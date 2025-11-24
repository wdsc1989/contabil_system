# Deploy Vision API - Checklist para Produção

## ✅ Dependências Atualizadas

O `requirements.txt` foi atualizado com todas as dependências necessárias para a Vision API:

### Dependências Principais:
- **openai>=1.0.0** - OBRIGATÓRIO para Vision API
- **PyMuPDF>=1.23.0** - Principal para conversão de PDFs (funciona no Linux sem poppler)
- **pdf2image>=1.16.3** - Fallback para PDFs (requer poppler-utils)
- **Pillow>=10.0.0** - Processamento de imagens

### Dependências do Sistema (Linux):
O script `deploy/setup_vps_hostinger.sh` já instala automaticamente:
- `poppler-utils` - Necessário para pdf2image (fallback)
- `libpoppler-cpp-dev` - Bibliotecas de desenvolvimento
- Outras dependências de imagem (libjpeg-dev, libpng-dev, etc.)

## 🚀 Como Fazer Deploy

### 1. Na VPS (Hostinger):

```bash
cd /opt/contabil
./deploy/deploy.sh
```

O script irá:
- ✅ Atualizar código do repositório
- ✅ Instalar/atualizar dependências Python
- ✅ Verificar e instalar poppler-utils se necessário
- ✅ Executar migrações do banco
- ✅ Reiniciar o serviço

### 2. Verificar Instalação:

```bash
# Verificar se PyMuPDF está instalado
source /opt/contabil/venv/bin/activate
python -c "import fitz; print('PyMuPDF OK:', fitz.__version__)"

# Verificar se poppler está instalado (fallback)
pdftoppm -v

# Verificar se openai está instalado
python -c "import openai; print('OpenAI OK:', openai.__version__)"
```

## 📋 Funcionalidades Implementadas

### ✅ Processamento de Arquivos com Vision API:
- **CSV/Excel**: Enviados como texto diretamente (mais rápido)
- **PDFs**: Convertidos para imagens (página por página) usando PyMuPDF
- **Imagens**: Enviadas diretamente como base64
- **Fallback automático**: Se PyMuPDF falhar, usa pdf2image

### ✅ Melhorias:
- Fluxo simplificado: Upload → Processamento → Edição → Importação
- Detecção automática do tipo de dado
- Classificação automática por grupos/subgrupos
- Mensagens de erro claras e úteis

## ⚠️ Notas Importantes

1. **Python 3.12**: Em produção (Linux), PyMuPDF funciona perfeitamente
2. **Fallback**: Se PyMuPDF falhar, o sistema usa pdf2image automaticamente
3. **Dependências do Sistema**: O script de setup instala tudo automaticamente
4. **Vision API**: Requer configuração da API key da OpenAI no `.env`

## 🔧 Troubleshooting

### Se PyMuPDF não funcionar:
```bash
# Reinstalar PyMuPDF
source /opt/contabil/venv/bin/activate
pip uninstall PyMuPDF
pip install PyMuPDF
```

### Se poppler não estiver instalado:
```bash
sudo apt-get update
sudo apt-get install -y poppler-utils
```

### Verificar logs:
```bash
journalctl -u contabil.service -f
```

## 📝 Arquivos Modificados

- `services/vision_processor.py` - NOVO: Processador Vision API
- `services/ai_service.py` - Integração com VisionProcessor
- `pages/2_Importacao_Dados.py` - Fluxo simplificado
- `config/ai_config.py` - Suporte a detecção de modelos Vision
- `requirements.txt` - Dependências atualizadas
- `deploy/setup_vps_hostinger.sh` - Instala dependências do sistema
- `deploy/deploy.sh` - Verifica poppler-utils

