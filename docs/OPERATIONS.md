# EmailBot - Operations Manual

**Version**: 1.0  
**Last Updated**: January 2025  
**Purpose**: Operational procedures, troubleshooting guides, and maintenance runbooks

## 🎯 Operations Overview

This manual provides comprehensive operational procedures for EmailBot, including monitoring, troubleshooting, maintenance, and emergency response procedures.

## 📊 System Monitoring

### Health Check Procedures

#### Daily Health Checks
```bash
#!/bin/bash
# daily_health_check.sh

echo "=== EmailBot Daily Health Check ==="
echo "Date: $(date)"

# Check API health
echo "1. Checking API health..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ $API_STATUS -eq 200 ]; then
    echo "✅ API is healthy"
else
    echo "❌ API is unhealthy (Status: $API_STATUS)"
fi

# Check detailed component health
echo "2. Checking component health..."
curl -s http://localhost:8000/health/detailed | jq '.components'

# Check processing status
echo "3. Checking processing status..."
curl -s http://localhost:8000/process/status | jq '.emails_processed_today, .current_queue_size'

# Check database connectivity
echo "4. Checking database..."
docker exec emailbot-postgres pg_isready -U emailbot

# Check Redis connectivity
echo "5. Checking Redis..."
docker exec emailbot-redis redis-cli ping

echo "=== Health Check Complete ==="
```

#### Automated Monitoring Alerts
```python
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

class SystemMonitor:
    """Automated system monitoring with alerting."""
    
    def __init__(self, alert_webhook: str, thresholds: Dict[str, Any]):
        self.alert_webhook = alert_webhook
        self.thresholds = thresholds
        self.last_alerts = {}
        self.alert_cooldown = 300  # 5 minutes
    
    async def run_monitoring_cycle(self):
        """Run complete monitoring cycle."""
        alerts = []
        
        # Check API health
        api_health = await self._check_api_health()
        if not api_health["healthy"]:
            alerts.append({
                "severity": "CRITICAL",
                "component": "API",
                "message": "API health check failed",
                "details": api_health
            })
        
        # Check processing metrics
        processing_metrics = await self._check_processing_metrics()
        if processing_metrics["alerts"]:
            alerts.extend(processing_metrics["alerts"])
        
        # Check external dependencies
        dependency_health = await self._check_dependencies()
        if dependency_health["alerts"]:
            alerts.extend(dependency_health["alerts"])
        
        # Check resource usage
        resource_alerts = await self._check_resource_usage()
        if resource_alerts:
            alerts.extend(resource_alerts)
        
        # Send alerts
        for alert in alerts:
            await self._send_alert(alert)
    
    async def _check_processing_metrics(self) -> Dict[str, Any]:
        """Check email processing performance metrics."""
        try:
            response = await httpx.get("http://localhost:8000/process/status")
            data = response.json()
            
            alerts = []
            
            # Check queue size
            queue_size = data.get("current_queue_size", 0)
            if queue_size > self.thresholds["max_queue_size"]:
                alerts.append({
                    "severity": "WARNING",
                    "component": "Processing Queue",
                    "message": f"Queue size is high: {queue_size}",
                    "details": {"queue_size": queue_size}
                })
            
            # Check processing rate
            stats = data.get("processing_stats", {})
            success_rate = stats.get("success_rate", 1.0)
            if success_rate < self.thresholds["min_success_rate"]:
                alerts.append({
                    "severity": "CRITICAL",
                    "component": "Processing",
                    "message": f"Low success rate: {success_rate:.2%}",
                    "details": stats
                })
            
            # Check average processing time
            avg_time = stats.get("average_processing_time", 0)
            if avg_time > self.thresholds["max_processing_time"]:
                alerts.append({
                    "severity": "WARNING",
                    "component": "Performance",
                    "message": f"Slow processing: {avg_time:.2f}s",
                    "details": {"avg_processing_time": avg_time}
                })
            
            return {"healthy": len(alerts) == 0, "alerts": alerts}
            
        except Exception as e:
            return {
                "healthy": False,
                "alerts": [{
                    "severity": "CRITICAL",
                    "component": "Monitoring",
                    "message": f"Failed to check processing metrics: {str(e)}"
                }]
            }
```

