# Quick commit script - adiciona tudo e commita com retry automatico
# Uso: .\scripts\git_quick_commit.ps1

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  QUICK COMMIT (AUTO-RETRY PRE-COMMIT)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$projectPath = "D:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"
Set-Location $projectPath

# Status
Write-Host "[STATUS] Arquivos modificados:" -ForegroundColor Yellow
git status --short
Write-Host ""

# Mensagem do commit
$message = Read-Host "Mensagem do commit"

if ([string]::IsNullOrWhiteSpace($message)) {
    Write-Host "[ERRO] Mensagem vazia!" -ForegroundColor Red
    exit 1
}

# Loop de retry (máximo 3 tentativas)
$maxRetries = 3
$attempt = 1

while ($attempt -le $maxRetries) {
    Write-Host "[TENTATIVA $attempt/$maxRetries] Commitando..." -ForegroundColor Yellow

    git add -A
    git commit -m $message 2>&1 | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[OK] Commit realizado com sucesso!" -ForegroundColor Green
        Write-Host ""

        # Push automático
        $push = Read-Host "Push agora? (s/n)"
        if ($push -eq "s" -or $push -eq "S") {
            git push
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[OK] Push concluido!" -ForegroundColor Green
            }
        }
        break
    } else {
        Write-Host "   [INFO] Pre-commit corrigiu arquivos, re-tentando..." -ForegroundColor Yellow
        $attempt++

        if ($attempt -gt $maxRetries) {
            Write-Host ""
            Write-Host "[ERRO] Falhou apos $maxRetries tentativas" -ForegroundColor Red
            Write-Host "Execute manualmente: git commit -m ""sua mensagem""" -ForegroundColor Yellow
            exit 1
        }
    }
}

Write-Host ""
