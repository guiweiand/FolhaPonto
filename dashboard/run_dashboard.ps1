# PowerShell script para executar o Dashboard
Write-Host "=== Dashboard de Cronoanálise da Jornada de Trabalho ===" -ForegroundColor Cyan
Write-Host ""

# Verificar se o Python está instalado
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERRO: Python não encontrado. Instale Python primeiro." -ForegroundColor Red
    exit 1
}

# Verificar se o Streamlit está instalado
try {
    $streamlitVersion = pip show streamlit 2>$null
    if ($streamlitVersion) {
        Write-Host "Streamlit já instalado." -ForegroundColor Green
    } else {
        throw "Streamlit não encontrado"
    }
} catch {
    Write-Host "Streamlit não encontrado. Instalando dependências..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO: Falha ao instalar dependências." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Iniciando o dashboard..." -ForegroundColor Cyan
Write-Host "Dashboard será aberto em: http://localhost:8501" -ForegroundColor Yellow
Write-Host ""
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor White
Write-Host ""

# Executar o Streamlit
streamlit run app.py

Read-Host "Pressione Enter para continuar..."
