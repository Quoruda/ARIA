import asyncio
import re
from typing import Optional
from .base import BaseChannel
from .message import MessageContext
from stt.micro_recorder import PushToTalkRecorder
from tts.voice import Voice

class LocalAudioChannel(BaseChannel):
    """A channel that connects the local microphone for STT and local speakers for TTS."""
    
    def __init__(self, name: str = "local_audio"):
        super().__init__(name)
        self.recorder: Optional[PushToTalkRecorder] = None
        self.voice: Optional[Voice] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._sentence_end_pattern = re.compile(r'([.!?]+(?:\s+|$))')

    async def start(self):
        self._loop = asyncio.get_running_loop()
        
        # Initialize Voice engine if not previously injected
        if self.voice is None:
            self.voice = Voice.from_env()
        
        # Initialize Microphone
        self.recorder = PushToTalkRecorder.from_env(
            on_transcription=self._on_mic_transcription,
            can_record=self.can_record
        )
        
        # recorder.start() is blocking (due to listener.join()), so we must run it in a thread
        import threading
        self._recorder_thread = threading.Thread(target=self.recorder.start, daemon=True)
        self._recorder_thread.start()

    async def stop(self):
        if self.recorder:
            self.recorder.running = False
        if self.voice:
            self.voice.unload_model()
            
    def can_record(self) -> bool:
        """Prevent recording if TTS is currently playing audio."""
        try:
            import sounddevice as sd
            stream = sd.get_stream()
            if stream and stream.active:
                return False
        except Exception:
            pass
        return True

    def _on_mic_transcription(self, user_text: str):
        """Called by the STT thread when a sentence is recognized."""
        if not user_text.strip() or not self.on_message_received:
            return
            
        print(f"\n🎙  Vous: {user_text}")
        msg = MessageContext(source_channel=self.name, content=user_text)
        
        # We are in a background thread here, route back to asyncio loop
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self.on_message_received(msg), self._loop)

    async def send_async(self, message: MessageContext):
        content = message.content
        
        sentence_buffer = ""
        sent_to_tts = set()
        print("🔊 ARIA: ", end="", flush=True)

        async def process_chunk(chunk):
            nonlocal sentence_buffer
            print(chunk, end="", flush=True)
            sentence_buffer += chunk

            match = self._sentence_end_pattern.search(sentence_buffer)
            if match:
                end_index = match.end()
                phrase = sentence_buffer[:end_index].strip()

                if len(phrase) > 1 and self.voice is not None:
                    if phrase not in sent_to_tts:
                        # Kokoro generation might block, run in thread to avoid freezing orchestrator
                        await asyncio.to_thread(self.voice.generate_audio, phrase)
                        sent_to_tts.add(phrase)

                sentence_buffer = sentence_buffer[end_index:]

        if hasattr(content, "__aiter__"):
            async for chunk in content:
                await process_chunk(chunk)
        elif hasattr(content, "__iter__") and not isinstance(content, str):
            for chunk in content:
                await process_chunk(chunk)
        else:
            await process_chunk(str(content))

        # Flush remaining words
        if sentence_buffer.strip():
            phrase = sentence_buffer.strip()
            if len(phrase) > 1 and self.voice is not None:
                if phrase not in sent_to_tts:
                    await asyncio.to_thread(self.voice.generate_audio, phrase)
                    sent_to_tts.add(phrase)
        print()
