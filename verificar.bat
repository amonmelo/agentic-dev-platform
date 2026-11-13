@echo off
rem Verificacao local completa: testes + demonstracao das metricas.
rem Uso: dar dois cliques neste arquivo ou rodar `verificar.bat` na raiz do repositorio.
setlocal
cd /d "%~dp0"

set PYTHON=.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=python

echo === pytest ===
%PYTHON% -m pytest -q
if errorlevel 1 goto :falhou

echo.
echo === demo de metricas (log sintetico, proporcoes reais) ===
%PYTHON% examples\log_demo.py
if errorlevel 1 goto :falhou

echo.
echo OK: testes e demo passaram.
exit /b 0

:falhou
echo.
echo FALHOU: veja o erro acima.
exit /b 1
