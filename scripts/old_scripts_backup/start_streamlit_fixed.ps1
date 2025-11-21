# Script robusto para iniciar Streamlit com PYTHONPATH correto
# Executar: .\scripts\start_streamlit_fixed.ps1

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  INICIANDO STREAMLIT - CONFIGURAÇÃO CORRETA" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Parar processos Streamlit existentes
Write-Host "[1/4] Parando processos Streamlit existentes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*streamlit*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process | Where-Object {$_.ProcessName -like "*python*" -and $_.CommandLine -like "*streamlit*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Navegar para o diretório do projeto
Write-Host "[2/4] Configurando diretório do projeto..." -ForegroundColor Yellow
$projectPath = "D:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"
Set-Location $projectPath
Write-Host "   Diretório: $projectPath" -ForegroundColor Gray

# Configurar PYTHONPATH
Write-Host "[3/4] Configurando PYTHONPATH..." -ForegroundColor Yellow
$env:PYTHONPATH = $projectPath
Write-Host "   PYTHONPATH = $env:PYTHONPATH" -ForegroundColor Gray

# Verificar se src existe
if (Test-Path "src") {
    Write-Host "   [OK] Diretório 'src' encontrado" -ForegroundColor Green
} else {
    Write-Host "   [ERRO] Diretório 'src' não encontrado!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[4/4] Iniciando Streamlit..." -ForegroundColor Green
Write-Host ""
Write-Host "URL Local: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""

# Executar Streamlit (app.py principal para menu multi-page)
python -m streamlit run app.py
