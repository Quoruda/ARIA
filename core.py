import os
import asyncio
import logging
import warnings
from dotenv import load_dotenv

from agents.default_agent import DefaultAgent
from agents.trigger_agent import TriggerAgent
from triggers.engine import TriggerEngine

from channels.message import MessageContext
from channels.local_audio_channel import LocalAudioChannel
from channels.local_terminal_channel import LocalTerminalChannel
from channels.telegram_channel import TelegramChannel

load_dotenv()

# Suppress HF Hub and other library warnings
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning)

class CoreOrchestrator:
    """The central asynchronous router for ARIA, dispatching messages between Inputs, LLM Brains, and Outputs."""
    
    def __init__(self):
        self.input_mode = os.getenv("INPUT_MODE", "audio").lower()
        self.output_mode = os.getenv("OUTPUT_MODE", "audio").lower()
        
        print(f"--- System Initialization (In: {self.input_mode}, Out: {self.output_mode}) ---")

        # 1. Brains
        self.brain = DefaultAgent.from_env()
        self.trigger_brain = TriggerAgent.from_env()

        # 2. Channels Registry
        self.channels = {}
        
        if self.input_mode == "audio" and self.output_mode == "audio":
            self.register_channel(LocalAudioChannel())
        else:
            self.register_channel(LocalTerminalChannel())
            
        if os.getenv("TELEGRAM_BOT_TOKEN"):
            self.register_channel(TelegramChannel())

        # 3. Trigger Engine
        self.trigger_engine = TriggerEngine(
            is_busy=self.is_busy,
            process_prompt=self.handle_trigger_prompt_sync,
        )

        self._loop = None
        self._is_generating = False

    def register_channel(self, channel):
        self.channels[channel.name] = channel
        channel.set_callback(self.handle_incoming_message)

    def is_busy(self) -> bool:
        """Returns True if the AI is generating, or the local audio system is occupied."""
        busy = self._is_generating
        
        local_audio = self.channels.get("local_audio")
        if local_audio:
            if local_audio.voice:
                try:
                    import sounddevice as sd
                    stream = sd.get_stream()
                    if stream and stream.active:
                        busy = True
                except Exception:
                    pass
            if local_audio.recorder:
                busy = busy or local_audio.recorder.is_recording
                
        return busy

    async def handle_incoming_message(self, message: MessageContext):
        """Callback invoked by any Channel when a user inputs something."""
        self._is_generating = True
        try:
            # Helper to wrap the synchronous Agent stream into an async generator
            async def async_generator(user_input):
                 from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed, retry_if_exception_type
                 _sentinel = object()
                 async for attempt in AsyncRetrying(
                     stop=stop_after_attempt(3),
                     wait=wait_fixed(5),
                     retry=retry_if_exception_type(Exception),
                     reraise=False,
                 ):
                     with attempt:
                         try:
                             gen = self.brain.stream(user_input)
                             while True:
                                 chunk = await asyncio.to_thread(next, gen, _sentinel)
                                 if chunk is _sentinel:
                                     break
                                 yield chunk
                         except Exception as e:
                             if attempt.retry_state.attempt_number == 3:
                                 yield "Sorry, I'm experiencing technical difficulties. Please try again later."
                             raise

            # Send back the reply on the target channel
            reply_msg = MessageContext(
                source_channel="orchestrator",
                target_channel=message.target_channel or message.source_channel,
                content=async_generator(message.content),
                user_id=message.user_id,
                payload=message.payload # Forward the payload (like telegram reply_mode)
            )
            
            target_chan = self.channels.get(reply_msg.target_channel)
            if target_chan:
                await target_chan.send_async(reply_msg)
            else:
                print(f"⚠️ Aucun canal trouvé pour le routage de la cible: {reply_msg.target_channel}")
                
        finally:
            self._is_generating = False

    def handle_trigger_prompt_sync(self, text: str):
        """Called synchronously by the TriggerEngine background thread."""
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._handle_trigger_async(text), self._loop)

    async def _handle_trigger_async(self, text: str):
        logging.info(f"Processing trigger: {text}")
        self._is_generating = True
        try:
            async def async_generator(user_input):
                from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed, retry_if_exception_type
                _sentinel = object()
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(3),
                    wait=wait_fixed(5),
                    retry=retry_if_exception_type(Exception),
                    reraise=False,
                ):
                    with attempt:
                        try:
                            gen = self.trigger_brain.stream(user_input)
                            while True:
                                chunk = await asyncio.to_thread(next, gen, _sentinel)
                                if chunk is _sentinel:
                                    break
                                yield chunk
                        except Exception as e:
                            if attempt.retry_state.attempt_number == 3:
                                # final failure, silently stop (no user‑visible chunk needed)
                                pass
                            raise
            # Send triggers to the active primary channel (e.g. local_audio)
            target = "local_audio" if "local_audio" in self.channels else "local_terminal"
            
            reply_msg = MessageContext(
                source_channel="trigger_engine",
                target_channel=target,
                content=async_generator(text)
            )
            
            if target in self.channels:
                await self.channels[target].send_async(reply_msg)
        finally:
            self._is_generating = False

    async def start(self):
        self._loop = asyncio.get_running_loop()
        
        # Special setup: If local audio is active, inject the Voice tools into the Brain
        if "local_audio" in self.channels:
            from tts.voice import Voice
            voice = Voice.from_env()
            self.brain.add_tools(voice.get_tools())
            
            # Inject preloaded voice into the channel so it doesn't double-load
            self.channels["local_audio"].voice = voice

        # Start all channels
        for chan in self.channels.values():
            await chan.start()
            
        self.trigger_engine.start()
        print("--- System Ready ---")
        
        # Infinite loop
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        finally:
            print("\nArrêt des canaux en cours...")
            for chan in self.channels.values():
                await chan.stop()
            self.trigger_engine.stop()

if __name__ == "__main__":
    core = CoreOrchestrator()
    try:
        asyncio.run(core.start())
    except KeyboardInterrupt:
        print("\n👋 Arrêt du système.")
