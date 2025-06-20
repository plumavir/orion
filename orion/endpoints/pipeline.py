from typing import Any

from fastapi import APIRouter

from orion.endpoints.docs.pipeline import (
    PIPELINE_INGEST_DESCRIPTION,
    PIPELINE_INGEST_RESPONSES,
)

router = APIRouter(
    prefix="/pipeline",
    tags=["Pipeline"],
)


@router.post(
    "/ingest",
    summary="""
    Ingere um formulário `json`, valida-o, e posta na fila de processamento do pipeline.
    Retornará o ID do lote de processamento criado.
    """,
    description=PIPELINE_INGEST_DESCRIPTION,
    responses=PIPELINE_INGEST_RESPONSES,
)
async def ingest(
    data: dict[str, Any],
) -> ...: ...
