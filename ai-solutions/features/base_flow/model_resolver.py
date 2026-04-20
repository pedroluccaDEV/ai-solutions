# features/chat/model_resolver.py
import importlib
import os

def instantiate_model_from_db(model_ref: str, provider_row: dict, model_row: dict):
    """
    model_ref: "openrouter:google/gemini-2.5-flash-image"
    provider_row: linha da tabela providers
    model_row: linha da tabela models
    """

    module_path = provider_row["module_path"]
    class_name = provider_row["class_name"]
    config_key = provider_row["config_key"]
    api_base_url = provider_row.get("api_base_url")

    api_key = os.getenv(config_key)
    if not api_key:
        raise RuntimeError(f"API key não encontrada: {config_key}")

    module = importlib.import_module(module_path)
    model_class = getattr(module, class_name)

    kwargs = {
        "id": model_row["model_name"],
        "api_key": api_key
    }

    # api_base_url é opcional
    if api_base_url:
        kwargs["base_url"] = api_base_url

    return model_class(**kwargs)
