from tts.voice import Voice
from langchain_core.tools import tool
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

    def generate_audio_file(self, text: str, output_path: str):
        """Generate audio with Kokoro and save it directly to a file."""
        import soundfile as sf
        if self.pipeline is None:
            self.load_model()

        voice_pack = self.get_voice_pack()
        generator = self.pipeline(text, voice=voice_pack, speed=self.speed)

        chunks = []
        for _, _, audio_chunk in generator:
            chunks.append(audio_chunk)

        if chunks:
            final_audio = np.concatenate(chunks)
            sf.write(output_path, final_audio, 24000)

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

    def get_tools(self) -> list:
        @tool
        def set_kokoro_voice_parameters(calm: float, warm: float, dynamic: float, gender: float) -> str:
            """Set the voice parameters for Kokoro TTS.

            Args:
                calm: Calmness level (-5 to +5)
                warm: Warmth level (-5 to +5)
                dynamic: Dynamism level (-5 to +5)
                gender: Gender balance (-5 for fully female, +5 for fully male)
            """

            self.calm_raw = np.clip(calm, -5, 5)
            self.warm_raw = np.clip(warm, -5, 5)
            self.dynamic_raw = np.clip(dynamic, -5, 5)
            self.gender_raw = np.clip(gender, -5, 5)

            return f"Voice parameters updated: calm={calm}, warm={warm}, dynamic={dynamic}, gender={gender}"

        return [set_kokoro_voice_parameters]

    def to_string(self) -> str:
        return f"KokoroVoice(calm={self.calm_raw:.2f}, warm={self.warm_raw:.2f}, dynamic={self.dynamic_raw:.2f}, gender={self.gender_raw:.2f})"
