# 🧠 Jarvis v2 — Self-Modifying AI Agent

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/danshu3007-lang/jarvis-v2/blob/main/notebooks/jarvis_v2_colab.ipynb)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![HuggingFace Space](https://img.shields.io/badge/🤗%20HuggingFace-Space-orange)](https://huggingface.co/spaces/danshu3007-lang/jarvis-v2)

> An AI agent that **rewrites its own code** when it fails — not metaphorically, literally.
> Runs free on Google Colab T4 GPU.

---

## What Makes This Different

Most AI agents have fixed tools. When a tool breaks, they return an error and move on.

Jarvis v2 does something different: when a domain handler fails repeatedly, the **AI Mind** reads the failure logs, asks the LLM to write a better version of its own handler code, A/B tests the patch on historical episodes, and hot-swaps it live — all without human intervention.

```
User message
    │
    ▼
detect_domain()       ← research / coding / os_control
    │
    ▼
run_handler()         ← exec() the current domain handler
    │
    ▼
Tools.*               ← DuckDuckGo / Python sandbox / safe shell
    │
    ▼  (after 👍/👎 feedback)
AIMind.log()          ← stores episode in ChromaDB vector memory
    │
    ▼  (every 30 episodes)
AIMind.cycle()
    ├── read failures from memory
    ├── LLM writes new handler code
    ├── A/B test: old vs new on last 10 episodes
    └── hot-swap if Δreward > 5%
```

---

## Key Features

**Self-modifying reflexion loop** — inspired by the [Reflexion paper (Shinn et al. 2023)](https://arxiv.org/abs/2303.11366), applied to *code* rather than text. Every accepted patch is versioned and stored.

**Quantum VQC reward head** — replaces the standard linear reward head with a Variational Quantum Circuit. The circuit auto-grows (adds entanglement layers) when loss plateaus, preventing reward stagnation without manual tuning.

**Three live domains** — each with its own handler, reward history, and independent patching loop:
- 🔬 **Research** — DuckDuckGo web search
- 💻 **Coding** — Python execution in a subprocess sandbox
- 🖥️ **OS Control** — safe read-only shell commands (allowlisted)

**ChromaDB episodic memory** — every interaction is stored as a vector with prompt, response, reward, domain, and version. Failures are retrieved by semantic similarity for the patch prompt.

**PPO training scaffold** — policy model wrapped with `AutoModelForCausalLMWithValueHead` via `trl`, ready for full RLHF loop.

**Gradio UI** — chat interface with 👍/👎 feedback buttons that feed directly into the reflexion cycle.

---

## Architecture

```
jarvis/
├── config.py           ← all hyperparameters in one place
├── quantum_reward.py   ← VQC reward head (auto-evolves on plateau)
├── tools.py            ← sandboxed domain tools
├── mind.py             ← AIMind: memory + routing + self-modification
├── models.py           ← model loading (Mistral-7B + Phi-3-mini, 4-bit)
├── agent.py            ← JarvisAgent: high-level chat API
└── ui.py               ← Gradio frontend
```

**Models used:**
- Policy: `mistral-7b-instruct-v0.2` — 4-bit quantised via Unsloth + LoRA (rank 16)
- Reward: `phi-3-mini-4k-instruct` — 4-bit quantised + EvolvingQuantumReward head

**Memory schema (ChromaDB):**
```json
{
  "document": "<user prompt>",
  "metadata": { "response": "...", "reward": 1.0, "domain": "coding", "version": 3 }
}
```

---

## Quickstart — Google Colab (free T4 GPU)

**No local setup needed.** Click the badge at the top or:

1. Open the [Colab notebook](https://colab.research.google.com/github/danshu3007-lang/jarvis-v2/blob/main/notebooks/jarvis_v2_colab.ipynb)
2. `Runtime → Change runtime type → T4 GPU`
3. Run **Step 1** (install) — restart runtime if prompted
4. Run **Steps 2–8** in order
5. A Gradio link appears — open it and start chatting

First boot downloads ~8 GB of models and takes ~6 minutes.

---

## Local Setup

```bash
git clone https://github.com/danshu3007-lang/jarvis-v2.git
cd jarvis-v2
pip install -e ".[dev]"

# Install Unsloth separately (requires CUDA)
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

# Run
python -m jarvis.main
```

Requirements: Python 3.10+, CUDA GPU (8 GB+ VRAM recommended), CUDA toolkit.

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM backbone | Mistral-7B-Instruct, Phi-3-mini |
| Quantisation | 4-bit NF4 via Unsloth + bitsandbytes |
| Fine-tuning | LoRA (PEFT), PPO (TRL) |
| Quantum | Qiskit, Qiskit-Aer (VQC simulator) |
| Vector memory | ChromaDB (ephemeral) |
| Web search | DuckDuckGo Search API |
| UI | Gradio 4.x |
| Orchestration | Pure Python (no LangChain) |

---

## Self-Modification Safety

The reflexion loop has two hard guards:

1. **Sandboxed exec** — patched handler code runs in a fresh `exec()` namespace. It cannot access or modify `AIMind` internals directly. Only `Tools`, `llm`, `re`, and `np` are in scope.
2. **A/B gate** — a patch is only accepted if the mean reward over the last 10 historical episodes improves by more than `PATCH_THRESHOLD` (default 5%). Patches that don't improve things are silently discarded.

OS commands are restricted to a fixed allowlist: `ls, pwd, date, echo, cat, head, tail, wc`.

---

## Project Structure

```
jarvis-v2/
├── jarvis/             ← core package
├── notebooks/          ← Colab notebook
├── tests/              ← pytest suite (CPU-safe, no GPU required)
├── scripts/            ← nightly autonomous training loop
├── docs/               ← architecture, quantum reward, self-modification docs
├── docker/             ← Dockerfile for containerised deployment
└── assets/             ← banner, diagrams
```

---

## Running Tests

```bash
pytest tests/ -v
```

Tests are CPU-safe — no GPU or model download required. They cover domain detection, memory logging, patch proposal/rejection, quantum circuit evolution, and all three tools.

---

## Roadmap

- [ ] Connect VQC to real IBM quantum hardware via `qiskit-ibm-runtime`
- [ ] Replace proxy A/B reward with full VQC reward model scoring
- [ ] Persistent ChromaDB (disk-backed) for cross-session memory
- [ ] Add `sql_query` and `web_scraping` domains
- [ ] Multi-agent: separate Jarvis instances collaborating via shared memory

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The most impactful contribution is adding a new domain — the checklist is in the guide.

---

## License

MIT — see [LICENSE](LICENSE).
