"""
Unit and integration tests for SpeechTranscriber module.
"""

import os
import sys
import unittest
import numpy as np

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from speech.transcriber import SpeechTranscriber


class TestSpeechTranscriber(unittest.TestCase):
    """Test suite for Faster-Whisper local speech transcriber."""

    @classmethod
    def setUpClass(cls):
        cls.transcriber = SpeechTranscriber(model_size_or_path="base", device="cpu", compute_type="int8")

    def test_transcriber_initialization(self):
        """Verifies default parameters and state."""
        self.assertEqual(self.transcriber.model_size_or_path, "base")
        self.assertEqual(self.transcriber.device, "cpu")
        self.assertEqual(self.transcriber.compute_type, "int8")

    def test_empty_audio_rejection(self):
        """Verifies empty and None buffers return an appropriate error."""
        success, text, meta = self.transcriber.transcribe(None)
        self.assertFalse(success)
        self.assertIn("empty", text.lower())

        success, text, meta = self.transcriber.transcribe(np.array([], dtype=np.float32))
        self.assertFalse(success)

    def test_short_audio_rejection(self):
        """Verifies audio shorter than 0.3s is rejected gracefully."""
        short_audio = np.zeros(1000, dtype=np.float32)  # ~0.06s
        success, text, meta = self.transcriber.transcribe(short_audio)
        self.assertFalse(success)
        self.assertIn("too short", text.lower())

    def test_model_loading_and_inference(self):
        """Verifies model loading and inference pipeline."""
        success, msg = self.transcriber.load_model()
        self.assertTrue(success, f"Failed to load model: {msg}")
        self.assertTrue(self.transcriber.is_loaded)

        # Generate 1s of a 440Hz tone with subtle amplitude
        sample_rate = 16000
        t = np.linspace(0, 1.0, sample_rate, False)
        tone = (0.05 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

        ok, result, meta = self.transcriber.transcribe(tone, language="en")
        self.assertTrue(ok)
        self.assertIsInstance(result, str)
        self.assertIn("language", meta)


if __name__ == "__main__":
    unittest.main()

