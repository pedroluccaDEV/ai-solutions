#!/usr/bin/env python3
"""
AI CRM — Intelligent Lead Management System
"""
import os
import sys
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.router_registery import router, load_result

app = FastAPI(
    title="AI CRM",
    description="CRM com agentes autônomos para gestão inteligente de leads.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "ai-crm",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.on_event("startup")
async def startup():
    ok = len(load_result["successful"])
    fail = len(load_result["failed"])
    logger.info(f"🚀 AI CRM iniciado — {ok} rota(s) ok | {fail} erro(s)")
    if load_result["failed"]:
        for m in load_result["failed"]:
            logger.error(f"❌ Falhou: {m}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=False,
        log_level="info",
    )