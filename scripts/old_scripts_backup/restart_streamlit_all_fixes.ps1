# Script para reiniciar Streamlit com TODAS correcoes aplicadas (SPRINT 4)
# Inclui: MECE Fix v2 + KPI Validation Fix + Pydantic Forward Reference Fix
# Executar: .\scripts\restart_streamlit_all_fixes.ps1

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  REINICIANDO STREAMLIT - SPRINT 4 COMPLETO" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Resumo das correcoes aplicadas
Write-Host "[INFO] Correcoes aplicadas nesta sessao:" -ForegroundColor Cyan
Write-Host "  1. MECE Validation Fix v2 (25-60% flex, caps 8-20)" -ForegroundColor White
Write-Host "  2. KPI Validation Fix (5 chars minimo vs 20)" -ForegroundColor White
Write-Host "  3. Pydantic Forward Reference Fix (model_rebuild)" -ForegroundColor White
Write-Host ""

# Parar processos Streamlit existentes
Write-Host "[1/4] Parando processos Streamlit existentes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*streamlit*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process | Where-Object {$_.ProcessName -like "*python*" -and $_.CommandLine -like "*streamlit*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Limpar cache Streamlit
Write-Host "[2/4] Limpando cache Streamlit..." -ForegroundColor Yellow
$cachePath = "$env:USERPROFILE\.streamlit\cache"
if (Test-Path $cachePath) {
    Remove-Item -Path $cachePath -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  - Cache limpo com sucesso" -ForegroundColor Gray
} else {
    Write-Host "  - Nenhum cache para limpar" -ForegroundColor Gray
}

# Verificar se ambiente virtual existe
Write-Host "[3/4] Verificando ambiente virtual..." -ForegroundColor Yellow
$venvPath = "D:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag\venv"
if (Test-Path $venvPath) {
    Write-Host "  - Ambiente virtual encontrado" -ForegroundColor Gray
} else {
    Write-Host "  - [WARN] Ambiente virtual nao encontrado!" -ForegroundColor Red
}

# Iniciar Streamlit
Write-Host "[4/4] Iniciando Streamlit..." -ForegroundColor Yellow
Set-Location "D:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"

# Usar o Python do venv se existir, senao usar Python global
if (Test-Path $venvPath) {
    $pythonExe = "$venvPath\Scripts\python.exe"
} else {
    $pythonExe = "python"
}

# Comando para executar Streamlit
$streamlitCommand = "& `"$pythonExe`" -m streamlit run app.py --server.port 8051 --browser.serverAddress localhost"

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  STREAMLIT INICIADO NA PORTA 8051" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "[INFO] Abra o navegador em: http://localhost:8051" -ForegroundColor Cyan
Write-Host "[INFO] Para parar: Ctrl+C nesta janela" -ForegroundColor Cyan
Write-Host ""
Write-Host "[OK] Executando com correcoes SPRINT 4:" -ForegroundColor Green
Write-Host "  - MECE: Aceita 25-60% (antes: 30-80% com bug min>max)" -ForegroundColor White
Write-Host "  - KPIs: Aceita >= 5 chars (antes: >= 20)" -ForegroundColor White
Write-Host "  - Pydantic: Forward refs resolvidas (model_rebuild)" -ForegroundColor White
Write-Host ""

# Executar Streamlit
Invoke-Expression $streamlitCommand
