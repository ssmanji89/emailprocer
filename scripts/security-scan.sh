#!/bin/bash

# EmailBot Security Scanning Script
# Comprehensive security assessment including vulnerability scanning,
# dependency checks, configuration audits, and compliance verification

set -euo pipefail

# Configuration
SCAN_DIR="/tmp/emailbot_security_scan"
REPORT_DIR="/var/log/emailbot/security"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SCAN_REPORT="security_scan_${TIMESTAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Setup scan environment
setup_scan_environment() {
    log "Setting up security scan environment..."
    
    # Create directories
    mkdir -p "$SCAN_DIR" "$REPORT_DIR"
    
    # Initialize report file
    cat > "${REPORT_DIR}/${SCAN_REPORT}.json" << EOF
{
    "scan_metadata": {
        "timestamp": "$TIMESTAMP",
        "date": "$(date -Iseconds)",
        "hostname": "$(hostname)",
        "scan_version": "1.0.0"
    },
    "scans": {}
}
EOF
    
    log "Scan environment ready"
}

# Install security tools if needed
install_security_tools() {
    log "Checking and installing security tools..."
    
    # Check if tools are available
    local tools_needed=()
    
    command -v trivy >/dev/null 2>&1 || tools_needed+=("trivy")
    command -v bandit >/dev/null 2>&1 || tools_needed+=("bandit")
    command -v safety >/dev/null 2>&1 || tools_needed+=("safety")
    command -v semgrep >/dev/null 2>&1 || tools_needed+=("semgrep")
    
    if [[ ${#tools_needed[@]} -gt 0 ]]; then
        info "Installing missing security tools: ${tools_needed[*]}"
        
        # Install Trivy
        if [[ " ${tools_needed[*]} " =~ " trivy " ]]; then
            curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
        fi
        
        # Install Python security tools
        if [[ " ${tools_needed[*]} " =~ " bandit " ]] || [[ " ${tools_needed[*]} " =~ " safety " ]]; then
            pip3 install bandit safety
        fi
        
        # Install Semgrep
        if [[ " ${tools_needed[*]} " =~ " semgrep " ]]; then
            pip3 install semgrep
        fi
    else
        log "All security tools are available"
    fi
}

# Container vulnerability scanning with Trivy
scan_container_vulnerabilities() {
    log "Starting container vulnerability scan..."
    
    local scan_output="${SCAN_DIR}/trivy_scan.json"
    
    # Scan backend container
    if trivy image --format json --output "$scan_output" emailbot-backend:latest 2>/dev/null; then
        log "Backend container scan completed"
    else
        warning "Backend container scan failed"
    fi
    
    # Scan frontend container
    local frontend_scan="${SCAN_DIR}/trivy_frontend.json"
    if trivy image --format json --output "$frontend_scan" emailbot-frontend:latest 2>/dev/null; then
        log "Frontend container scan completed"
    else
        warning "Frontend container scan failed"
    fi
    
    # Process results
    if [[ -f "$scan_output" ]]; then
        local critical_vulns=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length' "$scan_output" 2>/dev/null || echo "0")
        local high_vulns=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "HIGH")] | length' "$scan_output" 2>/dev/null || echo "0")
        
        # Update report
        jq --argjson critical "$critical_vulns" --argjson high "$high_vulns" \
           '.scans.container_vulnerabilities = {
               "status": "completed",
               "critical_vulnerabilities": $critical,
               "high_vulnerabilities": $high,
               "scan_file": "'$scan_output'"
           }' "${REPORT_DIR}/${SCAN_REPORT}.json" > "${REPORT_DIR}/${SCAN_REPORT}.tmp" && \
           mv "${REPORT_DIR}/${SCAN_REPORT}.tmp" "${REPORT_DIR}/${SCAN_REPORT}.json"
        
        if [[ $critical_vulns -gt 0 ]]; then
            error "Found $critical_vulns critical vulnerabilities in containers"
        elif [[ $high_vulns -gt 0 ]]; then
            warning "Found $high_vulns high severity vulnerabilities in containers"
        else
            log "No critical or high severity vulnerabilities found in containers"
        fi
    fi
}

