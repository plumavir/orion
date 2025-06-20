# Por motivos de organização, este arquivo contém apenas as definições de documentação dos endpoints,
# enquanto a lógica de implementação dos endpoints está em seus respectivos arquivos.
# Mantenha essa documentação ordenada pela ordem de implementação dos endpoints,
# e nomeie as variáveis com a sequência `ENDPOINT_NAME_DESCRIPTION` e `ENDPOINT_NAME_RESPONSES`.

from typing import Any

PIPELINE_INGEST_DESCRIPTION: str = """
Recebe dados de um caso clínico, valida o conteúdo e envia para processamento assíncrono.
Os dados serão validados, tageados e enviados para a fila de processamento.
O endpoint retorna metadados que permitem o acompanhamento do status do processamento.
"""

PIPELINE_INGEST_RESPONSES: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "O formulário foi processado com sucesso.",
        "content": {
            "application/json": {
                "example": {...},
            },
        },
    },
    400: {
        "description": "O formulário não é válido.",
        "content": {
            "application/json": {
                "example": {
                    "errors": [
                        {
                            "field": "foo",
                            "message": "O campo 'foo' é obrigatório.",
                            "type": "validation_error",
                        },
                        {
                            "field": "bar",
                            "message": "O campo 'bar' deve ser um número.",
                            "type": "type_error",
                        },
                    ]
                },
            },
        },
    },
}