### Performance Metrics Dashboard

#### Key Performance Indicators (KPIs)
```python
class PerformanceMetrics:
    """Performance metrics collection and analysis."""
    
    async def get_kpi_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get key performance indicators for the last N hours."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        metrics = {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            }
        }
        
        # Email processing metrics
        processing_data = await self._get_processing_metrics(start_time, end_time)
        metrics["email_processing"] = {
            "total_processed": processing_data["count"],
            "success_rate": processing_data["success_rate"],
            "avg_processing_time": processing_data["avg_time"],
            "automation_rate": processing_data["automation_rate"]
        }
        
        # Classification accuracy
        classification_data = await self._get_classification_metrics(start_time, end_time)
        metrics["classification"] = {
            "accuracy": classification_data["accuracy"],
            "confidence_distribution": classification_data["confidence_dist"],
            "category_distribution": classification_data["category_dist"]
        }
        
        # System performance
        system_data = await self._get_system_metrics()
        metrics["system"] = {
            "cpu_usage": system_data["cpu_percent"],
            "memory_usage": system_data["memory_percent"],
            "disk_usage": system_data["disk_percent"],
            "uptime": system_data["uptime_hours"]
        }
        
        # Service availability
        availability_data = await self._get_availability_metrics(start_time, end_time)
        metrics["availability"] = {
            "uptime_percentage": availability_data["uptime_percent"],
            "api_response_time": availability_data["avg_response_time"],
            "error_rate": availability_data["error_rate"]
        }
        
        return metrics
```

## 🚨 Troubleshooting Guide

### Common Issues and Resolutions

#### 1. Email Processing Issues

##### Issue: Emails Not Being Processed
**Symptoms:**
- Queue size increasing
- No new processing results
- API health shows processing issues

**Diagnosis Steps:**
```bash
# Check processing status
curl http://localhost:8000/process/status | jq '.'

# Check logs for errors
docker logs emailbot --tail 100 | grep ERROR

# Check M365 connectivity
curl http://localhost:8000/health/detailed | jq '.components.m365_auth'

# Check LLM service status
curl http://localhost:8000/health/detailed | jq '.components.llm_service'
```

**Resolution Steps:**
1. **Check Authentication:**
   ```bash
   # Verify M365 token validity
   curl http://localhost:8000/config/validation | jq '.validations.m365'
   
   # If token expired, restart service to force refresh
   docker restart emailbot
   ```

2. **Check API Rate Limits:**
   ```bash
   # Monitor for rate limit errors in logs
   docker logs emailbot | grep -i "rate limit\|throttle\|quota"
   
   # If rate limited, wait or increase delay between requests
   ```

3. **Manual Processing Trigger:**
   ```bash
   # Trigger manual processing
   curl -X POST http://localhost:8000/process/trigger
   ```

##### Issue: Low Classification Accuracy
**Symptoms:**
- High number of escalations
- Poor confidence scores
- Incorrect categorization

**Diagnosis:**
```bash
# Check recent classification results
curl http://localhost:8000/analytics/performance?period=day | jq '.metrics.classification_accuracy'

# Review confidence distribution
curl http://localhost:8000/analytics/performance | jq '.confidence_distribution'
```

**Resolution:**
1. **Review LLM Prompts:**
   - Check prompt templates in `app/utils/llm_prompts.py`
   - Validate prompt format and examples
   - Consider prompt engineering improvements

2. **Adjust Confidence Thresholds:**
   ```python
   # Temporarily lower thresholds for testing
   CONFIDENCE_THRESHOLDS = {
       "AUTO_HANDLE": 80,     # Reduced from 85
       "SUGGEST_RESPONSE": 55, # Reduced from 60
       "HUMAN_REVIEW": 35,    # Reduced from 40
   }
   ```

3. **Monitor and Analyze:**
   - Review manually processed emails
   - Update training examples
   - Consider fine-tuning approach

