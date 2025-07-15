"""
Main FastAPI application for CLIP.LRU
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import create_tables, settings
from app.frontend import setup_frontend, get_frontend_info, validate_frontend_setup
from app.routers import auth_router, clips_router, files_router, admin_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting CLIP.LRU application...")
    
    # Create database tables
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    # Create uploads directory
    os.makedirs(settings.storage_path, exist_ok=True)
    logger.info(f"Storage directory created: {settings.storage_path}")

    # Validate frontend setup
    frontend_valid, frontend_issues = validate_frontend_setup()
    if frontend_valid:
        logger.info("Frontend validation passed")
    else:
        logger.warning("Frontend validation issues found:")
        for issue in frontend_issues:
            logger.warning(f"  - {issue}")

    # Log frontend info
    frontend_info = get_frontend_info()
    logger.info(f"Frontend info: {frontend_info}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down CLIP.LRU application...")


# Create FastAPI app
app = FastAPI(
    title="CLIP.LRU API",
    description="Paste Before You Think - A next-generation clipboard management system",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
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


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CLIP.LRU API",
        "version": "0.1.0"
    }


# Root endpoint
@app.get("/info")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to CLIP.LRU API",
        "description": "Paste Before You Think",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "features": {
            "anonymous_access": settings.allow_anonymous,
            "max_file_size": settings.max_file_size,
            "anonymous_max_file_size": settings.anonymous_max_file_size if settings.allow_anonymous else None
        }
    }


# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(clips_router, prefix="/api")
app.include_router(files_router, prefix="/api")
app.include_router(admin_router, prefix="/api")

# Setup frontend (static files and page routes)
frontend_config = setup_frontend(app)

# Add frontend status endpoint
@app.get("/api/frontend/status", tags=["system"])
async def get_frontend_status():
    """Get frontend configuration status"""
    return {
        "status": "ok",
        "frontend_config": frontend_config.get_info(),
        "frontend_info": get_frontend_info()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
