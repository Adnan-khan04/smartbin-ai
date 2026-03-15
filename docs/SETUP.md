# SmartBin AI - Setup & Installation Guide

## System Requirements

- **OS**: Windows, macOS, or Linux
- **Python**: 3.8+
- **Node.js**: 16+
- **RAM**: 4GB minimum (8GB recommended for ML)
- **Disk Space**: 5GB minimum

## Installation Steps

### 1. Clone/Download Project

```bash
cd c:\Users\user\Desktop\hackathon
```

### 2. Backend Setup

```bash
cd smartbin-ai/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your configuration
# Start backend
python main.py
```

**Backend URL**: http://localhost:8000
**API Docs**: http://localhost:8000/docs

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Frontend URL**: http://localhost:5173

### 4. Database Setup (Optional)

#### Using SQLite (Default - No Setup Needed)
The backend automatically creates SQLite database for development.

#### Using PostgreSQL

```bash
# Install PostgreSQL (if not already installed)
# Windows: Download from https://www.postgresql.org/download/windows/
# macOS: brew install postgresql
# Linux: sudo apt-get install postgresql

# Create database
createdb smartbin_ai

# Update .env file
DATABASE_URL=postgresql://user:password@localhost:5432/smartbin_ai
```

### 5. AI Model Setup (Optional)

```bash
cd ../ai-model

# Install ML dependencies
pip install torch torchvision  # For PyTorch
# OR
pip install tensorflow keras  # For TensorFlow

# Prepare training data
mkdir -p ../data/plastic
mkdir -p ../data/paper
mkdir -p ../data/metal
mkdir -p ../data/organic

# Place training images in respective folders

# Train model
python waste_classifier.py
```

## Development Workflow

### 1. Start Backend
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python main.py
```

### 2. Start Frontend (in new terminal)
```bash
cd frontend
npm run dev
```

### 3. Backend Hot Reload
The backend automatically reloads on file changes. For manual reload:

```bash
# Install auto-reload (optional)
pip install python-dotenv watchdog
```

### 4. Frontend Hot Reload
Changes to React files automatically reload in the browser.

## Testing the Application

### Test Backend API

```bash
# Using curl
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password","username":"testuser"}'

# Or use API docs at http://localhost:8000/docs
```

### Test Classification

1. Open Frontend: http://localhost:5173
2. Click "Classify Waste"
3. Upload an image
4. See AI classification result

### Test Gamification

```bash
# Get user stats
curl http://localhost:8000/api/gamification/user-stats/user123

# Get leaderboard
curl http://localhost:8000/api/gamification/leaderboard
```

## Troubleshooting

### Port Already in Use

```bash
# Windows
netstat -ano | findstr :8000  # Find process using port 8000
taskkill /PID <PID> /F       # Kill the process

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

### Module Not Found Error

```bash
# Make sure virtual environment is activated
# And all dependencies are installed
pip install -r requirements.txt
```

### CORS Issues

Add to backend `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Database Connection Error

```bash
# Check if database is running
# For PostgreSQL:
psql -U postgres -d smartbin_ai

# Check DATABASE_URL in .env file
```

## Production Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access at http://localhost:3000
```

### Manual Deployment

#### Backend

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

#### Frontend

```bash
# Build for production
npm run build

# Serve with static server
npm install -g serve
serve -s dist
```

## Environment Variables

Create `.env` file in backend directory:

```env
# Database
DATABASE_URL=sqlite:///./smartbin.db
MONGODB_URL=mongodb://localhost:27017

# Security
SECRET_KEY=your-secure-random-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Model Path
MODEL_PATH=./models/waste_classifier.pth

# Environment
ENV=development
```

## Next Steps

1. **Train AI Model**: Add waste images to `data/` folder and train
2. **Connect Database**: Update `DATABASE_URL` in `.env`
3. **Customize**: Modify gamification rules in `gamification_engine.py`
4. **Deploy**: Follow docker-compose or production deployment steps

## Useful Commands

```bash
# Backend
python main.py              # Start development server
python -m pytest           # Run tests
pip freeze > requirements.txt  # Update dependencies

# Frontend
npm run dev               # Start dev server
npm run build            # Production build
npm run lint             # Run linter
npm test                 # Run tests

# Database
psql -U user -d smartbin_ai  # Connect to PostgreSQL
```

## Additional Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [PyTorch Guide](https://pytorch.org/docs/)
- [PostgreSQL Tutorial](https://www.postgresql.org/docs/)

---

**Happy coding! 🚀**
