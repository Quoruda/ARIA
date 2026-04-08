import asyncio
import os
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from .base import BaseChannel
from .message import MessageContext
from tts.kokoro_voice import KokoroVoice
from stt.whisper_faster import FasterWhisperTranscriber

class TelegramChannel(BaseChannel):
    """A channel that connects ARIA to a Telegram Bot."""
    
    def __init__(self, name: str = "telegram"):
        super().__init__(name)
        self.app = None
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.voice = None
        self.transcriber = None

    async def start(self):
        if not self.token:
            print("⚠️ [Telegram] TELEGRAM_BOT_TOKEN missing in .env, Telegram channel disabled.")
            return

        print("🚀 [Telegram] Loading STT and TTS models...")
        self.voice = KokoroVoice(
            lang_code=os.getenv("TTS_LANG", "f"),
            speed=float(os.getenv("TTS_SPEED", "1.0"))
        )
        # Avoid double-loading by just instantiating here and model is loaded when needed
        # Or load it to avoid lag on first message
        # self.voice.load_model()
        
        self.transcriber = FasterWhisperTranscriber(
            model_name=os.getenv("STT_MODEL", "small"), 
            language=os.getenv("STT_LANG", "fr")
        )

        self.app = Application.builder().token(self.token).build()
        self.app.add_handler(CommandHandler("start", self._start_handler))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text))
        self.app.add_handler(MessageHandler(filters.VOICE, self._handle_voice))
        
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        print("✅ [Telegram] Bot started successfully!")

    async def stop(self):
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
            self.app = None
            
    async def _start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔧 System: ARIA bot is online and ready.")

    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.on_message_received:
            return
            
        chat_id = str(update.effective_chat.id)
        user_text = update.message.text
        
        print(f"\n[Telegram Text] User: {user_text}")
        
        msg = MessageContext(
            source_channel=self.name,
            content=user_text,
            user_id=chat_id,
            payload={"reply_mode": "text"}
        )
        # Call the orchestrator in the background to not block the current handler
        asyncio.create_task(self.on_message_received(msg))

    async def _handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.on_message_received:
            return
            
        chat_id = str(update.effective_chat.id)
        print("\n[Telegram Voice] Downloading and transcribing voice message...")
        
        voice_file = await update.message.voice.get_file()
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_ogg:
            ogg_path = temp_ogg.name
            
        await voice_file.download_to_drive(ogg_path)
        
        try:
            user_text = await asyncio.to_thread(self.transcriber.transcribe, ogg_path)
        except Exception:
            await update.message.reply_text("🔧 System: Internal error during transcription.")
            os.remove(ogg_path)
            return

        os.remove(ogg_path)
        
        if not user_text.strip():
            await update.message.reply_text("🔧 System: Audio transcription was empty (no sound detected).")
            return

        print(f"[Telegram Voice] User: {user_text}")

        msg = MessageContext(
            source_channel=self.name,
            content=user_text,
            user_id=chat_id,
            payload={"reply_mode": "voice"}
        )
        asyncio.create_task(self.on_message_received(msg))

    async def send_async(self, message: MessageContext):
        if not self.app:
            return
            
        chat_id = message.user_id
        if not chat_id:
            return
            
        content = message.content
        response_text = ""
        
        if hasattr(content, "__aiter__"):
            async for chunk in content:
                response_text += chunk
        elif hasattr(content, "__iter__") and not isinstance(content, str):
            for chunk in content:
                response_text += chunk
        else:
            response_text = str(content)
            
        is_voice = message.payload and isinstance(message.payload, dict) and message.payload.get("reply_mode") == "voice"

        if is_voice and self.voice:
            if not response_text.strip():
                await self.app.bot.send_message(chat_id=chat_id, text="🔧 System: No text response could be generated by the AI.")
                return
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                wav_path = temp_wav.name
            try:
                # generate_audio_file loads the model dynamically if needed
                await asyncio.to_thread(self.voice.generate_audio_file, response_text, wav_path)
                with open(wav_path, 'rb') as f:
                    await self.app.bot.send_voice(chat_id=chat_id, voice=f)
            except Exception as e:
                print(f"[Telegram] TTS error: {e}")
                await self.app.bot.send_message(chat_id=chat_id, text=f"🔧 System: Voice rendering failed. Here is the text response:\n\n{response_text}")
            finally:
                if os.path.exists(wav_path):
                    os.remove(wav_path)
        else:
            if response_text.strip():
                await self.app.bot.send_message(chat_id=chat_id, text=response_text)
            else:
                print("[Telegram] No response generated (empty text).")
