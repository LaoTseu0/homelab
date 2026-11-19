"""Small NVIDIA collector based on the stable nvidia-smi query interface."""

from __future__ import annotations

import csv
import io
import logging
import subprocess
from threading import Event, Thread
import time

from .config import NvidiaConfig
from .metrics import Metrics


LOGGER = logging.getLogger(__name__)

QUERY = (
    "index,name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw"
)


class NvidiaCollector:
    def __init__(self, config: NvidiaConfig, metrics: Metrics) -> None:
        self.config = config
        self.metrics = metrics
        self.stop_event = Event()

    def start(self) -> Thread | None:
        self.metrics.nvidia_enabled.set(1 if self.config.enabled else 0)
        if not self.config.enabled:
            LOGGER.info("Collecteur NVIDIA désactivé par la configuration")
            return None
        thread = Thread(target=self._run, name="nvidia-collector", daemon=True)
        thread.start()
        return thread

    def _run(self) -> None:
        was_up = False
        while not self.stop_event.is_set():
            try:
                self.collect_once()
                self.metrics.nvidia_up.set(1)
                self.metrics.nvidia_last_poll.set(time.time())
                if not was_up:
                    LOGGER.info("Collecteur NVIDIA opérationnel")
                was_up = True
            except Exception as exc:  # nvidia-smi may disappear during driver reload
                self.metrics.nvidia_up.set(0)
                if was_up:
                    LOGGER.warning("Collecte NVIDIA interrompue : %s", exc)
                else:
                    LOGGER.debug("NVIDIA indisponible : %s", exc)
                was_up = False
            self.stop_event.wait(self.config.poll_interval_seconds)

    def collect_once(self) -> None:
        completed = subprocess.run(
            [
                "nvidia-smi",
                f"--query-gpu={QUERY}",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=self.config.command_timeout_seconds,
        )
        rows = list(csv.reader(io.StringIO(completed.stdout), skipinitialspace=True))
        if not rows:
            raise RuntimeError("nvidia-smi n'a renvoyé aucun GPU")
        for row in rows:
            if len(row) != 7:
                raise RuntimeError("Format nvidia-smi inattendu")
            self.metrics.set_gpu(
                {
                    "index": row[0].strip(),
                    "name": row[1].strip(),
                    "temperature": row[2].strip(),
                    "utilization": row[3].strip(),
                    "memory_used_mib": row[4].strip(),
                    "memory_total_mib": row[5].strip(),
                    "power_watts": row[6].strip(),
                }
            )

