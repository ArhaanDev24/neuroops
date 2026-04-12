# NeuroOps – Autonomous AI Task Execution System

A multi-agent AI system that plans, executes, and reflects on tasks using Ollama (Qwen), ChromaDB, and custom tools.

## Prerequisites

1. **Python 3.9+**
2. **Ollama** installed and running.
   - Pull the model: `ollama pull qwen2.5:latest` (or update `MODEL_NAME` in `backend/llm.py`)
3. **Environment Variables** (Optional, defaults used otherwise):
   - `OLLAMA_URL`: Default `http://localhost:11434`
   - `MODEL_NAME`: Default `qwen2.5:latest`

## Installation

```bash
pip install -r requirements.txt