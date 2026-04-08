# 🤖 Agent Handbook - Project ARIA

Welcome to the **ARIA** project (*AI Interface with a pixel-art face*). This document is designed to help you quickly understand the project architecture, runtime modes, and contribution conventions.

## 🌟 Overview
ARIA is a local-first AI interface featuring an animated pixel-art face. It combines:
- A LangGraph ReAct agent backed by **Ollama**, **Mistral**, or **Kobold**
- A **multi-channel I/O bus** (local audio, terminal, Telegram) via `asyncio`
- Optional **speech recognition** (push-to-talk STT)
- Optional **streaming speech synthesis** (TTS)
- Optional **Telegram bot** integration (text & voice messages)
- A lightweight **scheduled trigger engine** (reminders / delayed actions)
- Optional **scratchpad memory** (simple JSON user profile notes)

## 🧭 Repository Conventions (important)
- **All code, comments, docstrings, and identifiers must be in English.**
  The goal is to share this project publicly on GitHub and keep contributions consistent.
- The assistant’s *spoken language* is configurable via `.env` (see `TARGET_LANGUAGE`).

## 🏗️ Project Architecture

### 1. Core Orchestrator (`core.py`)
`core.py` is an `asyncio` event-driven Orchestrator that wires everything together:
- Loads `.env` via `python-dotenv`
- Instantiates the active **Channels** (Local Audio/Terminal, Telegram) based on env vars
- Instantiates 2 agents:
  - `DefaultAgent` for user conversations
  - `TriggerAgent` for scheduled trigger execution
- Acts as a **Message Router**, asynchronously forwarding `MessageContext` events from channels to the LLM, and streaming the generated replies back to the origin channel.
- Starts the `TriggerEngine` in the background

Key principle: **Core routes work as a message bus, it doesn’t decide behavior.**

### 2. Channels (I/O) (`channels/`)
The system follows an asynchronous Message Bus architecture. Instead of hardcoded inputs and outputs, ARIA uses "Channels" that implement `BaseChannel` and exchange `MessageContext` objects.

Active channels are automatically loaded by `core.py`:
- `LocalTerminalChannel`: Standard text input/output for debug and testing.
- `LocalAudioChannel`: Employs `PushToTalkRecorder` + Faster-Whisper for STT, and KokoroTTS for audio generation.
- `TelegramChannel`: Uses `python-telegram-bot` to expose ARIA via a Telegram bot, seamlessly supporting both text and voice messages.

Audio stack components used by channels:
- STT: `stt/micro_recorder.py` and `stt/whisper_faster.py`
- TTS: `tts/voice.py` and `tts/kokoro_voice.py`

### 3. Brain (LLM) (`brain/`, `agents/`)
The agent framework is implemented with LangGraph:
- `brain/brain_module.py`: `AgentBrain` base class (LangGraph ReAct agent)

Design note:
- `brain/` does not import `memory/`. Persistence is configured at the agent/orchestration layer by injecting a LangGraph checkpointer (see `memory/context_provider.py`).

- Providers:
  - `brain/ollama_provider.py`: Ollama model provider
  - `brain/mistral_provider.py`: Mistral model provider
  - `brain/kobold_provider.py`: OpenAI-compatible local endpoint provider

Two concrete agents live in `agents/`:
- `agents/default_agent.py`: main conversational assistant
  - Uses LangGraph checkpointer memory when enabled (see `memory/`)
  - Optional persistent scratchpad notes (`SCRATCHPAD_PATH`)
  - Tools: trigger scheduling + web search + weather + scratchpad
- `agents/trigger_agent.py`: stateless execution agent for triggers
  - No conversation memory
  - Tools: temporal context + trigger scheduling

### 4. Memory & Persistence (`memory/`)
ARIA has two distinct memory layers:

1) Conversation state (LangGraph checkpointer):
- **RAM context** (default): volatile, reset on restart
- **SQLite context**: persistent conversation state via LangGraph checkpointing

Implementation:
- `memory/context_provider.py` selects and builds the checkpointer from `.env`.
- The concrete checkpointers are instantiated there using LangGraph's built-ins:
  - `langgraph.checkpoint.memory.MemorySaver` (RAM)
  - `langgraph.checkpoint.sqlite.SqliteSaver` (SQLite)

2) Scratchpad notes (simple user profile):
- `memory/scratchpad.py` stores stable facts like Name/Location/Preferences.
- Enabled by setting `SCRATCHPAD_PATH` to a JSON file path.

