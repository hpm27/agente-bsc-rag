# ===================================================================
# SCRIPT: Recriar Virtual Environment (venv) do Zero
# ===================================================================
#
# USO: .\recreate_venv.ps1
#
# O que faz:
# 1. Para todos processos Python
# 2. Deleta venv existente
# 3. Cria novo venv
# 4. Instala dependências do requirements.txt
#
# TEMPO ESTIMADO: 5-10 minutos (depende da velocidade da internet)
#
# ===================================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  RECRIAR VENV - Solução Extrema para Cache Persistente" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[AVISO] Este processo vai demorar 5-10 minutos!" -ForegroundColor Yellow
Write-Host ""

# Confirmar com usuário
$confirm = Read-Host "Deseja continuar? (S/N)"
if ($confirm -ne "S" -and $confirm -ne "s") {
    Write-Host "[CANCELADO] Operação cancelada pelo usuário" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ===== STEP 1: Parar processos Python =====
Write-Host "[1/4] Parando processos Python..." -ForegroundColor Yellow

$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    foreach ($process in $pythonProcesses) {
        try {
            Stop-Process -Id $process.Id -Force -ErrorAction Stop
            Write-Host "      [OK] Processo PID $($process.Id) parado" -ForegroundColor Green
        } catch {
            Write-Host "      [ERRO] Falha ao parar PID $($process.Id)" -ForegroundColor Red
        }
    }
} else {
    Write-Host "      [INFO] Nenhum processo Python em execução" -ForegroundColor Gray
}

Start-Sleep -Seconds 2
Write-Host ""

# ===== STEP 2: Deletar venv existente =====
Write-Host "[2/4] Deletando venv existente..." -ForegroundColor Yellow

if (Test-Path "venv") {
    try {
        Write-Host "      Removendo diretório venv (pode demorar)..." -ForegroundColor Gray
        Remove-Item -Path "venv" -Recurse -Force -ErrorAction Stop
        Write-Host "      [OK] venv deletado com sucesso" -ForegroundColor Green
    } catch {
        Write-Host "      [ERRO] Falha ao deletar venv: $_" -ForegroundColor Red
        Write-Host "      [DICA] Feche VSCode e tente novamente" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "      [INFO] venv não existe (OK)" -ForegroundColor Gray
}

Write-Host ""

# ===== STEP 3: Criar novo venv =====
Write-Host "[3/4] Criando novo venv..." -ForegroundColor Yellow

try {
    Write-Host "      Executando: python -m venv venv" -ForegroundColor Gray
    python -m venv venv

    if (Test-Path "venv\Scripts\python.exe") {
        Write-Host "      [OK] venv criado com sucesso" -ForegroundColor Green
    } else {
        throw "venv criado mas python.exe não encontrado"
    }
} catch {
    Write-Host "      [ERRO] Falha ao criar venv: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ===== STEP 4: Instalar dependências =====
Write-Host "[4/4] Instalando dependências do requirements.txt..." -ForegroundColor Yellow

if (Test-Path "requirements.txt") {
    try {
        Write-Host "      Ativando venv..." -ForegroundColor Gray
        & "venv\Scripts\Activate.ps1"

        Write-Host "      Atualizando pip..." -ForegroundColor Gray
        python -m pip install --upgrade pip --quiet

        Write-Host "      Instalando requirements.txt (pode demorar 5-10 min)..." -ForegroundColor Gray
        pip install -r requirements.txt

        Write-Host "      [OK] Dependências instaladas com sucesso" -ForegroundColor Green
    } catch {
        Write-Host "      [ERRO] Falha ao instalar dependências: $_" -ForegroundColor Red
        Write-Host "      [DICA] Tente manualmente: .\venv\Scripts\Activate.ps1; pip install -r requirements.txt" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "      [ERRO] requirements.txt não encontrado!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  VENV RECRIADO COM SUCESSO!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "PRÓXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Ativar venv:" -ForegroundColor White
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Iniciar Streamlit:" -ForegroundColor White
Write-Host "   streamlit run app\main.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
