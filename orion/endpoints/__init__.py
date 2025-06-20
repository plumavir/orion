import importlib
import pkgutil

from fastapi import APIRouter

import orion


def discover_routers() -> list[APIRouter]:
    routers: list[APIRouter] = []

    for _finder, module_name, _is_pkg in pkgutil.iter_modules(orion.endpoints.__path__):  # type: ignore
        if module_name.startswith("_"):
            continue

        full_module_name = f"{orion.endpoints.__name__}.{module_name}"  # type: ignore
        module = importlib.import_module(full_module_name)

        router = getattr(module, "router", None)
        if isinstance(router, APIRouter):
            routers.append(router)

    return routers


routers = discover_routers()  # type: list[APIRouter]
