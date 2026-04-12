"""Transcribes audio using faster-whisper running locally."""

from faster_whisper import WhisperModel

# Model sizes: tiny (~75MB), base (~150MB), small (~500MB), medium (~1.5GB), large-v3 (~3GB)
DEFAULT_MODEL = "base"


class Transcriber:
    def __init__(self, model_size: str = DEFAULT_MODEL):
        self._model_size = model_size
        self._model = None

    def load(self):
        """Download (if needed) and load the model. Call once at startup."""
        print(f"Loading Whisper model '{self._model_size}'... (first run downloads it)")
        self._model = WhisperModel(self._model_size, device="cpu", compute_type="int8")
        print("Model ready.")

    def transcribe(self, audio_array, initial_prompt: str = "") -> str:
        """Transcribe a float32 numpy array (16kHz mono) to text.

        `initial_prompt` biases Whisper toward the supplied vocabulary
        (used for the custom dictionary feature).
        """
        if self._model is None:
            self.load()

        if len(audio_array) == 0:
            return ""

        kwargs = dict(beam_size=5, vad_filter=True)
        if initial_prompt:
            kwargs["initial_prompt"] = initial_prompt

        segments, _ = self._model.transcribe(audio_array, **kwargs)
        return " ".join(seg.text.strip() for seg in segments).strip()
