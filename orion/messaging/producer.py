import json
import logging
from functools import partial
from types import TracebackType
from typing import Any, Callable, Mapping, TypeAlias

import stomp
from stomp.exception import ConnectFailedException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from orion.config import messenger

Headers: TypeAlias = Mapping[str, str]

DEFAULT_HEADERS: dict[str, str] = {
    "content-type": "application/json",
    "persistent": "true",
}
MAX_LOG_BODY = 100
LOG_SENT = "Evento enviado para %s: %s"
LOG_FAIL = "Falha ao enviar evento: %s"

logger = logging.getLogger(__name__)


class StompConnection:
    """
    Context manager para stomp.Connection com listener e auto-desconexão.
    """

    conn: stomp.Connection

    def __enter__(self) -> stomp.Connection:
        self.conn = stomp.Connection(
            [(messenger.host, messenger.port)],
            heartbeats=messenger.heartbeat,
            timeout=messenger.connection_timeout,
        )

        self.conn.set_listener("listener", _ConnListener())  # type: ignore
        connection_headers = {"client-id": messenger.client_id}

        if messenger.username and messenger.password:
            self.conn.connect(  # type: ignore
                messenger.username,
                messenger.password,
                wait=True,
                headers=connection_headers,
            )
        else:
            self.conn.connect(  # type: ignore
                wait=True,
                headers=connection_headers,
            )

        return self.conn

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            self.conn.disconnect()  # type: ignore
        except ConnectFailedException as e:
            logger.warning("Falha ao desconectar do broker: %s", e)


class _ConnListener(stomp.ConnectionListener):
    """Listener para eventos de conexão STOMP."""

    def on_error(self, frame: Any) -> None:
        body = getattr(frame, "body", str(frame))
        logger.error("STOMP Error: %s", body)

    def on_disconnected(self) -> None:
        logger.warning("Desconectado do broker STOMP")


def _build_headers(extra: Headers | None = None) -> dict[str, str]:
    if not extra:
        return DEFAULT_HEADERS.copy()

    return {**DEFAULT_HEADERS, **extra}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(ConnectFailedException),
)
def _publish(dest: str, body: str, headers: dict[str, str]) -> None:
    with StompConnection() as conn:
        conn.send(  # type: ignore
            destination=dest,
            body=body,
            headers=headers,
        )


def dispatch(
    payload: Any,
    destination: str = messenger.default_destination,
    headers: Headers | None = None,
) -> bool:
    """
    Envia payload serializado para ActiveMQ via STOMP.
    """
    body = json.dumps(payload)
    hdrs = _build_headers(headers)
    try:
        _publish(
            destination,
            body,
            hdrs,
        )
        snippet = f"{body[:MAX_LOG_BODY]}..." if len(body) > MAX_LOG_BODY else body
        logger.debug(LOG_SENT, destination, snippet)
        return True
    except Exception as e:
        logger.error(LOG_FAIL, e)
        return False


def create_dispatcher(
    destination: str,
    headers: Headers | None = None,
) -> Callable[[Any], bool]:
    """
    Retorna função parcial de dispatch com destino e headers fixos.
    """
    return partial(
        dispatch,
        destination=destination,
        headers=headers,
    )
