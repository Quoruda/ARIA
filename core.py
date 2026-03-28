import re
import os
import threading
from dotenv import load_dotenv

from brain.brain_module import AgentBrain
from brain.ollama_provider import OllamaProvider
from brain.mistral_provider import MistralProvider
from tts.kokoro_voice import KokoroVoice

class CoreManager:
    def __init__(self):
        load_dotenv()
        print("--- Initialisation du Système ---")
        
        # 1. Sélection du Provider de Cerveau via .env
        source = os.getenv("ARIA_AI_SOURCE", "ollama").lower()
        if source == "mistral":
            print("Mode: Mistral AI API")
            provider = MistralProvider(
                model_id=os.getenv("MISTRAL_MODEL_ID", "mistral-small-latest"),
                api_key=os.getenv("MISTRAL_API_KEY")
            )
        else:
            print(f"Mode: Ollama ({os.getenv('OLLAMA_MODEL_ID', 'mistral-nemo:12b')})")
            provider = OllamaProvider(
                model_id=os.getenv("OLLAMA_MODEL_ID", "mistral-nemo:12b"),
                host=os.getenv("OLLAMA_HOST")
            )
            
        self.brain = AgentBrain(provider=provider)
        
        # 2. Configuration de la voix via .env
        self.voice = KokoroVoice(
            lang_code=os.getenv("TTS_LANG", "f"), 
            voice_name=os.getenv("TTS_VOICE", "ff_siwis"),
            speed=float(os.getenv("TTS_SPEED", "1.0"))
        )
        
        # Charge le modèle vocal en mémoire et démarre le flux
        self.voice.load_model()
        self.voice.start_playback() 
        print("--- Système Prêt ---")

    def process_input(self, user_text: str):
        """
        Reçoit l'entrée utilisateur et lance la réflexion dans un Thread
        pour ne pas bloquer l'interface.
        """
        print(f"\n💬 Vous : {user_text}")
        threading.Thread(target=self._think_and_stream, args=(user_text,), daemon=True).start()

    def _think_and_stream(self, user_text: str):
        """
        Récupère les mots un par un, construit des phrases et les envoie à la voix.
        """
        sentence_buffer = ""
        print("🔊 ARIA : ", end="", flush=True)
        
        # Regex pour détecter la fin d'une phrase (. ! ? suivis d'un espace ou fin de ligne)
        sentence_end_pattern = re.compile(r'([.!?]+(?:\s+|$))')

        # 1. On lit le flux de l'Agent mot par mot
        for word in self.brain.get_stream_response(user_text):
            print(word, end="", flush=True) # Affichage dans la console
            sentence_buffer += word
            
            # 2. Vérifie si on a une phrase complète
            match = sentence_end_pattern.search(sentence_buffer)
            if match:
                # On extrait la phrase complète
                end_index = match.end()
                phrase_to_speak = sentence_buffer[:end_index].strip()
                
                # --- NOUVEAU : LE FILTRE DE NETTOYAGE ---
                # 1. Enlève "Speaking:" ou "**Speaking:**" (insensible à la casse)
                phrase_propre = re.sub(r'\*?\*?Speaking:\*?\*?\s*', '', phrase_to_speak, flags=re.IGNORECASE)
                # 2. Enlève tous les astérisques restants
                phrase_propre = phrase_propre.replace('*', '').strip()
                
                # On l'envoie à la génération audio !
                if len(phrase_propre) > 1:
                    self.voice.generate_audio(phrase_propre)
                
                # On garde le reste (s'il y a des mots après le point)
                sentence_buffer = sentence_buffer[end_index:]

        # 3. À la fin, on envoie ce qui reste dans le buffer (s'il n'y avait pas de point final)
        if sentence_buffer.strip():
            phrase_finale = re.sub(r'\*?\*?Speaking:\*?\*?\s*', '', sentence_buffer, flags=re.IGNORECASE).replace('*', '').strip()
            if len(phrase_finale) > 1:
                self.voice.generate_audio(phrase_finale)
        print() # Retour à la ligne quand elle a fini de parler

if __name__ == "__main__":
    core = CoreManager()
    
    # Boucle de test console
    while True:
        try:
            user_input = input("\n>>> ")
            if user_input.lower() in ['q', 'quit', 'exit']:
                # On arrête proprement le thread audio avant de quitter
                core.voice.stop_playback()
                break
            if user_input.strip():
                core.process_input(user_input)
        except KeyboardInterrupt:
            core.voice.stop_playback()
            break