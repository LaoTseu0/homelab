"""Configuration loading with environment overrides for secrets and deployment."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
from typing import Any


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env(name: str, default: Any, cast: type = str) -> Any:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    if cast is bool:
        return _as_bool(value)
    return cast(value)


@dataclass(frozen=True)
class ServerConfig:
    listen_address: str
    port: int


@dataclass(frozen=True)
class OllamaConfig:
    enabled: bool
    url: str
    model: str
    timeout_seconds: float
    default_num_predict: int
    max_num_predict: int
    keep_alive: str


@dataclass(frozen=True)
class HomeAssistantConfig:
    enabled: bool
    websocket_url: str
    token: str
    poll_interval_seconds: float
    pipeline_ids: tuple[str, ...]


@dataclass(frozen=True)
class NvidiaConfig:
    enabled: bool
    poll_interval_seconds: float
    command_timeout_seconds: float


@dataclass(frozen=True)
class Config:
    server: ServerConfig
    ollama: OllamaConfig
    home_assistant: HomeAssistantConfig
    nvidia: NvidiaConfig


def load_config(path: str | Path) -> Config:
    with Path(path).open(encoding="utf-8") as handle:
        raw = json.load(handle)

    server = raw.get("server", {})
    ollama = raw.get("ollama", {})
    home_assistant = raw.get("home_assistant", {})
    nvidia = raw.get("nvidia", {})

    configured_pipeline_ids = home_assistant.get("pipeline_ids", [])
    env_pipeline_ids = os.getenv("HOME_ASSISTANT_PIPELINE_IDS", "").strip()
    pipeline_ids = (
        [item.strip() for item in env_pipeline_ids.split(",") if item.strip()]
        if env_pipeline_ids
        else configured_pipeline_ids
    )

    default_num_predict = _env(
        "OLLAMA_DEFAULT_NUM_PREDICT", ollama.get("default_num_predict", 64), int
    )
    max_num_predict = _env(
        "OLLAMA_MAX_NUM_PREDICT", ollama.get("max_num_predict", 256), int
    )
    if default_num_predict < 1 or max_num_predict < default_num_predict:
        raise ValueError(
            "OLLAMA_DEFAULT_NUM_PREDICT doit être positif et inférieur ou égal "
            "à OLLAMA_MAX_NUM_PREDICT"
        )

    server_port = _env("JARVIS_EXPORTER_PORT", server.get("port", 9102), int)
    ollama_timeout_seconds = _env(
        "OLLAMA_TIMEOUT_SECONDS", ollama.get("timeout_seconds", 30), float
    )
    home_assistant_poll_interval_seconds = _env(
        "HOME_ASSISTANT_POLL_INTERVAL_SECONDS",
        home_assistant.get("poll_interval_seconds", 10),
        float,
    )
    nvidia_poll_interval_seconds = _env(
        "NVIDIA_POLL_INTERVAL_SECONDS",
        nvidia.get("poll_interval_seconds", 15),
        float,
    )
    nvidia_command_timeout_seconds = _env(
        "NVIDIA_COMMAND_TIMEOUT_SECONDS",
        nvidia.get("command_timeout_seconds", 5),
        float,
    )
    if not 1 <= server_port <= 65_535:
        raise ValueError("JARVIS_EXPORTER_PORT doit être compris entre 1 et 65535")
    durations = {
        "OLLAMA_TIMEOUT_SECONDS": ollama_timeout_seconds,
        "HOME_ASSISTANT_POLL_INTERVAL_SECONDS": (
            home_assistant_poll_interval_seconds
        ),
        "NVIDIA_POLL_INTERVAL_SECONDS": nvidia_poll_interval_seconds,
        "NVIDIA_COMMAND_TIMEOUT_SECONDS": nvidia_command_timeout_seconds,
    }
    for name, value in durations.items():
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} doit être un nombre positif et fini")

    return Config(
        server=ServerConfig(
            listen_address=_env(
                "JARVIS_EXPORTER_LISTEN_ADDRESS",
                server.get("listen_address", "0.0.0.0"),
            ),
            port=server_port,
        ),
        ollama=OllamaConfig(
            enabled=_env("OLLAMA_COLLECTOR_ENABLED", ollama.get("enabled", True), bool),
            url=_env("OLLAMA_URL", ollama.get("url", "http://ollama:11434")),
            model=_env("OLLAMA_MODEL", ollama.get("model", "")),
            timeout_seconds=ollama_timeout_seconds,
            default_num_predict=default_num_predict,
            max_num_predict=max_num_predict,
            keep_alive=_env("OLLAMA_KEEP_ALIVE", ollama.get("keep_alive", "5m")),
        ),
        home_assistant=HomeAssistantConfig(
            enabled=_env(
                "HOME_ASSISTANT_COLLECTOR_ENABLED",
                home_assistant.get("enabled", True),
                bool,
            ),
            websocket_url=_env(
                "HOME_ASSISTANT_WEBSOCKET_URL",
                home_assistant.get(
                    "websocket_url", "ws://host.docker.internal:8123/api/websocket"
                ),
            ),
            token=os.getenv("HOME_ASSISTANT_TOKEN", "").strip(),
            poll_interval_seconds=home_assistant_poll_interval_seconds,
            pipeline_ids=tuple(str(item) for item in pipeline_ids),
        ),
        nvidia=NvidiaConfig(
            enabled=_env("NVIDIA_COLLECTOR_ENABLED", nvidia.get("enabled", True), bool),
            poll_interval_seconds=nvidia_poll_interval_seconds,
            command_timeout_seconds=nvidia_command_timeout_seconds,
        ),
    )
