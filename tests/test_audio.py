"""
Unit tests for AudioRecorder module.
"""

import os
import sys
import unittest
import time
import numpy as np

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio.recorder import AudioRecorder


class TestAudioRecorder(unittest.TestCase):
    """Test suite for AudioRecorder class."""

    def setUp(self):
        self.recorder = AudioRecorder(sample_rate=16000)

    def tearDown(self):
        if self.recorder.is_recording:
            self.recorder.stop_recording()

    def test_recorder_initialization(self):
        """Verifies default parameters and state on creation."""
        self.assertEqual(self.recorder.sample_rate, 16000)
        self.assertFalse(self.recorder.is_recording)
        self.assertEqual(self.recorder.duration, 0.0)
        self.assertEqual(self.recorder.current_rms, 0.0)

    def test_get_input_devices(self):
        """Checks that audio input devices can be queried without error."""
        devices = AudioRecorder.get_input_devices()
        self.assertIsInstance(devices, list)
        if devices:
            self.assertIn("name", devices[0])
            self.assertIn("channels", devices[0])

    def test_start_and_stop_recording(self):
        """Tests live recording workflow and returned NumPy audio array."""
        devices = AudioRecorder.get_input_devices()
        if not devices:
            self.skipTest("No audio input device available on host.")

        # Start recording
        success, msg = self.recorder.start_recording()
        self.assertTrue(success, f"Failed to start recording: {msg}")
        self.assertTrue(self.recorder.is_recording)

        # Record for 0.5s
        time.sleep(0.5)
        self.assertGreater(self.recorder.duration, 0.3)

        # Attempt duplicate start (should fail gracefully)
        dup_success, dup_msg = self.recorder.start_recording()
        self.assertFalse(dup_success)
        self.assertIn("already in progress", dup_msg)

        # Stop recording
        audio_data, stop_msg = self.recorder.stop_recording()
        self.assertFalse(self.recorder.is_recording)
        self.assertIsNotNone(audio_data)
        self.assertIsInstance(audio_data, np.ndarray)
        self.assertEqual(audio_data.dtype, np.float32)
        self.assertGreater(len(audio_data), 4000)  # at least ~0.25s of audio

    def test_stop_when_not_recording(self):
        """Verifies that stopping when inactive returns None and friendly message."""
        audio, msg = self.recorder.stop_recording()
        self.assertIsNone(audio)
        self.assertIn("not active", msg)


if __name__ == "__main__":
    unittest.main()