# Python code security scanning with Bandit
scan_python_security() {
    log "Starting Python security scan with Bandit..."
    
    local bandit_output="${SCAN_DIR}/bandit_scan.json"
    
    if [[ -d "app" ]]; then
        if bandit -r app/ -f json -o "$bandit_output" 2>/dev/null; then
            log "Python security scan completed"
            
            # Process results
            local high_issues=$(jq '[.results[] | select(.issue_severity == "HIGH")] | length' "$bandit_output" 2>/dev/null || echo "0")
            local medium_issues=$(jq '[.results[] | select(.issue_severity == "MEDIUM")] | length' "$bandit_output" 2>/dev/null || echo "0")
            
            # Update report
            jq --argjson high "$high_issues" --argjson medium "$medium_issues" \
               '.scans.python_security = {
                   "status": "completed",
                   "high_issues": $high,
                   "medium_issues": $medium,
                   "scan_file": "'$bandit_output'"
               }' "${REPORT_DIR}/${SCAN_REPORT}.json" > "${REPORT_DIR}/${SCAN_REPORT}.tmp" && \
               mv "${REPORT_DIR}/${SCAN_REPORT}.tmp" "${REPORT_DIR}/${SCAN_REPORT}.json"
            
            if [[ $high_issues -gt 0 ]]; then
                warning "Found $high_issues high severity Python security issues"
            else
                log "No high severity Python security issues found"
            fi
        else
            warning "Python security scan failed"
        fi
    else
        warning "Python app directory not found, skipping Python security scan"
    fi
}

# Dependency vulnerability scanning with Safety
scan_dependency_vulnerabilities() {
    log "Starting dependency vulnerability scan..."
    
    local safety_output="${SCAN_DIR}/safety_scan.json"
    
    if [[ -f "requirements.txt" ]]; then
        if safety check --json --output "$safety_output" 2>/dev/null; then
            log "Dependency vulnerability scan completed"
            
            # Process results
            local vuln_count=$(jq 'length' "$safety_output" 2>/dev/null || echo "0")
            
            # Update report
            jq --argjson count "$vuln_count" \
               '.scans.dependency_vulnerabilities = {
                   "status": "completed",
                   "vulnerable_packages": $count,
                   "scan_file": "'$safety_output'"
               }' "${REPORT_DIR}/${SCAN_REPORT}.json" > "${REPORT_DIR}/${SCAN_REPORT}.tmp" && \
               mv "${REPORT_DIR}/${SCAN_REPORT}.tmp" "${REPORT_DIR}/${SCAN_REPORT}.json"
            
            if [[ $vuln_count -gt 0 ]]; then
                warning "Found $vuln_count vulnerable dependencies"
            else
                log "No vulnerable dependencies found"
            fi
        else
            warning "Dependency vulnerability scan failed"
        fi
    else
        warning "requirements.txt not found, skipping dependency scan"
    fi
}

# Static code analysis with Semgrep
scan_static_analysis() {
    log "Starting static code analysis..."
    
    local semgrep_output="${SCAN_DIR}/semgrep_scan.json"
    
    if semgrep --config=auto --json --output="$semgrep_output" . 2>/dev/null; then
        log "Static code analysis completed"
        
        # Process results
        local error_count=$(jq '[.results[] | select(.extra.severity == "ERROR")] | length' "$semgrep_output" 2>/dev/null || echo "0")
        local warning_count=$(jq '[.results[] | select(.extra.severity == "WARNING")] | length' "$semgrep_output" 2>/dev/null || echo "0")
        
        # Update report
        jq --argjson errors "$error_count" --argjson warnings "$warning_count" \
           '.scans.static_analysis = {
               "status": "completed",
               "errors": $errors,
               "warnings": $warnings,
               "scan_file": "'$semgrep_output'"
           }' "${REPORT_DIR}/${SCAN_REPORT}.json" > "${REPORT_DIR}/${SCAN_REPORT}.tmp" && \
           mv "${REPORT_DIR}/${SCAN_REPORT}.tmp" "${REPORT_DIR}/${SCAN_REPORT}.json"
        
        if [[ $error_count -gt 0 ]]; then
            warning "Found $error_count static analysis errors"
        else
            log "No static analysis errors found"
        fi
    else
        warning "Static code analysis failed"
    fi
}

