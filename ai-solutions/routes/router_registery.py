from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

ROUTERS_CONFIG = [
    ("controllers.crm_controller", "router", "/v1/crm"),
]

def load_routers():
    successful = []
    failed = []

    for module_path, router_name, prefix in ROUTERS_CONFIG:
        try:
            module = __import__(module_path, fromlist=[router_name])
            router_instance = getattr(module, router_name)
            router.include_router(router_instance, prefix=prefix)
            successful.append(module_path)
            logger.info(f"✅ {module_path} -> {prefix}")
        except Exception as e:
            failed.append(module_path)
            logger.error(f"❌ {module_path}: {e}")

    logger.info(f"Rotas: {len(successful)} ok | {len(failed)} erro(s)")
    return {"successful": successful, "failed": failed}


load_result = load_routers()