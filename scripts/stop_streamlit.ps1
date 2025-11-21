# Script para FORÇAR parada de processos Streamlit
# Executar: .\scripts\stop_streamlit.ps1
# Usar quando Ctrl+C não funcionar

Write-Host ""
Write-Host "========================================" -ForegroundColor Red
Write-Host "  PARANDO STREAMLIT (FORÇA)" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""

# Parar processos Streamlit
Write-Host "[1/2] Buscando processos Streamlit..." -ForegroundColor Yellow

$streamlitProcs = Get-Process | Where-Object {$_.ProcessName -like "*streamlit*"}
$pythonProcs = Get-Process | Where-Object {$_.ProcessName -eq "python" -or $_.ProcessName -eq "pythonw"}

$totalProcs = ($streamlitProcs | Measure-Object).Count + ($pythonProcs | Measure-Object).Count

if ($totalProcs -eq 0) {
    Write-Host ""
    Write-Host "[INFO] Nenhum processo Streamlit encontrado" -ForegroundColor Green
    Write-Host ""
    exit 0
}

Write-Host "   Encontrados: $totalProcs processos" -ForegroundColor Cyan
Write-Host ""
Write-Host "[2/2] Parando processos..." -ForegroundColor Yellow

# Parar processos Streamlit específicos
if ($streamlitProcs) {
    $streamlitProcs | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "   [OK] Processos streamlit* parados" -ForegroundColor Green
}

# Parar processos Python (mais agressivo)
if ($pythonProcs) {
    foreach ($proc in $pythonProcs) {
        try {
            $cmdLine = $proc.CommandLine
            if ($cmdLine -like "*streamlit*") {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                Write-Host "   [OK] Python PID $($proc.Id) parado" -ForegroundColor Green
            }
        } catch {
            # Sem CommandLine disponível, parar se for python
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "   [OK] Python PID $($proc.Id) parado (fallback)" -ForegroundColor DarkGray
        }
    }
}

# Aguardar processos finalizarem
Start-Sleep -Seconds 2

# Verificar se ainda há processos rodando
$remaining = Get-Process | Where-Object {$_.ProcessName -like "*streamlit*" -or ($_.ProcessName -eq "python" -and $_.CommandLine -like "*streamlit*")}
$remainingCount = ($remaining | Measure-Object).Count

Write-Host ""
if ($remainingCount -eq 0) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  STREAMLIT PARADO COM SUCESSO!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  AVISO: $remainingCount processos restantes" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Tente fechar manualmente ou reiniciar o terminal" -ForegroundColor Gray
}
Write-Host ""
