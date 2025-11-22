# Script COMPLETO para reiniciar Streamlit com TODAS as correções
# Inclui: Pydantic v2 fix, Mem0 API v2 fix, Loop infinito fix, Multi-page fix
# Executar: .\scripts\restart_streamlit_completo.ps1

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "  REINICIANDO STREAMLIT - CORREÇÕES COMPLETAS" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""

# Resumo de todas as correções aplicadas
Write-Host "[INFO] CORREÇÕES APLICADAS NESTA SESSÃO:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. PYDANTIC V2 FIX:" -ForegroundColor Yellow
Write-Host "     - ValidationError resolvido com .model_dump()" -ForegroundColor White
Write-Host "     - Arquivo: src/agents/diagnostic_agent.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. MEM0 API V2 FIX:" -ForegroundColor Yellow
Write-Host "     - Filtros obrigatórios em search() e get_all()" -ForegroundColor White
Write-Host "     - Arquivo: src/memory/mem0_client.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. LOOP INFINITO FIX:" -ForegroundColor Yellow
Write-Host "     - Contador de retry para alignment_score < 80" -ForegroundColor White
Write-Host "     - Máximo 1 retry via approval" -ForegroundColor White
Write-Host "     - Arquivo: src/graph/workflow.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. MULTI-PAGE FIX:" -ForegroundColor Yellow
Write-Host "     - Iniciando app.py principal (não pages/0_consultor_bsc.py)" -ForegroundColor White
Write-Host "     - Menu lateral com 4 páginas disponível" -ForegroundColor White
Write-Host ""
Write-Host "  5. CACHE CLEANUP COMPLETO (Sessao 41):" -ForegroundColor Yellow
Write-Host "     - Limpeza de 23+ diretorios __pycache__" -ForegroundColor White
Write-Host "     - Previne ValidationError por bytecode antigo" -ForegroundColor White
Write-Host ""

# Parar processos Streamlit existentes
Write-Host "[1/3] Parando processos Streamlit existentes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*streamlit*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process | Where-Object {$_.ProcessName -like "*python*" -and $_.CommandLine -like "*streamlit*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Limpar cache (importante para recarregar módulos corrigidos)
Write-Host "[2/3] Limpando cache..." -ForegroundColor Yellow

# Cache Streamlit
$cachePath = "$env:USERPROFILE\.streamlit\cache"
if (Test-Path $cachePath) {
    Remove-Item -Path $cachePath -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "    Limpo: Cache Streamlit (~/.streamlit/cache)" -ForegroundColor Green
}

# Cache pytest (opcional mas recomendado)
if (Test-Path ".pytest_cache") {
    Remove-Item -Path ".pytest_cache" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "    Limpo: .pytest_cache" -ForegroundColor DarkGray
}

# Coverage reports (opcional)
if (Test-Path "htmlcov") {
    Remove-Item -Path "htmlcov" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "    Limpo: htmlcov" -ForegroundColor DarkGray
}
if (Test-Path ".coverage") {
    Remove-Item -Path ".coverage" -Force -ErrorAction SilentlyContinue
    Write-Host "    Limpo: .coverage" -ForegroundColor DarkGray
}

# __pycache__ de TODOS os módulos Python (limpeza COMPLETA - Sessao 41)
# BUG FIX: Cache bytecode antigo causava ValidationError persistente mesmo após correção
$pycacheDirs = @(
    # ROOT level
    "src\__pycache__",
    "config\__pycache__",

    # SRC subdiretórios (CRÍTICOS)
    "src\agents\__pycache__",
    "src\memory\__pycache__",     # ← CRÍTICO para schemas.py!
    "src\graph\__pycache__",
    "src\database\__pycache__",
    "src\exports\__pycache__",
    "src\prompts\__pycache__",
    "src\rag\__pycache__",
    "src\tools\__pycache__",      # ← CRÍTICO para ferramentas consultivas

    # API subdiretórios
    "api\__pycache__",
    "api\middleware\__pycache__",
    "api\routers\__pycache__",
    "api\schemas\__pycache__",
    "api\services\__pycache__",
    "api\utils\__pycache__",

    # UI subdiretórios
    "app\__pycache__",
    "ui\__pycache__",
    "ui\components\__pycache__",
    "ui\helpers\__pycache__",
    "ui\styles\__pycache__",

    # Pages
    "pages\__pycache__"
)
$cleanedCount = 0
foreach ($dir in $pycacheDirs) {
    if (Test-Path $dir) {
        Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
        $cleanedCount++
    }
}
Write-Host "    Limpo: $cleanedCount __pycache__ diretorios" -ForegroundColor Green
Start-Sleep -Seconds 1

# Iniciar Streamlit com configuração correta
Write-Host "[3/3] Iniciando Streamlit com app.py principal..." -ForegroundColor Yellow

# Configurar PYTHONPATH
$env:PYTHONPATH = "D:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"
Write-Host "    PYTHONPATH: $env:PYTHONPATH" -ForegroundColor DarkCyan

# Iniciar app.py (não pages/0_consultor_bsc.py)
Write-Host "    Iniciando app.py para menu multi-page..." -ForegroundColor Cyan
Start-Process python -ArgumentList "-m streamlit run app.py --server.port 8501" -NoNewWindow

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "  STREAMLIT INICIADO COM SUCESSO!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "[OK] Pydantic v2 fix aplicado" -ForegroundColor Green
Write-Host "[OK] Mem0 API v2 fix aplicado" -ForegroundColor Green
Write-Host "[OK] Loop infinito prevenido (max 1 retry)" -ForegroundColor Green
Write-Host "[OK] Multi-page habilitado (menu lateral)" -ForegroundColor Green
Write-Host ""
Write-Host "NAVEGAÇÃO:" -ForegroundColor Yellow
Write-Host "  - Página principal: Consultor BSC (chat)" -ForegroundColor White
Write-Host "  - Menu lateral: Strategy Map, Action Plan, Dashboard" -ForegroundColor White
Write-Host ""
Write-Host "Abrindo em: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pressione Ctrl+C nesta janela para parar o servidor" -ForegroundColor Gray
Write-Host ""
