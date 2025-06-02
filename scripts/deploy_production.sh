#!/bin/bash
set -e

# EmailBot Production Deployment Script
# =====================================
# 
# This script deploys EmailBot to production following the procedures in OPERATIONS.md
# 
# Usage:
#   ./scripts/deploy_production.sh [options]
# 
# Options:
#   --backup       Create backup before deployment
#   --migrate      Run database migrations
#   --restart      Restart services after deployment
#   --validate     Run validation tests after deployment
#   --rollback     Rollback to previous version
#   --help         Show this help message

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/backups"
LOG_FILE="$PROJECT_DIR/logs/deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker is not running"
        exit 1
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        error "docker-compose is not installed"
        exit 1
    fi
    
    # Check if .env file exists
    if [[ ! -f "$PROJECT_DIR/.env" ]]; then
        error ".env file not found. Please create it from env.template"
        exit 1
    fi
    
    # Verify environment variables
    source "$PROJECT_DIR/.env"
    
    local required_vars=(
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "OPENAI_API_KEY"
        "M365_TENANT_ID"
        "M365_CLIENT_ID"
        "M365_CLIENT_SECRET"
        "MASTER_ENCRYPTION_KEY"
        "JWT_SECRET_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    log "Prerequisites check passed"
}

# Create backup
create_backup() {
    log "Creating backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    local backup_name="emailbot_backup_$(date +'%Y%m%d_%H%M%S')"
    
    # Backup database
    info "Backing up database..."
    docker exec emailbot-postgres pg_dump -U emailbot -d emailbot > "$BACKUP_DIR/${backup_name}.sql"
    
    # Compress backup
    gzip "$BACKUP_DIR/${backup_name}.sql"
    
    # Backup application data
    info "Backing up application data..."
    tar -czf "$BACKUP_DIR/${backup_name}_data.tar.gz" \
        -C "$PROJECT_DIR" \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        --exclude='.venv' \
        --exclude='backups' \
        .
    
    log "Backup created: ${backup_name}"
    echo "$backup_name" > "$BACKUP_DIR/latest_backup.txt"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Run Alembic migrations
    docker exec emailbot-app alembic upgrade head
    
    if [[ $? -eq 0 ]]; then
        log "Database migrations completed successfully"
    else
        error "Database migrations failed"
        exit 1
    fi
}

# Build and deploy
deploy() {
    log "Starting deployment..."
    
    cd "$PROJECT_DIR"
    
    # Pull latest images
    info "Pulling latest images..."
    docker-compose pull
    
    # Build application image
    info "Building application image..."
    docker-compose build emailbot-app
    
    # Start services
    info "Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    info "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_service_health
    
    log "Deployment completed successfully"
}

# Check service health
check_service_health() {
    info "Checking service health..."
    
    local max_retries=30
    local retry_count=0
    
    while [[ $retry_count -lt $max_retries ]]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log "Application is healthy"
            return 0
        fi
        
        retry_count=$((retry_count + 1))
        info "Health check attempt $retry_count/$max_retries..."
        sleep 10
    done
    
    error "Application health check failed after $max_retries attempts"
    return 1
}

# Run validation tests
run_validation() {
    log "Running validation tests..."
    
    # Run health checks
    info "Running health checks..."
    python "$PROJECT_DIR/scripts/operational_tools.py" health-check --detailed --output "$PROJECT_DIR/logs/post_deployment_health.json"
    
    # Run security audit
    info "Running security audit..."
    python "$PROJECT_DIR/scripts/operational_tools.py" security-audit --output "$PROJECT_DIR/logs/post_deployment_security.json"
    
    # Test API endpoints
    info "Testing API endpoints..."
    
    # Generate test API key
    local test_api_response=$(python "$PROJECT_DIR/scripts/operational_tools.py" generate-api-key --user-id "deployment_test" --role "viewer")
    local test_api_key=$(echo "$test_api_response" | jq -r '.api_key')
    
    if [[ "$test_api_key" != "null" && -n "$test_api_key" ]]; then
        # Test API endpoints
        if curl -H "Authorization: Bearer $test_api_key" http://localhost:8000/process/status &> /dev/null; then
            log "API endpoint test passed"
        else
            error "API endpoint test failed"
            return 1
        fi
        
        # Revoke test API key
        local key_id=$(echo "$test_api_response" | jq -r '.key_id')
        curl -X DELETE "http://localhost:8000/security/api-keys/$key_id" \
             -H "Authorization: Bearer $test_api_key" &> /dev/null
    else
        error "Failed to generate test API key"
        return 1
    fi
    
    log "Validation tests completed successfully"
}

# Restart services
restart_services() {
    log "Restarting services..."
    
    cd "$PROJECT_DIR"
    
    # Graceful restart
    docker-compose restart emailbot-app
    docker-compose restart emailbot-scheduler
    
    # Wait for services to be ready
    sleep 20
    check_service_health
    
    log "Services restarted successfully"
}

