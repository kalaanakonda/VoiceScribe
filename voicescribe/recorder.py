"""Records audio from the mic into a NumPy buffer with live level metering."""

import math
import queue
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000  # Whisper expects 16 kHz mono


class Recorder:
    def __init__(self):
        self._q = queue.Queue()
        self._stream = None
        self.level = 0.0  # RMS level 0.0-1.0, updated in real-time
        self.freq_levels = [0.0] * 5  # frequency band levels for waveform

    def start(self):
        self._q = queue.Queue()
        self.level = 0.0
        self.freq_levels = [0.0] * 5
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        """Stop recording and return audio as a float32 numpy array."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        self.level = 0.0
        chunks = []
        while not self._q.empty():
            chunks.append(self._q.get())

        if not chunks:
            return np.array([], dtype="float32")

        return np.concatenate(chunks, axis=0).flatten()

    def _callback(self, indata, frames, time_info, status):
        self._q.put(indata.copy())
        data = indata[:, 0]
        # Compute RMS for level metering
        rms = math.sqrt(np.mean(data ** 2))
        self.level = min(1.0, rms * 8.0)  # amplified for visual sensitivity

        # Compute frequency band levels via FFT
        try:
            fft = np.abs(np.fft.rfft(data))
            n = len(fft)
            if n > 5:
                band_size = n // 5
                for i in range(5):
                    start = i * band_size
                    end = start + band_size if i < 4 else n
                    self.freq_levels[i] = min(1.0, float(np.mean(fft[start:end])) * 15.0)
        except Exception:
            pass
