import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from jarvis_exporter.config import load_config


BASE_CONFIG = {
    "server": {"listen_address": "0.0.0.0", "port": 9102},
    "ollama": {
        "enabled": True,
        "url": "http://ollama:11434",
        "model": "test-model",
        "timeout_seconds": 30,
        "default_num_predict": 32,
        "max_num_predict": 128,
        "keep_alive": "5m",
    },
    "home_assistant": {
        "enabled": True,
        "websocket_url": "ws://homeassistant/api/websocket",
        "poll_interval_seconds": 10,
        "pipeline_ids": [],
    },
    "nvidia": {
        "enabled": True,
        "poll_interval_seconds": 15,
        "command_timeout_seconds": 5,
    },
}


class LoadConfigTest(unittest.TestCase):
    def test_environment_overrides_secrets_and_pipeline_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(BASE_CONFIG), encoding="utf-8")
            with patch.dict(
                os.environ,
                {
                    "HOME_ASSISTANT_TOKEN": "token",
                    "HOME_ASSISTANT_PIPELINE_IDS": "one,two",
                    "OLLAMA_DEFAULT_NUM_PREDICT": "64",
                },
                clear=True,
            ):
                config = load_config(path)

        self.assertEqual("token", config.home_assistant.token)
        self.assertEqual(("one", "two"), config.home_assistant.pipeline_ids)
        self.assertEqual(64, config.ollama.default_num_predict)

    def test_rejects_inconsistent_generation_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(BASE_CONFIG), encoding="utf-8")
            with patch.dict(
                os.environ,
                {
                    "OLLAMA_DEFAULT_NUM_PREDICT": "256",
                    "OLLAMA_MAX_NUM_PREDICT": "128",
                },
                clear=True,
            ):
                with self.assertRaises(ValueError):
                    load_config(path)

    def test_rejects_non_positive_poll_interval(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(BASE_CONFIG), encoding="utf-8")
            with patch.dict(
                os.environ,
                {"HOME_ASSISTANT_POLL_INTERVAL_SECONDS": "0"},
                clear=True,
            ):
                with self.assertRaises(ValueError):
                    load_config(path)


if __name__ == "__main__":
    unittest.main()