# Rollback to previous version
rollback() {
    log "Starting rollback..."
    
    if [[ ! -f "$BACKUP_DIR/latest_backup.txt" ]]; then
        error "No backup found for rollback"
        exit 1
    fi
    
    local backup_name=$(cat "$BACKUP_DIR/latest_backup.txt")
    
    warning "Rolling back to backup: $backup_name"
    
    # Stop services
    info "Stopping services..."
    docker-compose down
    
    # Restore database
    info "Restoring database..."
    python "$PROJECT_DIR/scripts/operational_tools.py" restore-database --backup-file "${backup_name}.sql.gz"
    
    # Restore application data
    info "Restoring application data..."
    tar -xzf "$BACKUP_DIR/${backup_name}_data.tar.gz" -C "$PROJECT_DIR"
    
    # Start services
    info "Starting services..."
    docker-compose up -d
    
    # Wait and check health
    sleep 30
    check_service_health
    
    log "Rollback completed successfully"
}

# Clean up old backups
cleanup_backups() {
    log "Cleaning up old backups..."
    
    # Keep only last 10 backups
    find "$BACKUP_DIR" -name "emailbot_backup_*.sql.gz" -type f | sort -r | tail -n +11 | xargs rm -f
    find "$BACKUP_DIR" -name "emailbot_backup_*_data.tar.gz" -type f | sort -r | tail -n +11 | xargs rm -f
    
    log "Backup cleanup completed"
}

# Enable maintenance mode
enable_maintenance_mode() {
    log "Enabling maintenance mode..."
    
    # Create maintenance page
    cat > "$PROJECT_DIR/nginx/maintenance.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>EmailBot - Maintenance</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 100px; }
        .container { max-width: 600px; margin: 0 auto; }
        h1 { color: #333; }
        p { color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 EmailBot is under maintenance</h1>
        <p>We're performing scheduled maintenance to improve your experience.</p>
        <p>Please check back in a few minutes.</p>
        <p>If you need immediate assistance, please contact the IT support team.</p>
    </div>
</body>
</html>
EOF
    
    # Update nginx config for maintenance mode
    # This would typically redirect traffic to the maintenance page
    
    log "Maintenance mode enabled"
}

# Disable maintenance mode
disable_maintenance_mode() {
    log "Disabling maintenance mode..."
    
    # Remove maintenance page
    rm -f "$PROJECT_DIR/nginx/maintenance.html"
    
    # Restore normal nginx config
    # This would restore normal traffic routing
    
    log "Maintenance mode disabled"
}

# Show help
show_help() {
    cat << EOF
EmailBot Production Deployment Script

Usage: $0 [options]

Options:
    --backup       Create backup before deployment
    --migrate      Run database migrations
    --restart      Restart services after deployment
    --validate     Run validation tests after deployment
    --rollback     Rollback to previous version
    --maintenance  Enable maintenance mode
    --cleanup      Clean up old backups
    --help         Show this help message

Examples:
    # Full deployment with backup and validation
    $0 --backup --migrate --validate

    # Quick restart
    $0 --restart

    # Rollback deployment
    $0 --rollback

    # Enable maintenance mode for updates
    $0 --maintenance

EOF
}

# Main execution
main() {
    # Create logs directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Start logging
    log "EmailBot Production Deployment Script Started"
    log "Arguments: $*"
    
    # Check permissions
    check_permissions
    
    # Parse arguments
    local backup=false
    local migrate=false
    local restart=false
    local validate=false
    local rollback=false
    local maintenance=false
    local cleanup=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backup)
                backup=true
                shift
                ;;
            --migrate)
                migrate=true
                shift
                ;;
            --restart)
                restart=true
                shift
                ;;
            --validate)
                validate=true
                shift
                ;;
            --rollback)
                rollback=true
                shift
                ;;
            --maintenance)
                maintenance=true
                shift
                ;;
            --cleanup)
                cleanup=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # If no options provided, show help
    if [[ $backup == false && $migrate == false && $restart == false && 
          $validate == false && $rollback == false && $maintenance == false && 
          $cleanup == false ]]; then
        show_help
        exit 0
    fi
    
    # Check prerequisites (except for rollback)
    if [[ $rollback == false ]]; then
        check_prerequisites
    fi
    
    # Execute actions
    if [[ $maintenance == true ]]; then
        enable_maintenance_mode
    fi
    
    if [[ $rollback == true ]]; then
        rollback
        disable_maintenance_mode
        exit 0
    fi
    
    if [[ $backup == true ]]; then
        create_backup
    fi
    
    if [[ $migrate == true ]]; then
        run_migrations
    fi
    
    if [[ $restart == true ]]; then
        restart_services
    else
        # Full deployment if not just restarting
        if [[ $backup == true || $migrate == true ]]; then
            deploy
        fi
    fi
    
    if [[ $validate == true ]]; then
        run_validation
    fi
    
    if [[ $cleanup == true ]]; then
        cleanup_backups
    fi
    
    if [[ $maintenance == true ]]; then
        disable_maintenance_mode
    fi
    
    log "Deployment script completed successfully"
}

# Execute main function with all arguments
main "$@" 