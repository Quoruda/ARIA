# 🤖 Agent Handbook - Project ARIA

Welcome to the **ARIA** project (*AI Interface with a pixel-art face*). This document is designed to help you quickly understand the project architecture and how to contribute.

## 🌟 Overview
ARIA is a local-first AI interface featuring an animated pixel-art face. It combines:
- A LangGraph ReAct agent backed by **Ollama** or **Mistral**
- Optional **speech recognition** (push-to-talk STT)
- Optional **streaming speech synthesis** (TTS)
- A lightweight **scheduled trigger engine** (reminders / delayed actions)

## 🧭 Repository Conventions (important)
- **All code, comments, docstrings, and identifiers must be in English.**
  The goal is to share this project publicly on GitHub and keep contributions consistent.
- The assistant’s *spoken language* is configurable via `.env` (see `TARGET_LANGUAGE`).

## 🏗️ Project Architecture

### 1. Core Orchestrator (`core.py`)
`core.py` wires everything together:
- Loads `.env`
- Selects **input** mode (text or audio) and **output** mode (text or audio)
- Instantiates 2 brains:
  - `DefaultAgent` for user conversations
  - `TriggerAgent` for scheduled trigger execution
- Starts the `TriggerEngine` in the background

Key principle: **Core routes work, it doesn’t decide behavior.**

### 2. Input (`input.py`, `stt/`)
- `InputManager` supports two modes:
  - `INPUT_MODE=text`: read from the terminal
  - `INPUT_MODE=audio`: push-to-talk microphone recording
- `stt/micro_recorder.py` implements the push-to-talk recorder.
- `stt/whisper_faster.py` provides Faster-Whisper transcription.

### 3. Output (`output.py`, `tts/`)
- `OutputManager` consumes the LLM token stream.
- In `OUTPUT_MODE=audio`, it buffers sentences and sends them to TTS.
- In `OUTPUT_MODE=text`, it only prints to stdout.

TTS stack:
- `tts/tts.py` / `tts/voice.py`: queue + playback thread
- `tts/kokoro_voice.py`: Kokoro-ONNX voice backend

### 4. Brain (LLM) (`brain/`, `agents/`)
The agent framework is implemented with LangGraph:
- `brain/brain_module.py`: `AgentBrain` base class (LangGraph ReAct agent)
- `brain/ollama_provider.py`: Ollama model provider
- `brain/mistral_provider.py`: Mistral model provider

Two concrete agents live in `agents/`:
- `agents/default_agent.py`: main conversational assistant
  - Uses **memory** (see `memory/`)
  - Tools: trigger scheduling + web search
- `agents/trigger_agent.py`: stateless execution agent for triggers
  - No memory
  - Tools: temporal context + trigger scheduling

### 5. Memory & Persistence (`memory/`)
ARIA can run with:
- **RAM memory** (default): volatile, reset on restart
- **SQLite memory**: persistent conversation state via LangGraph checkpointing

Implementation:
- `memory/context_provider.py` selects the backend via `.env`.
- `memory/ram_context.py` and `memory/sqlite_context.py` provide LangGraph checkpointers.

### 6. Triggers (Scheduler) (`triggers/`, `tools/`)
The trigger system is decoupled from the UI and the LLM:
- `triggers/base_trigger.py`: base trigger type (with claim/execution locking)
- `triggers/time_trigger.py`: executes when a scheduled time window is reached
- `triggers/scheduler.py`: in-memory scheduler (thread-safe)
- `triggers/engine.py`: background polling loop that dispatches due triggers

Tools exposed to the LLM:
- `tools/time_trigger_tool.py`: `schedule_at_time()`, `schedule_in_delay()`
- `tools/trigger_tool.py`: list/delete triggers + `schedule_action()` wrapper

### 7. UI (Pixel Face) (`ui/`)
This repo also includes a Pygame pixel-art face UI:
- `ui/pixel_display.py`: window + event loop
- `ui/pixel_renderer.py`: animations and rendering
- `ui/window_manager.py`: window shaping/transparency helpers

Note: the UI can be run independently from the assistant core.

