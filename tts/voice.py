import threading
import queue
import sounddevice as sd
import os

class Voice:
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
        instance.start_playback()
        return instance

    def __init__(self):
        # --- STREAMING PLAYBACK SYSTEM (Common to all voices) ---
        self.audio_queue = queue.Queue()
        self.is_playing = False
        self.playback_thread = None

    def start_playback(self):
        """Starts the background audio playback thread."""
        if not self.is_playing:
            self.is_playing = True
            self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
            self.playback_thread.start()

    def stop_playback(self):
        """Stops playback and clears the buffer."""
        self.is_playing = False
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

    def _playback_loop(self):
        """Queue consumer loop (executed within the Thread)."""
        stream = None
        current_sr = None
        # Track if we need to force 48kHz resampling
        force_48k = False
        
        while self.is_playing:
            try:
                # We expect a tuple containing (audio_data, sample_rate)
                audio_data, sample_rate = self.audio_queue.get(timeout=0.1)
                
                if audio_data is not None:
                    import numpy as np
                    
                    if force_48k and sample_rate == 24000:
                        # Fast 2x upsampling by repeating samples
                        audio_data = np.repeat(audio_data, 2, axis=0)
                        sample_rate = 48000

                    # Recreate stream if sample rate changes or stream is None
                    if stream is None or current_sr != sample_rate:
                        if stream is not None:
                            stream.close()
                            
                        try:
                            stream = sd.OutputStream(samplerate=sample_rate, channels=1, dtype='float32')
                            stream.start()
                            current_sr = sample_rate
                        except sd.PortAudioError as e:
                            # If device doesn't support 24kHz natively (PaErrorCode -9997)
                            if "Invalid sample rate" in str(e) and sample_rate == 24000:
                                print("ALSA rejected 24000Hz. Activating 48000Hz upsampling fallback...")
                                force_48k = True
                                audio_data = np.repeat(audio_data, 2, axis=0)
                                sample_rate = 48000
                                stream = sd.OutputStream(samplerate=sample_rate, channels=1, dtype='float32')
                                stream.start()
                                current_sr = sample_rate
                            else:
                                raise e
                        
                    # Flatten/reshape data to fit OutputStream
                    if isinstance(audio_data, np.ndarray) and len(audio_data.shape) == 1:
                        audio_data = np.expand_dims(audio_data, axis=-1)
                    
                    stream.write(audio_data)
                
                self.audio_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Audio playback error: {e}")
                if stream is not None:
                    try:
                        stream.close()
                    except:
                        pass
                    stream = None
                    current_sr = None
                    
        # Cleanup
        if stream is not None:
            stream.stop()
            stream.close()

    def add_to_queue(self, audio_data, sample_rate: int):
        """Method to be called by child classes to play sound."""
        self.audio_queue.put((audio_data, sample_rate))

    # --- ABSTRACT METHODS (To be implemented by children) ---
    def load_model(self):
        raise NotImplementedError

    def unload_model(self):
        raise NotImplementedError
    
    def generate_audio(self, text: str):
        """Generates audio and calls self.add_to_queue(audio, sr)"""
        raise NotImplementedError