### 5. Triggers (Scheduler) (`triggers/`, `tools/`)
The trigger system is decoupled from the UI and the LLM:
- `triggers/base_trigger.py`: base trigger type (with claim/execution locking)
- `triggers/time_trigger.py`: executes when a scheduled time window is reached
- `triggers/scheduler.py`: in-memory scheduler (thread-safe)
- `triggers/engine.py`: background polling loop that dispatches due triggers

Tools exposed to the LLM:
- `triggers/time_trigger_tool.py`: `schedule_at_time()`, `schedule_in_delay()`
- `triggers/trigger_tool.py`: list/delete triggers + `schedule_action()` wrapper

Note:
- Trigger-related tools live under `triggers/` (domain ownership). The `tools/` folder contains unrelated tools (search, weather, time context).

### 6. UI (Pixel Face) (`ui/`)
This repo also includes a Pygame pixel-art face UI:
- `ui/pixel_display.py`: window + event loop
- `ui/pixel_renderer.py`: animations and rendering
- `ui/window_manager.py`: window shaping/transparency helpers

Note: the UI can be run independently from the assistant core.

## ⚙️ Configuration
ARIA uses `python-dotenv` in `core.py`.

- **Recommended:** Run the interactive setup wizard to generate your `.env`:
  ```bash
  python setup.py
  ```
- Or manually copy `.env.example` to `.env` and fill in your values.

Key variables (non-exhaustive):
- Modes: `INPUT_MODE` (`text|audio`), `OUTPUT_MODE` (`text|audio`)
- Telegram: `TELEGRAM_BOT_TOKEN` (optional, enables the Telegram channel)
- Provider: `AI_SOURCE` (`ollama|mistral|kobold`)
- Model: `AI_MODEL_ID`
- Provider-specific:
  - `OLLAMA_HOST` (optional)
  - `MISTRAL_API_KEY` (required if `AI_SOURCE=mistral`)
  - `KOBOLD_URL` (required if `AI_SOURCE=kobold`)
- Voice: `TTS_LANG`, `TTS_SPEED`, `TTS_OUTPUT_DEVICE` / `AUDIO_OUTPUT_DEVICE`
- STT: `STT_MODEL`, `STT_LANG`
- Conversation memory: `CONTEXT_BACKEND` (`ram|sqlite`), `CONTEXT_DB_PATH`
- Scratchpad: `SCRATCHPAD_PATH`
- Web search: requires `TAVILY_API_KEY`

## 🔐 Security & publishing checklist
Before publishing this repository on GitHub:
- **Never commit secrets**: API keys, tokens, private endpoints.
  - Keep `.env` ignored and only commit `.env.example`.
  - Rotate any key that has been committed or shared.
- Secrets to watch: `MISTRAL_API_KEY`, `TAVILY_API_KEY`, `HF_TOKEN`, `TELEGRAM_BOT_TOKEN`.

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

### 3) UI only
```bash
python ui/pixel_display.py
```

### 4) Interactive setup wizard
```bash
python setup.py
```

## 🧰 Tools available to the LLM
ARIA follows a strict separation of concerns:
- **Tools are dumb** (they expose capabilities)
- **The LLM decides** if/when/how to call them

Current tools (see `tools/`):
- Trigger scheduling:
  - `schedule_at_time(time_str, action_prompt, context=None)` where `time_str` is `HH:MM`
  - `schedule_in_delay(delay_str, action_prompt, context=None)` where `delay_str` is `+10m` / `+2h`
  - `schedule_action(time_str, action_prompt, context=None)` backward-compatible wrapper
- Trigger management:
  - `list_all_triggers()` returns a structured dict (ids + status + optional scheduled_time)
  - `delete_trigger(trigger_id)` returns `{success, message}`
  - `delete_triggers_by_prompt(prompt_substring)` returns `{success, deleted, message}`
- Time context:
  - `get_temporal_context()`
- Web search:
  - Tavily search tool in `tools/search_tool.py` (requires `TAVILY_API_KEY`, automatically disabled if missing)
- Weather:
  - Open-Meteo (no API key) via `get_weather_forecast(city, date_str="", country_code="")`
- Scratchpad memory:
  - `set_memory(key, value)` persists stable user info when `SCRATCHPAD_PATH` is set

## 🧪 Development Guidelines

### Language & Style
- **All code, comments, docstrings, variable names, and class names must be in English.** No exceptions.
- All user-facing strings (terminal logs, Telegram system messages, setup wizard) must also be in English.
- System messages sent to end-users via Telegram must be prefixed with `🔧 System:` to distinguish them from LLM-generated responses.

