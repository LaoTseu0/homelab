"""Passive collection of completed Home Assistant Assist debug runs."""

from __future__ import annotations

import json
import logging
from threading import Event, Thread
import time
from typing import Any

from websocket import WebSocket, create_connection

from .assist import analyze_pipeline_events
from .config import HomeAssistantConfig
from .metrics import Metrics


LOGGER = logging.getLogger(__name__)


class HomeAssistantCollector:
    def __init__(self, config: HomeAssistantConfig, metrics: Metrics) -> None:
        self.config = config
        self.metrics = metrics
        self.stop_event = Event()
        self.seen_runs: dict[str, set[str]] = {}
        self.initialized_pipelines: set[str] = set()
        self._message_id = 0

    def start(self) -> Thread | None:
        enabled = self.config.enabled and bool(self.config.token)
        self.metrics.home_assistant_enabled.set(1 if enabled else 0)
        if not self.config.enabled:
            LOGGER.info("Collecteur Home Assistant désactivé par la configuration")
            return None
        if not self.config.token:
            LOGGER.info(
                "Collecteur Home Assistant en attente : HOME_ASSISTANT_TOKEN est vide"
            )
            return None
        thread = Thread(target=self._run, name="home-assistant-collector", daemon=True)
        thread.start()
        return thread

    def _run(self) -> None:
        was_up = False
        while not self.stop_event.is_set():
            try:
                self.collect_once()
                self.metrics.home_assistant_up.set(1)
                self.metrics.home_assistant_last_poll.set(time.time())
                if not was_up:
                    LOGGER.info("Collecteur Home Assistant connecté")
                was_up = True
            except Exception as exc:  # keep the exporter alive across HA upgrades/outages
                self.metrics.home_assistant_up.set(0)
                if was_up:
                    LOGGER.warning("Collecte Home Assistant interrompue : %s", exc)
                else:
                    LOGGER.debug("Home Assistant indisponible : %s", exc)
                was_up = False
            self.stop_event.wait(self.config.poll_interval_seconds)

    def _next_id(self) -> int:
        self._message_id += 1
        return self._message_id

    def _call(self, websocket: WebSocket, command_type: str, **parameters: Any) -> Any:
        message_id = self._next_id()
        websocket.send(
            json.dumps({"id": message_id, "type": command_type, **parameters})
        )
        while True:
            response = json.loads(websocket.recv())
            if response.get("id") != message_id:
                continue
            if not response.get("success"):
                error = response.get("error", {})
                raise RuntimeError(
                    f"{command_type}: {error.get('code', 'unknown_error')}"
                )
            return response.get("result")

    def _connect(self) -> WebSocket:
        websocket = create_connection(
            self.config.websocket_url,
            timeout=min(self.config.poll_interval_seconds, 10),
            suppress_origin=True,
        )
        auth_required = json.loads(websocket.recv())
        if auth_required.get("type") != "auth_required":
            websocket.close()
            raise RuntimeError("Réponse d'authentification Home Assistant inattendue")
        websocket.send(
            json.dumps({"type": "auth", "access_token": self.config.token})
        )
        auth_result = json.loads(websocket.recv())
        if auth_result.get("type") != "auth_ok":
            websocket.close()
            raise RuntimeError("Jeton Home Assistant refusé")
        return websocket

    def collect_once(self) -> None:
        websocket = self._connect()
        try:
            pipeline_result = self._call(
                websocket, "assist_pipeline/pipeline/list"
            )
            pipelines = pipeline_result.get("pipelines", [])
            pipeline_names = {
                str(pipeline.get("id")): str(
                    pipeline.get("name") or pipeline.get("id") or "unknown"
                )
                for pipeline in pipelines
                if isinstance(pipeline, dict) and pipeline.get("id")
            }
            pipeline_ids = (
                self.config.pipeline_ids
                if self.config.pipeline_ids
                else tuple(pipeline_names)
            )

            for pipeline_id in pipeline_ids:
                completed_this_pipeline: list[tuple[str, str, Any]] = []
                run_result = self._call(
                    websocket,
                    "assist_pipeline/pipeline_debug/list",
                    pipeline_id=pipeline_id,
                )
                runs = run_result.get("pipeline_runs", [])
                seen = self.seen_runs.setdefault(pipeline_id, set())
                current_ids: set[str] = set()
                for run in runs:
                    run_id = str(run.get("pipeline_run_id") or "")
                    if not run_id:
                        continue
                    current_ids.add(run_id)
                    if run_id in seen:
                        continue
                    debug_result = self._call(
                        websocket,
                        "assist_pipeline/pipeline_debug/get",
                        pipeline_id=pipeline_id,
                        pipeline_run_id=run_id,
                    )
                    events = debug_result.get("events", [])
                    observation = analyze_pipeline_events(events)
                    if not observation.complete:
                        continue
                    completed_this_pipeline.append(
                        (
                            pipeline_id,
                            pipeline_names.get(pipeline_id, pipeline_id),
                            observation,
                        )
                    )
                    seen.add(run_id)
                # Home Assistant only retains a small rolling window of debug runs.
                self.seen_runs[pipeline_id] = seen.intersection(current_ids)
                # Existing runs seed each pipeline cursor independently, avoiding
                # duplicates after restart or when a new pipeline is discovered.
                if pipeline_id in self.initialized_pipelines:
                    for (
                        observed_pipeline_id,
                        pipeline_name,
                        observation,
                    ) in completed_this_pipeline:
                        self.metrics.observe_assist(
                            observed_pipeline_id, pipeline_name, observation
                        )
                else:
                    self.initialized_pipelines.add(pipeline_id)
        finally:
            websocket.close()
