# Script para reiniciar Streamlit com correcoes MECE
# Executar: .\scripts\restart_streamlit_mece_fix.ps1

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "REINICIANDO STREAMLIT COM FIX MECE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Parar processos Streamlit existentes
Write-Host "[1/3] Parando processos Streamlit existentes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*streamlit*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Limpar cache Streamlit (opcional)
Write-Host "[2/3] Limpando cache Streamlit..." -ForegroundColor Yellow
$cachePath = "$env:USERPROFILE\.streamlit\cache"
if (Test-Path $cachePath) {
    Remove-Item -Path $cachePath -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  - Cache limpo!" -ForegroundColor Green
} else {
    Write-Host "  - Cache nao encontrado (ok)" -ForegroundColor Gray
}

# Iniciar Streamlit
Write-Host "[3/3] Iniciando Streamlit..." -ForegroundColor Yellow
Write-Host ""

$env:PYTHONIOENCODING = "utf-8"
Set-Location "D:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"

Write-Host "CORRECOES MECE APLICADAS:" -ForegroundColor Green
Write-Host "- Issue Tree agora gera 30-80% solution paths (flexivel)" -ForegroundColor White
Write-Host "- Minimo: 30% dos leaf nodes" -ForegroundColor White
Write-Host "- Maximo: 80% dos leaf nodes ou 12 paths" -ForegroundColor White
Write-Host "- Validacao mais inteligente (issues vs warnings)" -ForegroundColor White
Write-Host ""
Write-Host "Iniciando em: http://localhost:8501" -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para parar" -ForegroundColor Gray
Write-Host ""

streamlit run Home.py
