from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn
import sys
import os

# Add utils directory to path for privilege checker
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from database import engine, Base
from routers import users, wipe_logs, storage, wipe, certificates, auth, devices, jobs, downloads
from privilege_checker import PrivilegeChecker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="DataWipe API",
    description="FastAPI backend with SQLite support for data wiping operations",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
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


@app.get("/")
async def root():
    return {"message": "DataWipe API is running"}


@app.get("/favicon.ico")
async def favicon():
    """Serve favicon.ico to prevent 404 errors"""
    # Create a simple 1x1 pixel favicon as base64 data URI
    # This prevents 404 errors without requiring an actual file
    from fastapi.responses import Response
    import base64
    
    # Simple 1x1 transparent PNG as base64
    favicon_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    
    return Response(
        content=favicon_data,
        media_type="image/x-icon",
        headers={"Cache-Control": "public, max-age=31536000"}
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


def check_privileges_and_start():
    """Check privileges and start the application"""
    print("DataWipe API Server")
    print("=" * 50)
    
    # Check if running with elevated privileges
    privilege_checker = PrivilegeChecker()
    
    # Check privileges
    is_elevated, message = privilege_checker.check_privileges()
    print(f"Privilege status: {message}")
    
    if not is_elevated:
        print("\n⚠️  WARNING: Not running with elevated privileges!")
        print("Some operations may fail or be limited.")
        print("\nFor full functionality, especially secure wiping operations,")
        print("it's recommended to run with administrator/root privileges.")
        
        # Ask user if they want to continue
        try:
            response = input("\nContinue anyway? (y/n): ").lower().strip()
            if response not in ['y', 'yes']:
                print("Exiting...")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(1)
    else:
        print("✅ Running with elevated privileges - full functionality available")
    
    print("\nStarting DataWipe API server...")
    print("Server will be available at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)


if __name__ == "__main__":
    check_privileges_and_start()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
