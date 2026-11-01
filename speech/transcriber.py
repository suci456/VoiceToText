"""
Speech-to-Text module for ParakeetAI Desktop Assistant using Faster-Whisper.
Runs on CPU with int8 quantization locally without any external/cloud API calls.
"""

import os
from typing import Optional, Tuple
import numpy as np
from faster_whisper import WhisperModel


class SpeechTranscriber:
    """
    Local speech transcriber utilizing Faster-Whisper.
    """

    DEFAULT_MODEL = "base"
    DEFAULT_DEVICE = "cpu"
    DEFAULT_COMPUTE_TYPE = "int8"

    def __init__(
        self,
        model_size_or_path: str = DEFAULT_MODEL,
        device: str = DEFAULT_DEVICE,
        compute_type: str = DEFAULT_COMPUTE_TYPE,
    ):
        self.model_size_or_path = model_size_or_path
        self.device = device
        self.compute_type = compute_type
        self._model: Optional[WhisperModel] = None
        self._is_loading = False

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load_model(self) -> Tuple[bool, str]:
        """
        Loads the whisper model into memory if not already loaded.
        Returns (success: bool, message: str).
        """
        if self._model is not None:
            return True, "Model already loaded."

        self._is_loading = True
        try:
            # Load Faster-Whisper model locally
            self._model = WhisperModel(
                self.model_size_or_path,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=4,
            )
            self._is_loading = False
            return True, f"Faster-Whisper ({self.model_size_or_path}) loaded successfully."
        except Exception as e:
            self._is_loading = False
            self._model = None
            return False, f"Failed to load Faster-Whisper model: {str(e)}"

    def transcribe(self, audio: np.ndarray, language: Optional[str] = "en") -> Tuple[bool, str, dict]:
        """
        Transcribes a 1D float32 numpy audio array at 16000Hz.
        Returns (success: bool, text: str, metadata: dict).
        """
        if audio is None or len(audio) == 0:
            return False, "Audio buffer is empty.", {}

        # Validate minimum duration: at least ~0.3s (4800 samples)
        if len(audio) < 4800:
            return False, "Audio is too short for transcription (less than 0.3 seconds).", {}

        # Ensure float32 1D
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        if audio.ndim > 1:
            audio = audio.flatten()

        # Check silence
        max_amp = float(np.max(np.abs(audio)))
        if max_amp < 1e-4:
            return False, "No audible speech detected (recording was near-silent).", {}

        # Ensure model is loaded
        if self._model is None:
            ok, msg = self.load_model()
            if not ok:
                return False, msg, {}

        try:
            # Transcribe audio using faster-whisper
            segments, info = self._model.transcribe(
                audio,
                beam_size=5,
                language=language,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
            )

            collected_texts = []
            for segment in segments:
                text = segment.text.strip()
                if text:
                    collected_texts.append(text)

            full_transcription = " ".join(collected_texts).strip()

            metadata = {
                "language": getattr(info, "language", "en"),
                "language_probability": getattr(info, "language_probability", 1.0),
                "duration": getattr(info, "duration", len(audio) / 16000.0),
            }

            if not full_transcription:
                return True, "(No clear speech recognized)", metadata

            return True, full_transcription, metadata

        except Exception as e:
            return False, f"Transcription error: {str(e)}", {}

