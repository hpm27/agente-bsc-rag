# Script wrapper para git commit que lida com pre-commit auto-corrections
# Execucao: .\scripts\git_commit.ps1 "mensagem do commit"

param(
    [Parameter(Mandatory=$true)]
    [string]$Message
)

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  GIT COMMIT COM PRE-COMMIT AUTO-CORRECTION" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$projectPath = "D:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"
Set-Location $projectPath

# Tentativa 1: Commit normal
Write-Host "[1/2] Tentando commit (pre-commit pode corrigir arquivos)..." -ForegroundColor Yellow
git add -A
$commitResult = git commit -m $Message 2>&1

# Verificar se falhou porque pre-commit modificou arquivos
if ($LASTEXITCODE -ne 0) {
    $output = $commitResult | Out-String

    if ($output -match "files were modified by this hook") {
        Write-Host "   [INFO] Pre-commit corrigiu arquivos automaticamente" -ForegroundColor Yellow
        Write-Host ""

        # Tentativa 2: Re-stage as correcoes e commit novamente
        Write-Host "[2/2] Re-adicionando correcoes e commitando novamente..." -ForegroundColor Yellow
        git add -u
        git commit -m $Message

        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "[OK] Commit realizado com sucesso!" -ForegroundColor Green
            Write-Host ""

            # Perguntar se quer fazer push
            $push = Read-Host "Deseja fazer push agora? (s/n)"
            if ($push -eq "s" -or $push -eq "S") {
                Write-Host ""
                Write-Host "[PUSH] Enviando para origin..." -ForegroundColor Cyan
                git push

                if ($LASTEXITCODE -eq 0) {
                    Write-Host "[OK] Push realizado com sucesso!" -ForegroundColor Green
                } else {
                    Write-Host "[ERRO] Falha no push" -ForegroundColor Red
                }
            }
        } else {
            Write-Host ""
            Write-Host "[ERRO] Commit falhou mesmo apos re-adicionar correcoes" -ForegroundColor Red
            Write-Host "Verifique os erros acima" -ForegroundColor Red
            exit 1
        }
    } else {
        # Erro diferente (não foi correção automática)
        Write-Host ""
        Write-Host "[ERRO] Commit falhou (não foi auto-correção)" -ForegroundColor Red
        Write-Host $output -ForegroundColor Red
        exit 1
    }
} else {
    # Commit passou na primeira tentativa
    Write-Host ""
    Write-Host "[OK] Commit realizado com sucesso (sem correcoes necessarias)!" -ForegroundColor Green
    Write-Host ""

    # Perguntar se quer fazer push
    $push = Read-Host "Deseja fazer push agora? (s/n)"
    if ($push -eq "s" -or $push -eq "S") {
        Write-Host ""
        Write-Host "[PUSH] Enviando para origin..." -ForegroundColor Cyan
        git push

        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Push realizado com sucesso!" -ForegroundColor Green
        } else {
            Write-Host "[ERRO] Falha no push" -ForegroundColor Red
        }
    }
}

Write-Host ""
