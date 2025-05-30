# EmailBot - Deployment Guide

**Version**: 1.0  
**Last Updated**: January 2025  
**Environments**: Development, Staging, Production

## 🎯 Deployment Overview

This guide covers deployment strategies for EmailBot across different environments, from local development to production cloud deployments.

## 🏗️ Architecture Requirements

### Minimum System Requirements

#### Development Environment
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 10GB
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.11+
- **Docker**: 20.10+ (optional)

#### Production Environment
- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 50GB SSD
- **OS**: Ubuntu 20.04+ LTS
- **Docker**: 20.10+
- **Network**: Outbound HTTPS access to Microsoft Graph API and OpenAI

### External Dependencies
- **Microsoft 365 Tenant** with admin access
- **OpenAI API** account with GPT-4 access
- **Redis** instance (local or cloud)
- **PostgreSQL** database (production)

## 🛠️ Local Development Setup

### 1. Prerequisites Installation

#### Python Environment
```bash
# Install Python 3.11+
# Windows (using chocolatey)
choco install python311

# macOS (using homebrew)
brew install python@3.11

# Ubuntu
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

#### Git and Basic Tools
```bash
# Ubuntu
sudo apt install git curl wget

# macOS
brew install git curl wget

# Windows
choco install git curl wget
```

### 2. Project Setup

```bash
# Clone repository
git clone <repository-url>
cd emailprocer

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Unix/macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
# Copy environment template
cp env.template .env

# Edit configuration
nano .env  # or use your preferred editor
```

**Required Environment Variables:**
```bash
# M365 Configuration
EMAILBOT_M365_TENANT_ID=your-tenant-id
EMAILBOT_M365_CLIENT_ID=your-client-id
EMAILBOT_M365_CLIENT_SECRET=your-client-secret
EMAILBOT_TARGET_MAILBOX=it-support@zgcompanies.com

# OpenAI Configuration
EMAILBOT_OPENAI_API_KEY=your-openai-key
EMAILBOT_OPENAI_MODEL=gpt-4

# Database (SQLite for development)
EMAILBOT_DATABASE_URL=sqlite:///./emailbot.db

# Redis (optional for development)
EMAILBOT_REDIS_URL=redis://localhost:6379/0
```

### 4. Database Setup

```bash
# Initialize database (if using PostgreSQL)
python scripts/initialize_database.py

# For SQLite, database will be created automatically
```

### 5. Run Application

```bash
# Development mode with hot reload
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Configuration validation
curl http://localhost:8000/config/validation
```

## 🐳 Docker Development Setup

### 1. Docker Compose for Development

Create `docker-compose.dev.yml`:
```yaml
version: '3.8'

services:
  emailbot:
    build: 
      context: .
      dockerfile: docker/Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - EMAILBOT_DEBUG=true
      - EMAILBOT_RELOAD=true
    env_file:
      - .env
    volumes:
      - .:/app
      - /app/venv
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: emailbot
      POSTGRES_USER: emailbot
      POSTGRES_PASSWORD: emailbot_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  redis_data:
  postgres_data:
```

### 2. Development Dockerfile

Create `docker/Dockerfile.dev`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Development command with reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### 3. Run with Docker Compose

```bash
# Build and start services
docker-compose -f docker-compose.dev.yml up --build

# Run in background
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f emailbot

# Stop services
docker-compose -f docker-compose.dev.yml down
```

## 🚀 Production Deployment

### Option 1: Docker Production Deployment

#### 1. Production Dockerfile

Create `docker/Dockerfile.prod`:
```dockerfile
# Multi-stage build for production
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r emailbot && useradd -r -g emailbot emailbot

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=emailbot:emailbot . .

# Switch to non-root user
USER emailbot

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### 2. Production Docker Compose

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  emailbot:
    build:
      context: .
      dockerfile: docker/Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - EMAILBOT_DEBUG=false
      - EMAILBOT_LOG_LEVEL=INFO
    env_file:
      - .env.prod
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_prod_data:/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - emailbot
    restart: unless-stopped

volumes:
  redis_prod_data:
  postgres_prod_data:
