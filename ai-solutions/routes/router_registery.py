import logging
import importlib
import pkgutil

from fastapi import FastAPI

logger = logging.getLogger(__name__)


def register_routers(app: FastAPI, base_package: str = "controllers"):
    successful = []
    failed = []

    package = importlib.import_module(base_package)

    for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        try:
            module = importlib.import_module(module_name)

            if hasattr(module, "router"):
                router = getattr(module, "router")

                # padrão opcional: prefix dentro do controller
                prefix = getattr(module, "ROUTER_PREFIX", "")

                app.include_router(router, prefix=prefix)

                successful.append(module_name)
                logger.info(f"✅ {module_name} registrado ({prefix})")

        except Exception as e:
            failed.append(module_name)
            logger.error(f"❌ {module_name}: {e}")

    logger.info(f"[RouterRegistry] {len(successful)} ok | {len(failed)} erro(s)")

    return {"successful": successful, "failed": failed}