### Core Philosophy: Modularity
ARIA is designed to be **modular above all else**. Every component (agent, channel, tool, provider) must be swappable, removable, or replaceable without affecting the rest of the system. Before writing any code, ask yourself:
- Can this feature be disabled via `.env` without breaking anything?
- Can someone add a similar feature without modifying existing files?
- Does this introduce a hard dependency between two modules that were previously independent?

If the answer to any of these is wrong, rethink the design. The goal is a system where you can plug in a new LLM provider, a new communication channel, or a new tool in minutes — not hours.

### Architecture Principles
- **Separation of concerns is strict.** Each folder owns its domain:
  - `brain/` → LLM providers and the generic `AgentBrain` base class. Must not import `memory/`, `channels/`, or `tools/`.
  - `agents/` → Concrete agent subclasses (personality, system prompt, tool selection). Each agent uses `AgentBrain` via inheritance and can import from `memory/`, `tools/`, and `triggers/`.
  - `channels/` → I/O adapters (terminal, audio, Telegram). Channels never call the LLM directly; they emit `MessageContext` objects to the orchestrator.
  - `tools/` → Standalone LLM-callable tools (search, weather, time). A tool must not import from `brain/` or `channels/`.
  - `triggers/` → Trigger domain (scheduler, engine, trigger types, trigger-related tools). Trigger tools live here, not in `tools/`.
  - `core.py` → The async orchestrator. It routes messages and wires components. It must not contain business logic.

### Adding a New Agent
1. Create a new file in `agents/` (e.g., `agents/my_agent.py`).
2. Subclass `AgentBrain` from `brain/brain_module.py`.
3. Override `get_system_prompt()` to define the agent's personality and instructions.
4. Select tools in `__init__()` and pass them to `super().__init__()`.
5. Implement a `from_env()` classmethod that reads configuration from `.env` and returns a ready instance.
6. Use `AgentBrain.build_provider(source, temperature)` to instantiate the LLM provider.

### Adding a New Channel
1. Create a new file in `channels/` (e.g., `channels/discord_channel.py`).
2. Subclass `BaseChannel` from `channels/base.py`.
3. Implement `start()`, `stop()`, and `send_async(message: MessageContext)`.
4. When user input is received, build a `MessageContext` and call `await self.on_message_received(msg)`.
5. Register the channel in `core.py` → `CoreOrchestrator.__init__()` using `self.register_channel(...)`.
6. The `send_async()` method must handle both `async generators` and plain strings in `message.content`.

### Adding a New Tool
1. Create a new file in `tools/` (or `triggers/` if trigger-related).
2. Use the `@tool` decorator from `langchain_core.tools`.
3. The tool function must return a `str` (the result the LLM will see).
4. Include a detailed docstring with `Args:`, `Returns:`, and `Failure modes:` so the LLM knows when and how to use it.
5. Wire the tool into the appropriate agent's `__init__()` in `agents/`.

### Adding a New LLM Provider
1. Create a new file in `brain/` (e.g., `brain/openrouter_provider.py`).
2. Subclass `ModelProvider` from `brain/model_provider.py` and implement `get_model()`.
3. Register it in `AgentBrain.build_provider()` inside `brain/brain_module.py`.
4. Add the corresponding env vars to `.env.example` and to `setup.py`.

### Configuration & Environment
- All runtime configuration goes through `.env` (loaded by `python-dotenv`).
- Every new env var must be added to **both** `.env.example` (with a comment) and `setup.py` (interactive wizard).
- Use `os.getenv("KEY", "default")` with sensible defaults so ARIA can start with minimal configuration.

### General Rules
- Prefer small, composable modules over large monolithic files.
- Keep orchestration in `core.py` — it wires components, it doesn't decide behavior.
- Keep business logic out of tools: tools should delegate to modules and return structured results.
- `core.py` runs on `asyncio`. Any blocking call (LLM inference, audio generation, STT) must be wrapped with `asyncio.to_thread()`.
- When consuming LLM output in a channel, always check for `__aiter__` (async generator) first, then `__iter__`, then plain `str`.

## 🗺️ Roadmap (high-level)
- Link `core.py` runtime states to Pygame face animations (Idle, Listening, Thinking, Speaking).
- Add non-time triggers (event-based triggers).
- Make trigger storage persistent (optional).
- ~~Create an interactive install/setup script to generate and validate `.env`.~~ ✅ Done (`setup.py`)
- Implement a "Visual Cortex" tool (screenshot capture + analysis via a sub-agent to protect VRAM).
- Add basic system control tools (launch local apps and simple browser control).
- Expand the action/tooling layer (system automation) with safe permissions.
