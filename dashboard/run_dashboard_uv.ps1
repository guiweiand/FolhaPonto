# PowerShell script para executar o Dashboard usando UV
Write-Host "=== Dashboard de Cronoanálise da Jornada de Trabalho ===" -ForegroundColor Cyan
Write-Host "Usando UV Python Package Manager" -ForegroundColor Green
Write-Host ""

# Verificar se UV está instalado
try {
    $uvVersion = uv --version 2>&1
    Write-Host "UV encontrado: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "ERRO: UV não encontrado. Instale UV primeiro:" -ForegroundColor Red
    Write-Host "powershell -c `"irm https://astral.sh/uv/install.ps1 | iex`"" -ForegroundColor Yellow
    Read-Host "Pressione Enter para continuar..."
    exit 1
}

Write-Host "Verificando dependências..." -ForegroundColor Yellow

# Navegar para o diretório do dashboard
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host ""
Write-Host "Iniciando o dashboard..." -ForegroundColor Cyan
Write-Host "Dashboard será aberto em: http://localhost:8501" -ForegroundColor Yellow
Write-Host ""
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor White
Write-Host ""

# Executar o dashboard com UV
try {
    uv run streamlit run app.py
} catch {
    Write-Host "ERRO: Falha ao executar o dashboard." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Read-Host "Pressione Enter para continuar..."
