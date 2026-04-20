# core/database/mongo_model_loader.py

import pkgutil
import importlib
import inspect

from models.mongo.base import MongoModel


def load_mongo_models():
    models = []

    package = "models.mongo"

    for _, module_name, _ in pkgutil.walk_packages(
        path=__import__(package, fromlist=[""]).__path__,
        prefix=f"{package}."
    ):
        try:
            module = importlib.import_module(module_name)

            for _, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, MongoModel)
                    and obj is not MongoModel
                ):
                    models.append(obj)

        except Exception as e:
            print(f"[MongoLoader] Erro ao importar {module_name}: {e}")

    return models