# SmartBin AI - Smart Waste Segregation & Gamified Recycling System

<div align="center">

![SmartBin AI](https://img.shields.io/badge/SmartBin%20AI-Production%20Ready-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-Private-blue?style=for-the-badge)

**Intelligent waste management system that uses machine learning to classify waste and gamify recycling**

[🚀 Quick Start](#quick-start) • [📚 Docs](#documentation) • [🐳 Deployment](#deployment) • [🤝 Contributing](#contributing)

</div>

---

## 📋 Project Overview

SmartBin AI is a **production-ready** intelligent waste management system that uses machine learning to classify waste and gamify the recycling process. Users take photos of waste, the AI identifies the type (plastic, paper, metal, organic), guides them to proper disposal, and rewards them with points and badges.

## 🎯 Key Features

### Core Features
- **📸 AI-Powered Classification**: Real-time waste classification using PyTorch (MobileNetV2)
- **♻️ Smart Disposal Guidance**: Generates specific disposal instructions for each waste type
- **🔐 Secure Authentication**: JWT-based auth with bcrypt password hashing
- **⭐ Gamification System**: 
  - Points & Badges for each classification
  - 6-tier ranking system (Novice → Legendary)
  - Real-time leaderboards with user rankings
- **🌍 Environmental Impact Tracking**: 
  - Personal dashboard with statistics
  - CO₂ impact calculation
  - Classification history by type
- **📱 Mobile-Friendly Interface**: Responsive design for all devices

### Production Features
- ✅ **Logging & Monitoring**: Comprehensive logging with file/console output
- ✅ **Input Validation**: Pydantic models with strict validation
- ✅ **Error Handling**: Detailed error messages with proper HTTP status codes
- ✅ **Security Headers**: CORS, X-Frame-Options, XSS protection
- ✅ **Database Backups**: PostgreSQL backup strategy ready
- ✅ **Docker Support**: Multi-stage builds, non-root users, health checks
- ✅ **Environment Configuration**: 12-factor app setup with .env support
- ✅ **Rate Limiting**: Framework for implementing rate limiting
- ✅ **Performance Optimized**: Asset caching, gzip compression, database indexing

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18 + Vite + React Router |
| **Backend** | FastAPI + Uvicorn/Gunicorn |
| **AI Model** | PyTorch (MobileNetV2) |
| **Database** | PostgreSQL 15 |
| **Authentication** | JWT + bcrypt |
| **Deployment** | Docker + Nginx |
| **Reverse Proxy** | Nginx with SSL/TLS |

## 📁 Project Structure

```
smartbin-ai/
├── backend/                      # FastAPI backend (production-ready)
│   ├── main.py                  # App initialization with logging/CORS
│   ├── database.py              # SQLAlchemy models
│   ├── requirements.txt         # Dependencies (optimized)
│   ├── Dockerfile               # Multi-stage production build
│   ├── models/                  # ML models directory
│   ├── logs/                    # Application logs
│   └── routes/                  # API endpoints
│       ├── auth.py              # Registration/Login (validated)
│       ├── classification.py    # Waste classification with logging
│       ├── gamification.py      # Points & badges system
│       ├── dashboard.py         # User dashboard/stats
│       └── users.py             # User management
│
├── frontend/                     # React frontend (optimized)
│   ├── src/
│   │   ├── config.js            # Centralized configuration
│   │   ├── services/api.js      # API service with error handling
│   │   ├── pages/               # React pages
│   │   └── components/          # Reusable components
│   ├── vite.config.js           # Vite build optimization
│   ├── package.json             # Dependencies
│   ├── Dockerfile.prod          # Production build (Nginx)
│   └── nginx*.conf              # Nginx configuration
│
├── ai-model/                     # ML model code
│   ├── waste_classifier.py      # PyTorch classifier
│   └── gamification_engine.py   # Points calculation
│
├── docs/
│   ├── API.md                   # API documentation
│   ├── SETUP.md                 # Setup instructions
│   └── DEPLOYMENT.md            # Production deployment
│
├── docker-compose.yml           # Development setup
├── docker-compose.prod.yml      # Production setup
├── .env.example                 # Environment template
├── .env.production              # Production config template
├── DEPLOYMENT.md                # Comprehensive deployment guide
├── PRODUCTION_CHECKLIST.md      # Pre-deployment verification
└── setup.py                     # Automated setup script
```
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── pages/         # Page components
│   │   ├── App.jsx        # Main app
│   │   └── index.css      # Global styles
│   └── package.json
│
├── ai-model/              # Machine learning
│   ├── waste_classifier.py      # PyTorch model
│   ├── tensorflow_classifier.py # TensorFlow model
│   ├── gamification_engine.py  # Points calculation
│   └── README.md
│
└── docs/                  # Documentation

```

## 🚀 Quick Start

### Prerequisites
- **Docker & Docker Compose** (recommended for both dev and production)
- **Python 3.11+** (if running locally without Docker)
- **Node.js 18+** (if running frontend locally)
- **PostgreSQL 15+** (for production)

### Option 1: Automated Setup (Recommended)

```bash
# Run automated setup script
python setup.py

# This will:
# 1. Create .env from .env.example
# 2. Check Docker installation
# 3. Build Docker images
# 4. Start all services
# 5. Wait for services to be ready
```

**Access the application:**
- 🌐 Frontend: http://localhost:5173
- 🔙 Backend API: http://localhost:8000
- 📖 API Docs: http://localhost:8000/api/docs

### Option 2: Manual Docker Setup

```bash
# Clone the repository
git clone <repository-url>
cd smartbin-ai

# Setup environment
cp .env.example .env

# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 3: Local Development Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**Frontend (in another terminal):**
```bash
cd frontend
npm install
npm run dev
```

## 🌐 First Use

1. **Register** with username and password (min 8 chars, must include uppercase and number)
2. **Login** to your account
3. **Capture/Upload** a waste image
4. **Confirm** classification result (if needed)
5. **View Points** and **Leaderboard**

Default test account (if pre-populated):
- Username: `testuser`
- Password: `Test@1234`

## 📊 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### Classification
- `POST /api/classify/image` - Classify waste from image
- `POST /api/classify/confirm` - Confirm low-confidence classification

### Gamification
- `GET /api/gamification/stats/<user_id>` - User statistics and rank
- `GET /api/gamification/leaderboard` - Global leaderboard

### Dashboard
- `GET /api/dashboard` - User dashboard data

Full API documentation available at: http://localhost:8000/api/docs

## 🐳 Deployment

### Production Deployment

For comprehensive production deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md):

```bash
# Quick production deploy
export $(cat .env.production | xargs)
docker-compose -f docker-compose.prod.yml up -d

# Verify services
docker-compose -f docker-compose.prod.yml health check
```

### Pre-Deployment Checklist

Before deploying to production, review [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) to ensure:
- ✅ Security configuration
- ✅ Environment variables
- ✅ Database setup
- ✅ SSL/TLS certificates
- ✅ Monitoring & logging
- ✅ Backup strategy

## 🔒 Security

SmartBin AI implements security best practices:

- **JWT Authentication** with username as token subject
- **Password Hashing** with bcrypt (min 8 chars, complex requirements)
- **Input Validation** with Pydantic on all endpoints
- **CORS Restriction** to configured domains only
- **Security Headers** (X-Frame-Options, X-Content-Type-Options, CSP)
- **SQL Injection Protection** via SQLAlchemy ORM
- **XSS Protection** with Content Security Policy
- **Non-root Docker Users** for reduced container privileges
- **Environment Variable Isolation** for secrets management

### Password Requirements
- Minimum 8 characters
- Must contain: uppercase letter, lowercase letter, and digit
- Examples: `Secure@Password123`, `MyApp#2025`

## 📈 Performance

Production optimizations included:

- **Frontend**: Gzip compression, asset caching, code splitting
- **Backend**: Database connection pooling, query optimization, logging
- **Database**: Indexes on frequently queried columns
- **Docker**: Multi-stage builds, Alpine base images, health checks
- **Nginx**: Reverse proxy, SSL termination, static file caching

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Complete deployment guide for production |
| [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) | Pre-deployment verification checklist |
| [docs/API.md](./docs/API.md) | API endpoint reference |
| [docs/SETUP.md](./docs/SETUP.md) | Detailed setup instructions |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System architecture documentation |

## 🐛 Troubleshooting

### Services won't start
```bash
# Check Docker
docker ps
docker logs <container_name>

# View Docker Compose logs
docker-compose logs -f
```

### Backend errors
```bash
# View backend logs
docker-compose logs -f backend

# Verify database connection
docker-compose exec backend python -c "from database import SessionLocal; db = SessionLocal(); print('DB OK')"
```

### Frontend won't load
```bash
# Clear browser cache (Ctrl+Shift+Delete)
# Check VITE_API_URL environment variable
docker-compose exec frontend env | grep VITE

# View frontend logs
docker-compose logs -f frontend
```

### Model loading issues
```bash
# Check if model file exists
docker-compose exec backend ls -lah models/

# Verify model format
docker-compose exec backend python -c "import torch; m = torch.load('models/waste_classifier.pth'); print(type(m))"
```

## 🤝 Contributing

For development and contributing guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Commit: `git commit -am 'Add feature'`
5. Push: `git push origin feature/my-feature`
6. Open a Pull Request

## 📝 Environment Variables

See [.env.example](./.env.example) for all available configuration options.

Key variables for production:
```bash
SECRET_KEY=<strong-random-key>
CORS_ORIGINS=https://yourdomain.com
DATABASE_URL=postgresql://user:pass@host:5432/db
ENV=production
LOG_LEVEL=WARNING
VITE_API_URL=https://yourdomain.com/api
```

## 📦 Dependencies

**Backend:**
- fastapi==0.104.1
- sqlalchemy==2.0.23
- PyJWT==2.8.0
- bcrypt==5.0.0
- torch==2.1.1
- pillow==10.1.0

**Frontend:**
- react@18.2.0
- vite@4.3.9
- react-router-dom@6.20.0
- tailwindcss@3.3.0

See [backend/requirements.txt](./backend/requirements.txt) and [frontend/package.json](./frontend/package.json) for complete lists.

## 📄 License

This project is private property of SmartBin AI. All rights reserved.

## 🆘 Support

For issues, bugs, or questions:
1. Check existing documentation in `docs/`
2. Review [Troubleshooting](#-troubleshooting) section
3. Check Docker logs: `docker-compose logs -f`
4. Contact the team

---

<div align="center">

Made with ♻️ for environmental sustainability

**Questions?** See [docs/](./docs/) for comprehensive documentation.

</div>

### One-command dev start (frontend + backend) ✅

- Windows (PowerShell):

```powershell
# from repository root
.\smartbin-ai\scripts\start.ps1
```

- Unix / WSL / Git-Bash:

```bash
./smartbin-ai/scripts/start.sh
```

- You can also run via npm from the `frontend` folder (Windows):

```bash
cd frontend
npm run dev:all:win
```


## 📡 API Endpoints

### Authentication
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout

### Classification
- `POST /api/classify/image` - Classify waste from image
- `GET /api/classify/categories` - Get waste categories

### Gamification
- `POST /api/gamification/add-points/{user_id}/{points}` - Add points
- `GET /api/gamification/user-stats/{user_id}` - Get user stats
- `GET /api/gamification/leaderboard` - Get leaderboard
- `GET /api/gamification/badges` - Get all badges
- `GET /api/gamification/ranks` - Get all ranks

### Dashboard
- `GET /api/dashboard/impact/{user_id}` - Get user impact
- `GET /api/dashboard/global-impact` - Get global impact
- `GET /api/dashboard/history/{user_id}` - Get classification history

### Users
- `GET /api/users/{user_id}` - Get user profile
- `PUT /api/users/{user_id}` - Update profile
- `DELETE /api/users/{user_id}` - Delete account

## 🤖 AI Model Training

### Using PyTorch

```python
from ai_model.waste_classifier import train_model

# Organize data in data/ directory
data_structure = """
data/
├── plastic/
├── paper/
├── metal/
└── organic/
"""

model = train_model("./data", epochs=20, batch_size=32)
```

### Using TensorFlow

```python
from ai_model.tensorflow_classifier import TensorFlowWasteClassifier

classifier = TensorFlowWasteClassifier()
classifier.train("./data", epochs=20, batch_size=32)
```

## 🏆 Gamification System

### Points System
- Base: 10 points per classification
- Confidence bonus: 0-10 points (based on model confidence)

### Badge System
- **First Step**: Classify 1 item
- **Active Recycler**: Classify 10 items
- **Eco Warrior**: Classify 50 items
- **Planet Protector**: Classify 100 items
- **Plastic/Paper/Metal/Organic Collector**: Classify 20 items of specific type

### Ranking System
1. Novice (0-100 points)
2. Apprentice (100-300 points)
3. Expert (300-600 points)
4. Master (600-1000 points)
5. Legendary (1000+ points)

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    username VARCHAR UNIQUE,
    email VARCHAR UNIQUE,
    password_hash VARCHAR,
    points INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    rank VARCHAR DEFAULT 'Novice',
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Classifications Table
```sql
CREATE TABLE classifications (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR,
    waste_type VARCHAR,
    confidence FLOAT,
    points_earned INTEGER,
    image_path VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## 🐳 Docker Deployment

```bash
# Build and run
docker-compose up --build

# Access at http://localhost:3000
```

## 📈 Performance Metrics

| Metric | Target |
|--------|--------|
| Model Accuracy | 90%+ |
| Inference Time | <100ms |
| API Response | <200ms |
| Model Size | 10-50MB |

## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- CORS enabled for frontend
- Environment variables for sensitive data

## 📝 Example Usage Flow

1. **User Registration** → POST `/api/auth/register`
2. **Capture Waste Photo** → Take photo in camera page
3. **Classification** → POST `/api/classify/image`
4. **Points Awarded** → POST `/api/gamification/add-points`
5. **View Profile** → GET `/api/users/{user_id}`
6. **Check Leaderboard** → GET `/api/gamification/leaderboard`
7. **View Impact** → GET `/api/dashboard/impact/{user_id}`

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Submit a pull request

## 📄 License

MIT License

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [TensorFlow Guide](https://www.tensorflow.org/guide/)

## 📞 Support

For issues and questions, please create an issue in the repository.

---

**Made with ♻️ for a sustainable future**
