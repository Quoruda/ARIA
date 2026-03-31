import os
from faster_whisper import WhisperModel
from stt.transcriber import BaseTranscriber

class FasterWhisperTranscriber(BaseTranscriber):
    def __init__(self, model_name="small", language="fr"):
        print(f"⏳ Loading model '{model_name}'...")
        
        hf_token = os.getenv("HF_TOKEN")
        
        self.model = WhisperModel(
            model_name, 
            device="cpu", 
            compute_type="int8",
            download_root=None,
            use_auth_token=hf_token
        )
        self.language = language
        self.last_context = ""
        print("✅ Model ready.")

    def transcribe(self, audio_data) -> str:
        segments, _ = self.model.transcribe(
            audio_data,
            language=self.language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=300),
            initial_prompt=self.last_context
        )
        
        text = " ".join(seg.text.strip() for seg in segments).strip()
        
        # Preserve context for subsequent transcriptions
        if text:
            words = text.split()
            self.last_context = " ".join(words[-15:])
            
        return text