#### 2. Microsoft 365 Integration Issues

##### Issue: Authentication Failures
**Symptoms:**
- 401 Unauthorized errors
- Token refresh failures
- Permission denied messages

**Diagnosis:**
```bash
# Check M365 authentication status
curl http://localhost:8000/health/detailed | jq '.components.m365_auth'

# Verify app registration
az ad app show --id $M365_CLIENT_ID
```

**Resolution:**
1. **Verify App Registration:**
   ```bash
   # Check app permissions
   az ad app permission list --id $M365_CLIENT_ID
   
   # Grant admin consent if needed
   az ad app permission admin-consent --id $M365_CLIENT_ID
   ```

2. **Regenerate Client Secret:**
   ```bash
   # Generate new client secret
   NEW_SECRET=$(az ad app credential reset --id $M365_CLIENT_ID --query password -o tsv)
   
   # Update environment variable
   echo "EMAILBOT_M365_CLIENT_SECRET=$NEW_SECRET" >> .env
   
   # Restart service
   docker restart emailbot
   ```

3. **Check Token Cache:**
   ```bash
   # Clear Redis token cache
   docker exec emailbot-redis redis-cli FLUSHDB
   ```

##### Issue: Teams Group Creation Failures
**Symptoms:**
- Escalations not creating Teams groups
- Permission errors in Teams operations
- Members not being added to groups

**Diagnosis:**
```bash
# Check Teams permissions
curl http://localhost:8000/config/validation | jq '.validations.teams'

# Review escalation logs
docker logs emailbot | grep -i teams | tail -20
```

**Resolution:**
1. **Verify Teams Permissions:**
   - Ensure `Chat.Create` and `ChatMember.ReadWrite` permissions
   - Check Graph API quotas

2. **Test Teams Operations:**
   ```python
   # Manual Teams test
   from app.integrations.teams_manager import TeamsManager
   
   teams_manager = TeamsManager(...)
   test_result = await teams_manager.test_teams_operations()
   ```

#### 3. Database and Performance Issues

##### Issue: Slow Database Queries
**Symptoms:**
- High response times
- Database timeout errors
- Memory usage warnings

**Diagnosis:**
```bash
# Check database performance
docker exec emailbot-postgres psql -U emailbot -c "
    SELECT query, calls, total_time, mean_time 
    FROM pg_stat_statements 
    ORDER BY mean_time DESC 
    LIMIT 10;"

# Check connection pool status
curl http://localhost:8000/health/detailed | jq '.components.database'
```

**Resolution:**
1. **Optimize Queries:**
   ```sql
   -- Add missing indexes
   CREATE INDEX CONCURRENTLY idx_emails_received_datetime 
   ON emails(received_datetime);
   
   CREATE INDEX CONCURRENTLY idx_processing_results_email_id 
   ON processing_results(email_id);
   ```

2. **Tune Connection Pool:**
   ```python
   # Adjust pool settings in database config
   "pool_config": {
       "min_connections": 10,
       "max_connections": 50,
       "command_timeout": 60
   }
   ```

3. **Database Maintenance:**
   ```bash
   # Run VACUUM and ANALYZE
   docker exec emailbot-postgres psql -U emailbot -c "VACUUM ANALYZE;"
   
   # Update table statistics
   docker exec emailbot-postgres psql -U emailbot -c "ANALYZE;"
   ```

## 🔧 Maintenance Procedures

### Regular Maintenance Tasks

#### Daily Maintenance
```bash
#!/bin/bash
# daily_maintenance.sh

echo "=== Daily Maintenance: $(date) ==="

# 1. Health check
./daily_health_check.sh

# 2. Log rotation
docker exec emailbot logrotate /etc/logrotate.conf

# 3. Clear temporary files
docker exec emailbot find /tmp -type f -mtime +1 -delete

# 4. Update metrics
curl -X POST http://localhost:8000/internal/metrics/update

echo "=== Daily Maintenance Complete ==="
```

