"""Main FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from life_organizer.api.routes import classifier
from life_organizer.config import get_settings
from life_organizer.logging_config import get_logger, setup_logging

# Initialize settings and logging
settings = get_settings()
setup_logging(settings)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan manager for startup and shutdown events.

    Args:
        _app: FastAPI application instance (unused but required by protocol)

    Yields:
        None
    """
    # Startup
    logger.info("Starting Life Organizer Backend")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"API version: {settings.api_version}")
    logger.info(f"Log level: {settings.log_level}")

    yield

    # Shutdown
    logger.info("Shutting down Life Organizer Backend")


# Create FastAPI application
app = FastAPI(
    title="Life Organizer Backend",
    description="Voice-first intelligent agent for life organization",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=f"/api/{settings.api_version}/docs",
    redoc_url=f"/api/{settings.api_version}/redoc",
    openapi_url=f"/api/{settings.api_version}/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    classifier.router,
    prefix=f"/api/{settings.api_version}",
    tags=["classification"],
)


# Root endpoint
@app.get("/")
async def root() -> JSONResponse:
    """Root endpoint with basic API information.

    Returns:
        JSONResponse with API information
    """
    return JSONResponse(
        content={
            "message": "Life Organizer Backend API",
            "version": "0.1.0",
            "api_version": settings.api_version,
            "docs": f"/api/{settings.api_version}/docs",
        }
    )


# Health check endpoint
@app.get("/health")
@app.get(f"/api/{settings.api_version}/health")
async def health_check() -> JSONResponse:
    """Health check endpoint to verify service is running.

    Returns:
        JSONResponse with health status
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "life-organizer-backend",
            "version": "0.1.0",
        }
    )


# Example API endpoint (will be replaced with real endpoints later)
@app.get(f"/api/{settings.api_version}/status")
async def api_status() -> JSONResponse:
    """API status endpoint with configuration info.

    Returns:
        JSONResponse with API status
    """
    return JSONResponse(
        content={
            "api_version": settings.api_version,
            "debug": settings.debug,
            "endpoints": {
                "health": f"/api/{settings.api_version}/health",
                "docs": f"/api/{settings.api_version}/docs",
            },
        }
    )
