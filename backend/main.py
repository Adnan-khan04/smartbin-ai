from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv
import os
import logging
from pathlib import Path
import sys

load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "./logs/app.log")
ENV = os.getenv("ENV", "development")

# Create logs directory if it doesn't exist
Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"Starting SmartBin AI API in {ENV} mode")

app = FastAPI(
    title="SmartBin AI API",
    description="Smart Waste Segregation & Gamified Recycling System",
    version="1.0.0",
    docs_url="/api/docs" if ENV == "development" else None,
    redoc_url="/api/redoc" if ENV == "development" else None,
    openapi_url="/api/openapi.json" if ENV == "development" else None,
)

# CORS configuration - restrict in production
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:5174" if ENV == "development" else "https://yourdomain.com"
).split(",")

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Enable CORS with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Import routers
from routes import auth, classification, gamification, dashboard, users

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(classification.router, prefix="/api/classify", tags=["Classification"])
app.include_router(gamification.router, prefix="/api/gamification", tags=["Gamification"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])

# Serve built frontend (if present) so backend can act as a single deployable unit
from fastapi.staticfiles import StaticFiles

_backend_root = Path(__file__).resolve().parents[1]
_possible_frontend_dirs = [
    _backend_root / 'frontend' / 'dist',                # primary frontend build
    _backend_root / 'frontend' / 'smartbin-ai' / 'dist'  # nested frontend (fallback)
]

for d in _possible_frontend_dirs:
    if d.exists():
        logger.info(f"Mounting frontend static files from: {d}")
        app.mount('/', StaticFiles(directory=str(d), html=True), name='frontend')
        break



@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
