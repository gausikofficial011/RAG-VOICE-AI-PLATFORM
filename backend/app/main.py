"""
RAG Voice Intelligence Platform — Main Application Entrypoint
FastAPI application factory, lifespan table initialization, middleware pipeline, and route mounts.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.middleware.security import (
    SecurityHeadersMiddleware,
    RequestIDMiddleware,
    RateLimitMiddleware,
)
from backend.app.api.auth import router as auth_router
from backend.app.api.knowledge_bases import router as kb_router
from backend.app.api.documents import router as doc_router
from backend.app.api.rag import router as rag_router
from backend.app.api.voice import router as voice_router
from backend.app.api.ml import router as ml_router
from backend.app.api.organizations import router as org_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.audit import router as audit_router
from backend.app.api.health import router as health_router
from backend.app.api.agent import router as agent_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database Tables
    await init_db()
    yield
    # Shutdown logic if needed


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise voice-first, evidence-grounded AI platform for private knowledge.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 1. Security & Traceability Middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Mount API Routers under /api
app.include_router(auth_router, prefix="/api")
app.include_router(kb_router, prefix="/api")
app.include_router(doc_router, prefix="/api")
app.include_router(rag_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(ml_router, prefix="/api")
app.include_router(org_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(agent_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
    }
