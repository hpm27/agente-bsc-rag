# ===================================================================
# SCRIPT: Reset Completo para Teste - Parar Python + Limpar Cache
# ===================================================================
# 
# USO: .\reset_test.ps1
#
# O que faz:
# 1. Para TODOS os processos Python
# 2. Limpa __pycache__ 
# 3. Limpa .pyc files
# 4. Mostra instruções para reiniciar
#
# ===================================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  RESET COMPLETO - Parar Python + Limpar Cache" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ===== STEP 1: Parar processos Python =====
Write-Host "[1/3] Parando processos Python..." -ForegroundColor Yellow

$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    Write-Host "      Encontrados $($pythonProcesses.Count) processo(s) em execução" -ForegroundColor Gray
    
    foreach ($process in $pythonProcesses) {
        try {
            Stop-Process -Id $process.Id -Force -ErrorAction Stop
            Write-Host "      [OK] PID $($process.Id) parado" -ForegroundColor Green
        } catch {
            Write-Host "      [ERRO] Falha ao parar PID $($process.Id)" -ForegroundColor Red
        }
    }
} else {
    Write-Host "      [INFO] Nenhum processo Python em execução" -ForegroundColor Gray
}

Write-Host ""

# ===== STEP 2: Limpar __pycache__ =====
Write-Host "[2/3] Limpando __pycache__ directories..." -ForegroundColor Yellow

$pycacheDirs = Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue

if ($pycacheDirs) {
    $count = ($pycacheDirs | Measure-Object).Count
    $pycacheDirs | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "      [OK] $count directories removidos" -ForegroundColor Green
} else {
    Write-Host "      [INFO] Nenhum __pycache__ encontrado" -ForegroundColor Gray
}

Write-Host ""

# ===== STEP 3: Limpar .pyc files =====
Write-Host "[3/3] Limpando .pyc files..." -ForegroundColor Yellow

$pycFiles = Get-ChildItem -Path src, app, config, tests -Filter "*.pyc" -Recurse -ErrorAction SilentlyContinue

if ($pycFiles) {
    $count = ($pycFiles | Measure-Object).Count
    $pycFiles | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "      [OK] $count arquivos .pyc removidos" -ForegroundColor Green
} else {
    Write-Host "      [INFO] Nenhum .pyc encontrado" -ForegroundColor Gray
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  RESET COMPLETO!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "PRÓXIMO PASSO:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  streamlit run app\main.py" -ForegroundColor White
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

