"""
Main FastAPI application entry point.
ProxyAdminPanel - X-UI style proxy management system.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.database import init_database
from app.routers import auth, users, outbounds, rules, system, core_config, game_inventory, settings, external_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:     %(name)s - %(message)s'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown.
    """
    # Startup
    print("Starting ProxyAdminPanel...")
    await init_database()
    print("Database initialized.")

    yield

    # Shutdown
    print("Shutting down ProxyAdminPanel...")


# Create FastAPI application
app = FastAPI(
    title="ProxyAdminPanel",
    description="X-UI style proxy management system with BFF architecture",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(outbounds.router)
app.include_router(rules.router)
app.include_router(system.router)
app.include_router(core_config.router)
app.include_router(game_inventory.router)
app.include_router(settings.router)
# API key management removed for security - use create_api_key.py script instead
app.include_router(external_api.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ProxyAdminPanel API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
