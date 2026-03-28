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
        print("--- System Initialization ---")
        
        # 1. Select Brain Provider via .env
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
        
        # 2. Configure Voice via .env
        self.voice = KokoroVoice(
            lang_code=os.getenv("TTS_LANG", "f"), 
            voice_name=os.getenv("TTS_VOICE", "ff_siwis"),
            speed=float(os.getenv("TTS_SPEED", "1.0"))
        )
        
        # Load voice model into memory and start playback stream
        self.voice.load_model()
        self.voice.start_playback() 
        print("--- System Ready ---")

    def process_input(self, user_text: str):
        """
        Receives user input and starts the thinking process in a thread
        to avoid blocking the interface.
        """
        print(f"\n💬 You: {user_text}")
        threading.Thread(target=self._think_and_stream, args=(user_text,), daemon=True).start()

    def _think_and_stream(self, user_text: str):
        """
        Retrieves words one by one, builds sentences, and sends them to the voice module.
        """
        sentence_buffer = ""
        print("🔊 ARIA: ", end="", flush=True)
        
        # Regex to detect the end of a sentence (. ! ? followed by a space or end of line)
        sentence_end_pattern = re.compile(r'([.!?]+(?:\s+|$))')

        # 1. Read the Agent's stream word by word
        for word in self.brain.get_stream_response(user_text):
            print(word, end="", flush=True) # Console output
            sentence_buffer += word
            
            # 2. Check if we have a complete sentence
            match = sentence_end_pattern.search(sentence_buffer)
            if match:
                # Extract the full sentence
                end_index = match.end()
                phrase_to_speak = sentence_buffer[:end_index].strip()
                
                # --- NEW: CLEANING FILTER ---
                # 1. Remove "Speaking:" or "**Speaking:**" (case insensitive)
                phrase_propre = re.sub(r'\*?\*?Speaking:\*?\*?\s*', '', phrase_to_speak, flags=re.IGNORECASE)
                # 2. Remove any remaining asterisks
                phrase_propre = phrase_propre.replace('*', '').strip()
                
                # Send to audio generation!
                if len(phrase_propre) > 1:
                    self.voice.generate_audio(phrase_propre)
                
                # Keep the rest (if there are words after the punctuation)
                sentence_buffer = sentence_buffer[end_index:]

        # 3. Finally, send whatever remains in the buffer (if there was no trailing punctuation)
        if sentence_buffer.strip():
            phrase_finale = re.sub(r'\*?\*?Speaking:\*?\*?\s*', '', sentence_buffer, flags=re.IGNORECASE).replace('*', '').strip()
            if len(phrase_finale) > 1:
                self.voice.generate_audio(phrase_finale)
        print() # New line when finished speaking

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