@echo off
:: Script de instalação rápida para Windows
:: TrucoCLI - Instalador Windows

echo.
echo ===============================================
echo   INSTALADOR TRUCOCLI PARA WINDOWS
echo ===============================================
echo.

:: Verifica Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo.
    echo Por favor, instale Python 3.7+ de:
    echo https://www.python.org/downloads/
    echo.
    echo Certifique-se de marcar "Add Python to PATH"
    pause
    exit /b 1
)

echo [OK] Python encontrado!
python --version

:: Instala dependências
echo.
echo Instalando dependencias...
python -m pip install --upgrade pip
python -m pip install rich

if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar dependencias
    pause
    exit /b 1
)

echo.
echo ===============================================
echo   INSTALACAO CONCLUIDA!
echo ===============================================
echo.
echo Para jogar:
echo   1. Execute "iniciar_servidor.bat" em uma janela
echo   2. Execute "iniciar_cliente.bat" em 4 janelas separadas
echo.
echo Use o Windows Terminal para melhor experiencia!
echo.
pause
