"""
Audio recording module for ParakeetAI Desktop Assistant.
Captures mono audio at 16,000 Hz using SoundDevice and NumPy.
"""

import time
import threading
from typing import Optional, Tuple
import numpy as np
import sounddevice as sd


class AudioRecorder:
    """
    Thread-safe microphone recorder capturing 16kHz mono float32 audio.
    """

    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = "float32"

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self._stream: Optional[sd.InputStream] = None
        self._frames: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._is_recording = False
        self._start_time: float = 0.0
        self._latest_rms: float = 0.0

    @property
    def is_recording(self) -> bool:
        with self._lock:
            return self._is_recording

    @property
    def duration(self) -> float:
        with self._lock:
            if not self._is_recording:
                return 0.0
            return max(0.0, time.time() - self._start_time)

    @property
    def current_rms(self) -> float:
        """Returns the most recent Root-Mean-Square volume level (0.0 to 1.0)."""
        with self._lock:
            return self._latest_rms

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """Internal callback invoked by sounddevice for each audio buffer."""
        if status:
            # Status can indicate input overflow or underflow
            pass

        # Make a copy of the input buffer
        chunk = indata.copy()

        with self._lock:
            if self._is_recording:
                self._frames.append(chunk)
                # Compute RMS for live level display
                rms = float(np.sqrt(np.mean(chunk**2)))
                self._latest_rms = min(1.0, rms * 5.0)

    def start_recording(self) -> Tuple[bool, str]:
        """
        Starts microphone recording.
        Returns (success: bool, message: str).
        """
        with self._lock:
            if self._is_recording:
                return False, "Recording is already in progress."

            try:
                # Test query default device
                default_device = sd.query_devices(kind="input")
                if not default_device or default_device.get("max_input_channels", 0) <= 0:
                    return False, "No valid microphone input device found."
            except Exception as e:
                return False, f"Failed to access audio hardware: {str(e)}"

            self._frames = []
            self._latest_rms = 0.0
            self._start_time = time.time()

            try:
                self._stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=self.CHANNELS,
                    dtype=self.DTYPE,
                    callback=self._audio_callback,
                    blocksize=1024,
                )
                self._stream.start()
                self._is_recording = True
                return True, "Recording started."
            except Exception as e:
                self._is_recording = False
                self._stream = None
                return False, f"Failed to open microphone stream: {str(e)}"

    def stop_recording(self) -> Tuple[Optional[np.ndarray], str]:
        """
        Stops recording and returns the concatenated float32 mono audio array.
        Returns (audio_array or None, message: str).
        """
        with self._lock:
            if not self._is_recording:
                return None, "Recording was not active."

            self._is_recording = False
            stream = self._stream
            self._stream = None

        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass

        with self._lock:
            if not self._frames:
                return None, "Recording is empty (no audio frames captured)."

            # Concatenate all chunks along time axis
            audio_array = np.concatenate(self._frames, axis=0).flatten()
            self._frames = []
            self._latest_rms = 0.0

        if len(audio_array) == 0:
            return None, "Captured audio contains 0 samples."

        # Check if the audio is purely zero amplitude
        max_amplitude = float(np.max(np.abs(audio_array)))
        if max_amplitude < 1e-6:
            return audio_array, "Warning: Recording contains near-complete silence."

        return audio_array, "Recording completed successfully."

    @staticmethod
    def get_input_devices() -> list[dict]:
        """Returns a list of available input audio devices."""
        devices = []
        try:
            device_list = sd.query_devices()
            for idx, dev in enumerate(device_list):
                if dev.get("max_input_channels", 0) > 0:
                    devices.append({
                        "id": idx,
                        "name": dev.get("name", f"Device {idx}"),
                        "channels": dev.get("max_input_channels", 1),
                        "default_samplerate": dev.get("default_samplerate", 16000),
                    })
        except Exception:
            pass
        return devices

