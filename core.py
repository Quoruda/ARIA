import re
import os
import threading
import logging
import warnings
import argparse
from dotenv import load_dotenv
from brain.triggers.engine import TriggerEngine

# Suppress HF Hub and other library warnings
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning)

from brain.brain_module import AgentBrain
from brain.ollama_provider import OllamaProvider
from brain.mistral_provider import MistralProvider
from tts.kokoro_voice import KokoroVoice

class CoreManager:
    def __init__(self, text_mode: bool = False):
        load_dotenv()
        self.text_mode = text_mode
        print("--- System Initialization ---")
        
        # 1. Select Brain Provider via .env
        source = os.getenv("ARIA_AI_SOURCE", "ollama").lower()
        temperature = float(os.getenv("ARIA_TEMPERATURE", "0.4"))

        if source == "mistral":
            print(f"Mode: Mistral AI API (temp: {temperature})")
            provider = MistralProvider(
                model_id=os.getenv("MISTRAL_MODEL_ID", "mistral-small-latest"),
                api_key=os.getenv("MISTRAL_API_KEY"),
                temperature=temperature
            )
        else:
            print(f"Mode: Ollama ({os.getenv('OLLAMA_MODEL_ID', 'mistral-nemo:12b')}, temp: {temperature})")
            provider = OllamaProvider(
                model_id=os.getenv("OLLAMA_MODEL_ID", "mistral-nemo:12b"),
                host=os.getenv("OLLAMA_HOST"),
                temperature=temperature
            )
            
        self.brain = AgentBrain(provider=provider)

        self._is_generating = False

        if not self.text_mode:
            # 2. Configure Voice via .env
            self.voice = KokoroVoice(
                lang_code=os.getenv("TTS_LANG", "f"),
                voice_name=os.getenv("TTS_VOICE", "ff_siwis"),
                speed=float(os.getenv("TTS_SPEED", "1.0"))
            )

            # Load voice model into memory and start playback stream
            self.voice.load_model()
            self.voice.start_playback()
        else:
            self.voice = None
            print("Text mode enabled: TTS/STT disabled. Terminal input/output only.")

        if not self.text_mode:
            # 3. Configure Micro (STT)
            from stt.micro_recorder import PushToTalkRecorder
            from stt.whisper_faster import FasterWhisperTranscriber
            stt_model = os.getenv("ARIA_STT_MODEL", "small")
            stt_lang = os.getenv("ARIA_STT_LANG", "fr")
            self.stt_engine = FasterWhisperTranscriber(model_name=stt_model, language=stt_lang)
            self.recorder = PushToTalkRecorder(
                transcriber=self.stt_engine,
                on_transcription=self.process_input,
                can_record=lambda: not self.is_busy()
            )
        else:
            self.stt_engine = None
            self.recorder = None

        # 4. Start Trigger Engine
        self.trigger_engine = TriggerEngine(
            is_busy=self.is_busy,
            process_prompt=self._handle_trigger_prompt,
        )
        self.trigger_engine.start()

        print("--- System Ready ---")

    def is_busy(self):
        """Returns True if the AI is generating, speaking, or if the user is currently recording."""
        if self.text_mode:
            return self._is_generating
        return (
            self._is_generating
            or self.voice.audio_queue.unfinished_tasks > 0
            or self.recorder.is_recording
        )

    def _handle_trigger_prompt(self, text: str):
        """Internal callback used by TriggerEngine."""
        self.handle_trigger_prompt(text)

    def handle_user_prompt(self, text: str):
        """Handle user input from STT or terminal."""
        print(f"\n💬 You: {text}")
        threading.Thread(target=self._think_and_stream_user, args=(text,), daemon=True).start()

    def handle_trigger_prompt(self, text: str):
        """Handle trigger execution from TriggerEngine."""
        logging.info(f"Processing trigger: {text}")
        threading.Thread(target=self._think_and_stream_trigger, args=(text,), daemon=True).start()

    def handle_prompt(self, text: str, source: str = "user"):
        """Unified entry point to process any prompt (user or trigger)."""
        if source == "user":
            self.handle_user_prompt(text)
        else:
            self.handle_trigger_prompt(text)

    def process_input(self, user_text: str):
        """Backward-compatible wrapper for STT callback."""
        self.handle_user_prompt(user_text)

    def _think_and_stream_user(self, user_text: str):
        """Stream response for user prompts."""
        self._is_generating = True
        try:
            sentence_buffer = ""
            print("🔊 ARIA: ", end="", flush=True)

            sentence_end_pattern = re.compile(r'([.!?]+(?:\s+|$))')

            for word in self.brain.get_stream_response(user_text):
                print(word, end="", flush=True)
                sentence_buffer += word

                match = sentence_end_pattern.search(sentence_buffer)
                if match:
                    end_index = match.end()
                    phrase_to_speak = sentence_buffer[:end_index].strip()

                    phrase_propre = re.sub(r'(?i)\b(speaking|thinking|processing|outputting)\b[:.]*\s*', '', phrase_to_speak)
                    phrase_propre = re.sub(r'\*[^*]+\*', '', phrase_propre)
                    phrase_propre = phrase_propre.replace('*', '').strip()

                    if len(phrase_propre) > 1 and self.voice is not None:
                        self.voice.generate_audio(phrase_propre)

                    sentence_buffer = sentence_buffer[end_index:]

            if sentence_buffer.strip():
                phrase_finale = re.sub(r'(?i)\b(speaking|thinking|processing|outputting)\b[:.]*\s*', '', sentence_buffer)
                phrase_finale = re.sub(r'\*[^*]+\*', '', phrase_finale)
                phrase_finale = phrase_finale.replace('*', '').strip()
                if len(phrase_finale) > 1 and self.voice is not None:
                    self.voice.generate_audio(phrase_finale)
        finally:
            self._is_generating = False
            if self.text_mode:
                print("\n💡 Type your message and press Enter (Ctrl+C to quit).", flush=True)
            else:
                print("\n💡 Press Ctrl+Alt to speak.", flush=True)

    def _think_and_stream_trigger(self, user_text: str):
        """Stream response for trigger execution (executes directly without reformulation)."""
        self._is_generating = True
        try:
            sentence_buffer = ""
            print("🔊 ARIA: ", end="", flush=True)

            sentence_end_pattern = re.compile(r'([.!?]+(?:\s+|$))')

            for word in self.brain.get_stream_response_trigger(user_text):
                print(word, end="", flush=True)
                sentence_buffer += word

                match = sentence_end_pattern.search(sentence_buffer)
                if match:
                    end_index = match.end()
                    phrase_to_speak = sentence_buffer[:end_index].strip()

                    phrase_propre = re.sub(r'(?i)\b(speaking|thinking|processing|outputting)\b[:.]*\s*', '', phrase_to_speak)
                    phrase_propre = re.sub(r'\*[^*]+\*', '', phrase_propre)
                    phrase_propre = phrase_propre.replace('*', '').strip()

                    if len(phrase_propre) > 1 and self.voice is not None:
                        self.voice.generate_audio(phrase_propre)

                    sentence_buffer = sentence_buffer[end_index:]

            if sentence_buffer.strip():
                phrase_finale = re.sub(r'(?i)\b(speaking|thinking|processing|outputting)\b[:.]*\s*', '', sentence_buffer)
                phrase_finale = re.sub(r'\*[^*]+\*', '', phrase_finale)
                phrase_finale = phrase_finale.replace('*', '').strip()
                if len(phrase_finale) > 1 and self.voice is not None:
                    self.voice.generate_audio(phrase_finale)
        finally:
            self._is_generating = False
            if self.text_mode:
                print("\n💡 Type your message and press Enter (Ctrl+C to quit).", flush=True)
            else:
                print("\n💡 Press Ctrl+Alt to speak.", flush=True)

    def run(self):
        """Run the main input loop."""
        if self.text_mode:
            print("\n💡 Type your message and press Enter (Ctrl+C to quit).")
            while True:
                try:
                    user_text = input("> ").strip()
                except EOFError:
                    return
                if not user_text:
                    continue
                self.handle_prompt(user_text, source="user")
        else:
            # Blocking recording loop
            try:
                self.recorder.start()
            except KeyboardInterrupt:
                self.voice.stop_playback()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ARIA")
    parser.add_argument("--text", action="store_true", help="Run in text-only mode (no TTS/STT)")
    args = parser.parse_args()

    # Env var also supported
    env_text = os.getenv("ARIA_TEXT_MODE", "0").strip().lower() in ("1", "true", "yes", "on")
    core = CoreManager(text_mode=args.text or env_text)
    core.run()
