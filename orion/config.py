from typing import Literal

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
