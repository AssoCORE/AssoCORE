import pkgutil
import importlib
import logging
from typing import List

from fastapi import APIRouter

routers: List[APIRouter] = []
api_router = APIRouter()


# Dynamically discover and register route modules in the app.routes package
def discover_and_register() -> None:
    import app.routes as _pkg

    for _finder, name, ispkg in pkgutil.iter_modules(_pkg.__path__):
        try:
            module = importlib.import_module(f".{name}", package=_pkg.__name__)
        except Exception:
            logging.exception("Failed to import route module %s", name)
            continue

        router = getattr(module, "router", None)
        if isinstance(router, APIRouter):
            routers.append(router)
            api_router.include_router(router)
        else:
            logging.warning(
                "Module %s has no APIRouter 'router' attribute", module.__name__
            )


discover_and_register()

__all__ = ("routers", "api_router")
