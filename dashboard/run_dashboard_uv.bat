@echo off
REM Script para executar o dashboard usando UV no Windows

echo === Dashboard de Cronoanálise da Jornada de Trabalho ===
echo Usando UV Python Package Manager
echo.

REM Verificar se UV está instalado
uv --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: UV não encontrado. Instale UV primeiro:
    echo powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    pause
    exit /b 1
)

echo UV encontrado. Verificando dependências...

REM Navegar para o diretório do dashboard
cd /d "%~dp0"

echo.
echo Iniciando o dashboard...
echo Dashboard será aberto em: http://localhost:8501
echo.
echo Pressione Ctrl+C para parar o servidor
echo.

REM Executar o dashboard com UV
uv run streamlit run app.py

pause
