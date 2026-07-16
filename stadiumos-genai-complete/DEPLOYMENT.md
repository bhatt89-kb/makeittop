# StadiumOS GenAI - Docker Deployment Guide

## Quick Start (5 minutes)

### Prerequisites

1. **Install Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
   - Windows: https://docs.docker.com/desktop/install/windows-install/
   - Mac: https://docs.docker.com/desktop/install/mac-install/
   - Linux: https://docs.docker.com/engine/install/

2. **Install Docker Compose** (included with Docker Desktop, separate for Linux)
   - Verify: `docker-compose --version` should show v2.x or higher

3. **Git** (to clone the repository)

---

## Step-by-Step Deployment

### 1. Navigate to Project Directory

```bash
cd c:\Users\User\OneDrive\Desktop\project4\stadiumos-genai-complete\stadiumos-genai
```

### 2. Configure Environment Variables

Create a `.env` file in the `backend` directory:

```bash
# Copy the example file
copy backend\.env.example backend\.env

# Edit with your favorite editor
notepad backend\.env
```

**Required Configuration:**

```env
# --- GenAI provider ---
# Get your API key from: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here
ANTHROPIC_MODEL=claude-sonnet-4-6

# --- Redis Cache ---
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_ENABLED=true

# --- Environment ---
ENVIRONMENT=production
DEBUG=false

# --- Security ---
# Generate a secure key: python -c "import secrets; print(secrets.token_urlsafe(32))"
ADMIN_API_KEY=your-secure-random-key-here
ALLOWED_ORIGINS=["http://localhost:8080","http://your-domain.com"]
RATE_LIMIT_REQUESTS=30
RATE_LIMIT_WINDOW_SECONDS=60
MAX_REQUEST_BODY_BYTES=20000

# --- Feature flags ---
ENABLE_RULE_BASED_FALLBACK=true
```

### 3. Build and Start Services

```bash
# Build all services
docker-compose build

# Start all services in detached mode
docker-compose up -d

# View logs
docker-compose logs -f
```

**Expected Output:**
```
✔ Container stadiumos-genai-redis-1      Started
✔ Container stadiumos-genai-backend-1    Started
✔ Container stadiumos-genai-frontend-1   Started
```

### 4. Verify Deployment

**Check Service Health:**
```bash
# Check all containers are running
docker-compose ps

# Should show:
# NAME                           STATUS              PORTS
# stadiumos-genai-backend-1      Up (healthy)        0.0.0.0:8000->8000/tcp
# stadiumos-genai-frontend-1     Up                  0.0.0.0:8080->8080/tcp
# stadiumos-genai-redis-1        Up (healthy)        0.0.0.0:6379->6379/tcp
```

**Test the API:**
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Expected: {"status":"healthy","genai_available":true}
```

**Access the Application:**
- **Frontend:** http://localhost:8080
- **API Docs:** http://localhost:8000/docs
- **API Health:** http://localhost:8000/api/v1/health

---

## Service Architecture

```
┌─────────────────────────────────────────┐
│     Docker Compose Stack                │
│                                         │
│  ┌────────────┐  ┌────────────┐       │
│  │  Frontend  │  │  Backend   │       │
│  │  :8080     │◄─┤  :8000     │       │
│  └────────────┘  └──────┬─────┘       │
│                          │              │
│                  ┌───────▼────────┐    │
│                  │     Redis      │    │
│                  │     :6379      │    │
│                  └────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

---

## Common Operations

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f redis

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Stop Services

```bash
# Stop all (preserves data)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove everything including volumes (⚠️ deletes Redis data)
docker-compose down -v
```

### Update Code

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose build
docker-compose up -d

# Or do it in one command
docker-compose up -d --build
```

### Scale Backend (Load Balancing)

```bash
# Run 3 backend instances
docker-compose up -d --scale backend=3

# Note: Requires load balancer configuration (nginx)
```

---

## Monitoring & Maintenance

### Check Container Stats

```bash
# Real-time resource usage
docker stats

# CPU, Memory, Network I/O for each container
```

### Access Container Shell

```bash
# Backend container
docker-compose exec backend bash

# Redis CLI
docker-compose exec redis redis-cli

# Check Redis cache
docker-compose exec redis redis-cli INFO stats
```

### Database Backup (Redis)

```bash
# Trigger Redis save
docker-compose exec redis redis-cli BGSAVE

# Copy Redis dump file
docker cp stadiumos-genai-redis-1:/data/dump.rdb ./backup/dump-$(date +%Y%m%d).rdb
```

### View Cache Stats

```bash
# Using admin API
curl -H "X-Admin-Key: your-admin-key" http://localhost:8000/admin/cache/stats
```

---

## Troubleshooting

### Port Already in Use

**Error:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (Windows)
taskkill /PID <PID> /F

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use external port 8001
```

### Backend Won't Start

**Error:** `ANTHROPIC_API_KEY is required`

**Solution:**
```bash
# Check .env file exists and has API key
cat backend\.env | findstr ANTHROPIC_API_KEY

# If missing, add it:
echo ANTHROPIC_API_KEY=sk-ant-your-key >> backend\.env

# Restart
docker-compose restart backend
```

### Redis Connection Failed

**Error:** `Redis unavailable, caching disabled`

**Solution:**
```bash
# Check Redis is running
docker-compose ps redis

# Check Redis health
docker-compose exec redis redis-cli ping
# Should return: PONG

# Check logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

### Container Keeps Restarting

```bash
# Check logs for the failing container
docker-compose logs backend

