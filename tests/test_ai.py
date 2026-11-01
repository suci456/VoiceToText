"""
Unit and integration tests for local OllamaClient module.
"""

import os
import sys
import unittest

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.ollama_client import OllamaClient


class TestOllamaClient(unittest.TestCase):
    """Test suite for Ollama local client."""

    def setUp(self):
        self.client = OllamaClient(base_url="http://localhost:11434", model="qwen2.5:3b")

    def test_client_initialization(self):
        """Verifies default properties."""
        self.assertEqual(self.client.base_url, "http://localhost:11434")
        self.assertEqual(self.client.model, "qwen2.5:3b")

    def test_empty_prompt_validation(self):
        """Verifies that an empty prompt raises ValueError immediately."""
        with self.assertRaises(ValueError):
            list(self.client.stream_chat(""))

        with self.assertRaises(ValueError):
            list(self.client.stream_chat("   "))

    def test_check_connection(self):
        """Verifies connection status to local Ollama daemon."""
        is_connected, msg = self.client.check_connection()
        self.assertIsInstance(is_connected, bool)
        self.assertIsInstance(msg, str)
        print(f"Ollama Connection Test: {is_connected} - {msg}")

    def test_model_chat_streaming_if_available(self):
        """If Ollama is running and qwen2.5:3b is pulled, test streaming token chunks."""
        is_connected, _ = self.client.check_connection()
        if not is_connected:
            self.skipTest("Ollama is not running locally.")

        has_model, _ = self.client.has_model("qwen2.5:3b")
        if not has_model:
            self.skipTest("Model 'qwen2.5:3b' is not yet installed in local Ollama.")

        # Test prompt
        prompt = "What is the time complexity of searching in a balanced binary search tree? Answer in one sentence."
        tokens = []
        for chunk in self.client.stream_chat(prompt):
            tokens.append(chunk)

        full_reply = "".join(tokens)
        self.assertGreater(len(tokens), 0)
        self.assertIn("O(log", full_reply)
        print(f"Ollama streaming test PASSED! Response: {full_reply.strip()}")


if __name__ == "__main__":
    unittest.main()