# Configuration security audit
audit_configuration() {
    log "Starting configuration security audit..."
    
    local config_issues=0
    local config_report="${SCAN_DIR}/config_audit.txt"
    
    # Check environment file security
    if [[ -f ".env" ]]; then
        if [[ $(stat -c "%a" .env) != "600" ]]; then
            echo "ISSUE: .env file permissions are too permissive" >> "$config_report"
            ((config_issues++))
        fi
        
        # Check for default/weak passwords
        if grep -q "password.*=.*password\|password.*=.*123\|password.*=.*admin" .env 2>/dev/null; then
            echo "ISSUE: Weak default passwords detected in .env" >> "$config_report"
            ((config_issues++))
        fi
        
        # Check for missing encryption keys
        if ! grep -q "MASTER_ENCRYPTION_KEY" .env 2>/dev/null; then
            echo "ISSUE: Missing MASTER_ENCRYPTION_KEY in .env" >> "$config_report"
            ((config_issues++))
        fi
    fi
    
    # Check Docker Compose security
    if [[ -f "docker-compose.yml" ]]; then
        # Check for privileged containers
        if grep -q "privileged.*true" docker-compose.yml 2>/dev/null; then
            echo "ISSUE: Privileged containers detected in docker-compose.yml" >> "$config_report"
            ((config_issues++))
        fi
        
        # Check for host network mode
        if grep -q "network_mode.*host" docker-compose.yml 2>/dev/null; then
            echo "ISSUE: Host network mode detected in docker-compose.yml" >> "$config_report"
            ((config_issues++))
        fi
    fi
    
    # Check SSL/TLS configuration
    if [[ -f "nginx/nginx.conf" ]]; then
        # Check for weak SSL protocols
        if grep -q "ssl_protocols.*TLSv1\." nginx/nginx.conf 2>/dev/null; then
            if ! grep -q "ssl_protocols.*TLSv1.2\|ssl_protocols.*TLSv1.3" nginx/nginx.conf 2>/dev/null; then
                echo "ISSUE: Weak SSL protocols in nginx configuration" >> "$config_report"
                ((config_issues++))
            fi
        fi
        
        # Check for security headers
        if ! grep -q "X-Frame-Options\|X-Content-Type-Options\|X-XSS-Protection" nginx/nginx.conf 2>/dev/null; then
            echo "ISSUE: Missing security headers in nginx configuration" >> "$config_report"
            ((config_issues++))
        fi
    fi
    
    # Update report
    jq --argjson issues "$config_issues" \
       '.scans.configuration_audit = {
           "status": "completed",
           "issues_found": $issues,
           "audit_file": "'$config_report'"
       }' "${REPORT_DIR}/${SCAN_REPORT}.json" > "${REPORT_DIR}/${SCAN_REPORT}.tmp" && \
       mv "${REPORT_DIR}/${SCAN_REPORT}.tmp" "${REPORT_DIR}/${SCAN_REPORT}.json"
    
    if [[ $config_issues -gt 0 ]]; then
        warning "Found $config_issues configuration security issues"
    else
        log "No configuration security issues found"
    fi
}

# Network security assessment
assess_network_security() {
    log "Starting network security assessment..."
    
    local network_issues=0
    local network_report="${SCAN_DIR}/network_audit.txt"
    
    # Check open ports
    local open_ports=$(ss -tuln | grep LISTEN | wc -l)
    echo "Open listening ports: $open_ports" >> "$network_report"
    
    # Check for unnecessary services
    if ss -tuln | grep -q ":23\|:21\|:135\|:139\|:445" 2>/dev/null; then
        echo "ISSUE: Potentially unnecessary services detected" >> "$network_report"
        ((network_issues++))
    fi
    
    # Check firewall status
    if command -v ufw >/dev/null 2>&1; then
        if ! ufw status | grep -q "Status: active" 2>/dev/null; then
            echo "ISSUE: UFW firewall is not active" >> "$network_report"
            ((network_issues++))
        fi
    fi
    
    # Update report
    jq --argjson issues "$network_issues" \
       '.scans.network_security = {
           "status": "completed",
           "issues_found": $issues,
           "open_ports": '$open_ports',
           "audit_file": "'$network_report'"
       }' "${REPORT_DIR}/${SCAN_REPORT}.json" > "${REPORT_DIR}/${SCAN_REPORT}.tmp" && \
       mv "${REPORT_DIR}/${SCAN_REPORT}.tmp" "${REPORT_DIR}/${SCAN_REPORT}.json"
    
    if [[ $network_issues -gt 0 ]]; then
        warning "Found $network_issues network security issues"
    else
        log "No network security issues found"
    fi
}