#### Weekly Maintenance
```bash
#!/bin/bash
# weekly_maintenance.sh

echo "=== Weekly Maintenance: $(date) ==="

# 1. Database maintenance
echo "Running database maintenance..."
docker exec emailbot-postgres psql -U emailbot -c "VACUUM ANALYZE;"

# 2. Backup database
echo "Creating database backup..."
./backup_database.sh

# 3. Clean old logs
echo "Cleaning old logs..."
find /var/log/emailbot -name "*.log" -mtime +7 -delete

# 4. Update system packages
echo "Updating system packages..."
apt update && apt upgrade -y

# 5. Restart services for fresh start
echo "Restarting services..."
docker-compose restart

echo "=== Weekly Maintenance Complete ==="
```

#### Monthly Maintenance
```bash
#!/bin/bash
# monthly_maintenance.sh

echo "=== Monthly Maintenance: $(date) ==="

# 1. Full system backup
echo "Creating full system backup..."
./full_system_backup.sh

# 2. Performance analysis
echo "Generating performance report..."
curl http://localhost:8000/analytics/performance?period=month > "performance_$(date +%Y%m).json"

# 3. Pattern analysis
echo "Running pattern discovery..."
curl -X POST http://localhost:8000/internal/patterns/analyze

# 4. Security audit
echo "Running security audit..."
./security_audit.sh

# 5. Capacity planning review
echo "Checking capacity metrics..."
./capacity_review.sh

echo "=== Monthly Maintenance Complete ==="
```

### Backup and Recovery

#### Database Backup Strategy
```bash
#!/bin/bash
# backup_database.sh

BACKUP_DIR="/backups/database"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="emailbot_backup_${TIMESTAMP}.sql"

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Create database dump
docker exec emailbot-postgres pg_dump -U emailbot -h localhost emailbot > ${BACKUP_DIR}/${BACKUP_FILE}

# Compress backup
gzip ${BACKUP_DIR}/${BACKUP_FILE}

# Upload to cloud storage (if configured)
if [ ! -z "$AWS_S3_BACKUP_BUCKET" ]; then
    aws s3 cp ${BACKUP_DIR}/${BACKUP_FILE}.gz s3://${AWS_S3_BACKUP_BUCKET}/database/
fi

# Clean old backups (keep last 30 days)
find ${BACKUP_DIR} -name "emailbot_backup_*.sql.gz" -mtime +30 -delete

echo "Database backup completed: ${BACKUP_FILE}.gz"
```

#### System Configuration Backup
```bash
#!/bin/bash
# backup_config.sh

CONFIG_BACKUP_DIR="/backups/config"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p ${CONFIG_BACKUP_DIR}

# Backup configuration files
tar -czf ${CONFIG_BACKUP_DIR}/config_${TIMESTAMP}.tar.gz \
    .env \
    app/config/ \
    docker-compose.yml \
    nginx/nginx.conf

# Backup integration configurations
cp app/config/integrations.json ${CONFIG_BACKUP_DIR}/integrations_${TIMESTAMP}.json

echo "Configuration backup completed"
```

#### Recovery Procedures
```bash
#!/bin/bash
# restore_database.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./restore_database.sh <backup_file>"
    exit 1
fi

echo "Restoring database from: $BACKUP_FILE"

# Stop application
docker-compose stop emailbot

# Drop and recreate database
docker exec emailbot-postgres psql -U postgres -c "DROP DATABASE IF EXISTS emailbot;"
docker exec emailbot-postgres psql -U postgres -c "CREATE DATABASE emailbot OWNER emailbot;"

# Restore from backup
gunzip -c $BACKUP_FILE | docker exec -i emailbot-postgres psql -U emailbot emailbot

# Start application
docker-compose start emailbot

echo "Database restore completed"
```

## 🔒 Security Operations

