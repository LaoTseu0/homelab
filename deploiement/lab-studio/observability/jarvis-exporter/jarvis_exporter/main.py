"""jarvis-exporter entrypoint."""

from __future__ import annotations

import logging
import os

from . import __version__
from .config import load_config
from .home_assistant import HomeAssistantCollector
from .metrics import Metrics
from .nvidia import NvidiaCollector
from .server import ExporterApplication, serve


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    config_path = os.getenv(
        "JARVIS_EXPORTER_CONFIG", "/etc/jarvis-exporter/config.json"
    )
    config = load_config(config_path)
    metrics = Metrics()
    metrics.build_info.labels(version=__version__).set(1)
    metrics.ollama_enabled.set(1 if config.ollama.enabled else 0)

    HomeAssistantCollector(config.home_assistant, metrics).start()
    NvidiaCollector(config.nvidia, metrics).start()

    serve(ExporterApplication(config, metrics))


if __name__ == "__main__":
    main()

