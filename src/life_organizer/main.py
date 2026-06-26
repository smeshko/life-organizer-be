"""Main FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from life_organizer.api.routes import budget, feedback, meals
from life_organizer.auth import verify_api_key
from life_organizer.config import get_settings
from life_organizer.db.session import engine
from life_organizer.logging_config import get_logger, setup_logging
from life_organizer.middleware import RequestLoggingMiddleware
from life_organizer.rate_limit import limiter

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

    # Initialize database
    logger.info("Initializing database connection...")
    # Database URL sanitized (password masked)
    db_url = settings.async_database_url
    if "@" in db_url:
        # Mask password in log
        parts = db_url.split("@")
        user_pass = parts[0].split("://")[1]
        if ":" in user_pass:
            user = user_pass.split(":")[0]
            masked_url = db_url.replace(user_pass, f"{user}:****")
            logger.info(f"Database URL: {masked_url}")
        else:
            logger.info(f"Database URL: {db_url}")
    else:
        logger.info(f"Database URL: {db_url}")
    logger.info("Database engine initialized")

    yield

    # Shutdown
    logger.info("Closing database connection...")
    await engine.dispose()
    logger.info("Database engine disposed")
    logger.info("Shutting down Life Organizer Backend")


# Create FastAPI application
# Disable docs/openapi in production to avoid leaking API schema
app = FastAPI(
    title="Life Organizer Backend",
    description="Voice-first intelligent agent for life organization",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=f"/api/{settings.api_version}/docs" if settings.debug else None,
    redoc_url=f"/api/{settings.api_version}/redoc" if settings.debug else None,
    openapi_url=f"/api/{settings.api_version}/openapi.json" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log every request (method, path, status, duration) and capture unhandled
# exceptions with a full traceback. Added last so it runs outermost.
app.add_middleware(RequestLoggingMiddleware)

# Configure rate limiting
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:  # noqa: ARG001
    """Handle rate limit exceeded errors with Retry-After header."""
    return JSONResponse(
        status_code=429,
        content={"error": f"Rate limit exceeded: {exc.detail}"},
        headers={"Retry-After": str(60)},
    )


# Include routers (all protected by API key)
app.include_router(
    budget.router,
    prefix=f"/api/{settings.api_version}/budget",
    tags=["budget"],
    dependencies=[Depends(verify_api_key)],
)
app.include_router(
    feedback.router,
    prefix=f"/api/{settings.api_version}/feedback",
    tags=["feedback"],
    dependencies=[Depends(verify_api_key)],
)
app.include_router(
    meals.router,
    prefix=f"/api/{settings.api_version}/meals",
    tags=["meals"],
    dependencies=[Depends(verify_api_key)],
)


# All remaining endpoints require API key
@app.get("/", dependencies=[Depends(verify_api_key)])
async def root() -> JSONResponse:
    """Root endpoint with basic API information."""
    return JSONResponse(
        content={
            "message": "Life Organizer Backend API",
            "version": "0.1.0",
            "api_version": settings.api_version,
        }
    )


# Unauthenticated: the Docker HEALTHCHECK probes this without an API key, and it
# only exposes liveness info (status/service/version). Keeping it behind
# verify_api_key made the probe 401 and the container perpetually "unhealthy".
@app.get("/health")
@app.get(f"/api/{settings.api_version}/health")
async def health_check() -> JSONResponse:
    """Health check endpoint to verify service is running."""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "life-organizer-backend",
            "version": "0.1.0",
        }
    )


@app.get(f"/api/{settings.api_version}/status", dependencies=[Depends(verify_api_key)])
async def api_status() -> JSONResponse:
    """API status endpoint with configuration info."""
    return JSONResponse(
        content={
            "api_version": settings.api_version,
            "debug": settings.debug,
        }
    )