# Generate security summary report
generate_summary_report() {
    log "Generating security summary report..."
    
    local summary_file="${REPORT_DIR}/${SCAN_REPORT}_summary.txt"
    
    cat > "$summary_file" << EOF
EmailBot Security Scan Summary
==============================
Scan Date: $(date)
Hostname: $(hostname)

SCAN RESULTS:
EOF
    
    # Extract results from JSON report
    if [[ -f "${REPORT_DIR}/${SCAN_REPORT}.json" ]]; then
        # Container vulnerabilities
        local critical_vulns=$(jq -r '.scans.container_vulnerabilities.critical_vulnerabilities // 0' "${REPORT_DIR}/${SCAN_REPORT}.json")
        local high_vulns=$(jq -r '.scans.container_vulnerabilities.high_vulnerabilities // 0' "${REPORT_DIR}/${SCAN_REPORT}.json")
        
        echo "Container Vulnerabilities:" >> "$summary_file"
        echo "  Critical: $critical_vulns" >> "$summary_file"
        echo "  High: $high_vulns" >> "$summary_file"
        echo "" >> "$summary_file"
        
        # Python security issues
        local python_high=$(jq -r '.scans.python_security.high_issues // 0' "${REPORT_DIR}/${SCAN_REPORT}.json")
        echo "Python Security Issues:" >> "$summary_file"
        echo "  High Severity: $python_high" >> "$summary_file"
        echo "" >> "$summary_file"
        
        # Dependency vulnerabilities
        local vuln_deps=$(jq -r '.scans.dependency_vulnerabilities.vulnerable_packages // 0' "${REPORT_DIR}/${SCAN_REPORT}.json")
        echo "Vulnerable Dependencies: $vuln_deps" >> "$summary_file"
        echo "" >> "$summary_file"
        
        # Configuration issues
        local config_issues=$(jq -r '.scans.configuration_audit.issues_found // 0' "${REPORT_DIR}/${SCAN_REPORT}.json")
        echo "Configuration Issues: $config_issues" >> "$summary_file"
        echo "" >> "$summary_file"
        
        # Calculate overall risk score
        local risk_score=$((critical_vulns * 10 + high_vulns * 5 + python_high * 3 + vuln_deps * 2 + config_issues))
        
        echo "OVERALL RISK SCORE: $risk_score" >> "$summary_file"
        echo "" >> "$summary_file"
        
        if [[ $risk_score -eq 0 ]]; then
            echo "SECURITY STATUS: EXCELLENT" >> "$summary_file"
        elif [[ $risk_score -lt 10 ]]; then
            echo "SECURITY STATUS: GOOD" >> "$summary_file"
        elif [[ $risk_score -lt 25 ]]; then
            echo "SECURITY STATUS: MODERATE" >> "$summary_file"
        else
            echo "SECURITY STATUS: NEEDS ATTENTION" >> "$summary_file"
        fi
        
        # Update JSON report with summary
        jq --argjson score "$risk_score" \
           '.summary = {
               "risk_score": $score,
               "status": (if $score == 0 then "excellent" elif $score < 10 then "good" elif $score < 25 then "moderate" else "needs_attention" end),
               "summary_file": "'$summary_file'"
           }' "${REPORT_DIR}/${SCAN_REPORT}.json" > "${REPORT_DIR}/${SCAN_REPORT}.tmp" && \
           mv "${REPORT_DIR}/${SCAN_REPORT}.tmp" "${REPORT_DIR}/${SCAN_REPORT}.json"
    fi
    
    log "Security summary report generated: $summary_file"
}

# Send security alert if needed
send_security_alert() {
    local risk_score=$(jq -r '.summary.risk_score // 0' "${REPORT_DIR}/${SCAN_REPORT}.json" 2>/dev/null)
    
    # Send alert if risk score is high
    if [[ $risk_score -gt 25 ]]; then
        warning "High security risk detected (Score: $risk_score)"
        
        # Send webhook notification if configured
        if [[ -n "${SECURITY_WEBHOOK_URL:-}" ]]; then
            local payload="{\"text\":\"🚨 EmailBot Security Alert: High risk detected (Score: $risk_score)\",\"timestamp\":\"$(date -Iseconds)\"}"
            
            if curl -s -X POST -H "Content-Type: application/json" -d "$payload" "$SECURITY_WEBHOOK_URL" >/dev/null; then
                log "Security alert sent successfully"
            else
                warning "Failed to send security alert"
            fi
        fi
    fi
}

# Cleanup scan files
cleanup_scan_files() {
    log "Cleaning up temporary scan files..."
    
    # Keep scan results but remove temporary files
    rm -rf "$SCAN_DIR"
    
    # Cleanup old scan reports (keep last 10)
    find "$REPORT_DIR" -name "security_scan_*.json" -type f | sort -r | tail -n +11 | xargs rm -f 2>/dev/null || true
    find "$REPORT_DIR" -name "security_scan_*_summary.txt" -type f | sort -r | tail -n +11 | xargs rm -f 2>/dev/null || true
    
    log "Cleanup completed"
}

# Main security scan function
main() {
    log "Starting EmailBot security scan..."
    
    # Setup
    setup_scan_environment
    install_security_tools
    
    # Run security scans
    scan_container_vulnerabilities
    scan_python_security
    scan_dependency_vulnerabilities
    scan_static_analysis
    audit_configuration
    assess_network_security
    
    # Generate reports and alerts
    generate_summary_report
    send_security_alert
    cleanup_scan_files
    
    log "Security scan completed successfully!"
    log "Report available at: ${REPORT_DIR}/${SCAN_REPORT}.json"
    log "Summary available at: ${REPORT_DIR}/${SCAN_REPORT}_summary.txt"
}

# Error handling
trap 'error "Security scan failed with exit code $?"; exit 1' ERR

# Run main function
main "$@" 