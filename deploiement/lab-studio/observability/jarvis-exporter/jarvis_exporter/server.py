"""HTTP endpoints for Prometheus, health checks and manual benchmarks."""

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
from threading import Lock
from typing import Any

from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .config import Config
from .metrics import Metrics
from .ollama import BenchmarkError, run_benchmark


LOGGER = logging.getLogger(__name__)
MAX_REQUEST_BYTES = 32 * 1024


class ExporterApplication:
    def __init__(self, config: Config, metrics: Metrics) -> None:
        self.config = config
        self.metrics = metrics
        self.benchmark_lock = Lock()

    def benchmark(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        if not self.benchmark_lock.acquire(blocking=False):
            return HTTPStatus.CONFLICT, {
                "error": "benchmark_busy",
                "message": "Un benchmark Ollama est déjà en cours",
            }

        self.metrics.ollama_running.set(1)
        raw_model = payload.get("model", self.config.ollama.model)
        model = raw_model if isinstance(raw_model, str) else "unknown"
        try:
            if not isinstance(raw_model, str):
                raise BenchmarkError("invalid_request", "model doit être une chaîne")
            prompt = payload.get(
                "prompt",
                "Réponds en français avec une seule phrase courte : présente-toi.",
            )
            if not isinstance(prompt, str):
                raise BenchmarkError("invalid_request", "prompt doit être une chaîne")
            num_predict = payload.get("num_predict")
            if num_predict is not None and (
                not isinstance(num_predict, int) or isinstance(num_predict, bool)
            ):
                raise BenchmarkError(
                    "invalid_request", "num_predict doit être un entier"
                )
            temperature = payload.get("temperature", 0.0)
            if not isinstance(temperature, (int, float)) or isinstance(
                temperature, bool
            ):
                raise BenchmarkError(
                    "invalid_request", "temperature doit être un nombre"
                )

            result = run_benchmark(
                self.config.ollama,
                prompt=prompt,
                model=model,
                num_predict=num_predict,
                temperature=float(temperature),
            )
            self.metrics.observe_ollama_success(result)
            return HTTPStatus.OK, result.to_dict()
        except BenchmarkError as exc:
            self.metrics.observe_ollama_error(model, exc.reason)
            status = (
                HTTPStatus.BAD_REQUEST
                if exc.reason in {"invalid_request", "disabled"}
                else HTTPStatus.BAD_GATEWAY
            )
            return status, {"error": exc.reason, "message": str(exc)}
        except Exception:
            LOGGER.exception("Échec inattendu du benchmark Ollama")
            self.metrics.observe_ollama_error(model, "unexpected")
            return HTTPStatus.INTERNAL_SERVER_ERROR, {
                "error": "unexpected",
                "message": "Erreur interne du benchmark",
            }
        finally:
            self.metrics.ollama_running.set(0)
            self.benchmark_lock.release()


def handler_factory(application: ExporterApplication) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "jarvis-exporter"

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
            if self.path == "/metrics":
                body = generate_latest(application.metrics.registry)
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", CONTENT_TYPE_LATEST)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if self.path == "/healthz":
                self._send_json(HTTPStatus.OK, {"status": "ok"})
                return
            if self.path == "/":
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "service": "jarvis-exporter",
                        "metrics": "/metrics",
                        "health": "/healthz",
                        "manual_benchmark": "POST /benchmark/ollama",
                    },
                )
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
            if self.path != "/benchmark/ollama":
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._send_json(
                    HTTPStatus.BAD_REQUEST, {"error": "invalid_content_length"}
                )
                return
            if content_length < 0 or content_length > MAX_REQUEST_BYTES:
                self._send_json(
                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    {"error": "request_too_large"},
                )
                return
            try:
                raw = self.rfile.read(content_length) if content_length else b"{}"
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise ValueError
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "invalid_json", "message": "Corps JSON invalide"},
                )
                return
            status, response = application.benchmark(payload)
            self._send_json(status, response)

        def log_message(self, format_string: str, *args: Any) -> None:
            LOGGER.debug("HTTP %s", format_string % args)

    return Handler


def serve(application: ExporterApplication) -> None:
    address = (
        application.config.server.listen_address,
        application.config.server.port,
    )
    server = ThreadingHTTPServer(address, handler_factory(application))
    LOGGER.info("jarvis-exporter écoute sur http://%s:%d", *address)
    server.serve_forever()
