# Script simples para iniciar Streamlit
# Uso: .\scripts\start_streamlit.ps1

Write-Host ""
Write-Host "Iniciando BSC RAG Agent..." -ForegroundColor Green

# Configurar PYTHONPATH
$env:PYTHONPATH = "D:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"

# Iniciar aplicação
Start-Process python -ArgumentList "-m streamlit run app.py --server.port 8501" -NoNewWindow

Write-Host "Streamlit iniciado em: http://localhost:8501" -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor Gray
Write-Host ""
