# Script para reiniciar Streamlit com correções de ALIGNMENT SCORE
# Executar: .\scripts\restart_streamlit_alignment_fix.ps1

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  REINICIANDO STREAMLIT - ALIGNMENT FIX" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Resumo das correções aplicadas
Write-Host "[INFO] Correções aplicadas:" -ForegroundColor Green
Write-Host ""
Write-Host "  1. LOOP INFINITO:" -ForegroundColor Yellow
Write-Host "     - Score < 80 agora vai para APPROVAL (não discovery)" -ForegroundColor White
Write-Host "     - Permite aprovação manual mesmo com score 75%" -ForegroundColor White
Write-Host ""
Write-Host "  2. VALIDAÇÃO RATIONALE:" -ForegroundColor Yellow
Write-Host "     - Descriptions agora exigem 60+ chars (era 50)" -ForegroundColor White
Write-Host "     - Prompt atualizado para gerar descriptions longas" -ForegroundColor White
Write-Host ""
Write-Host "  3. VALIDAÇÃO JARGON:" -ForegroundColor Yellow
Write-Host "     - Lista explícita de termos a evitar no prompt" -ForegroundColor White
Write-Host "     - Linguagem específica e acionável" -ForegroundColor White
Write-Host ""

# Parar processos Streamlit existentes
Write-Host "[1/3] Parando processos Streamlit existentes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*streamlit*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process | Where-Object {$_.ProcessName -like "*python*" -and $_.CommandLine -like "*streamlit*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Limpar cache
Write-Host "[2/3] Limpando cache Streamlit..." -ForegroundColor Yellow
$cachePath = "$env:USERPROFILE\.streamlit\cache"
if (Test-Path $cachePath) {
    Remove-Item -Path $cachePath -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "   Cache limpo" -ForegroundColor Gray
} else {
    Write-Host "   Cache já está limpo" -ForegroundColor Gray
}

# Iniciar Streamlit
Write-Host "[3/3] Iniciando Streamlit..." -ForegroundColor Green
$scriptPath = Join-Path $PSScriptRoot ".."
Set-Location $scriptPath

Write-Host ""
Write-Host "[OK] Streamlit reiniciado com ALIGNMENT FIX!" -ForegroundColor Green
Write-Host ""
Write-Host "EXPECTATIVAS:" -ForegroundColor Cyan
Write-Host "  - Score pode subir de 75% para 87.5% ou 100%" -ForegroundColor White
Write-Host "  - Mesmo com 75%, NÃO voltará para discovery" -ForegroundColor White
Write-Host "  - Usuário pode aprovar manualmente" -ForegroundColor White
Write-Host ""

# Configurar PYTHONPATH
$env:PYTHONPATH = $scriptPath
Write-Host "PYTHONPATH configurado: $env:PYTHONPATH" -ForegroundColor Gray

# Executar Streamlit
streamlit run pages/0_consultor_bsc.py
