# ============================================
# Script de Setup Automatico - Agente BSC RAG
# ============================================

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "[SETUP] Agente BSC RAG - Setup Automatico" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Verificar Python
Write-Host "[CHECK] Verificando Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Python nao encontrado! Instale Python 3.10+ primeiro." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] $pythonVersion" -ForegroundColor Green

# Verificar Docker
Write-Host "`n[CHECK] Verificando Docker..." -ForegroundColor Yellow
$dockerVersion = docker --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Docker nao encontrado! Instale Docker Desktop primeiro." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] $dockerVersion" -ForegroundColor Green

# Passo 1: Criar Ambiente Virtual
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "[PASSO 1] Criando Ambiente Virtual" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

if (Test-Path "venv") {
    Write-Host "[WARN] Ambiente virtual ja existe. Deseja recriar? (s/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq 's' -or $response -eq 'S') {
        Write-Host "[INFO] Removendo ambiente antigo..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force venv
        python -m venv venv
        Write-Host "[OK] Ambiente virtual recriado" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Pulando criacao do ambiente virtual" -ForegroundColor Yellow
    }
} else {
    python -m venv venv
    Write-Host "[OK] Ambiente virtual criado" -ForegroundColor Green
}

# Ativar ambiente virtual
Write-Host "`n[INFO] Ativando ambiente virtual..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Passo 2: Instalar Dependencias
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "[PASSO 2] Instalando Dependencias" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

Write-Host "`n[INFO] Atualizando pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

Write-Host "`n[INFO] Instalando dependencias essenciais..." -ForegroundColor Yellow
pip install loguru pydantic pydantic-settings python-dotenv --quiet
Write-Host "[OK] Dependencias essenciais instaladas" -ForegroundColor Green

Write-Host "`n[INFO] Instalando LangChain e LangGraph..." -ForegroundColor Yellow
pip install langchain langchain-openai langchain-community langchain-core langgraph --quiet
Write-Host "[OK] LangChain instalado" -ForegroundColor Green

Write-Host "`n[INFO] Instalando APIs (OpenAI, Cohere, Anthropic)..." -ForegroundColor Yellow
pip install openai cohere anthropic --quiet
Write-Host "[OK] APIs instaladas" -ForegroundColor Green

Write-Host "`n[INFO] Instalando Vector Databases..." -ForegroundColor Yellow
pip install redis redis-om qdrant-client weaviate-client --quiet
Write-Host "[OK] Vector DBs instalados" -ForegroundColor Green

Write-Host "`n[INFO] Instalando ferramentas de teste..." -ForegroundColor Yellow
pip install pytest pytest-asyncio pytest-cov pytest-mock --quiet
Write-Host "[OK] Ferramentas de teste instaladas" -ForegroundColor Green

Write-Host "`n[INFO] Instalando processamento de documentos..." -ForegroundColor Yellow
pip install pypdf python-docx beautifulsoup4 lxml --quiet
Write-Host "[OK] Processamento de documentos instalado" -ForegroundColor Green

# Passo 3: Configurar .env
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "[PASSO 3] Configurando Variaveis de Ambiente" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

if (Test-Path ".env") {
    Write-Host "[WARN] Arquivo .env ja existe!" -ForegroundColor Yellow
    Write-Host "[INFO] Mantendo configuracoes existentes..." -ForegroundColor Yellow
} else {
    Write-Host "`n[INFO] Criando arquivo .env..." -ForegroundColor Yellow
    Write-Host "`n[WARN] IMPORTANTE: Voce precisara adicionar suas API keys!" -ForegroundColor Yellow
    Write-Host "   1. OpenAI API Key (OBRIGATORIO)" -ForegroundColor White
    Write-Host "   2. Cohere API Key (OBRIGATORIO)" -ForegroundColor White
    Write-Host "   3. Anthropic API Key (OPCIONAL)" -ForegroundColor White
    
    @"
# OpenAI (OBRIGATORIO)
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# Cohere (OBRIGATORIO)
COHERE_API_KEY=your-cohere-key-here

# Anthropic (OPCIONAL)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Vector Store
VECTOR_STORE_TYPE=qdrant
VECTOR_STORE_INDEX=bsc_documents

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Weaviate
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080

# RAG Config
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=10
TOP_N_RERANK=5
HYBRID_SEARCH_WEIGHT_SEMANTIC=0.7
HYBRID_SEARCH_WEIGHT_BM25=0.3

# Contextual Retrieval
ENABLE_CONTEXTUAL_RETRIEVAL=true
CONTEXTUAL_MODEL=claude-3-5-sonnet-20241022
CONTEXTUAL_CACHE_ENABLED=true

# Agents
MAX_ITERATIONS=10
TEMPERATURE=0.0
MAX_TOKENS=2000

# Paths
DATA_DIR=./data
LITERATURE_DIR=./data/bsc_literature
MODELS_DIR=./models
LOGS_DIR=./logs

# Monitoring
ENABLE_METRICS=true
DEBUG=false
LOG_LEVEL=INFO
"@ | Out-File -FilePath ".env" -Encoding UTF8
    
    Write-Host "`n[OK] Arquivo .env criado" -ForegroundColor Green
    Write-Host "[WARN] ATENCAO: Edite o arquivo .env e adicione suas API keys!" -ForegroundColor Yellow
}

# Passo 4: Criar Diretorios
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "[PASSO 4] Criando Estrutura de Diretorios" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$directories = @("data", "data/bsc_literature", "models", "logs")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "[OK] Criado: $dir" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Ja existe: $dir" -ForegroundColor Yellow
    }
}

# Passo 5: Docker Compose
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "[PASSO 5] Iniciando Servicos Docker" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

Write-Host "`n[INFO] Deseja iniciar os servicos Docker agora? (S/n)" -ForegroundColor Yellow
$response = Read-Host
if ($response -ne 'n' -and $response -ne 'N') {
    Write-Host "`n[INFO] Iniciando containers..." -ForegroundColor Yellow
    docker-compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n[OK] Servicos Docker iniciados com sucesso!" -ForegroundColor Green
        Write-Host "`n[INFO] Status dos servicos:" -ForegroundColor Cyan
        docker-compose ps
    } else {
        Write-Host "`n[ERRO] Erro ao iniciar Docker. Verifique se o Docker Desktop esta rodando." -ForegroundColor Red
    }
} else {
    Write-Host "[INFO] Pulando inicializacao do Docker" -ForegroundColor Yellow
    Write-Host "   Execute manualmente: docker-compose up -d" -ForegroundColor White
}

# Resumo Final
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "[OK] Setup Completo!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan

Write-Host "`n[INFO] Proximos Passos:" -ForegroundColor Yellow
Write-Host "   1. Edite o arquivo .env com suas API keys" -ForegroundColor White
Write-Host "   2. Adicione PDFs BSC em data/bsc_literature/" -ForegroundColor White
Write-Host "   3. Rode os testes: pytest tests/ -v" -ForegroundColor White
Write-Host "   4. Execute ingestao: python scripts/build_knowledge_base.py" -ForegroundColor White

Write-Host "`n[INFO] Links Uteis:" -ForegroundColor Yellow
Write-Host "   - Qdrant: http://localhost:6333" -ForegroundColor White
Write-Host "   - Weaviate: http://localhost:8080" -ForegroundColor White
Write-Host "   - Documentacao: SETUP.md" -ForegroundColor White

Write-Host "`n[INFO] Dica: Leia o arquivo SETUP.md para detalhes completos!" -ForegroundColor Cyan
Write-Host "`n============================================`n" -ForegroundColor Cyan
