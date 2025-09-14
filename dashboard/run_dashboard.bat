@echo off
echo Iniciando Dashboard de Cronoanálise da Jornada de Trabalho...
echo.

:: Verificar se o Streamlit está instalado
pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo Streamlit não encontrado. Instalando dependências...
    pip install -r requirements.txt
) else (
    echo Streamlit já instalado.
)

echo.
echo Abrindo o dashboard...
echo Dashboard será aberto em: http://localhost:8501
echo.
echo Pressione Ctrl+C para parar o servidor
echo.

streamlit run app.py

pause