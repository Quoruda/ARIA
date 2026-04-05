import os
import threading
import logging
import warnings
from dotenv import load_dotenv
load_dotenv()

from triggers.engine import TriggerEngine
from agents.default_agent import DefaultAgent
from agents.trigger_agent import TriggerAgent
from tts.tts import Voice
from input import InputManager
from output import OutputManager

# Suppress HF Hub and other library warnings
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning)


class CoreManager:
    def __init__(self):
        
        # Read modes from .env
        self.input_mode = os.getenv("INPUT_MODE", "audio").lower()
        self.output_mode = os.getenv("OUTPUT_MODE", "audio").lower()
        
        print(f"--- System Initialization (In: {self.input_mode}, Out: {self.output_mode}) ---")

        # 1. Brains
        self.brain = DefaultAgent.from_env()
        self.trigger_brain = TriggerAgent.from_env()

        # 2. Voice (TTS) — Loaded only if output is audio
        self.voice = Voice.from_env() if self.output_mode == "audio" else None

        # 3. Output
        self.output = OutputManager.from_env(
            voice=self.voice,
            mode=self.output_mode,
        )

        # 4. Input
        self.input = InputManager.from_env(
            on_input=self.handle_user_prompt,
            is_busy=self.is_busy,
            mode=self.input_mode,
            voice=self.voice,
        )

        # 5. Trigger Engine
        self.trigger_engine = TriggerEngine(
            is_busy=self.is_busy,
            process_prompt=self.handle_trigger_prompt,
        )
        self.trigger_engine.start()

        print("--- System Ready ---")

    def is_busy(self) -> bool:
        """Returns True if the AI is generating, speaking, or the user is recording."""
        busy = self.output.is_generating
        
        if self.output_mode == "audio" and self.voice:
            busy = busy or (self.voice.audio_queue.unfinished_tasks > 0)
            
        if self.input_mode == "audio" and self.input.recorder:
            busy = busy or self.input.recorder.is_recording
            
        return busy

    def handle_user_prompt(self, text: str):
        """Handle user input from STT or terminal."""
        print(f"\n💬 You: {text}")
        self.output.stream_async(lambda: self.brain.stream(text))

    def handle_trigger_prompt(self, text: str):
        """Handle trigger execution from TriggerEngine."""
        logging.info(f"Processing trigger: {text}")
        self.output.stream_async(lambda: self.trigger_brain.stream(text))

    def run(self):
        """Run the main input loop."""
        self.input.run()


if __name__ == "__main__":
    core = CoreManager()
    core.run()
