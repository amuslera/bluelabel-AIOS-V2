# AIOS v2 Operational Runbook

This runbook contains step-by-step procedures for common operational tasks and incident response.

## Table of Contents
- [Daily Operations](#daily-operations)
- [Deployment Procedures](#deployment-procedures)
- [Incident Response](#incident-response)
- [Maintenance Tasks](#maintenance-tasks)
- [Disaster Recovery](#disaster-recovery)
- [Performance Tuning](#performance-tuning)

## Daily Operations

### Morning Health Check
```bash
# 1. Check system health
curl https://api.aios.example.com/health/detailed

# 2. Check metrics
curl https://api.aios.example.com/metrics | grep -E "error|failed"

# 3. Check disk space
ssh prod-server df -h

# 4. Check logs for errors
ssh prod-server 'cd /opt/aios && docker-compose logs --tail=100 | grep ERROR'

# 5. Verify backups completed
ssh prod-server ls -la /opt/aios/backups/
```

### Monitor Active Users
```sql
-- Connect to production database
psql $DATABASE_URL

-- Check active users in last hour
SELECT COUNT(DISTINCT user_id) as active_users
FROM user_activity
WHERE created_at >= NOW() - INTERVAL '1 hour';

-- Check agent installations today
SELECT COUNT(*) as new_installations
FROM agent_installations
WHERE installed_at >= CURRENT_DATE;
```

## Deployment Procedures

### Standard Deployment

#### Pre-deployment Checklist
- [ ] All tests passing in CI/CD
- [ ] Change log updated
- [ ] Database migrations reviewed
- [ ] Rollback plan prepared
- [ ] Team notified via Slack

#### Deployment Steps
1. **Create deployment tag**
   ```bash
   git tag -a v1.0.1 -m "Release v1.0.1: Bug fixes"
   git push origin v1.0.1
   ```

2. **Trigger deployment**
   ```bash
   gh workflow run production.yml -f version=v1.0.1
   ```

3. **Monitor deployment**
   ```bash
   # Watch GitHub Actions
   gh run watch

   # Monitor application logs
   ssh prod-server 'cd /opt/aios && docker-compose logs -f'
   ```

4. **Verify deployment**
   ```bash
   # Check version
   curl https://api.aios.example.com/health | jq .version

   # Run smoke tests
   ./scripts/test/smoke_tests.sh production
   ```

### Emergency Deployment

When critical fixes need immediate deployment:

1. **Create hotfix branch**
   ```bash
   git checkout -b hotfix/critical-fix
   git cherry-pick <commit-hash>
   git push origin hotfix/critical-fix
   ```

2. **Fast-track deployment**
   ```bash
   # Skip staging, deploy directly
   ./scripts/deployment/deploy.sh production --emergency --skip-tests
   ```

3. **Post-deployment verification**
   ```bash
   # Extensive health checks
   for endpoint in health metrics marketplace/stats; do
     curl -f https://api.aios.example.com/$endpoint || echo "FAILED: $endpoint"
   done
   ```

## Incident Response

### Severity Levels
- **SEV1**: Complete outage, data loss risk
- **SEV2**: Major functionality broken, significant performance degradation
- **SEV3**: Minor functionality affected, workaround available
- **SEV4**: Cosmetic issues, minor bugs

### SEV1 Response Procedure

1. **Immediate Actions** (0-5 minutes)
   ```bash
   # Check if site is up
   curl -I https://aios.example.com

   # Check API health
   curl https://api.aios.example.com/health

   # Check all containers
   ssh prod-server docker ps -a
   ```

2. **Triage** (5-15 minutes)
   ```bash
   # Check error logs
   ssh prod-server 'cd /opt/aios && docker-compose logs --tail=500 | grep -E "ERROR|CRITICAL"'

   # Check database
   ssh prod-server 'docker exec aios-postgres pg_isready'

   # Check disk space
   ssh prod-server df -h

   # Check memory
   ssh prod-server free -h
   ```

3. **Mitigation** (15-30 minutes)
   
   **If containers crashed:**
   ```bash
   ssh prod-server 'cd /opt/aios && docker-compose restart'
   ```
   
   **If database issues:**
   ```bash
   # Restart database
   ssh prod-server 'docker restart aios-postgres'
   
   # If corrupted, restore from backup
   ./scripts/restore_database.sh latest
   ```
   
   **If out of disk space:**
   ```bash
   # Clean up logs
   ssh prod-server 'docker system prune -a --volumes'
   
   # Archive old logs
   ssh prod-server 'cd /opt/aios/logs && tar -czf archive_$(date +%Y%m%d).tar.gz *.log && rm *.log'
   ```

4. **Communication**
   - Update status page
   - Post in #incidents Slack channel
   - Email major customers if > 30 min downtime

### Performance Degradation Response

1. **Identify bottleneck**
   ```bash
   # Check CPU usage
   ssh prod-server 'docker stats --no-stream'
   
   # Check slow queries
   ssh prod-server 'docker exec aios-postgres psql -U aios -d aios_v2 -c "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"'
   
   # Check Redis memory
   ssh prod-server 'docker exec aios-redis redis-cli INFO memory'
   ```

2. **Scale resources**
   ```bash
   # Scale API workers
   ssh prod-server 'cd /opt/aios && docker-compose scale api=4'
   
   # Clear Redis cache
   ssh prod-server 'docker exec aios-redis redis-cli FLUSHDB'
   ```

## Maintenance Tasks

### Weekly Maintenance

1. **Database maintenance**
   ```sql
   -- Vacuum and analyze
   VACUUM ANALYZE;
   
   -- Update statistics
   ANALYZE;
   
   -- Check table sizes
   SELECT 
     schemaname,
     tablename,
     pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
   FROM pg_tables
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
   LIMIT 20;
   ```

2. **Log rotation**
   ```bash
   # Archive logs older than 7 days
   ssh prod-server 'find /opt/aios/logs -name "*.log" -mtime +7 -exec gzip {} \;'
   
   # Move to archive
   ssh prod-server 'mv /opt/aios/logs/*.gz /opt/aios/logs/archive/'
   ```

3. **Security updates**
   ```bash
   # Check for security updates
   docker run --rm aquasec/trivy image aios-api:latest
   
   # Update base images if needed
   docker pull python:3.11-slim
   docker pull node:18-alpine
   ```

### Monthly Maintenance

1. **Full backup test**
   ```bash
   # Restore backup to staging
   ./scripts/restore_database.sh latest staging
   
   # Verify data integrity
   ./scripts/verify_backup.sh
   ```

2. **Certificate renewal**
   ```bash
   # Check certificate expiry
   echo | openssl s_client -servername aios.example.com -connect aios.example.com:443 2>/dev/null | openssl x509 -noout -dates
   
   # Renew if needed (Let's Encrypt)
   ssh prod-server 'certbot renew'
   ```

3. **Dependency updates**
   ```bash
   # Check for updates
   pip list --outdated
   npm outdated
   
   # Update in development first
   pip install --upgrade -r requirements.txt
   npm update
   ```

## Disaster Recovery

### Data Recovery

1. **Identify last good backup**
   ```bash
   ssh prod-server 'ls -la /opt/aios/backups/ | tail -10'
   ```

2. **Restore database**
   ```bash
   # Stop application
   ssh prod-server 'cd /opt/aios && docker-compose stop api web'
   
   # Restore database
   ssh prod-server 'docker exec -i aios-postgres psql -U aios -d aios_v2 < /opt/aios/backups/db_backup_20240101_120000.sql'
   
   # Restart application
   ssh prod-server 'cd /opt/aios && docker-compose start api web'
   ```

3. **Verify data integrity**
   ```sql
   -- Check record counts
   SELECT 
     'users' as table_name, COUNT(*) as count FROM users
   UNION ALL
   SELECT 'agents', COUNT(*) FROM marketplace_agents
   UNION ALL
   SELECT 'installations', COUNT(*) FROM agent_installations;
   ```

### Full System Recovery

If entire system needs to be rebuilt:

1. **Provision new infrastructure**
   ```bash
   # Use Terraform if available
   cd terraform
   terraform apply -var="environment=production"
   ```

2. **Deploy application**
   ```bash
   # Clone repository
   git clone https://github.com/your-org/bluelabel-AIOS-V2.git
   cd bluelabel-AIOS-V2
   
   # Deploy
   ./scripts/deployment/deploy.sh production --fresh-install
   ```

3. **Restore data**
   ```bash
   # Restore database
   ./scripts/restore_database.sh latest
   
   # Restore file uploads
   aws s3 sync s3://aios-backups/files/ /opt/aios/data/
   ```

## Performance Tuning

### Database Optimization

1. **Identify slow queries**
   ```sql
   -- Install pg_stat_statements if not exists
   CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
   
   -- Find slow queries
   SELECT 
     query,
     calls,
     total_time,
     mean_time,
     min_time,
     max_time
   FROM pg_stat_statements
   WHERE mean_time > 100  -- queries taking > 100ms
   ORDER BY mean_time DESC
   LIMIT 20;
   ```

2. **Add indexes**
   ```sql
   -- Check missing indexes
   SELECT 
     schemaname,
     tablename,
     attname,
     n_distinct,
     most_common_vals
   FROM pg_stats
   WHERE schemaname = 'public'
   AND n_distinct > 100
   AND attname NOT IN (
     SELECT column_name
     FROM information_schema.constraint_column_usage
   );
   ```

3. **Connection pooling**
   ```bash
   # Adjust pool size in .env
   DATABASE_POOL_SIZE=20
   DATABASE_MAX_OVERFLOW=40
   
   # Monitor connections
   ssh prod-server 'docker exec aios-postgres psql -U aios -d aios_v2 -c "SELECT count(*) FROM pg_stat_activity;"'
   ```

### Application Optimization

1. **Enable caching**
   ```python
   # Redis caching for expensive operations
   from functools import lru_cache
   from redis import Redis
   
   redis_client = Redis.from_url(REDIS_URL)
   
   @lru_cache(maxsize=1000)
   def get_popular_agents():
       # Cache for 1 hour
       return redis_client.get("popular_agents")
   ```

2. **API response optimization**
   ```bash
   # Enable compression
   # Add to nginx config
   gzip on;
   gzip_types application/json;
   gzip_min_length 1000;
   ```

## Monitoring Alerts

### Critical Alerts

1. **API Down**
   - Threshold: 3 failed health checks in 5 minutes
   - Action: Check containers, restart if needed

2. **High Error Rate**
   - Threshold: > 5% 5xx errors
   - Action: Check logs, scale resources

3. **Database Connection Pool Exhausted**
   - Threshold: > 90% connections used
   - Action: Increase pool size, check for connection leaks

4. **Disk Space Low**
   - Threshold: < 10% free space
   - Action: Clean logs, archive old data

### Alert Configuration

```yaml
# prometheus/alerts.yml
groups:
  - name: aios_alerts
    rules:
      - alert: APIDown
        expr: up{job="aios-api"} == 0
        for: 5m
        annotations:
          summary: "API is down"
          
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 10m
        annotations:
          summary: "High error rate detected"
```

## Contact Information

### Escalation Chain
1. On-call engineer (PagerDuty)
2. Team lead
3. CTO

### External Contacts
- **Hosting Provider**: support@provider.com
- **Database Support**: dba@consultancy.com
- **Security Team**: security@company.com

## Appendix

### Useful Commands
```bash
# Container management
docker-compose ps                    # List containers
docker-compose logs -f api          # Follow API logs
docker-compose exec api bash        # Shell into API container
docker stats                        # Monitor resource usage

# Database queries
psql $DATABASE_URL                  # Connect to database
\dt                                # List tables
\d+ table_name                     # Describe table
\x                                 # Expanded display mode

# Network debugging
curl -v https://api.aios.example.com/health
dig api.aios.example.com
traceroute api.aios.example.com
```

### Environment Variables Reference
See [.env.example](../../.env.example) for complete list of configuration options.