# Common issues:
# 1. Missing environment variables → check .env
# 2. Port conflicts → change ports in docker-compose.yml
# 3. Dependency not ready → check depends_on and healthcheck
```

### Clear Cache and Rebuild

```bash
# Remove all containers, images, and volumes
docker-compose down -v --rmi all

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

---

## Production Deployment

### Using Docker Compose (Production)

1. **Create production .env file:**
   ```bash
   cp backend/.env.example backend/.env.production
   # Edit with production values
   ```

2. **Use production compose file:**
   ```yaml
   # docker-compose.prod.yml
   version: "3.9"
   
   services:
     backend:
       build: ./backend
       restart: always
       env_file:
         - ./backend/.env.production
       environment:
         - ENVIRONMENT=production
         - DEBUG=false
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 2G
           reservations:
             cpus: '1'
             memory: 512M
   ```

3. **Deploy:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Using Docker Swarm (High Availability)

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml stadiumos

# Scale services
docker service scale stadiumos_backend=3

# Update service
docker service update --image stadiumos-backend:v2 stadiumos_backend

# Remove stack
docker stack rm stadiumos
```

### Using Kubernetes (Enterprise)

See `k8s/` directory for Kubernetes manifests:
- `k8s/deployment.yml` - Backend deployment
- `k8s/service.yml` - Service definitions
- `k8s/ingress.yml` - Ingress rules
- `k8s/redis.yml` - Redis StatefulSet

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check status
kubectl get pods
kubectl get services
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes* | - | Anthropic API key (* optional if fallback enabled) |
| `ANTHROPIC_MODEL` | No | claude-sonnet-4-6 | AI model to use |
| `REDIS_HOST` | No | localhost | Redis server hostname |
| `REDIS_PORT` | No | 6379 | Redis server port |
| `REDIS_DB` | No | 0 | Redis database number |
| `REDIS_ENABLED` | No | true | Enable/disable caching |
| `ENVIRONMENT` | No | development | Environment (development/production) |
| `DEBUG` | No | false | Enable debug logging |
| `ADMIN_API_KEY` | Yes | - | Admin endpoint authentication key |
| `ALLOWED_ORIGINS` | No | ["*"] | CORS allowed origins (JSON array) |
| `RATE_LIMIT_REQUESTS` | No | 30 | Max requests per window |
| `RATE_LIMIT_WINDOW_SECONDS` | No | 60 | Rate limit window |
| `MAX_REQUEST_BODY_BYTES` | No | 20000 | Max request body size |
| `ENABLE_RULE_BASED_FALLBACK` | No | true | Enable deterministic fallback |

---

## Performance Optimization

### Production Settings

```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
  
  redis:
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
    deploy:
      resources:
        limits:
          memory: 512M
```

### Add Nginx Load Balancer

```yaml
# docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
```

---

## Security Checklist

- [ ] Generate strong `ADMIN_API_KEY` (32+ characters)
- [ ] Set `ENVIRONMENT=production` and `DEBUG=false`
- [ ] Configure `ALLOWED_ORIGINS` with your domain
- [ ] Enable SSL/TLS (use nginx reverse proxy)
- [ ] Set resource limits in docker-compose
- [ ] Use Docker secrets for sensitive data
- [ ] Enable Docker Content Trust (`export DOCKER_CONTENT_TRUST=1`)
- [ ] Run containers as non-root user (already configured)
- [ ] Scan images for vulnerabilities (`docker scan stadiumos-backend`)
- [ ] Keep base images updated (`docker-compose pull`)

---

## Backup & Recovery

### Backup Script

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/$DATE"

mkdir -p "$BACKUP_DIR"

# Backup Redis data
docker-compose exec redis redis-cli BGSAVE
docker cp stadiumos-genai-redis-1:/data/dump.rdb "$BACKUP_DIR/redis-dump.rdb"

# Backup configuration
cp backend/.env "$BACKUP_DIR/.env.backup"
cp docker-compose.yml "$BACKUP_DIR/docker-compose.yml.backup"

# Backup logs
docker-compose logs > "$BACKUP_DIR/logs.txt"

echo "Backup completed: $BACKUP_DIR"
```

### Restore Script

```bash
#!/bin/bash
# restore.sh

BACKUP_DIR=$1

# Stop services
docker-compose down

# Restore Redis data
docker-compose up -d redis
sleep 5
docker cp "$BACKUP_DIR/redis-dump.rdb" stadiumos-genai-redis-1:/data/dump.rdb
docker-compose restart redis

# Restore configuration
cp "$BACKUP_DIR/.env.backup" backend/.env

# Start all services
docker-compose up -d
```

---

## Next Steps

1. ✅ Deploy with Docker Compose
2. 📊 Set up monitoring (Grafana + Prometheus)
3. 🔒 Configure SSL/TLS with Let's Encrypt
4. 📈 Load test with Locust
5. 🚀 Set up CI/CD with GitHub Actions
6. 📱 Configure domain and DNS
7. 🔔 Set up alerting (Alertmanager)

---

## Support & Resources

- **Documentation:** `docs/` directory
- **Architecture:** `docs/ARCHITECTURE.md`
- **Security:** `docs/SECURITY.md`
- **Performance:** `docs/PERFORMANCE.md`
- **API Reference:** http://localhost:8000/docs (when running)

---

## Quick Commands Cheat Sheet

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Logs
docker-compose logs -f

# Restart
docker-compose restart

# Rebuild
docker-compose up -d --build

# Shell access
docker-compose exec backend bash

# Redis CLI
docker-compose exec redis redis-cli

# Stats
docker stats

# Clean up
docker-compose down -v
docker system prune -a
```

---

**You're now ready to deploy StadiumOS GenAI with Docker! 🎉**

For production deployment, see the Production section above or contact the team.