### Security Monitoring
```python
class SecurityMonitor:
    """Monitor security events and anomalies."""
    
    async def check_security_events(self) -> List[Dict[str, Any]]:
        """Check for security-related events."""
        events = []
        
        # Check failed authentication attempts
        failed_auth = await self._check_failed_auth()
        if failed_auth["count"] > 10:  # More than 10 failures in last hour
            events.append({
                "severity": "WARNING",
                "type": "authentication",
                "message": f"High number of failed auth attempts: {failed_auth['count']}",
                "details": failed_auth
            })
        
        # Check unusual access patterns
        access_patterns = await self._analyze_access_patterns()
        for anomaly in access_patterns["anomalies"]:
            events.append({
                "severity": "INFO",
                "type": "access_pattern",
                "message": f"Unusual access pattern detected: {anomaly['description']}",
                "details": anomaly
            })
        
        # Check data encryption status
        encryption_status = await self._check_encryption_status()
        if not encryption_status["all_encrypted"]:
            events.append({
                "severity": "CRITICAL",
                "type": "encryption",
                "message": "Unencrypted sensitive data detected",
                "details": encryption_status
            })
        
        return events
```

### Incident Response Procedures

#### Security Incident Response
```bash
#!/bin/bash
# security_incident_response.sh

INCIDENT_TYPE=$1
SEVERITY=$2

if [ -z "$INCIDENT_TYPE" ] || [ -z "$SEVERITY" ]; then
    echo "Usage: ./security_incident_response.sh <type> <severity>"
    echo "Types: data_breach, unauthorized_access, malware, dos_attack"
    echo "Severity: low, medium, high, critical"
    exit 1
fi

echo "=== Security Incident Response ==="
echo "Type: $INCIDENT_TYPE"
echo "Severity: $SEVERITY"
echo "Time: $(date)"

# 1. Immediate containment
if [ "$SEVERITY" = "critical" ] || [ "$SEVERITY" = "high" ]; then
    echo "Implementing immediate containment..."
    
    # Block suspicious IPs
    ./block_suspicious_ips.sh
    
    # Disable external API access
    docker-compose stop nginx
    
    # Enable enhanced logging
    ./enable_debug_logging.sh
fi

# 2. Evidence collection
echo "Collecting evidence..."
mkdir -p /var/log/incidents/$(date +%Y%m%d_%H%M%S)
INCIDENT_DIR="/var/log/incidents/$(date +%Y%m%d_%H%M%S)"

# Collect logs
cp /var/log/emailbot/* $INCIDENT_DIR/
docker logs emailbot > $INCIDENT_DIR/application.log
docker logs emailbot-postgres > $INCIDENT_DIR/database.log
docker logs emailbot-redis > $INCIDENT_DIR/cache.log

# System state
ps aux > $INCIDENT_DIR/processes.txt
netstat -tulpn > $INCIDENT_DIR/network.txt
df -h > $INCIDENT_DIR/disk_usage.txt

# 3. Notification
./send_incident_notification.sh "$INCIDENT_TYPE" "$SEVERITY" "$INCIDENT_DIR"

echo "Incident response procedures initiated"
echo "Evidence collected in: $INCIDENT_DIR"
```

## 📈 Capacity Planning

