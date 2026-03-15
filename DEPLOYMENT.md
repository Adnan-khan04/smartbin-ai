# SmartBin AI - Production Deployment Guide

## Overview

SmartBin AI is a smart waste segregation and gamified recycling system with:
- **Backend**: FastAPI + PostgreSQL + PyTorch ML model
- **Frontend**: React + Vite
- **Deployment**: Docker Compose with Nginx reverse proxy

## Prerequisites

- Docker & Docker Compose (latest versions)
- 4GB minimum RAM
- 20GB minimum disk space
- A domain name (for production SSL)

## Quick Start - Development

```bash
cd smartbin-ai

# Copy environment template
cp .env.example .env

# Start services
docker-compose up -d

# Access the application
# Frontend: http://localhost:5173 (dev server)
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

## Production Deployment

### 1. Environment Configuration

```bash
# Copy example template
cp .env.example .env.production

# Edit with production values
nano .env.production
```

**Critical settings:**
```env
SECRET_KEY=<generate-strong-random-key>
CORS_ORIGINS=https://yourdomain.com
DATABASE_URL=postgresql://smartbin:STRONG_PASSWORD@postgres:5432/smartbin_ai
ENV=production
LOG_LEVEL=WARNING
```

Generate a strong SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Deploy with Docker Compose

```bash
# Load production environment
export $(cat .env.production | xargs)

# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Verify services are running
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### 3. SSL/TLS with Let's Encrypt (Nginx Reverse Proxy)

Create an additional nginx service in docker-compose for SSL termination:

```yaml
nginx-proxy:
  image: nginx:alpine
  restart: always
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx-proxy.conf:/etc/nginx/nginx.conf:ro
    - ./certs:/etc/nginx/certs:ro
  depends_on:
    - frontend
```

Or use Caddy for automatic SSL:

```bash
# Add to docker-compose.prod.yml
caddy:
  image: caddy:latest
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./Caddyfile:/etc/caddy/Caddyfile:ro
    - caddy_data:/data
  depends_on:
    - backend
    - frontend
```

### 4. Database Backups

```bash
# Backup PostgreSQL database
docker-compose exec postgres pg_dump -U smartbin smartbin_ai > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
docker-compose exec -T postgres psql -U smartbin smartbin_ai < backup_20250217_120000.sql
```

### 5. Health Checks & Monitoring

**Backend health:**
```bash
curl http://localhost:8000/health
```

**Frontend health:**
```bash
curl http://localhost/health
```

**Monitor logs:**
```bash
# Real-time logs
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

## Security Best Practices

### Implemented Features
✅ JWT authentication with username-only
✅ Password hashing with bcrypt
✅ Input validation & sanitization
✅ CORS restriction to configured domains only
✅ Security headers (X-Frame-Options, X-Content-Type-Options, etc.)
✅ Non-root Docker users
✅ Rate limiting ready (configure in production)
✅ HTTPS/TLS termination via Nginx
✅ Database credentials in environment variables

### Additional Recommendations

1. **Firewall**: Restrict access to port 5432 (PostgreSQL)
2. **Secrets Management**: Use cloud secrets manager (AWS Secrets Manager, Azure Key Vault)
3. **Rate Limiting**: Add to production deployment
4. **WAF**: Use cloud WAF (AWS WAF, Cloudflare)
5. **DDoS Protection**: Enable on CDN/proxy
6. **Audit Logging**: Monitor authentication and classification events
7. **API Key Rotation**: Implement in production
8. **SSL Certificate**: Renew before expiration

## Scaling & Performance

### Horizontal Scaling
```bash
# Scale backend services
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Use load balancer (HAProxy, Nginx, or cloud LB)
```

### Database Optimization
```sql
-- Create indexes on frequently queried columns
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_classifications_user_id ON classifications(user_id);
CREATE INDEX idx_classifications_created ON classifications(created_at);
```

### Caching Strategy
- Frontend: Browser cache (1 year for assets)
- API: Redis caching for leaderboard, user stats
- Database: Connection pooling with PgBouncer

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Verify database connection
docker-compose exec backend python -c "from database import SessionLocal; db = SessionLocal(); print('OK')"

# Check SECRET_KEY is set
docker-compose exec backend echo $SECRET_KEY
```

### Frontend not loading
```bash
# Check Nginx configuration
docker-compose logs frontend

# Verify API URL
curl http://localhost/api/health
```

### Database connection issues
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U smartbin -d smartbin_ai -c "SELECT 1"
```

### Model loading errors
```bash
# Verify model file exists in backend/models/
docker-compose exec backend ls -lah models/

# Check model format
docker-compose exec backend python -c "import torch; torch.load('models/waste_classifier.pth')"
```

## Maintenance

### Regular Tasks

**Daily**
- Monitor logs for errors
- Check disk space
- Verify backups

**Weekly**
- Review application metrics
- Check for security updates

**Monthly**
- Database optimization & vacuum
- SSL certificate renewal check
- Security audit

### Updating the Application

```bash
# Pull latest code
git pull origin main

# Rebuild Docker images
docker-compose -f docker-compose.prod.yml build

# Redeploy with zero downtime
docker-compose -f docker-compose.prod.yml up -d
```

## Environment Variables Reference

```env
# Security
SECRET_KEY=<strong-random-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# Database
DATABASE_URL=postgresql://user:password@host:5432/db
DB_HOST=postgres
DB_PORT=5432
DB_NAME=smartbin_ai
DB_USER=smartbin
DB_PASSWORD=<strong-password>

# Model
MODEL_PATH=./models/waste_classifier.pth
AUTO_AWARD_THRESHOLD=0.6

# Server
ENV=production
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_WORKERS=4
CORS_ORIGINS=https://yourdomain.com

# Frontend
VITE_API_URL=https://yourdomain.com/api
VITE_APP_NAME=SmartBin AI
VITE_ENVIRONMENT=production

# Logging
LOG_LEVEL=WARNING
LOG_FILE=./logs/app.log

# Features
ENABLE_GAMIFICATION=true
ENABLE_LEADERBOARD=true
ENABLE_DEBUG_MODE=false
```

## Support & Documentation

- API Documentation: `http://localhost:8000/api/docs`
- Backend Setup: `docs/SETUP.md`
- API Reference: `docs/API.md`

## License

Private - SmartBin AI Hackathon Project