```

#### 3. Production Environment Configuration

Create `.env.prod`:
```bash
# Application
EMAILBOT_DEBUG=false
EMAILBOT_LOG_LEVEL=INFO
EMAILBOT_HOST=0.0.0.0
EMAILBOT_PORT=8000

# M365 Configuration
EMAILBOT_M365_TENANT_ID=your-prod-tenant-id
EMAILBOT_M365_CLIENT_ID=your-prod-client-id
EMAILBOT_M365_CLIENT_SECRET=your-prod-client-secret
EMAILBOT_TARGET_MAILBOX=it-support@zgcompanies.com

# OpenAI Configuration
EMAILBOT_OPENAI_API_KEY=your-prod-openai-key
EMAILBOT_OPENAI_MODEL=gpt-4

# Database
EMAILBOT_DATABASE_URL=postgresql://emailbot:${DB_PASSWORD}@postgres:5432/emailbot
DB_NAME=emailbot
DB_USER=emailbot
DB_PASSWORD=secure_db_password

# Redis
EMAILBOT_REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
REDIS_PASSWORD=secure_redis_password

# Security
EMAILBOT_API_KEY=your-secure-api-key
EMAILBOT_ENCRYPTION_KEY=your-encryption-key

# Performance
EMAILBOT_POLLING_INTERVAL_MINUTES=5
EMAILBOT_BATCH_SIZE=20
EMAILBOT_MAX_RETRIES=3
```

#### 4. Deploy to Production

```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d --build

# Monitor deployment
docker-compose -f docker-compose.prod.yml logs -f

# Health check
curl https://your-domain.com/health
```

### Option 2: Cloud Platform Deployment

#### Azure Container Instances

```bash
# Create resource group
az group create --name emailbot-rg --location eastus

# Create container registry
az acr create --resource-group emailbot-rg --name emailbotregistry --sku Basic

# Build and push image
az acr build --registry emailbotregistry --image emailbot:latest .

# Deploy container instance
az container create \
  --resource-group emailbot-rg \
  --name emailbot \
  --image emailbotregistry.azurecr.io/emailbot:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --environment-variables \
    EMAILBOT_M365_TENANT_ID=your-tenant-id \
    EMAILBOT_M365_CLIENT_ID=your-client-id \
    --secure-environment-variables \
    EMAILBOT_M365_CLIENT_SECRET=your-secret \
    EMAILBOT_OPENAI_API_KEY=your-api-key
