import sounddevice as sd
import os
from abc import ABC, abstractmethod

class Voice(ABC):
    @classmethod
    def from_env(cls) -> "Voice":
        """Factory method to create the correct voice instance based on ENV."""
        # For now, Kokoro is our only implementation.
        # In the future, we could check an env var here to return different subclasses.
        from tts.kokoro_voice import KokoroVoice
        instance = KokoroVoice(
            lang_code=os.getenv("TTS_LANG", "f"),
            speed=float(os.getenv("TTS_SPEED", "1.0"))
        )
        instance.load_model()

        # Output device selection (cross-platform):
        # - Windows/macOS: rely on PortAudio default output (typically follows the OS default).
        # - Linux: prefer the 'pulse' device when available (PipeWire/PulseAudio default sink).
        # - Users can override via TTS_OUTPUT_DEVICE / AUDIO_OUTPUT_DEVICE (index or name).
        output_device = os.getenv("TTS_OUTPUT_DEVICE") or os.getenv("AUDIO_OUTPUT_DEVICE")

        if output_device is None or str(output_device).strip() == "":
            # Only auto-pick on Linux; on Windows/macOS, default output is usually correct.
            if os.name == "posix":
                try:
                    devices = sd.query_devices()
                    has_pulse = any(
                        isinstance(d.get("name"), str) and d["name"].lower() == "pulse"
                        for d in devices
                    )
                    if has_pulse:
                        output_device = "pulse"
                except Exception:
                    # If querying devices fails, just keep PortAudio defaults.
                    output_device = None

        if output_device is not None and str(output_device).strip() != "":
            value = str(output_device).strip()
            try:
                # Accept either an integer device index...
                sd.default.device = (sd.default.device[0], int(value))
                print(f"[TTS] Using output device index: {int(value)}")
            except ValueError:
                # ...or a device name like 'pulse'.
                sd.default.device = (sd.default.device[0], value)
                print(f"[TTS] Using output device name: {value}")
            except Exception as e:
                # Don't crash the app if the override is invalid.
                print(f"[TTS] Failed to set output device ({value}): {e}. Falling back to default.")

        return instance

    def add_to_queue(self, audio_data, sample_rate: int):
        """Play audio immediately via sounddevice."""
        try:
            sd.play(audio_data, samplerate=sample_rate)
            sd.wait()
        except Exception as e:
            print(f"[TTS] Playback error: {e}")

    # --- ABSTRACT METHODS (must be implemented by subclasses) ---
    @abstractmethod
    def load_model(self):
        """Loads the underlying TTS model into memory."""
        ...

    @abstractmethod
    def unload_model(self):
        """Releases the TTS model from memory."""
        ...

    @abstractmethod
    def generate_audio(self, text: str):
        """Generates audio chunks and enqueues them via self.add_to_queue(audio, sr)."""
        ...

    @abstractmethod
    def generate_audio_file(self, text: str, output_path: str):
        """Generates audio and saves it to a file at output_path."""
        ...

    @abstractmethod
    def to_string(self) -> str:
        """Returns a human-readable string describing the current voice configuration."""
        ...

    def get_tools(self) -> list:
        """Optional: returns LangChain tools this voice exposes to the agent. Override if needed."""
        return []

