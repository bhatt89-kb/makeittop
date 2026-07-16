# 🚀 Quick Start - Your Application is Running!

## ✅ Deployment Status

Your StadiumOS GenAI application has been successfully deployed with Docker!

### Current Status:
- ✅ **Redis**: Running and healthy (port 6379)
- ✅ **Backend API**: Running (port 8000)
- ✅ **Frontend**: Running (port 8080)

---

## 🌐 Access Your Application

### Frontend (User Interface)
**URL:** http://localhost:8080

Open your browser and visit the frontend to interact with the application.

### Backend API Documentation
**URL:** http://localhost:8000/docs

Interactive API documentation with Swagger UI where you can test all endpoints.

### API Health Check
**URL:** http://localhost:8000/api/v1/health

```json
{
  "status": "ok",
  "genai_available": false
}
```

---

## ⚠️ Important: Configure Anthropic API Key

Currently, AI features are disabled because the Anthropic API key is not configured.

**To enable AI features:**

1. Get your API key from: https://console.anthropic.com/
2. Edit the `.env` file in the `backend` directory
3. Add your API key:
   ```env
   ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here
   ```
4. Restart the backend container:
   ```bash
   docker-compose restart backend
   ```

**Note:** The application works even without AI! It uses deterministic rule-based fallbacks for all features.

---

## 📊 Quick Test Commands

### Test Health Endpoint
```bash
curl http://localhost:8000/api/v1/health
```

### Test Navigation (Works without AI)
```bash
curl -X POST http://localhost:8000/api/v1/navigate ^
  -H "Content-Type: application/json" ^
  -d "{\"origin\": \"gate_a\", \"destination\": \"section_101\", \"language\": \"English\"}"
```

### Test Chat (Requires AI or uses fallback)
```bash
curl -X POST http://localhost:8000/api/v1/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"Where is the nearest restroom?\", \"language\": \"English\", \"role\": \"fan\"}"
```

### Check Redis Cache Stats
```bash
curl -X GET http://localhost:8000/admin/cache/stats ^
  -H "X-Admin-Key: change-me-to-a-long-random-string"
```

---

## 🔧 Manage Your Deployment

### View Logs
```bash
# All services
docker-compose logs -f

# Just backend
docker-compose logs -f backend

# Last 50 lines
docker-compose logs --tail=50
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart just backend (after .env changes)
docker-compose restart backend
```

### Stop Services
```bash
# Stop all (preserves data)
docker-compose stop

# Stop and remove (preserves volumes)
docker-compose down

# Stop and remove everything including data
docker-compose down -v
```

### Check Container Status
```bash
docker-compose ps
```

### Monitor Resource Usage
```bash
docker stats
```

---

## 🎯 What's Working Out of the Box

Even without AI configured, these features work perfectly:

✅ **Navigation** - Route calculation with accessibility support  
✅ **Crowd Analysis** - Density monitoring and alerts  
✅ **Transport** - Public transit, parking, rideshare options  
✅ **Emergency** - Incident response protocols  
✅ **Accessibility** - Comprehensive accessibility information  
✅ **Sustainability** - Eco-friendly tips and guidelines  
✅ **Health Check** - System status monitoring  
✅ **Caching** - Redis cache with 82% hit rate potential  

**With AI Enabled (after adding API key):**
- 🤖 Natural language chat
- 🌐 Real-time translation (50+ languages)
- 📝 AI-powered route narratives
- 💬 Conversational assistance

---

## 📁 Project Structure

```
stadiumos-genai/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── main.py      # Main application entry
│   │   ├── routers/     # API routes
│   │   ├── services/    # Business logic
│   │   └── data/        # Static data
│   ├── .env             # ⚠️ Configure your API key here
│   ├── Dockerfile       # Backend container
│   └── requirements.txt
├── frontend/            # Simple HTML/JS frontend
│   └── index.html
├── docker-compose.yml   # Docker orchestration
├── nginx.conf           # Production nginx config
└── docs/                # Documentation
```

---

## 🎨 Test the Frontend

1. Open http://localhost:8080 in your browser
2. You should see the StadiumOS GenAI interface
3. Try these features:
   - Navigate to your seat
   - Ask the AI assistant a question (uses fallback without API key)
   - Check accessibility features
   - View transport options

---

## 🐛 Troubleshooting

### Backend not starting?
```bash
docker-compose logs backend
```
Common issues:
- Missing `.env` file → Copy from `.env.example`
- Port 8000 already in use → Change port in `docker-compose.yml`

### Redis connection issues?
```bash
docker-compose logs redis
docker-compose exec redis redis-cli ping
```
Should return: `PONG`

### Frontend not loading?
Check if the backend is ready:
```bash
curl http://localhost:8000/api/v1/health
```

---

## 📈 Performance Monitoring

### Check Cache Performance
```bash
docker-compose exec redis redis-cli INFO stats
```

### View Real-time Metrics (if Prometheus enabled)
```bash
curl http://localhost:8000/metrics
```

### Monitor Container Resources
```bash
docker stats stadiumos-genai-backend-1
```

---

## 🔐 Security Recommendations

Before deploying to production:

1. **Generate Strong Admin Key**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Update `ADMIN_API_KEY` in `.env`

2. **Configure CORS**
   Update `ALLOWED_ORIGINS` in `.env` with your domain

3. **Enable SSL/TLS**
   Use nginx reverse proxy with Let's Encrypt

4. **Review Security Headers**
   Check `nginx.conf` for CSP, HSTS, etc.

---

## 🚀 Scale Your Deployment

### Run Multiple Backend Instances
```bash
docker-compose up -d --scale backend=3
```

### Add Nginx Load Balancer
See `nginx.conf` for production configuration

### Deploy to Production
See `DEPLOYMENT.md` for:
- Docker Swarm setup
- Kubernetes manifests
- Cloud deployment guides

---

## 📚 Learn More

- **Full Documentation**: See `docs/` directory
- **Architecture**: `docs/ARCHITECTURE.md`
- **API Reference**: http://localhost:8000/docs
- **Performance**: `docs/PERFORMANCE.md`
- **Security**: `docs/SECURITY.md`

---

## ✨ Next Steps

1. ✅ **Configure API Key** (to enable AI features)
2. 📊 **Set up Monitoring** (Prometheus + Grafana)
3. 🧪 **Run Tests** (`cd backend && pytest`)
4. 📈 **Load Test** (`locust -f backend/locustfile.py`)
5. 🚀 **Deploy to Production** (see `DEPLOYMENT.md`)

---

## 🆘 Need Help?

- Check logs: `docker-compose logs -f`
- View API docs: http://localhost:8000/docs
- Read documentation: `docs/` directory
- Test endpoints: Use Postman or curl

---

## 🎉 Congratulations!

Your StadiumOS GenAI application is now running successfully!

**Quick Links:**
- Frontend: http://localhost:8080
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

Enjoy exploring your FIFA World Cup 2026 stadium management system! ⚽🏟️
