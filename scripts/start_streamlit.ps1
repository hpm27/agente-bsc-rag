# Script simplificado para iniciar Streamlit (RESPONDE A Ctrl+C)
# Executar: .\scripts\start_streamlit.ps1

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  STREAMLIT - BSC RAG AGENT" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Navegar para o diretório do projeto
$projectPath = "D:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"
Set-Location $projectPath

# Configurar PYTHONPATH
$env:PYTHONPATH = $projectPath

Write-Host "[INFO] Diretório: $projectPath" -ForegroundColor Cyan
Write-Host "[INFO] PYTHONPATH configurado" -ForegroundColor Cyan
Write-Host ""
Write-Host "Iniciando Streamlit..." -ForegroundColor Yellow
Write-Host ""
Write-Host "URL: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "[CTRL+C] Pressione Ctrl+C para parar" -ForegroundColor Gray
Write-Host ""

# Executar em FOREGROUND (permite Ctrl+C)
python -m streamlit run app.py
