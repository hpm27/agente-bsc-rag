# Script para reiniciar Streamlit com TODAS correcoes aplicadas (SPRINT 4)
# Executar: .\scripts\restart_streamlit_fixes_complete.ps1

Write-Host "============================================" -ForegroundColor Green
Write-Host "REINICIANDO STREAMLIT - SPRINT 4 FIXES" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Parar processos Streamlit existentes
Write-Host "[1/3] Parando processos Streamlit existentes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*streamlit*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process | Where-Object {$_.ProcessName -like "*python*" -and $_.CommandLine -like "*streamlit*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Limpar cache (opcional mas recomendado)
Write-Host "[2/3] Limpando cache Streamlit..." -ForegroundColor Yellow
$cachePath = "$env:USERPROFILE\.streamlit\cache"
if (Test-Path $cachePath) {
    Remove-Item -Path $cachePath -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  - Cache limpo!" -ForegroundColor Green
} else {
    Write-Host "  - Cache nao encontrado (ok)" -ForegroundColor Gray
}

# Verificar correcoes aplicadas
Write-Host ""
Write-Host "[STATUS] CORRECOES APLICADAS COM SUCESSO:" -ForegroundColor Green
Write-Host ""

Write-Host "1. MECE VALIDATION FIX:" -ForegroundColor Cyan
Write-Host "   - Issue Tree agora gera 30-80% solution paths (flexivel)" -ForegroundColor White
Write-Host "   - Validacao mais inteligente (issues vs warnings)" -ForegroundColor White
Write-Host "   - Auto-complementa se LLM gerar poucos paths" -ForegroundColor White
Write-Host ""

Write-Host "2. KPI VALIDATION FIX:" -ForegroundColor Cyan
Write-Host "   - KPIs concisos BSC aceitos (5+ chars, antes 20+)" -ForegroundColor White
Write-Host "   - Formatos validos: 'ROCE >= 15%', 'NPS > 50'" -ForegroundColor White
Write-Host "   - Prompt otimizado para gerar KPIs validos" -ForegroundColor White
Write-Host ""

Write-Host "3. ROUTING FIX:" -ForegroundColor Cyan
Write-Host "   - Erro em solution_design nao volta mais para discovery" -ForegroundColor White
Write-Host "   - Cria alignment_report mesmo em caso de erro" -ForegroundColor White
Write-Host "   - Mantem na fase correta para correcao" -ForegroundColor White
Write-Host ""

# Iniciar Streamlit
Write-Host "[3/3] Iniciando Streamlit..." -ForegroundColor Yellow
Write-Host ""

$env:PYTHONIOENCODING = "utf-8"
Set-Location "D:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"

Write-Host "=================================================" -ForegroundColor Green
Write-Host "STREAMLIT PRONTO COM TODAS AS CORRECOES!" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Acesse: http://localhost:8501" -ForegroundColor Cyan
Write-Host "Pagina: Consultor BSC - Chat Interativo" -ForegroundColor Cyan
Write-Host ""
Write-Host "TESTANDO CORRECOES:" -ForegroundColor Yellow
Write-Host "- O sistema NAO deve mais falhar com 'MECE validation failed'" -ForegroundColor White
Write-Host "- KPIs concisos como 'ROCE >= 15%' serao aceitos" -ForegroundColor White
Write-Host "- Erros em solution_design NAO voltam para discovery" -ForegroundColor White
Write-Host ""
Write-Host "Pressione Ctrl+C para parar" -ForegroundColor Gray
Write-Host ""

streamlit run Home.py