## ⚙️ Configuration (.env reference)
ARIA uses `python-dotenv` in `core.py`. Create a `.env` file at repo root.

### Modes
- `INPUT_MODE`:
  - `text` (terminal input)
  - `audio` (push-to-talk STT)
  Default: `audio`

- `OUTPUT_MODE`:
  - `text` (print only)
  - `audio` (streaming TTS)
  Default: `audio`

### LLM Provider
- `AI_SOURCE`: `ollama` or `mistral` (default: `ollama`)
- `AI_MODEL_ID`:
  - For Ollama default is `mistral-nemo:12b`
  - For Mistral default is `mistral-small-latest`
- `OLLAMA_HOST`: optional (set if Ollama is remote)
- `MISTRAL_API_KEY`: required when `AI_SOURCE=mistral`
- `TEMPERATURE`: float (default: `0.4`)

### Assistant language (spoken text)
- `TARGET_LANGUAGE`: language the assistant must ALWAYS respond in (default: `English`)

### Agent memory
- `MEMORY_MAX_MESSAGES`: max message history fed to the agent (default: `20`)

Memory backend selection:
- `CONTEXT_BACKEND`: `ram` (default) or `sqlite`
- `CONTEXT_DB_PATH`: path for SQLite DB (default: `data/context.db`)

### Web search (optional)
- `TAVILY_MAX_RESULTS`: integer (default: `4`)
- `TAVILY_RETURN_METADATA`: `true`/`false` (default: `true`)

Important: `tools/search_tool.py` uses `langchain_tavily`. If you enable/keep this tool,
make sure the dependency is installed in your environment.

## 🔐 Security & publishing checklist
Before publishing this repository on GitHub:
- **Never commit secrets**: API keys, tokens, private endpoints.
  - Add `.env` to `.gitignore` and only commit a `.env.example`.
  - Rotate any key that has been committed or shared.
- If you enable Tavily search, keep `TAVILY_API_KEY` out of the repo.
- If you use Mistral, keep `MISTRAL_API_KEY` out of the repo.

Recommended files:
- `.env.example` with safe defaults and empty placeholders
- `README.md` section explaining how to configure keys locally

## 🚀 Installation
```bash
pip install -r requirements.txt
```

If you plan to use STT/TTS, you may also need system packages (audio device access, PortAudio).

## ▶️ Running the project

### 1) Full assistant (audio in/out)
```bash
python core.py
```

### 2) Silent / CI-friendly mode (text in/out)
```bash
INPUT_MODE=text OUTPUT_MODE=text python core.py
```

### 3) Mixed modes
Text input but audio output:
```bash
INPUT_MODE=text OUTPUT_MODE=audio python core.py
```

### 4) UI only
```bash
python ui/pixel_display.py
```

## 🧰 Tools available to the LLM
ARIA follows a strict separation of concerns:
- **Tools are dumb** (they expose capabilities)
- **The LLM decides** if/when/how to call them

Current tools:
- Trigger scheduling:
  - `schedule_at_time(time_str, action_prompt, context=None)` where `time_str` is `HH:MM`
  - `schedule_in_delay(delay_str, action_prompt, context=None)` where `delay_str` is `+10m` / `+2h`
  - `schedule_action(time_str, action_prompt, context=None)` backward-compatible wrapper
- Trigger management:
  - `list_all_triggers()` returns a structured list (ids + status)
  - `delete_trigger(trigger_id)`
  - `delete_triggers_by_prompt(prompt_substring)`
- Time context:
  - `get_temporal_context()`
- Web search:
  - Tavily search tool (see `tools/search_tool.py`)

## 🧪 Development notes
- Prefer small, composable modules.
- Keep the assistant personality in `agents/default_agent.py` and `agents/trigger_agent.py`.
- Keep orchestration in `core.py`.
- Keep business logic out of tools: tools should delegate to modules and return structured results.

## 🗺️ Roadmap (high-level)
- Connect core state (thinking/speaking/working) to the pixel face animations.
- Add non-time triggers (event-based triggers).
- Make trigger storage persistent (optional).
- Expand the action/tooling layer (system automation) with safe permissions.
