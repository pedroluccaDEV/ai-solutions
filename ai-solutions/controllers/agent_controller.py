#!/usr/bin/env python3
"""
AI CRM — Intelligent Lead Management System
Entrypoint da aplicação.
"""
import os
import sys
import logging
from datetime import datetime

# ─── LOGGING ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ─── FASTAPI ──────────────────────────────────────────────────────────────────
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from controllers.v1.crm_controller import router as crm_router

app = FastAPI(
    title="AI CRM",
    description="CRM com agentes autônomos para gestão inteligente de leads.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── ROTAS ────────────────────────────────────────────────────────────────────
app.include_router(crm_router, prefix="/v1/crm")

# ─── HEALTH ───────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "ai-crm",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "docs": "/docs",
    }

# ─── STARTUP ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    logger.info("🚀 AI CRM iniciado")
    logger.info(f"📄 Docs disponíveis em /docs")

# ─── ENTRYPOINT ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=False,
        log_level="info",
    )