# ===================================================================
# SCRIPT DE LIMPEZA AGRESSIVA DE CACHE PYTHON + STREAMLIT
# ===================================================================
#
# USO:
# 1. PARE o Streamlit completamente (Ctrl+C)
# 2. Execute: .\clear_all_cache.ps1
# 3. Reinicie Streamlit: streamlit run main.py
#
# ===================================================================

Write-Host "🧹 LIMPEZA AGRESSIVA DE CACHE - INICIANDO..." -ForegroundColor Yellow
Write-Host ""

# 1. Limpar __pycache__ recursivamente
Write-Host "📁 [1/5] Removendo __pycache__ directories..." -ForegroundColor Cyan
Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force
Write-Host "✅ __pycache__ removidos" -ForegroundColor Green
Write-Host ""

# 2. Limpar .pyc files soltos
Write-Host "📄 [2/5] Removendo .pyc files soltos..." -ForegroundColor Cyan
Get-ChildItem -Path . -Filter "*.pyc" -Recurse -File | Remove-Item -Force
Write-Host "✅ .pyc files removidos" -ForegroundColor Green
Write-Host ""

# 3. Limpar cache do Streamlit
Write-Host "🌐 [3/5] Removendo cache do Streamlit..." -ForegroundColor Cyan
if (Test-Path ".streamlit/cache") {
    Remove-Item -Path ".streamlit/cache" -Recurse -Force
    Write-Host "✅ .streamlit/cache removido" -ForegroundColor Green
} else {
    Write-Host "⚠️  .streamlit/cache não existe (OK)" -ForegroundColor Yellow
}
Write-Host ""

# 4. Limpar .pytest_cache
Write-Host "🧪 [4/5] Removendo .pytest_cache..." -ForegroundColor Cyan
if (Test-Path ".pytest_cache") {
    Remove-Item -Path ".pytest_cache" -Recurse -Force
    Write-Host "✅ .pytest_cache removido" -ForegroundColor Green
} else {
    Write-Host "⚠️  .pytest_cache não existe (OK)" -ForegroundColor Yellow
}
Write-Host ""

# 5. Limpar checkpoints LangGraph (opcional - descomente se necessário)
Write-Host "🗂️  [5/5] Checkpoints LangGraph..." -ForegroundColor Cyan
Write-Host "⚠️  Checkpoints LangGraph NÃO foram removidos (preservar estado)" -ForegroundColor Yellow
Write-Host "    Se quiser remover, descomente a linha no script" -ForegroundColor Gray
# if (Test-Path "checkpoints") {
#     Remove-Item -Path "checkpoints/*" -Recurse -Force
#     Write-Host "✅ checkpoints/ limpo" -ForegroundColor Green
# }
Write-Host ""

Write-Host "============================================================" -ForegroundColor Green
Write-Host "✅ LIMPEZA CONCLUÍDA!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 PRÓXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host "1. Reinicie Streamlit: streamlit run main.py" -ForegroundColor White
Write-Host "2. Procure pelo log:" -ForegroundColor White
Write-Host "   🚀🚀🚀 [DIAGNOSTIC v2.1-20251021-16:10] run_diagnostic() VERSÃO NOVA EXECUTANDO! 🚀🚀🚀" -ForegroundColor Magenta
Write-Host "3. Se NÃO aparecer, cache ainda está ativo (considere reiniciar PowerShell/IDE)" -ForegroundColor White
Write-Host ""
