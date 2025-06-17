from fastapi import FastAPI

from orion import __version__
from orion.endpoints import routers

app = FastAPI(title="Orion")

for router in routers:
    app.include_router(router)


@app.get(
    "/meta",
    tags=[
        "root",
        "metadata",
    ],
)
async def metadata() -> dict[str, str]:
    """
    Serve os metadados associado ao servidor em execução.

    Returns:
        dict[str, str]: um dicionário com metadados sobre o servidor.
    """
    return {"version": __version__}
