from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            ".env.local",
            ".env",
        ),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


class _Server(
    EnvConfig,
    env_prefix="server_",
):
    host: str = "0.0.0.0"
    port: int = 8000

    debug: bool = False
    reload: bool = False
    log_level: str = "info"

    workers: int = 1
    loop: Literal[
        "none",
        "auto",
        "asyncio",
        "uvloop",
    ] = "uvloop"
    http: Literal[
        "auto",
        "h11",
        "httptools",
    ] = "httptools"

    proxy_headers: bool = True
    forwarded_allow_ips: str = "*"

    origins: list[str] = ["*"]
    hosts: list[str] = ["*"]


server = _Server()


class _Messenger(
    EnvConfig,
    env_prefix="messenger_",
):
    host: str = "localhost"
    port: int = 61613
    connection_timeout: float = 3.0

    username: Optional[str] = None
    password: Optional[str] = None
    client_id: str = "orion-client"

    # SSL não é utilizado diretamente pela lib stomp,
    # mas pode ser usado para configuração de contexto TLS
    # Use_ssl deve ser omitido ao criar Connection
    use_ssl: bool = False

    heartbeat: tuple[int, int] = (10000, 10000)
    default_destination: str = "orion.events"


messenger = _Messenger()