### Resource Usage Analysis
```python
class CapacityAnalyzer:
    """Analyze system capacity and usage trends."""
    
    async def analyze_capacity_trends(self, days: int = 30) -> Dict[str, Any]:
        """Analyze capacity trends over specified period."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        analysis = {
            "analysis_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            }
        }
        
        # Email volume trends
        email_volume = await self._analyze_email_volume(start_date, end_date)
        analysis["email_volume"] = {
            "current_daily_average": email_volume["daily_avg"],
            "growth_rate": email_volume["growth_rate"],
            "peak_daily_volume": email_volume["peak_day"],
            "projected_volume": email_volume["projected_volume"]
        }
        
        # System resource usage
        resource_usage = await self._analyze_resource_usage(start_date, end_date)
        analysis["resource_usage"] = {
            "cpu": {
                "average": resource_usage["cpu"]["avg"],
                "peak": resource_usage["cpu"]["peak"],
                "trend": resource_usage["cpu"]["trend"]
            },
            "memory": {
                "average": resource_usage["memory"]["avg"],
                "peak": resource_usage["memory"]["peak"],
                "trend": resource_usage["memory"]["trend"]
            },
            "storage": {
                "used": resource_usage["storage"]["used"],
                "growth_rate": resource_usage["storage"]["growth_rate"],
                "projected_full": resource_usage["storage"]["projected_full"]
            }
        }
        
        # Capacity recommendations
        analysis["recommendations"] = await self._generate_capacity_recommendations(
            email_volume, resource_usage
        )
        
        return analysis

    async def _generate_capacity_recommendations(
        self, 
        email_volume: Dict[str, Any], 
        resource_usage: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate capacity planning recommendations."""
        recommendations = []
        
        # Email volume scaling
        if email_volume["growth_rate"] > 0.2:  # 20% growth
            recommendations.append({
                "type": "scaling",
                "priority": "medium",
                "description": "Email volume growing rapidly",
                "action": "Consider increasing processing capacity",
                "details": {
                    "current_growth": f"{email_volume['growth_rate']:.1%}",
                    "recommended_action": "Add processing workers or increase batch size"
                }
            })
        
        # CPU scaling
        if resource_usage["cpu"]["avg"] > 70:
            recommendations.append({
                "type": "cpu",
                "priority": "high",
                "description": "High CPU utilization",
                "action": "Scale up CPU resources",
                "details": {
                    "current_avg": f"{resource_usage['cpu']['avg']}%",
                    "recommended_action": "Increase CPU cores or add horizontal scaling"
                }
            })
        
        # Memory scaling
        if resource_usage["memory"]["avg"] > 80:
            recommendations.append({
                "type": "memory",
                "priority": "high",
                "description": "High memory utilization",
                "action": "Increase memory allocation",
                "details": {
                    "current_avg": f"{resource_usage['memory']['avg']}%",
                    "recommended_action": "Increase RAM or optimize memory usage"
                }
            })
        
        # Storage planning
        if resource_usage["storage"]["projected_full"] < 90:  # Less than 90 days
            recommendations.append({
                "type": "storage",
                "priority": "medium",
                "description": "Storage will be full soon",
                "action": "Plan storage expansion",
                "details": {
                    "projected_full_days": resource_usage["storage"]["projected_full"],
                    "recommended_action": "Implement data archival or expand storage"
                }
            })
        
        return recommendations
```

## 🚨 Emergency Procedures

### System Recovery Checklist
```markdown
# Emergency System Recovery Checklist

## Immediate Response (0-15 minutes)
- [ ] Assess severity of outage
- [ ] Check system status dashboard
- [ ] Verify external dependencies (M365, OpenAI)
- [ ] Check basic connectivity (ping, DNS)
- [ ] Review recent changes/deployments

## Containment (15-30 minutes)
- [ ] Isolate affected components
- [ ] Enable maintenance mode if needed
- [ ] Preserve logs and evidence
- [ ] Notify stakeholders
- [ ] Document incident start time

## Investigation (30-60 minutes)
- [ ] Review application logs
- [ ] Check database connectivity
- [ ] Verify external API status
- [ ] Check resource utilization
- [ ] Identify root cause

## Recovery (60+ minutes)
- [ ] Implement fix or workaround
- [ ] Restore from backup if needed
- [ ] Verify system functionality
- [ ] Gradual traffic restoration
- [ ] Monitor for stability

## Post-Incident
- [ ] Complete incident report
- [ ] Update runbooks if needed
- [ ] Schedule post-mortem review
- [ ] Implement preventive measures
```

### Contact Information
```yaml
# Emergency Contacts
Primary On-Call: +1-555-0101
Secondary On-Call: +1-555-0102
IT Manager: +1-555-0103
System Administrator: +1-555-0104

# Vendor Support
Microsoft Support: support.microsoft.com
OpenAI Support: help.openai.com
Cloud Provider: [provider-specific]

# Internal Escalation
Level 1: Help Desk
Level 2: System Administrator  
Level 3: IT Manager
Level 4: CIO
```

---

**Document Status**: Operations Ready  
**Last Updated**: January 2025  
**Next Review**: Quarterly operations review 