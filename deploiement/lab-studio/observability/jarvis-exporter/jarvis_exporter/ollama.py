"""On-demand Ollama benchmark client. No request is scheduled automatically."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
import time
from typing import Any
from urllib import error, request

from .config import OllamaConfig


class BenchmarkError(RuntimeError):
    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class BenchmarkResult:
    model: str
    response: str
    wall_duration_seconds: float
    time_to_first_token_seconds: float
    server_duration_seconds: float
    load_duration_seconds: float
    prompt_eval_duration_seconds: float
    eval_duration_seconds: float
    prompt_tokens: int
    generated_tokens: int
    tokens_per_second: float
    done_reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _nanoseconds_to_seconds(value: Any) -> float:
    try:
        return float(value or 0) / 1_000_000_000
    except (TypeError, ValueError):
        return 0.0


def run_benchmark(
    config: OllamaConfig,
    *,
    prompt: str,
    model: str | None = None,
    num_predict: int | None = None,
    temperature: float = 0.0,
) -> BenchmarkResult:
    if not config.enabled:
        raise BenchmarkError("disabled", "Les benchmarks Ollama sont désactivés")

    selected_model = (model or config.model).strip()
    if not selected_model:
        raise BenchmarkError("invalid_request", "Le modèle Ollama est obligatoire")
    if not prompt.strip():
        raise BenchmarkError("invalid_request", "Le prompt ne peut pas être vide")
    if len(prompt) > 16_000:
        raise BenchmarkError("invalid_request", "Le prompt dépasse 16 000 caractères")

    selected_num_predict = (
        num_predict if num_predict is not None else config.default_num_predict
    )
    if selected_num_predict < 1 or selected_num_predict > config.max_num_predict:
        raise BenchmarkError(
            "invalid_request",
            f"num_predict doit être compris entre 1 et {config.max_num_predict}",
        )
    if not math.isfinite(temperature) or temperature < 0 or temperature > 2:
        raise BenchmarkError(
            "invalid_request", "temperature doit être comprise entre 0 et 2"
        )

    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": True,
        "keep_alive": config.keep_alive,
        "options": {
            "num_predict": selected_num_predict,
            "temperature": temperature,
        },
    }
    http_request = request.Request(
        f"{config.url.rstrip('/')}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started = time.perf_counter()
    first_token_at: float | None = None
    chunks: list[str] = []
    final: dict[str, Any] | None = None

    try:
        with request.urlopen(http_request, timeout=config.timeout_seconds) as response:
            for raw_line in response:
                if not raw_line.strip():
                    continue
                try:
                    chunk = json.loads(raw_line)
                except json.JSONDecodeError as exc:
                    raise BenchmarkError(
                        "invalid_response", "Ollama a renvoyé un flux JSON invalide"
                    ) from exc
                text = chunk.get("response")
                if isinstance(text, str) and text:
                    if first_token_at is None:
                        first_token_at = time.perf_counter()
                    chunks.append(text)
                if chunk.get("done") is True:
                    final = chunk
    except BenchmarkError:
        raise
    except error.HTTPError as exc:
        raise BenchmarkError("http_error", f"Ollama a répondu HTTP {exc.code}") from exc
    except TimeoutError as exc:
        raise BenchmarkError("timeout", "Le benchmark Ollama a expiré") from exc
    except error.URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            raise BenchmarkError("timeout", "Le benchmark Ollama a expiré") from exc
        raise BenchmarkError("connection_error", "Ollama est injoignable") from exc
    except OSError as exc:
        raise BenchmarkError("connection_error", "Ollama est injoignable") from exc

    finished = time.perf_counter()
    if final is None:
        raise BenchmarkError(
            "incomplete_response", "Ollama n'a pas envoyé de fragment final"
        )

    eval_duration_seconds = _nanoseconds_to_seconds(final.get("eval_duration"))
    generated_tokens = int(final.get("eval_count") or 0)
    tokens_per_second = (
        generated_tokens / eval_duration_seconds if eval_duration_seconds > 0 else 0.0
    )

    return BenchmarkResult(
        model=str(final.get("model") or selected_model),
        response="".join(chunks),
        wall_duration_seconds=finished - started,
        time_to_first_token_seconds=(first_token_at or finished) - started,
        server_duration_seconds=_nanoseconds_to_seconds(final.get("total_duration")),
        load_duration_seconds=_nanoseconds_to_seconds(final.get("load_duration")),
        prompt_eval_duration_seconds=_nanoseconds_to_seconds(
            final.get("prompt_eval_duration")
        ),
        eval_duration_seconds=eval_duration_seconds,
        prompt_tokens=int(final.get("prompt_eval_count") or 0),
        generated_tokens=generated_tokens,
        tokens_per_second=tokens_per_second,
        done_reason=str(final.get("done_reason") or "unknown"),
    )
