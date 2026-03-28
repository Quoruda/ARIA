import re
import threading
from brain.brain_module import AgentBrain
from tts.kokoro_voice import KokoroVoice

class CoreManager:
    def __init__(self):
        print("--- Initialisation du Système ---")
        self.brain = AgentBrain()
        self.voice = KokoroVoice(lang_code='f', voice_name='ff_siwis')
        
        # On charge le modèle vocal en mémoire
        self.voice.load_model()
        # 🔥 C'est ici qu'était l'erreur : on appelle la nouvelle méthode du parent
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