# LLM from Scratch

**Every core mechanism of an LLM application, rebuilt with plain Python and raw HTTP calls — no LangChain, no SDK, no framework.**

This project runs against a self-hosted [Ollama](https://ollama.com) server (a homelab NUC serving `qwen3:4b`), and deliberately uses a *small* model: its failures are visible, reproducible, and that is exactly where the learning happens. Every abstraction that frameworks hide — the message list, the sampling pipeline, the tool-call loop, the retry logic — is written out by hand here.

> Code comments are in French: this repository doubles as a learning journal.
> [PROGRESSION.md](PROGRESSION.md) tracks every concept validated in practice, and the incidents that taught the most.

## The curriculum

One script = one mechanism. Each builds on the previous one.

| Step | File | Mechanism | The takeaway |
|------|------|-----------|--------------|
| 01 | [`01_hello.py`](01_hello.py) | A raw LLM call | An LLM call is just `POST {model, messages}` → JSON. Everything else is decoration. |
| 02 | [`02_chat.py`](02_chat.py) | Chat with history | The model is **stateless**: the "conversation" is a client-side list, re-sent in full on every turn. |
| 03 | [`03_stream.py`](03_stream.py) | Token streaming | Generation is token by token; streaming is one JSON line per chunk (`iter_lines` + `json.loads`). |
| 04 | [`04_sampling.ipynb`](04_sampling.ipynb) | Sampling (temperature, top-k, top-p) | The pipeline order matters: probabilities → top-k/top-p filters → temperature → draw. `top_k=1` makes temperature irrelevant. |
| 05 | [`05_contexte.py`](05_contexte.py) | Context management | Truncation, then **compaction**: an LLM call summarizing old turns, restarting from `[system + summary]` (420 → 184 tokens in the test). |
| 06 | [`06_outils.py`](06_outils.py) | Function calling, by hand | A tool call is a *request* in JSON. The model proposes, **our code disposes** — it never executes anything itself. |
| 07 | [`07_agent.py`](07_agent.py) | A mini agent loop | `agent = LLM + tools + while loop`. New tools (read/write/exec) demand new guardrails: sandbox, path-traversal check, human confirmation, bounded loop. |
| 08 | [`08_structured.py`](08_structured.py) | Structured output | Politely asking for JSON is a lottery. Constrained decoding (`format` = JSON schema) guarantees **shape**; Pydantic validation + retry guards the **content**. |

## Lessons that stuck (the hard way)

- **Unbounded generation is an outage.** An open-ended question with unrestricted sampling pinned the GPU indefinitely — `num_predict`/`max_tokens` is mandatory in anything serious.
- **Sampling defaults stack in layers.** The model's Modelfile silently imposes its own `temperature`/`top_p`; an option missing from the request falls back to them. Debugging this produced a full [debug methodology](../../guides/methodologie-debug.md): hypotheses → discriminating test → one variable at a time.
- **Placement in context matters.** A perfect compaction summary was *ignored* as a `user` message and *used* as a `system` message. The authority of the system voice is a tool.
- **Tools make the data reliable, not the reasoning.** The agent once concluded a file "was not deleted" while staring at a listing proving it was — anchored on its own earlier doubt. Interpreting a tool result is still probabilistic generation.
- **Constrained decoding guarantees shape, never completeness.** The grammar happily let the model skip an optional field that was present in the text, and an empty string passes a `str` validation. Semantic checks (`Field(min_length=1)`…) remain necessary.
- **Everything the model produces is untrusted input** — including tool arguments (it once typo'd a filename it was asked to create) and including the effects of your own prompt ("use null for missing info" → null on required fields).

## Running it

Requirements: an Ollama server, Python 3.12, and [mise](https://mise.jdx.dev) (optional — it pins Python and auto-activates the venv via [`mise.toml`](mise.toml)).

```bash
# adjust OLLAMA_URL and MODEL at the top of each script first
pip install -r requirements.txt
python 01_hello.py
```

Every script is standalone and numbered: run them in order, read them in order.

## Why no framework?

Frameworks are fine — but you can only debug what you understand. After writing the agent loop in 30 lines and watching a 4B model argue with a file listing, LangChain stops being magic and starts being a convenience. That was the point.
