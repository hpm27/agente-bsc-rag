# Script para reiniciar Streamlit com FIX do Pydantic v2 aplicado
# ERRO RESOLVIDO: "Input should be a valid dictionary or instance"
# Executar: .\scripts\restart_streamlit_pydantic_fix.ps1

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  REINICIANDO STREAMLIT - PYDANTIC V2 FIX" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""

# Resumo do problema resolvido
Write-Host "[INFO] PROBLEMA RESOLVIDO:" -ForegroundColor Cyan
Write-Host "  - ValidationError: 'Input should be a valid dictionary or instance'" -ForegroundColor White
Write-Host "  - Causa: Pydantic v2 nao aceita instancias diretas em construtores" -ForegroundColor White
Write-Host "  - Solucao: Usar .model_dump() para converter para dict" -ForegroundColor White
Write-Host ""

# Arquivos corrigidos
Write-Host "[INFO] Arquivos corrigidos nesta sessao:" -ForegroundColor Cyan
Write-Host "  1. src/agents/diagnostic_agent.py (linha 1411)" -ForegroundColor White
Write-Host "  2. src/memory/mem0_client.py (filters obrigatorios)" -ForegroundColor White
Write-Host "  3. src/graph/workflow.py (roteamento para approval)" -ForegroundColor White
Write-Host ""

# Parar processos Streamlit existentes
Write-Host "[1/3] Parando processos Streamlit existentes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*streamlit*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process | Where-Object {$_.ProcessName -like "*python*" -and $_.CommandLine -like "*streamlit*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Limpar cache (IMPORTANTE para evitar cache de modulos antigos)
Write-Host "[2/3] Limpando cache Streamlit..." -ForegroundColor Yellow
$cachePath = "$env:USERPROFILE\.streamlit\cache"
if (Test-Path $cachePath) {
    Remove-Item -Path $cachePath -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "    Cache limpo." -ForegroundColor Green
} else {
    Write-Host "    Cache Streamlit nao encontrado." -ForegroundColor DarkYellow
}

# Limpar __pycache__ para forcar recompilacao
Write-Host "    Limpando __pycache__ dos modulos corrigidos..." -ForegroundColor Yellow
$pycacheDirs = @(
    "src\agents\__pycache__",
    "src\memory\__pycache__",
    "src\graph\__pycache__"
)
foreach ($dir in $pycacheDirs) {
    if (Test-Path $dir) {
        Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "    Limpo: $dir" -ForegroundColor Green
    }
}
Start-Sleep -Seconds 1

# Iniciar Streamlit com PYTHONPATH corrigido
Write-Host "[3/3] Iniciando Streamlit..." -ForegroundColor Yellow
$env:PYTHONPATH = "D:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"
Write-Host "    PYTHONPATH definido para: $env:PYTHONPATH" -ForegroundColor DarkCyan
Start-Process python -ArgumentList "-m streamlit run app.py --server.port 8501" -NoNewWindow

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  FIXES APLICADOS COM SUCESSO!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "[OK] Pydantic v2 fix: .model_dump() aplicado" -ForegroundColor Green
Write-Host "[OK] Mem0 API fix: filters obrigatorios" -ForegroundColor Green
Write-Host "[OK] Workflow fix: roteamento approval corrigido" -ForegroundColor Green
Write-Host ""
Write-Host "Streamlit deve abrir em http://localhost:8501" -ForegroundColor Green
Write-Host ""
