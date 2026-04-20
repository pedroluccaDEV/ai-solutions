from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
import os

from core.config.init_db import init_db
from routes.router_registery import register_routers

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Zenith Server",
    description="AI Services Platform",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.on_event("startup")
async def startup():
    # 🔥 banco
    await init_db()

    # 🔥 rotas
    result = register_routers(app)

    logger.info(f"🚀 Server iniciado — {len(result['successful'])} módulos carregados")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
    )