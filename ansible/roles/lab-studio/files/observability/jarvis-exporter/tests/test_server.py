import math
from http import HTTPStatus
from http.server import ThreadingHTTPServer
import json
from threading import Thread
import unittest
from urllib import request

from jarvis_exporter.config import (
    Config,
    HomeAssistantConfig,
    NvidiaConfig,
    OllamaConfig,
    ServerConfig,
)
from jarvis_exporter.metrics import Metrics
from jarvis_exporter.server import ExporterApplication, handler_factory


CONFIG = Config(
    server=ServerConfig(listen_address="127.0.0.1", port=9102),
    ollama=OllamaConfig(
        enabled=True,
        url="http://ollama:11434",
        model="test-model",
        timeout_seconds=30,
        default_num_predict=32,
        max_num_predict=64,
        keep_alive="5m",
    ),
    home_assistant=HomeAssistantConfig(
        enabled=False,
        websocket_url="ws://homeassistant/api/websocket",
        token="",
        poll_interval_seconds=10,
        pipeline_ids=(),
    ),
    nvidia=NvidiaConfig(
        enabled=False,
        poll_interval_seconds=15,
        command_timeout_seconds=5,
    ),
)


class ExporterApplicationTest(unittest.TestCase):
    def setUp(self):
        self.application = ExporterApplication(CONFIG, Metrics())

    def test_rejects_boolean_generation_limit(self):
        status, payload = self.application.benchmark({"num_predict": True})
        self.assertEqual(HTTPStatus.BAD_REQUEST, status)
        self.assertEqual("invalid_request", payload["error"])

    def test_rejects_non_finite_temperature_and_releases_lock(self):
        status, payload = self.application.benchmark({"temperature": math.nan})
        self.assertEqual(HTTPStatus.BAD_REQUEST, status)
        self.assertEqual("invalid_request", payload["error"])

        status, _payload = self.application.benchmark({"temperature": math.inf})
        self.assertEqual(HTTPStatus.BAD_REQUEST, status)

    def test_health_and_metrics_http_endpoints(self):
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0), handler_factory(self.application)
        )
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        try:
            with request.urlopen(f"{base_url}/healthz", timeout=2) as response:
                self.assertEqual(
                    {"status": "ok"}, json.loads(response.read().decode("utf-8"))
                )
            with request.urlopen(f"{base_url}/metrics", timeout=2) as response:
                body = response.read()
                self.assertIn(b"python_info", body)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