```

#### AWS ECS Deployment

Create `ecs-task-definition.json`:
```json
{
  "family": "emailbot",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "emailbot",
      "image": "your-account.dkr.ecr.region.amazonaws.com/emailbot:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "EMAILBOT_M365_TENANT_ID",
          "value": "your-tenant-id"
        }
      ],
      "secrets": [
        {
          "name": "EMAILBOT_M365_CLIENT_SECRET",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:emailbot/m365-secret"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/emailbot",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## 🔧 Advanced Production Configuration

### 1. Nginx Reverse Proxy

Create `nginx/nginx.conf`:
```nginx
upstream emailbot_backend {
    server emailbot:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    location / {
        proxy_pass http://emailbot_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    location /health {
        proxy_pass http://emailbot_backend/health;
        access_log off;
    }
}
```

### 2. Monitoring and Logging

#### Prometheus Metrics (Future)
```yaml
# Add to docker-compose.prod.yml
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
```

#### Centralized Logging
```yaml
# Add to docker-compose.prod.yml
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.6.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.6.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

### 3. Backup and Recovery

#### Database Backup Script
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_BACKUP_FILE="emailbot_backup_${TIMESTAMP}.sql"

# Create backup directory
mkdir -p ${BACKUP_DIR}

# PostgreSQL backup
docker exec postgres pg_dump -U emailbot emailbot > ${BACKUP_DIR}/${DB_BACKUP_FILE}

# Compress backup
gzip ${BACKUP_DIR}/${DB_BACKUP_FILE}

# Clean old backups (keep last 7 days)
find ${BACKUP_DIR} -name "emailbot_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: ${DB_BACKUP_FILE}.gz"
```

#### Automated Backup with Cron
```bash
# Add to crontab
0 2 * * * /path/to/backup.sh >> /var/log/emailbot-backup.log 2>&1
```

## 🔐 Security Configuration

### 1. SSL/TLS Setup

#### Let's Encrypt with Certbot
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. Firewall Configuration

```bash
# UFW firewall setup
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. Environment Security

```bash
# Secure environment file permissions
chmod 600 .env.prod

# Use Docker secrets for sensitive data
docker secret create m365_client_secret m365_secret.txt
docker secret create openai_api_key openai_key.txt
```

## 📊 Monitoring and Health Checks

### 1. Health Check Script

```bash
#!/bin/bash
# health_check.sh

HEALTH_URL="https://your-domain.com/health"
SLACK_WEBHOOK="your-slack-webhook-url"

response=$(curl -s -o /dev/null -w "%{http_code}" ${HEALTH_URL})

if [ $response -ne 200 ]; then
    message="🚨 EmailBot health check failed! HTTP status: $response"
    curl -X POST -H 'Content-type: application/json' \
         --data "{\"text\":\"$message\"}" \
         ${SLACK_WEBHOOK}
fi
```

### 2. Uptime Monitoring

Add to crontab:
```bash
# Check every 5 minutes
*/5 * * * * /path/to/health_check.sh
```

## 🔄 Deployment Workflow

### 1. CI/CD Pipeline (GitHub Actions)

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy EmailBot

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest
    
    - name: Run tests
      run: pytest
    
    - name: Build Docker image
      run: docker build -f docker/Dockerfile.prod -t emailbot:latest .
    
    - name: Deploy to production
      run: |
        # Add your deployment commands here
        echo "Deploying to production..."
```

### 2. Blue-Green Deployment

```bash
#!/bin/bash
# blue_green_deploy.sh

NEW_IMAGE="emailbot:$(git rev-parse --short HEAD)"
CURRENT_CONTAINER="emailbot_blue"
NEW_CONTAINER="emailbot_green"

# Build new image
docker build -f docker/Dockerfile.prod -t ${NEW_IMAGE} .

# Start new container
docker run -d --name ${NEW_CONTAINER} \
  --env-file .env.prod \
  -p 8001:8000 \
  ${NEW_IMAGE}

# Health check new container
sleep 30
if curl -f http://localhost:8001/health; then
    # Switch traffic
    docker stop ${CURRENT_CONTAINER}
    docker rm ${CURRENT_CONTAINER}
    docker rename ${NEW_CONTAINER} ${CURRENT_CONTAINER}
    
    # Update nginx upstream
    # (Implementation depends on load balancer setup)
    
    echo "Deployment successful"
else
    echo "Health check failed, rolling back"
    docker stop ${NEW_CONTAINER}
    docker rm ${NEW_CONTAINER}
    exit 1
fi
```

## 🆘 Troubleshooting

### Common Issues

#### 1. M365 Authentication Failures
```bash
# Check token status
curl http://localhost:8000/health/detailed | jq '.components.m365_auth'

# Verify app registration permissions
# Check Azure Portal → App Registrations → API permissions
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL connectivity
docker exec -it postgres psql -U emailbot -d emailbot -c "SELECT 1;"

# Check connection string
echo $EMAILBOT_DATABASE_URL
```

#### 3. High Memory Usage
```bash
# Monitor container resources
docker stats emailbot

# Check for memory leaks
docker exec emailbot ps aux --sort=-%mem | head
```

#### 4. Performance Issues
```bash
# Check processing metrics
curl http://localhost:8000/process/status | jq '.processing_stats'

# Monitor API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
```

### Log Analysis

```bash
# View application logs
docker logs emailbot -f

# Search for errors
docker logs emailbot 2>&1 | grep ERROR

# Export logs for analysis
docker logs emailbot > emailbot.log 2>&1
```

---

**Document Status**: Production Ready  
**Last Updated**: January 2025  
**Maintained By**: DevOps Team 