# ===================================================================
# SCRIPT DE FORCE RELOAD DE MÓDULOS PYTHON + STREAMLIT
# ===================================================================
# 
# PROBLEMA: Python mantém módulos em sys.modules na memória
# SOLUÇÃO: Deletar sys.modules + Limpar cache + Reiniciar Python
#
# USO: 
# 1. PARE o Streamlit completamente (Ctrl+C)
# 2. Execute: .\force_reload_modules.ps1
# 3. Reinicie Streamlit: streamlit run app\main.py
#
# ===================================================================

Write-Host "[START] Force Reload - Limpeza Agressiva de Cache Python + Streamlit" -ForegroundColor Yellow
Write-Host ""

# Step 1: Limpar __pycache__ directories
Write-Host "[1/6] Removendo __pycache__ directories..." -ForegroundColor Cyan
Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "   [OK] __pycache__ removidos" -ForegroundColor Green
Write-Host ""

# Step 2: Limpar .pyc files soltos
Write-Host "[2/6] Removendo .pyc files soltos..." -ForegroundColor Cyan
Get-ChildItem -Path src, app, config, tests -Filter "*.pyc" -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "   [OK] .pyc files removidos" -ForegroundColor Green
Write-Host ""

# Step 3: Limpar Streamlit cache
Write-Host "[3/6] Removendo Streamlit cache..." -ForegroundColor Cyan
if (Test-Path ".streamlit") {
    Remove-Item ".streamlit" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "   [OK] .streamlit cache removido" -ForegroundColor Green
} else {
    Write-Host "   [INFO] .streamlit nao existe (OK)" -ForegroundColor Gray
}
Write-Host ""

# Step 4: Limpar LangGraph checkpoints (podem ter estado antigo serializado)
Write-Host "[4/6] Removendo LangGraph checkpoints..." -ForegroundColor Cyan
if (Test-Path ".langgraph") {
    Remove-Item ".langgraph" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "   [OK] .langgraph checkpoints removidos" -ForegroundColor Green
} else {
    Write-Host "   [INFO] .langgraph nao existe (OK)" -ForegroundColor Gray
}
Write-Host ""

# Step 5: Criar script Python para forçar reload
Write-Host "[5/6] Criando script Python para force reload sys.modules..." -ForegroundColor Cyan
$pythonScript = @"
import sys
import os

# Módulos críticos do projeto que DEVEM ser deletados do cache
critical_modules = [
    'src.agents.diagnostic_agent',
    'src.agents.orchestrator',
    'src.agents.financial_agent',
    'src.agents.customer_agent',
    'src.agents.process_agent',
    'src.agents.learning_agent',
    'src.agents.onboarding_agent',
    'src.agents.client_profile_agent',
    'src.agents.judge_agent',
    'src.graph.workflow',
    'src.graph.consulting_orchestrator',
    'src.graph.states',
    'src.memory.schemas',
    'src.memory.mem0_client',
    'app.main',
    'app.components.results',
    'app.components.sidebar',
]

deleted_count = 0
print('[PYTHON] Deletando módulos críticos de sys.modules...')
for module_name in critical_modules:
    if module_name in sys.modules:
        del sys.modules[module_name]
        deleted_count += 1
        print(f'   [DEL] {module_name}')

# Deletar TODOS os módulos src.* (garantir limpeza completa)
src_modules = [name for name in sys.modules.keys() if name.startswith('src.') or name.startswith('app.')]
for module_name in src_modules:
    if module_name not in critical_modules:  # Evitar duplicatas
        del sys.modules[module_name]
        deleted_count += 1
        print(f'   [DEL] {module_name}')

print(f'[OK] {deleted_count} módulos deletados de sys.modules')
print('[INFO] Próximo: Reinicie Streamlit para reimportar módulos LIMPOS')
"@

$pythonScript | Out-File -FilePath "temp_force_reload.py" -Encoding UTF8
Write-Host "   [OK] Script Python criado" -ForegroundColor Green
Write-Host ""

# Step 6: Executar script Python
Write-Host "[6/6] Executando force reload em Python..." -ForegroundColor Cyan
python temp_force_reload.py
Write-Host ""

# Cleanup: Remover script temporário
Remove-Item "temp_force_reload.py" -Force -ErrorAction SilentlyContinue

Write-Host "[COMPLETE] Force Reload Completo!" -ForegroundColor Green
Write-Host ""
Write-Host "===================================================================" -ForegroundColor Yellow
Write-Host "PRÓXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host "1. Reinicie Streamlit: streamlit run app\main.py" -ForegroundColor White
Write-Host "2. Verifique o log por: 🚀🚀🚀 [DIAGNOSTIC v2.1..." -ForegroundColor White
Write-Host "3. Se log NÃO aparecer, problema é mais profundo (ver opções below)" -ForegroundColor White
Write-Host "===================================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "TROUBLESHOOTING EXTREMO (se ainda falhar):" -ForegroundColor Red
Write-Host "- Opção A: Fechar VSCode/IDE completamente + Reabrir" -ForegroundColor White
Write-Host "- Opção B: Deletar venv e recriar (pip install -r requirements.txt)" -ForegroundColor White  
Write-Host "- Opção C: Reiniciar máquina (último recurso)" -ForegroundColor White
Write-Host ""

