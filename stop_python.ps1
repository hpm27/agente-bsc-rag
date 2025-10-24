# ===================================================================
# SCRIPT: Parar TODOS os processos Python
# ===================================================================
# 
# USO: .\stop_python.ps1
#
# O que faz:
# - Para TODOS os processos python.exe em execução
# - Útil para forçar reload de código em Streamlit
#
# ===================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  PARANDO PROCESSOS PYTHON" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# Buscar processos Python (inclui variações comuns)
$pythonProcesses = Get-Process -Name python, python3, pythonw -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    Write-Host "[INFO] Encontrados $($pythonProcesses.Count) processo(s) Python em execução" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($process in $pythonProcesses) {
        $processId = $process.Id
        Write-Host "[KILL] Parando processo Python (PID: $processId)..." -ForegroundColor Red

        # Revalida se o processo ainda existe (pode ter encerrado entre o Get-Process e o Stop-Process)
        $stillRunning = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if (-not $stillRunning) {
            Write-Host "   [INFO] Processo PID $processId já não existe. Ignorando." -ForegroundColor Gray
            continue
        }

        try {
            Stop-Process -Id $processId -Force -ErrorAction Stop
            Write-Host "   [OK] Processo PID $processId parado com sucesso" -ForegroundColor Green
        } catch {
            # Caso o processo tenha terminado entre a verificação e o Stop-Process, tratar como sucesso
            if ($_.Exception -and ($_.Exception.Message -match "Cannot find a process with the process identifier")) {
                Write-Host "   [OK] Processo PID $processId já finalizado." -ForegroundColor Green
            } else {
                Write-Host ("   [ERRO] Falha ao parar processo PID {0}: {1}" -f $processId, $_.Exception.Message) -ForegroundColor Red
            }
        }
    }
    
    Write-Host ""
    Write-Host "[SUCCESS] Todos os processos Python foram parados!" -ForegroundColor Green
    
} else {
    Write-Host "[INFO] Nenhum processo Python em execução" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  CONCLUÍDO" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

