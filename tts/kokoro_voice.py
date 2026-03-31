from tts.voice import Voice
from kokoro import KPipeline
import numpy as np
import torch

class KokoroVoice(Voice):
    def __init__(self, lang_code='a', speed=1.0):
        super().__init__() # Initializes the parent queue
        self.lang_code = lang_code
        self.speed = speed
        self.pipeline = None
        self.female_voices=("af_sarah", "af_heart", "af_bella")
        self.male_voices=("am_adam", "am_michael", "am_fenrir")
        self.calm_raw = 0.0
        self.warm_raw = 0.0
        self.dynamic_raw = 0.0
        self.gender_raw = 0.0

    def load_model(self):
        """Load the Kokoro model (CPU-only)."""
        print(f"Loading Kokoro model (lang={self.lang_code}) on CPU...")

        try:
            # device='cpu' ensures it runs on CPU
            self.pipeline = KPipeline(lang_code=self.lang_code, device='cpu')
        except NameError as e:
            raise RuntimeError(
                "KPipeline is not available. Ensure the 'kokoro' package is installed and exports KPipeline."
            ) from e

        print("Kokoro model loaded!")

    def unload_model(self):
        self.pipeline = None

    def generate_audio(self, text: str):
        """Generate audio with Kokoro and enqueue it for playback."""
        if self.pipeline is None:
            self.load_model()

        # Kokoro natively splits long sentences into generators
        voice_pack = self.get_voice_pack()
        generator = self.pipeline(text, voice=voice_pack, speed=self.speed)

        for _, _, audio_chunk in generator:
            # Kokoro always outputs 24000 Hz.
            self.add_to_queue(audio_chunk, 24000)

    def get_voice_pack(self):
        weights = np.exp([self.calm_raw, self.warm_raw, self.dynamic_raw])
        weights /= weights.sum()  # softmax
        gender = 1 / (1 + np.exp(-self.gender_raw))  # sigmoid

        voice_weights = {}
        for i, (f, m) in enumerate(zip(self.female_voices, self.male_voices)):
            f_weight = weights[i] * (1 - gender)
            m_weight = weights[i] * gender
            if f_weight > 0.01: voice_weights[f] = f_weight
            if m_weight > 0.01: voice_weights[m] = m_weight

        total = sum(voice_weights.values())
        
        packs = []
        for voice, w in voice_weights.items():
            normalized_weight = w / total
            pack = self.pipeline.load_single_voice(voice)
            packs.append(pack * normalized_weight)
            
        return torch.sum(torch.stack(packs), dim=0)
