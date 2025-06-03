#!/bin/bash

# EmailBot Backup Script
# This script creates comprehensive backups of the EmailBot system
# including database, configuration, logs, and application data

set -euo pipefail

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="emailbot_backup_${TIMESTAMP}"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Docker compose project name
COMPOSE_PROJECT="emailbot"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root or with sudo
check_permissions() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root or with sudo"
        exit 1
    fi
}

# Create backup directory structure
setup_backup_dir() {
    log "Setting up backup directory structure..."
    
    mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"/{database,config,logs,monitoring,ssl}
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        error "Failed to create backup directory: $BACKUP_DIR"
        exit 1
    fi
    
    log "Backup directory created: ${BACKUP_DIR}/${BACKUP_NAME}"
}

# Check if Docker services are running
check_services() {
    log "Checking Docker services status..."
    
    if ! docker-compose -p "$COMPOSE_PROJECT" ps | grep -q "Up"; then
        error "EmailBot services are not running"
        exit 1
    fi
    
    log "Docker services are running"
}

# Backup PostgreSQL database
backup_database() {
    log "Starting database backup..."
    
    local db_backup_file="${BACKUP_DIR}/${BACKUP_NAME}/database/emailbot_db.sql"
    local db_backup_compressed="${db_backup_file}.gz"
    
    # Create database dump
    if docker-compose -p "$COMPOSE_PROJECT" exec -T emailbot-postgres pg_dump -U emailbot -d emailbot > "$db_backup_file"; then
        log "Database dump created successfully"
        
        # Compress the dump
        if gzip "$db_backup_file"; then
            log "Database dump compressed: $db_backup_compressed"
        else
            warning "Failed to compress database dump"
        fi
        
        # Verify backup integrity
        if gunzip -t "$db_backup_compressed" 2>/dev/null; then
            log "Database backup integrity verified"
        else
            error "Database backup integrity check failed"
            exit 1
        fi
    else
        error "Failed to create database dump"
        exit 1
    fi
}

# Backup Redis data
backup_redis() {
    log "Starting Redis backup..."
    
    local redis_backup_dir="${BACKUP_DIR}/${BACKUP_NAME}/database"
    
    # Create Redis dump
    if docker-compose -p "$COMPOSE_PROJECT" exec -T emailbot-redis redis-cli BGSAVE; then
        log "Redis background save initiated"
        
        # Wait for background save to complete
        sleep 5
        
        # Copy Redis dump file
        if docker cp "${COMPOSE_PROJECT}_emailbot-redis_1:/data/dump.rdb" "$redis_backup_dir/redis_dump.rdb"; then
            log "Redis dump copied successfully"
        else
            warning "Failed to copy Redis dump file"
        fi
    else
        warning "Failed to initiate Redis background save"
    fi
}

# Backup configuration files
backup_config() {
    log "Starting configuration backup..."
    
    local config_backup_dir="${BACKUP_DIR}/${BACKUP_NAME}/config"
    
    # Backup environment files
    if [[ -f ".env" ]]; then
        cp .env "$config_backup_dir/env.backup"
        log "Environment file backed up"
    fi
    
    if [[ -f ".env.production" ]]; then
        cp .env.production "$config_backup_dir/env.production.backup"
        log "Production environment file backed up"
    fi
    
    # Backup Docker Compose files
    cp docker-compose.yml "$config_backup_dir/"
    log "Docker Compose file backed up"
    
    # Backup Nginx configuration
    if [[ -d "nginx" ]]; then
        cp -r nginx "$config_backup_dir/"
        log "Nginx configuration backed up"
    fi
    
    # Backup monitoring configuration
    if [[ -d "monitoring" ]]; then
        cp -r monitoring "$config_backup_dir/"
        log "Monitoring configuration backed up"
    fi
}

