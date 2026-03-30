# transcription.py
import os
from faster_whisper import WhisperModel
from transcriber import BaseTranscriber

class FasterWhisperTranscriber(BaseTranscriber):
    def __init__(self, model_name="small", language="fr"):
        print(f"⏳ Chargement du modèle '{model_name}'...")
        
        # Récupération du token Hugging Face (optionnel)
        hf_token = os.getenv("HF_TOKEN")
        
        # Modifie compute_type si tu passes sur GPU ("float16" ou "int8_float16")
        self.model = WhisperModel(
            model_name, 
            device="cpu", 
            compute_type="int8",
            download_root=None, # Utilise le cache par défaut
            use_auth_token=hf_token
        )
        self.language = language
        self.last_context = ""
        print("✅ Modèle prêt.")

    def transcribe(self, audio_data) -> str:
        segments, _ = self.model.transcribe(
            audio_data,
            language=self.language,
            beam_size=5,
            vad_filter=True, # Laisse Whisper gérer les silences
            vad_parameters=dict(min_silence_duration_ms=300),
            initial_prompt=self.last_context # Garde le contexte du chunk précédent !
        )
        
        text = " ".join(seg.text.strip() for seg in segments).strip()
        
        # Conserve les ~15 derniers mots en mémoire pour aider la prochaine transcription
        if text:
            words = text.split()
            self.last_context = " ".join(words[-15:])
            
        return text