from tts.voice import Voice
from kokoro import KPipeline

class KokoroVoice(Voice):
    def __init__(self, lang_code='a', voice_name='af_heart', speed=1.0):
        super().__init__() # Initializes the parent queue
        self.lang_code = lang_code
        self.voice_name = voice_name
        self.speed = speed
        self.pipeline = None

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
        generator = self.pipeline(text, voice=self.voice_name, speed=self.speed)

        for _, _, audio_chunk in generator:
            # Kokoro always outputs 24000 Hz.
            self.add_to_queue(audio_chunk, 24000)
