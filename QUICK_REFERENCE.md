# SmartBin AI - Quick Reference Card

## 🚀 Local Setup (< 5 minutes)

```bash
# Automated
python setup.py

# OR Manual
cp .env.example .env
docker-compose up -d
```

**Access:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

## 📦 Production Deployment

```bash
# 1. Prepare environment
cp .env.production .env.prod
# EDIT .env.prod with real values:
# - SECRET_KEY
# - CORS_ORIGINS
# - DATABASE_URL
# - VITE_API_URL

# 2. Deploy
export $(cat .env.prod | xargs)
docker-compose -f docker-compose.prod.yml up -d

# 3. Verify
docker-compose -f docker-compose.prod.yml ps
curl http://localhost:8000/health
```

## 🔐 Security Checklist

- [ ] `SECRET_KEY` - Use: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] `CORS_ORIGINS` - Set to your domain: `https://yourdomain.com`
- [ ] `DB_PASSWORD` - Strong password (min 16 chars)
- [ ] SSL/TLS - Certificates installed
- [ ] Firewall - Port 5432 (DB) restricted

## 📝 Environment Variables (Key)

```env
# Security
SECRET_KEY=<random-string>
CORS_ORIGINS=https://yourdomain.com
ENV=production

# Database
DATABASE_URL=postgresql://user:password@postgres:5432/smartbin_ai

# Frontend
VITE_API_URL=https://yourdomain.com/api

# Logging
LOG_LEVEL=WARNING
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Services won't start | `docker-compose logs -f backend` |
| Database connection failed | `docker-compose exec postgres psql -U smartbin -d smartbin_ai -c "SELECT 1"` |
| Frontend not loading | Check `VITE_API_URL` environment variable |
| Model not found | Verify `backend/models/waste_classifier.pth` exists |
| 401 Unauthorized | Token may be invalid, try logging in again |
| 500 Server Error | Check backend logs: `docker-compose logs backend` |

## 📊 Key Metrics

```
Launch Time:     < 30 seconds
API Response:    < 500ms (p95)
Error Rate:      < 0.1%
Availability:    > 99.5%
```

## 🔄 Common Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart service
docker-compose restart backend

# Stop all
docker-compose down

# Full reset
docker-compose down -v  # Warning: deletes data

# Database backup
docker-compose exec postgres pg_dump -U smartbin smartbin_ai > backup.sql

# Database restore
docker-compose exec -T postgres psql -U smartbin smartbin_ai < backup.sql
```

## 📚 Documentation

- **Full Guide**: [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Pre-Launch**: [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md)
- **API Reference**: [docs/API.md](./docs/API.md)
- **Setup Help**: [docs/SETUP.md](./docs/SETUP.md)

## 👤 Test User Registration

```
Username: testuser
Password: Test@1234  (uppercase, lowercase, number, min 8 chars)
```

## 🆘 Emergency Contacts

- API Docs: http://localhost:8000/api/docs (development)
- Health Check: http://localhost:8000/health
- Database Container: smartbin-postgres
- Backend Container: smartbin-backend
- Frontend Container: smartbin-frontend

---

**Version**: 1.0.0 | **Status**: Production Ready ✅ | **Updated**: Feb 17, 2025