# Backup SSL certificates
backup_ssl() {
    log "Starting SSL certificates backup..."
    
    local ssl_backup_dir="${BACKUP_DIR}/${BACKUP_NAME}/ssl"
    
    if [[ -d "/etc/nginx/ssl" ]]; then
        cp -r /etc/nginx/ssl/* "$ssl_backup_dir/" 2>/dev/null || true
        log "SSL certificates backed up"
    else
        warning "SSL directory not found, skipping SSL backup"
    fi
}

# Backup application logs
backup_logs() {
    log "Starting logs backup..."
    
    local logs_backup_dir="${BACKUP_DIR}/${BACKUP_NAME}/logs"
    
    # Backup application logs
    if [[ -d "logs" ]]; then
        cp -r logs "$logs_backup_dir/app_logs"
        log "Application logs backed up"
    fi
    
    # Backup Docker logs
    mkdir -p "$logs_backup_dir/docker_logs"
    
    for service in emailbot-app emailbot-dashboard emailbot-postgres emailbot-redis; do
        if docker-compose -p "$COMPOSE_PROJECT" logs --no-color "$service" > "$logs_backup_dir/docker_logs/${service}.log" 2>/dev/null; then
            log "Docker logs for $service backed up"
        else
            warning "Failed to backup Docker logs for $service"
        fi
    done
}

# Create backup metadata
create_metadata() {
    log "Creating backup metadata..."
    
    local metadata_file="${BACKUP_DIR}/${BACKUP_NAME}/backup_metadata.json"
    
    cat > "$metadata_file" << EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$TIMESTAMP",
    "date": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "emailbot_version": "$(docker-compose -p "$COMPOSE_PROJECT" exec -T emailbot-app python -c "from app.config.settings import settings; print(settings.app_version)" 2>/dev/null || echo "unknown")",
    "docker_compose_version": "$(docker-compose --version)",
    "backup_components": [
        "database",
        "redis",
        "configuration",
        "ssl_certificates",
        "logs"
    ],
    "backup_size": "$(du -sh "${BACKUP_DIR}/${BACKUP_NAME}" | cut -f1)",
    "retention_days": $RETENTION_DAYS
}
EOF
    
    log "Backup metadata created"
}

# Compress backup
compress_backup() {
    log "Compressing backup archive..."
    
    local archive_file="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    
    if tar -czf "$archive_file" -C "$BACKUP_DIR" "$BACKUP_NAME"; then
        log "Backup compressed successfully: $archive_file"
        
        # Remove uncompressed backup directory
        rm -rf "${BACKUP_DIR}/${BACKUP_NAME}"
        log "Temporary backup directory removed"
        
        # Display final backup size
        local backup_size=$(du -sh "$archive_file" | cut -f1)
        log "Final backup size: $backup_size"
    else
        error "Failed to compress backup"
        exit 1
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups (retention: $RETENTION_DAYS days)..."
    
    local deleted_count=0
    
    # Find and delete old backup files
    while IFS= read -r -d '' file; do
        rm -f "$file"
        ((deleted_count++))
        log "Deleted old backup: $(basename "$file")"
    done < <(find "$BACKUP_DIR" -name "emailbot_backup_*.tar.gz" -mtime +$RETENTION_DAYS -print0 2>/dev/null)
    
    if [[ $deleted_count -eq 0 ]]; then
        log "No old backups to clean up"
    else
        log "Cleaned up $deleted_count old backup(s)"
    fi
}

# Verify backup integrity
verify_backup() {
    log "Verifying backup integrity..."
    
    local archive_file="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    
    if tar -tzf "$archive_file" >/dev/null 2>&1; then
        log "Backup archive integrity verified"
    else
        error "Backup archive integrity check failed"
        exit 1
    fi
}

# Send notification (optional)
send_notification() {
    local status=$1
    local message=$2
    
    # Check if webhook URL is configured
    if [[ -n "${BACKUP_WEBHOOK_URL:-}" ]]; then
        local payload="{\"text\":\"EmailBot Backup $status: $message\",\"timestamp\":\"$(date -Iseconds)\"}"
        
        if curl -s -X POST -H "Content-Type: application/json" -d "$payload" "$BACKUP_WEBHOOK_URL" >/dev/null; then
            log "Notification sent successfully"
        else
            warning "Failed to send notification"
        fi
    fi
}

# Main backup function
main() {
    log "Starting EmailBot backup process..."
    
    # Check prerequisites
    check_permissions
    check_services
    
    # Create backup
    setup_backup_dir
    backup_database
    backup_redis
    backup_config
    backup_ssl
    backup_logs
    create_metadata
    compress_backup
    verify_backup
    cleanup_old_backups
    
    local backup_file="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    local backup_size=$(du -sh "$backup_file" | cut -f1)
    
    log "Backup completed successfully!"
    log "Backup file: $backup_file"
    log "Backup size: $backup_size"
    
    # Send success notification
    send_notification "SUCCESS" "Backup completed successfully (Size: $backup_size)"
}

# Error handling
trap 'error "Backup failed with exit code $?"; send_notification "FAILED" "Backup process failed"; exit 1' ERR

# Run main function
main "$@" 