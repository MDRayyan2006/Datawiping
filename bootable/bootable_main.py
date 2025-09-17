#!/usr/bin/env python3
"""
Bootable DataWipe Main Application
Optimized for bootable ISO environment.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from database import engine, Base
from routers import users, wipe_logs, storage, wipe, certificates, auth, devices, jobs, downloads
from utils.privilege_checker import PrivilegeChecker

# Configure logging for bootable environment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/live/datawipe/logs/datawipe.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bootable-specific configuration
BOOTABLE_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "auto_reload": False,
    "log_level": "info",
    "data_dir": "/live/datawipe",
    "cert_dir": "/live/datawipe/certificates",
    "log_dir": "/live/datawipe/logs"
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for bootable environment"""
    logger.info("Starting DataWipe Bootable System...")
    
    # Create necessary directories
    os.makedirs(BOOTABLE_CONFIG["cert_dir"], exist_ok=True)
    os.makedirs(BOOTABLE_CONFIG["log_dir"], exist_ok=True)
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized")
    
    # Check privileges
    privilege_checker = PrivilegeChecker()
    is_elevated, message = privilege_checker.check_privileges()
    logger.info(f"Privilege check: {message}")
    
    if not is_elevated:
        logger.warning("Not running with elevated privileges - some operations may be limited")
    
    logger.info("DataWipe Bootable System ready")
    yield
    
    logger.info("Shutting down DataWipe Bootable System...")

# Create FastAPI app
app = FastAPI(
    title="DataWipe Bootable",
    description="Secure System Wipe Tool - Bootable Version",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(wipe_logs.router, prefix="/api/v1/wipe-logs", tags=["wipe-logs"])
app.include_router(storage.router, prefix="/api/v1/storage", tags=["storage"])
app.include_router(wipe.router, prefix="/api/v1/wipe", tags=["wipe"])
app.include_router(certificates.router, prefix="/api/v1/certificates", tags=["certificates"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["devices"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(downloads.router, prefix="/api/v1/downloads", tags=["downloads"])

# Mount static files for frontend
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

@app.get("/")
async def root():
    """Root endpoint - redirect to frontend"""
    return FileResponse(str(frontend_path / "index.html"))

@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "message": "DataWipe Bootable API",
        "version": "1.0.0",
        "status": "running",
        "environment": "bootable"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": "bootable",
        "privileges": "elevated" if PrivilegeChecker().check_privileges()[0] else "limited"
    }

@app.get("/api/system")
async def system_info():
    """System information endpoint"""
    import platform
    import psutil
    
    return {
        "platform": platform.system(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "memory": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent
        },
        "disk": {
            "total": psutil.disk_usage('/').total,
            "free": psutil.disk_usage('/').free,
            "used": psutil.disk_usage('/').used
        },
        "bootable": True
    }

def main():
    """Main function for bootable environment"""
    logger.info("Starting DataWipe Bootable Server...")
    
    # Configure uvicorn for bootable environment
    config = uvicorn.Config(
        app=app,
        host=BOOTABLE_CONFIG["host"],
        port=BOOTABLE_CONFIG["port"],
        log_level=BOOTABLE_CONFIG["log_level"],
        access_log=True,
        server_header=False,
        date_header=False
    )
    
    server = uvicorn.Server(config)
    
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
