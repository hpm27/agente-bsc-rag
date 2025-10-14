# 🚀 Guia de Deployment - Agente BSC RAG

> Deploy do sistema BSC RAG em ambientes local, Docker e cloud (AWS/Azure/GCP)

---

## 📋 Índice

- [Pré-requisitos de Produção](#pré-requisitos-de-produção)
- [Opção 1: Deploy Local](#opção-1-deploy-local)
- [Opção 2: Deploy com Docker](#opção-2-deploy-com-docker)
- [Opção 3: Deploy em Cloud](#opção-3-deploy-em-cloud)
- [Configuração de Produção](#configuração-de-produção)
- [Monitoramento e Logs](#monitoramento-e-logs)
- [Backup e Disaster Recovery](#backup-e-disaster-recovery)
- [Escalabilidade](#escalabilidade)
- [Segurança](#segurança)
- [Custos Estimados](#custos-estimados)

---

## 🛠️ Pré-requisitos de Produção

### Recursos Mínimos Recomendados

| Componente | Mínimo | Recomendado | Produção |
|------------|--------|-------------|----------|
| **CPU** | 2 cores | 4 cores | 8+ cores |
| **RAM** | 8 GB | 16 GB | 32+ GB |
| **Disco (SSD)** | 50 GB | 100 GB | 200+ GB |
| **Rede** | 10 Mbps | 100 Mbps | 1 Gbps |

### Software Necessário

- ✅ **Python 3.12+**
- ✅ **Docker 24.0+** (para Qdrant)
- ✅ **Docker Compose 2.20+**
- ✅ **Git**
- ✅ **HTTPS/SSL** (Let's Encrypt recomendado)

### API Keys

- ✅ **OpenAI API Key** (tier 2+ recomendado para produção)
- ✅ **Cohere API Key** (Trial ou Production)
- ✅ **Anthropic API Key** (tier 2+ recomendado)

💡 **Dica**: Configure rate limits adequados para produção.

---

## 🖥️ Opção 1: Deploy Local

Deploy em servidor Linux/Windows físico ou VM.

### Ubuntu/Debian

#### 1. Preparar Servidor

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y python3.12 python3.12-venv python3-pip git curl

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker
```

#### 2. Clonar e Configurar Projeto

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/agente-bsc-rag.git
cd agente-bsc-rag

# Criar ambiente virtual
python3.12 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

#### 3. Configurar Variáveis de Ambiente

```bash
# Copiar template
cp .env.example .env

# Editar .env
nano .env
```

**Configurações de Produção**:

```env
# APIs
OPENAI_API_KEY=sk-proj-...
COHERE_API_KEY=...
ANTHROPIC_API_KEY=sk-ant-...

# Vector Store
VECTOR_STORE_TYPE=qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Cache
ENABLE_EMBEDDING_CACHE=true
EMBEDDING_CACHE_DIR=/var/cache/agente-bsc/embeddings

# Performance
AGENT_MAX_WORKERS=4

# Logs
LOG_LEVEL=INFO
LOG_FILE=/var/log/agente-bsc/app.log
```

#### 4. Iniciar Qdrant

```bash
# Criar volume persistente
docker volume create qdrant_data

# Iniciar Qdrant
docker run -d \
  --name qdrant \
  --restart unless-stopped \
  -p 6333:6333 \
  -v qdrant_data:/qdrant/storage \
  qdrant/qdrant:v1.11.3
```

#### 5. Indexar Dataset BSC

```bash
source venv/bin/activate
python scripts/build_knowledge_base.py
```

#### 6. Criar Serviço systemd

```bash
# Criar arquivo de serviço
sudo nano /etc/systemd/system/agente-bsc.service
```

**Conteúdo do arquivo**:

```ini
[Unit]
Description=Agente BSC RAG - Streamlit Interface
After=network.target docker.service qdrant.service
Requires=docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/agente-bsc-rag
Environment="PATH=/home/ubuntu/agente-bsc-rag/venv/bin"
ExecStart=/home/ubuntu/agente-bsc-rag/venv/bin/streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10
StandardOutput=append:/var/log/agente-bsc/app.log
StandardError=append:/var/log/agente-bsc/error.log

[Install]
WantedBy=multi-user.target
```

#### 7. Ativar e Iniciar Serviço

```bash
# Criar diretório de logs
sudo mkdir -p /var/log/agente-bsc
sudo chown ubuntu:ubuntu /var/log/agente-bsc

# Recarregar systemd
sudo systemctl daemon-reload

# Ativar serviço (iniciar no boot)
sudo systemctl enable agente-bsc

# Iniciar serviço
sudo systemctl start agente-bsc

# Verificar status
sudo systemctl status agente-bsc
```

#### 8. Configurar Nginx (Reverse Proxy + HTTPS)

```bash
# Instalar Nginx
sudo apt install -y nginx certbot python3-certbot-nginx

# Criar configuração
sudo nano /etc/nginx/sites-available/agente-bsc
```

**Configuração Nginx**:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    # Redirecionar HTTP → HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com;

    # SSL (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Logs
    access_log /var/log/nginx/agente-bsc-access.log;
    error_log /var/log/nginx/agente-bsc-error.log;

    # Proxy para Streamlit
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (para Streamlit)
        proxy_read_timeout 86400;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
```

**Ativar configuração**:

```bash
# Criar link simbólico
sudo ln -s /etc/nginx/sites-available/agente-bsc /etc/nginx/sites-enabled/

# Testar configuração
sudo nginx -t

# Gerar certificado SSL (Let's Encrypt)
sudo certbot --nginx -d seu-dominio.com

# Reiniciar Nginx
sudo systemctl restart nginx
```

#### 9. Verificar Deploy

```bash
# Verificar serviço
sudo systemctl status agente-bsc

# Verificar logs
sudo journalctl -u agente-bsc -f

# Testar endpoint
curl https://seu-dominio.com/health
```

✅ **Deploy completo!** Acesse: `https://seu-dominio.com`

---

## 🐳 Opção 2: Deploy com Docker

Deploy completo usando Docker Compose.

### 1. Dockerfile Otimizado (Multi-Stage)

Crie `Dockerfile.prod`:

```dockerfile
# ==============================================================================
# Stage 1: Builder - Instalar dependências
# ==============================================================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Instalar dependências de sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==============================================================================
# Stage 2: Runtime - Aplicação
# ==============================================================================
FROM python:3.12-slim

WORKDIR /app

# Copiar dependências instaladas do builder
COPY --from=builder /root/.local /root/.local

# Atualizar PATH
ENV PATH=/root/.local/bin:$PATH

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p logs data/bsc_literature .cache/embeddings

# Expor porta Streamlit
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/health || exit 1

# Comando de inicialização
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. Docker Compose para Produção

Crie `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  # Qdrant Vector Database
  qdrant:
    image: qdrant/qdrant:v1.11.3
    container_name: agente-bsc-qdrant
    restart: unless-stopped
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
    networks:
      - bsc-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Aplicação BSC RAG
  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: agente-bsc-app
    restart: unless-stopped
    ports:
      - "8501:8501"
    depends_on:
      qdrant:
        condition: service_healthy
    env_file:
      - .env
    environment:
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
    volumes:
      - app_logs:/app/logs
      - embedding_cache:/app/.cache/embeddings
      - ./data/bsc_literature:/app/data/bsc_literature:ro
    networks:
      - bsc-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # Nginx Reverse Proxy (Opcional)
  nginx:
    image: nginx:alpine
    container_name: agente-bsc-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - nginx_logs:/var/log/nginx
    depends_on:
      - app
    networks:
      - bsc-network

volumes:
  qdrant_data:
    driver: local
  app_logs:
    driver: local
  embedding_cache:
    driver: local
  nginx_logs:
    driver: local

networks:
  bsc-network:
    driver: bridge
```

### 3. Build e Deploy

```bash
# Build da imagem
docker-compose -f docker-compose.prod.yml build

# Iniciar serviços
docker-compose -f docker-compose.prod.yml up -d

# Verificar logs
docker-compose -f docker-compose.prod.yml logs -f app

# Verificar status
docker-compose -f docker-compose.prod.yml ps
```

### 4. Indexar Dataset (Container)

```bash
# Executar indexação dentro do container
docker exec -it agente-bsc-app python scripts/build_knowledge_base.py
```

### 5. Comandos Úteis

```bash
# Parar serviços
docker-compose -f docker-compose.prod.yml down

# Reiniciar aplicação
docker-compose -f docker-compose.prod.yml restart app

# Ver logs em tempo real
docker-compose -f docker-compose.prod.yml logs -f

# Backup Qdrant
docker exec agente-bsc-qdrant tar czf /backup.tar.gz /qdrant/storage
docker cp agente-bsc-qdrant:/backup.tar.gz ./qdrant_backup_$(date +%Y%m%d).tar.gz

# Restore Qdrant
docker cp qdrant_backup_20251014.tar.gz agente-bsc-qdrant:/backup.tar.gz
docker exec agente-bsc-qdrant tar xzf /backup.tar.gz -C /
```

---

## ☁️ Opção 3: Deploy em Cloud

### AWS (Amazon Web Services)

#### Arquitetura Recomendada

```
┌─────────────────────────────────────────────┐
│          Route 53 (DNS)                     │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│   Application Load Balancer (ALB)          │
│   - HTTPS (certificado ACM)                 │
│   - Health checks                           │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│     Auto Scaling Group                      │
│  ┌────────────┐      ┌────────────┐         │
│  │  EC2 #1    │      │  EC2 #2    │         │
│  │  t3.large  │      │  t3.large  │         │
│  └────────────┘      └────────────┘         │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│       ECS (Qdrant Container)                │
│       ou EC2 dedicado para Qdrant           │
└─────────────────────────────────────────────┘
```

#### 1. EC2 Instance Setup

```bash
# Conectar via SSH
ssh -i sua-chave.pem ubuntu@ec2-xx-xxx-xxx-xx.compute-1.amazonaws.com

# Seguir passos de Deploy Local (Ubuntu)
# ... (ver Opção 1)
```

**Tipo de Instance Recomendado**:

| Uso | Instance Type | vCPU | RAM | Custo/mês (US East) |
|-----|---------------|------|-----|---------------------|
| Dev/Test | t3.medium | 2 | 4 GB | ~$30 |
| Produção Pequena | t3.large | 2 | 8 GB | ~$60 |
| Produção Média | t3.xlarge | 4 | 16 GB | ~$120 |
| Produção Grande | t3.2xlarge | 8 | 32 GB | ~$240 |

#### 2. RDS para Metadata (Opcional)

Se precisar de BD relacional para metadata:

```bash
# PostgreSQL RDS
aws rds create-db-instance \
    --db-instance-identifier agente-bsc-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username admin \
    --master-user-password SuaSenhaSegura123 \
    --allocated-storage 20
```

#### 3. S3 para Backups

```bash
# Criar bucket
aws s3 mb s3://agente-bsc-backups

# Backup automático do Qdrant
#!/bin/bash
DATE=$(date +%Y%m%d-%H%M%S)
docker exec qdrant tar czf - /qdrant/storage | aws s3 cp - s3://agente-bsc-backups/qdrant-$DATE.tar.gz
```

---

### Azure

#### 1. Azure Container Instances (ACI)

```bash
# Login
az login

# Criar resource group
az group create --name agente-bsc-rg --location eastus

# Deploy container
az container create \
    --resource-group agente-bsc-rg \
    --name agente-bsc-app \
    --image seu-usuario/agente-bsc:latest \
    --cpu 4 \
    --memory 16 \
    --ports 8501 \
    --dns-name-label agente-bsc \
    --environment-variables \
        OPENAI_API_KEY=$OPENAI_API_KEY \
        COHERE_API_KEY=$COHERE_API_KEY \
        ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
```

#### 2. Azure VM (Ubuntu)

Similar ao deploy EC2, mas usando Azure CLI:

```bash
# Criar VM
az vm create \
    --resource-group agente-bsc-rg \
    --name agente-bsc-vm \
    --image Ubuntu2204 \
    --size Standard_B4ms \
    --admin-username azureuser \
    --generate-ssh-keys

# Abrir porta 80/443
az vm open-port --port 80 --resource-group agente-bsc-rg --name agente-bsc-vm
az vm open-port --port 443 --resource-group agente-bsc-rg --name agente-bsc-vm

# SSH e seguir passos Ubuntu
```

**Tipos de VM Recomendados**:

| Uso | VM Type | vCPU | RAM | Custo/mês (East US) |
|-----|---------|------|-----|---------------------|
| Dev/Test | B2s | 2 | 4 GB | ~$30 |
| Produção Pequena | B4ms | 4 | 16 GB | ~$120 |
| Produção Média | D4s_v3 | 4 | 16 GB | ~$140 |

---

### Google Cloud Platform (GCP)

#### 1. Compute Engine

```bash
# Login
gcloud auth login

# Criar instância
gcloud compute instances create agente-bsc-vm \
    --zone=us-central1-a \
    --machine-type=e2-standard-4 \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=100GB \
    --tags=http-server,https-server

# SSH
gcloud compute ssh agente-bsc-vm --zone=us-central1-a

# Seguir passos Ubuntu
```

**Tipos de Machine Recomendados**:

| Uso | Machine Type | vCPU | RAM | Custo/mês (US Central) |
|-----|--------------|------|-----|------------------------|
| Dev/Test | e2-medium | 2 | 4 GB | ~$25 |
| Produção Pequena | e2-standard-4 | 4 | 16 GB | ~$100 |
| Produção Média | e2-standard-8 | 8 | 32 GB | ~$200 |

---

## ⚙️ Configuração de Produção

### Variáveis de Ambiente (.env Produção)

```env
# ==============================================================================
# APIs - Produção
# ==============================================================================

OPENAI_API_KEY=sk-proj-...  # Tier 2+ recomendado
COHERE_API_KEY=...           # Production plan
ANTHROPIC_API_KEY=sk-ant-... # Tier 2+ recomendado

# ==============================================================================
# Performance - Produção
# ==============================================================================

# Cache (CRITICAL para produção)
ENABLE_EMBEDDING_CACHE=true
EMBEDDING_CACHE_DIR=/var/cache/agente-bsc/embeddings
EMBEDDING_CACHE_TTL_DAYS=90
EMBEDDING_CACHE_SIZE_GB=20

# Workers (ajustar conforme CPU)
AGENT_MAX_WORKERS=8  # Para 8-core machine

# ==============================================================================
# Logs - Produção
# ==============================================================================

LOG_LEVEL=INFO            # DEBUG apenas para troubleshooting
LOG_FILE=/var/log/agente-bsc/app.log
LOG_ROTATION=100MB        # Rotacionar a cada 100MB
LOG_RETENTION_DAYS=30     # Manter 30 dias

# ==============================================================================
# Segurança - Produção
# ==============================================================================

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=60
MAX_REQUESTS_PER_HOUR=1000

# Session
SESSION_SECRET_KEY=...    # Gerar com: openssl rand -hex 32
SESSION_TIMEOUT_MINUTES=60

# CORS (se API exposta)
ALLOWED_ORIGINS=https://seu-dominio.com
```

---

## 📊 Monitoramento e Logs

### 1. Logs Centralizados

#### Usando `loguru` (já integrado)

```python
from loguru import logger

# Configuração em config/settings.py
logger.add(
    "/var/log/agente-bsc/app.log",
    rotation="100 MB",
    retention="30 days",
    compression="zip",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)
```

#### Agregação de Logs (CloudWatch, Stackdriver)

**AWS CloudWatch**:

```bash
# Instalar CloudWatch Agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb

# Configurar
sudo nano /opt/aws/amazon-cloudwatch-agent/etc/config.json
```

**Configuração CloudWatch**:

```json
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/agente-bsc/app.log",
            "log_group_name": "/aws/agente-bsc/app",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
```

### 2. Métricas de Aplicação

**Prometheus + Grafana (Recomendado)**:

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'agente-bsc'
    static_configs:
      - targets: ['localhost:9090']
```

**Métricas Custom no Código**:

```python
from prometheus_client import Counter, Histogram

# Contadores
queries_total = Counter('queries_total', 'Total queries processadas')
errors_total = Counter('errors_total', 'Total de erros')

# Histogramas (latências)
query_latency = Histogram('query_latency_seconds', 'Latência das queries')

# Usar no código
@query_latency.time()
def process_query(query):
    queries_total.inc()
    # ...
```

### 3. Health Checks

```python
# app/health.py
from fastapi import FastAPI
from qdrant_client import QdrantClient

app = FastAPI()

@app.get("/health")
def health_check():
    try:
        # Verificar Qdrant
        client = QdrantClient("localhost", port=6333)
        collections = client.get_collections()
        
        # Verificar cache
        cache_ok = os.path.exists("/var/cache/agente-bsc/embeddings")
        
        return {
            "status": "healthy",
            "qdrant": "ok",
            "cache": "ok" if cache_ok else "degraded",
            "collections": len(collections.collections)
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 503
```

---

## 💾 Backup e Disaster Recovery

### 1. Backup do Qdrant

**Script de Backup Automático**:

```bash
#!/bin/bash
# /usr/local/bin/backup-qdrant.sh

BACKUP_DIR="/backups/qdrant"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/qdrant-$DATE.tar.gz"
S3_BUCKET="s3://agente-bsc-backups/qdrant"

# Criar backup
docker exec qdrant tar czf - /qdrant/storage > $BACKUP_FILE

# Upload para S3 (ou Azure Blob, GCS)
aws s3 cp $BACKUP_FILE $S3_BUCKET/

# Remover backups locais >7 dias
find $BACKUP_DIR -name "qdrant-*.tar.gz" -mtime +7 -delete

echo "[OK] Backup Qdrant concluído: $BACKUP_FILE"
```

**Agendar com Cron**:

```bash
# Backup diário às 2h AM
0 2 * * * /usr/local/bin/backup-qdrant.sh >> /var/log/backup-qdrant.log 2>&1
```

### 2. Backup do Embedding Cache

```bash
#!/bin/bash
# /usr/local/bin/backup-cache.sh

CACHE_DIR="/var/cache/agente-bsc/embeddings"
BACKUP_DIR="/backups/cache"
DATE=$(date +%Y%m%d)
BACKUP_FILE="$BACKUP_DIR/cache-$DATE.tar.gz"

tar czf $BACKUP_FILE $CACHE_DIR

# Upload (opcional)
# aws s3 cp $BACKUP_FILE s3://agente-bsc-backups/cache/

echo "[OK] Backup Cache concluído: $BACKUP_FILE"
```

### 3. Restore Procedure

```bash
# Parar serviços
sudo systemctl stop agente-bsc
docker stop qdrant

# Restore Qdrant
aws s3 cp s3://agente-bsc-backups/qdrant/qdrant-20251014-020000.tar.gz ./
docker cp qdrant-20251014-020000.tar.gz qdrant:/backup.tar.gz
docker exec qdrant tar xzf /backup.tar.gz -C /

# Restore Cache
tar xzf cache-20251014.tar.gz -C /

# Reiniciar serviços
docker start qdrant
sudo systemctl start agente-bsc
```

---

## 📈 Escalabilidade

### Horizontal Scaling (Load Balancer)

```
       ┌────────────────┐
       │ Load Balancer  │
       └────────┬───────┘
                │
        ┌───────┴───────┐
        │               │
   ┌────▼────┐     ┌────▼────┐
   │ App #1  │     │ App #2  │
   │ (8501)  │     │ (8501)  │
   └────┬────┘     └────┬────┘
        │               │
        └───────┬───────┘
                │
        ┌───────▼───────┐
        │  Qdrant (shared)│
        └─────────────────┘
```

**Nginx Load Balancer**:

```nginx
upstream agente_bsc_backend {
    least_conn;
    server app1:8501;
    server app2:8501;
}

server {
    listen 443 ssl;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://agente_bsc_backend;
        # ... proxy_set_header ...
    }
}
```

### Vertical Scaling

Aumentar recursos da VM/container conforme necessidade:

| Queries/min | vCPU | RAM | Qdrant RAM |
|-------------|------|-----|------------|
| 1-10 | 2 | 8 GB | 2 GB |
| 10-50 | 4 | 16 GB | 4 GB |
| 50-100 | 8 | 32 GB | 8 GB |
| 100+ | 16+ | 64+ GB | 16+ GB |

---

## 🔒 Segurança

### 1. Autenticação (Streamlit)

```python
# app/auth.py
import streamlit as st
import hmac

def check_password():
    """Returns True if user entered correct password."""
    
    def password_entered():
        """Callback when password is entered."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show password input
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("Password incorrect")
        return False
    else:
        # Password correct
        return True

# Em app/main.py
if not check_password():
    st.stop()

# ... resto da app
```

**Configurar senha** (`.streamlit/secrets.toml`):

```toml
password = "SuaSenhaSegura123"
```

### 2. HTTPS Obrigatório

- ✅ Let's Encrypt (gratuito)
- ✅ TLS 1.2+ apenas
- ✅ HSTS Header

**Nginx HSTS**:

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### 3. Rate Limiting

**Nginx**:

```nginx
limit_req_zone $binary_remote_addr zone=bsc_limit:10m rate=10r/m;

location / {
    limit_req zone=bsc_limit burst=20 nodelay;
    # ...
}
```

### 4. Secrets Management

**AWS Secrets Manager**:

```python
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

# Usar
openai_key = get_secret('prod/agente-bsc/openai-key')
```

---

## 💰 Custos Estimados

### AWS (US East - Mensais)

| Componente | Tipo | Custo/mês (USD) |
|------------|------|-----------------|
| EC2 t3.large | 8 GB RAM, 2 vCPU | $60 |
| EBS 100 GB SSD | Storage | $10 |
| Load Balancer | ALB | $20 |
| Route 53 | DNS | $1 |
| S3 Backups (50 GB) | Storage | $1 |
| **Total Infraestrutura** | | **~$92/mês** |
| OpenAI API | ~1000 queries/mês | $50-100 |
| Cohere API | ~1000 queries/mês | $20 |
| Anthropic API | ~1000 queries/mês | $30-60 |
| **Total com APIs** | | **~$192-272/mês** |

### Azure (East US - Mensais)

| Componente | Tipo | Custo/mês (USD) |
|------------|------|-----------------|
| VM B4ms | 16 GB RAM, 4 vCPU | $120 |
| Managed Disk 100 GB | SSD | $5 |
| Load Balancer | Basic | $20 |
| **Total Infraestrutura** | | **~$145/mês** |

### GCP (US Central - Mensais)

| Componente | Tipo | Custo/mês (USD) |
|------------|------|-----------------|
| e2-standard-4 | 16 GB RAM, 4 vCPU | $100 |
| Persistent Disk 100 GB | SSD | $17 |
| Load Balancer | HTTPS | $20 |
| **Total Infraestrutura** | | **~$137/mês** |

💡 **Dica**: Use Spot/Preemptible instances para economizar ~70% em cargas não-críticas.

---

## 📞 Suporte

Para dúvidas sobre deployment:

- 📖 Consulte [README.md](../README.md) para visão geral
- 📘 Veja [TUTORIAL.md](TUTORIAL.md) para uso pós-deploy
- 🐛 Reporte issues: [GitHub Issues](https://github.com/seu-usuario/agente-bsc-rag/issues)

---

<p align="center">
  <strong>🚀 Deployment Guide v1.0</strong><br>
  <em>Agente BSC RAG - MVP Out/2025</em>
</p>

