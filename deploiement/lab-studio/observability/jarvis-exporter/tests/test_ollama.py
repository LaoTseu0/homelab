import json
import math
import unittest
from unittest.mock import patch

from jarvis_exporter.config import OllamaConfig
from jarvis_exporter.ollama import BenchmarkError, run_benchmark


CONFIG = OllamaConfig(
    enabled=True,
    url="http://ollama:11434",
    model="test-model",
    timeout_seconds=30,
    default_num_predict=32,
    max_num_predict=64,
    keep_alive="5m",
)


class FakeResponse:
    def __init__(self, chunks):
        self.lines = [json.dumps(chunk).encode() + b"\n" for chunk in chunks]

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def __iter__(self):
        return iter(self.lines)


class RunBenchmarkTest(unittest.TestCase):
    def test_parses_stream_and_usage_metrics(self):
        response = FakeResponse(
            [
                {"model": "test-model", "response": "Bon", "done": False},
                {"model": "test-model", "response": "jour", "done": False},
                {
                    "model": "test-model",
                    "response": "",
                    "done": True,
                    "done_reason": "stop",
                    "total_duration": 2_000_000_000,
                    "load_duration": 200_000_000,
                    "prompt_eval_duration": 100_000_000,
                    "eval_duration": 1_000_000_000,
                    "prompt_eval_count": 10,
                    "eval_count": 50,
                },
            ]
        )
        with patch("jarvis_exporter.ollama.request.urlopen", return_value=response):
            result = run_benchmark(CONFIG, prompt="Bonjour")

        self.assertEqual("Bonjour", result.response)
        self.assertEqual(50, result.generated_tokens)
        self.assertEqual(50, result.tokens_per_second)
        self.assertEqual(2, result.server_duration_seconds)
        self.assertGreaterEqual(result.time_to_first_token_seconds, 0)

    def test_rejects_unbounded_generation(self):
        with self.assertRaises(BenchmarkError) as context:
            run_benchmark(CONFIG, prompt="Bonjour", num_predict=65)
        self.assertEqual("invalid_request", context.exception.reason)

    def test_rejects_zero_generation_limit(self):
        with self.assertRaises(BenchmarkError) as context:
            run_benchmark(CONFIG, prompt="Bonjour", num_predict=0)
        self.assertEqual("invalid_request", context.exception.reason)

    def test_rejects_non_finite_temperature(self):
        with self.assertRaises(BenchmarkError) as context:
            run_benchmark(CONFIG, prompt="Bonjour", temperature=math.nan)
        self.assertEqual("invalid_request", context.exception.reason)


if __name__ == "__main__":
    unittest.main()
