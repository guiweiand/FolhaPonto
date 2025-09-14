#!/bin/bash
# Script para executar o dashboard usando UV

echo "=== Dashboard de Cronoanálise da Jornada de Trabalho ==="
echo "Usando UV Python Package Manager"
echo ""

# Verificar se UV está instalado
if ! command -v uv &> /dev/null; then
    echo "ERRO: UV não encontrado. Instale UV primeiro:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "UV encontrado. Verificando dependências..."

# Navegar para o diretório do dashboard
cd "$(dirname "$0")"

echo ""
echo "Iniciando o dashboard..."
echo "Dashboard será aberto em: http://localhost:8501"
echo ""
echo "Pressione Ctrl+C para parar o servidor"
echo ""

# Executar o dashboard com UV
uv run streamlit run app.py
