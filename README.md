# 🤖 ARIA

ARIA is a local-first AI assistant with an animated pixel-art face. It supports voice interaction (push-to-talk + TTS), a Telegram bot, and a modular LLM backend (Ollama, Mistral, KoboldAI).

## Requirements

- **Python 3.12** (Python 3.13 is **not supported** due to dependency incompatibilities)
- System audio access (PortAudio) if using voice mode
- An LLM provider: [Ollama](https://ollama.com), [Mistral AI](https://mistral.ai), or a KoboldAI-compatible server

## Installation

```bash
git clone https://github.com/Quoruda/ARIA.git
cd ARIA
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Run the interactive setup wizard:

```bash
python setup.py
```

Or manually copy `.env.example` to `.env` and fill in your values.

## Usage

```bash
python core.py
```

In audio mode, hold **Ctrl+Alt** to speak. If a Telegram bot token is configured, the bot starts automatically alongside the local interface.

## Project Structure

```
core.py              # Async orchestrator (message router)
setup.py             # Interactive .env setup wizard
channels/            # I/O channels (terminal, audio, Telegram)
brain/               # LLM providers & AgentBrain base class
agents/              # Concrete agents (default + trigger)
memory/              # Context persistence (RAM / SQLite) & scratchpad
triggers/            # Scheduled trigger engine & tools
stt/                 # Speech-to-text (Faster-Whisper)
tts/                 # Text-to-speech (Kokoro)
tools/               # LLM tools (web search, weather, time)
ui/                  # Pixel-art face UI (Pygame)
```

## License

MIT
