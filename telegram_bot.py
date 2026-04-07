import os
import tempfile
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Import ARIA components
from agents.default_agent import DefaultAgent
from tts.kokoro_voice import KokoroVoice
from stt.whisper_faster import FasterWhisperTranscriber

# ======================================================================
# Bot Implementation
# ======================================================================
def initialize_system():
    # Load env variables
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Erreur: TELEGRAM_BOT_TOKEN n'est pas défini dans le fichier .env")
        return None

    # Initialize AI Brain
    print("⏳ Chargement du cerveau ARIA...")
    brain = DefaultAgent.from_env()

    # Initialize Voice
    print("⏳ Chargement du modèle vocal...")
    voice = KokoroVoice(
        lang_code=os.getenv("TTS_LANG", "f"),
        speed=float(os.getenv("TTS_SPEED", "1.0"))
    )
    voice.load_model()
    # Add voice tools to the agent, similar to core.py
    brain.add_tools(voice.get_tools())

    # Initialize STT
    print("⏳ Chargement du modèle de transcription...")
    model_name = os.getenv("STT_MODEL", "small")
    language = os.getenv("STT_LANG", "fr")
    transcriber = FasterWhisperTranscriber(model_name=model_name, language=language)

    return token, brain, voice, transcriber


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bonjour ! Je suis ARIA, ton assistant. Envoie-moi un message texte ou vocal !")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    brain = context.bot_data['brain']
    
    print(f"\n[Telegram Text] Utilisateur: {user_text}")
    
    # Exécution synchrone dans un thread pour ne pas bloquer
    response_text = await asyncio.to_thread(brain.get_response, user_text)
    
    print(f"[Telegram Text] ARIA: {response_text}")
    await update.message.reply_text(response_text)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    brain = context.bot_data['brain']
    voice = context.bot_data['voice']
    transcriber = context.bot_data['transcriber']

    # Téléchargement du fichier ogg
    voice_file = await update.message.voice.get_file()
    
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_ogg:
        ogg_path = temp_ogg.name
    
    print("\n[Telegram Voice] Réception d'un message audio...")
    await voice_file.download_to_drive(ogg_path)
    
    # 1. Transcription (STT)
    try:
        user_text = await asyncio.to_thread(transcriber.transcribe, ogg_path)
    except Exception as e:
        print(f"Erreur de transcription: {e}")
        await update.message.reply_text("Désolé, je n'ai pas pu transcrire ton message vocal.")
        os.remove(ogg_path)
        return
        
    print(f"[Telegram Voice] Transcrit: {user_text}")
    
    if not user_text.strip():
        await update.message.reply_text("Je n'ai rien entendu dans ton message.")
        os.remove(ogg_path)
        return
        
    # 2. Réponse du modèle (Brain)
    response_text = await asyncio.to_thread(brain.get_response, user_text)
    print(f"[Telegram Voice] ARIA: {response_text}")
    
    # 3. Génération Vocale (TTS)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        wav_path = temp_wav.name
        
    try:
        await asyncio.to_thread(voice.generate_audio_file, response_text, wav_path)
        
        # Envoi de l'audio via Telegram
        with open(wav_path, 'rb') as f:
            await update.message.reply_voice(f)
            
    except Exception as e:
        print(f"Erreur de génération TTS: {e}")
        # Message de secours si le TTS échoue
        await update.message.reply_text(response_text) 
        
    finally:
        if os.path.exists(ogg_path):
            os.remove(ogg_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

def main():
    system = initialize_system()
    if not system:
        return
        
    token, brain, voice, transcriber = system
    
    app = Application.builder().token(token).build()
    
    # Stockage de nos instances dans bot_data pour les retrouver dans les handlers
    app.bot_data['brain'] = brain
    app.bot_data['voice'] = voice
    app.bot_data['transcriber'] = transcriber
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    print("✅ Bot Telegram ARIA démarré !")
    app.run_polling()

if __name__ == "__main__":
    main()
