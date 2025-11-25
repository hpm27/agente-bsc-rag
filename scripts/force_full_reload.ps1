# ===================================================================
# FORCE FULL RELOAD - Mata Python, limpa cache, reinicia Streamlit
# ===================================================================
#
# Este script resolve problemas de cache de módulos Python em Streamlit.
# Força reload completo do código atualizado.
#
# USO: .\force_full_reload.ps1
# ===================================================================

Write-Host "[START] Forçando reload completo do sistema..." -ForegroundColor Cyan

# STEP 1: Matar TODOS os processos Python e Streamlit
Write-Host "`n[STEP 1] Matando todos os processos Python e Streamlit..." -ForegroundColor Yellow

$pythonProcesses = Get-Process -Name python, pythonw, streamlit -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    $pythonProcesses | ForEach-Object {
        Write-Host "  [KILL] PID $($_.Id) - $($_.ProcessName)" -ForegroundColor Red
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }

    # Aguardar 2 segundos para garantir que processos foram terminados
    Write-Host "  [WAIT] Aguardando 2 segundos..." -ForegroundColor Gray
    Start-Sleep -Seconds 2

    Write-Host "  [OK] $($pythonProcesses.Count) processos terminados" -ForegroundColor Green
} else {
    Write-Host "  [INFO] Nenhum processo Python/Streamlit encontrado" -ForegroundColor Gray
}

# STEP 2: Limpar TODOS os caches Python
Write-Host "`n[STEP 2] Limpando caches Python..." -ForegroundColor Yellow

# 2.1: Remover __pycache__ recursivamente
Write-Host "  [CACHE] Removendo __pycache__ directories..." -ForegroundColor Gray
Get-ChildItem -Path . -Recurse -Directory -Filter __pycache__ -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "    [DELETE] $($_.FullName)" -ForegroundColor DarkGray
    Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
}

# 2.2: Remover arquivos .pyc
Write-Host "  [CACHE] Removendo arquivos .pyc..." -ForegroundColor Gray
Get-ChildItem -Path . -Recurse -File -Filter *.pyc -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "    [DELETE] $($_.FullName)" -ForegroundColor DarkGray
    Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
}

# 2.3: Limpar Streamlit cache (se existir)
$streamlitCache = ".streamlit/cache"
if (Test-Path $streamlitCache) {
    Write-Host "  [CACHE] Limpando Streamlit cache..." -ForegroundColor Gray
    Remove-Item -Path $streamlitCache -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "    [DELETE] $streamlitCache" -ForegroundColor DarkGray
}

Write-Host "  [OK] Caches limpos" -ForegroundColor Green

# STEP 3: Verificar código v3.2 está no arquivo
Write-Host "`n[STEP 3] Verificando versão do código..." -ForegroundColor Yellow

$diagnosticFile = "src\agents\diagnostic_agent.py"
if (Test-Path $diagnosticFile) {
    $v32Count = (Select-String -Path $diagnosticFile -Pattern "DIAGNOSTIC v3\.2" -AllMatches).Matches.Count

    if ($v32Count -gt 0) {
        Write-Host "  [OK] Código v3.2 encontrado ($v32Count occorrências)" -ForegroundColor Green
    } else {
        Write-Host "  [ERRO] Código v3.2 NÃO encontrado! Arquivo não foi salvo corretamente." -ForegroundColor Red
        Write-Host "  [HINT] Verifique se as alterações foram salvas no Cursor." -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "  [ERRO] Arquivo $diagnosticFile não encontrado!" -ForegroundColor Red
    exit 1
}

# STEP 4: Aguardar confirmação do usuário antes de reiniciar
Write-Host "`n[STEP 4] Reiniciando Streamlit..." -ForegroundColor Yellow
Write-Host "  [INFO] Streamlit será iniciado em 3 segundos..." -ForegroundColor Gray
Write-Host "  [INFO] Pressione Ctrl+C para cancelar." -ForegroundColor Gray

Start-Sleep -Seconds 3

# STEP 5: Reiniciar Streamlit em nova janela
Write-Host "`n[STEP 5] Iniciando Streamlit em nova janela..." -ForegroundColor Yellow

# Ativar venv (se necessário)
$venvActivate = "venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    Write-Host "  [VENV] Ativando virtual environment..." -ForegroundColor Gray
}

# Iniciar Streamlit em nova janela PowerShell
$streamlitCommand = @"
& '$venvActivate'
python run_streamlit.py
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $streamlitCommand

Write-Host "  [OK] Streamlit iniciado em nova janela" -ForegroundColor Green

# STEP 6: Instruções finais
Write-Host "`n[SUCCESS] Reload completo concluído!" -ForegroundColor Green
Write-Host "`n==================================================================" -ForegroundColor Cyan
Write-Host "PRÓXIMOS PASSOS:" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "1. Aguarde Streamlit carregar na nova janela (15-30 segundos)" -ForegroundColor White
Write-Host "2. Abra http://localhost:8501 no navegador" -ForegroundColor White
Write-Host "3. Procure nos logs por:" -ForegroundColor White
Write-Host "   - [APP v3.2-20251021-19:20]" -ForegroundColor Yellow
Write-Host "   - [ORCHESTRATOR v3.2-20251021-19:20]" -ForegroundColor Yellow
Write-Host "   - [DIAGNOSTIC v3.2-20251021-19:20]" -ForegroundColor Yellow
Write-Host "   - [DIAGNOSTIC v3.2 PRINT]" -ForegroundColor Yellow
Write-Host "`n4. Se os logs v3.2 NÃO aparecerem, PARE e reporte o problema." -ForegroundColor Red
Write-Host "==================================================================" -ForegroundColor Cyan

exit 0
