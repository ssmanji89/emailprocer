# EmailBot Production Deployment Guide

## Overview

This guide covers the complete production deployment process for EmailBot, an enterprise-grade AI-powered email classification and escalation management system.

## Prerequisites

### System Requirements
- **Operating System**: Ubuntu 20.04 LTS or CentOS 8+
- **CPU**: Minimum 4 cores, Recommended 8+ cores
- **Memory**: Minimum 16GB RAM, Recommended 32GB+
- **Storage**: Minimum 100GB SSD, Recommended 500GB+ SSD
- **Network**: Stable internet connection with static IP

### Software Dependencies
- Docker Engine 24.0+
- Docker Compose 2.20+
- Git 2.30+
- SSL certificates (Let's Encrypt or commercial)

### External Services
- **Microsoft 365 Tenant** with app registration
- **OpenAI API** account with GPT-4 access
- **Domain name** with DNS control
- **SMTP service** for notifications (optional)

## Pre-Deployment Checklist

### 1. Environment Preparation
- [ ] Server provisioned with required specifications
- [ ] Docker and Docker Compose installed
- [ ] Firewall configured (ports 80, 443, 22)
- [ ] SSL certificates obtained and validated
- [ ] Domain DNS records configured

### 2. Security Setup
- [ ] SSH key-based authentication configured
- [ ] Non-root user created with sudo privileges
- [ ] Fail2ban installed and configured
- [ ] UFW firewall enabled with proper rules
- [ ] System updates applied

### 3. Application Configuration
- [ ] Environment variables configured
- [ ] SSL certificates placed in correct directories
- [ ] Database backup strategy implemented
- [ ] Monitoring alerts configured

## Deployment Process

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

### Step 2: Application Deployment

```bash
# Clone repository
git clone https://github.com/your-org/emailbot.git
cd emailbot

# Checkout production branch
git checkout main

# Copy production environment file
cp .env.production .env

# Edit environment variables
nano .env
```

### Step 3: SSL Certificate Setup

```bash
# Create SSL directory
sudo mkdir -p /etc/nginx/ssl

# Copy SSL certificates
sudo cp /path/to/your/cert.pem /etc/nginx/ssl/
sudo cp /path/to/your/key.pem /etc/nginx/ssl/
sudo cp /path/to/your/chain.pem /etc/nginx/ssl/

# Set proper permissions
sudo chmod 600 /etc/nginx/ssl/key.pem
sudo chmod 644 /etc/nginx/ssl/cert.pem
sudo chmod 644 /etc/nginx/ssl/chain.pem
```

### Step 4: Database Initialization

```bash
# Start database services
docker-compose up -d emailbot-postgres emailbot-redis

# Wait for services to be ready
sleep 30

# Run database migrations
docker-compose exec emailbot-app python -m alembic upgrade head

# Create initial admin user
docker-compose exec emailbot-app python scripts/create_admin_user.py
```

### Step 5: Application Startup

```bash
# Start all services
docker-compose up -d

# Verify all services are running
docker-compose ps

# Check logs for any errors
docker-compose logs -f
```

### Step 6: Health Verification

```bash
# Test health endpoints
curl -k https://your-domain.com/health
curl -k https://api.your-domain.com/health

# Test frontend accessibility
curl -k https://your-domain.com

# Test API functionality
curl -k -H "Authorization: Bearer YOUR_API_KEY" https://api.your-domain.com/process/status
```

## Environment Configuration

### Required Environment Variables

```bash
# Application
APP_NAME=EmailBot
APP_VERSION=1.0.0
NODE_ENV=production
DEBUG=false

# Security
MASTER_ENCRYPTION_KEY=your_32_byte_base64_encryption_key
JWT_SECRET_KEY=your_jwt_secret_key
SESSION_SECRET=your_session_secret

# Database
POSTGRES_PASSWORD=your_secure_db_password
REDIS_PASSWORD=your_secure_redis_password

# Microsoft 365
M365_TENANT_ID=your_tenant_id
M365_CLIENT_ID=your_client_id
M365_CLIENT_SECRET=your_client_secret

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Monitoring
GRAFANA_PASSWORD=your_grafana_password
ALERT_WEBHOOK_URL=your_alert_webhook_url
```

### SSL/TLS Configuration

```nginx
# Nginx SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;
```

## Monitoring and Alerting

### Prometheus Metrics
- Application performance metrics
- System resource utilization
- Database connection pools
- API response times
- Error rates and availability

### Grafana Dashboards
- **System Overview**: CPU, memory, disk, network
- **Application Metrics**: Request rates, response times, errors
- **Business Metrics**: Email processing, escalations, SLA compliance
- **Security Metrics**: Authentication attempts, API usage

### Alert Rules
- Service downtime (Critical)
- High error rates (Warning)
- Performance degradation (Warning)
- Security incidents (Critical)
- Resource exhaustion (Warning)

## Backup and Recovery

### Database Backup

```bash
# Daily automated backup
0 2 * * * docker-compose exec -T emailbot-postgres pg_dump -U emailbot emailbot | gzip > /backups/emailbot_$(date +\%Y\%m\%d).sql.gz

# Backup retention (keep 30 days)
0 3 * * * find /backups -name "emailbot_*.sql.gz" -mtime +30 -delete
```

### Application Data Backup

```bash
# Backup configuration and logs
tar -czf /backups/emailbot_config_$(date +%Y%m%d).tar.gz \
  /opt/emailbot/.env \
  /opt/emailbot/logs \
  /opt/emailbot/monitoring
```

### Recovery Procedures

```bash
# Database recovery
gunzip -c /backups/emailbot_YYYYMMDD.sql.gz | \
docker-compose exec -T emailbot-postgres psql -U emailbot -d emailbot

# Application recovery
docker-compose down
docker-compose pull
docker-compose up -d
```

## Security Hardening

### System Security
- Regular security updates
- Fail2ban for intrusion prevention
- UFW firewall configuration
- SSH key-based authentication only
- Regular security audits

### Application Security
- API rate limiting
- Input validation and sanitization
- Secure headers (HSTS, CSP, etc.)
- Regular dependency updates
- Security scanning in CI/CD

### Network Security
- TLS 1.2+ only
- Strong cipher suites
- Certificate pinning
- VPN access for admin interfaces
- Network segmentation

## Performance Optimization

### Database Optimization
```sql
-- Index optimization
CREATE INDEX CONCURRENTLY idx_emails_processed_at ON emails(processed_at);
CREATE INDEX CONCURRENTLY idx_escalations_status ON escalations(status);

-- Connection pooling
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
```

### Application Optimization
```yaml
# Docker resource limits
services:
  emailbot-app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### Nginx Optimization
```nginx
# Performance tuning
worker_processes auto;
worker_connections 2048;
keepalive_timeout 65;
client_max_body_size 50M;
gzip on;
gzip_comp_level 6;
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker-compose logs emailbot-app

# Check resource usage
docker stats

# Verify environment variables
docker-compose config
```

#### Database Connection Issues
```bash
# Test database connectivity
docker-compose exec emailbot-postgres psql -U emailbot -d emailbot -c "SELECT 1;"

# Check connection pool
docker-compose exec emailbot-app python -c "from app.database import test_connection; test_connection()"
```

#### SSL Certificate Issues
```bash
# Verify certificate validity
openssl x509 -in /etc/nginx/ssl/cert.pem -text -noout

# Test SSL configuration
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

### Performance Issues
```bash
# Monitor resource usage
htop
iotop
nethogs

# Check application metrics
curl -s https://api.your-domain.com/monitoring/metrics

# Analyze slow queries
docker-compose exec emailbot-postgres psql -U emailbot -d emailbot -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily
- [ ] Check service health status
- [ ] Review error logs
- [ ] Verify backup completion
- [ ] Monitor resource usage

#### Weekly
- [ ] Update system packages
- [ ] Review security logs
- [ ] Analyze performance metrics
- [ ] Test backup restoration

#### Monthly
- [ ] Update application dependencies
- [ ] Review and rotate logs
- [ ] Security vulnerability scan
- [ ] Performance optimization review

### Update Procedures

```bash
# Application update
git pull origin main
docker-compose pull
docker-compose up -d --force-recreate

# Database migration
docker-compose exec emailbot-app python -m alembic upgrade head

# Verify update
curl -s https://api.your-domain.com/health | jq '.version'
```

## Support and Escalation

### Contact Information
- **Primary Support**: support@your-company.com
- **Emergency Contact**: +1-XXX-XXX-XXXX
- **Escalation Manager**: manager@your-company.com

### Support Levels
- **Level 1**: Basic troubleshooting, service restarts
- **Level 2**: Application debugging, configuration changes
- **Level 3**: Code fixes, infrastructure changes

### Documentation
- **API Documentation**: https://api.your-domain.com/docs
- **User Manual**: https://docs.your-domain.com
- **Admin Guide**: https://admin.your-domain.com/docs 