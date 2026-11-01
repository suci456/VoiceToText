"""
Local LLM integration module for ParakeetAI Desktop Assistant using Ollama.
Streams responses chunk-by-chunk from http://localhost:11434/api/chat with Qwen2.5:3b.
"""

import json
from typing import Generator, Optional, Tuple
import requests


class OllamaClient:
    """
    Client for interacting locally with Ollama REST API.
    """

    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "qwen2.5:3b"

    SYSTEM_PROMPT = (
        "You are ParakeetAI, an expert technical interview assistant and Senior Staff Software Engineer. "
        "The user will speak or ask a technical interview or coding question. "
        "Provide a concise, direct, articulate, and accurate answer suitable for a high-level technical interview. "
        "Structure your response with clear key points, trade-offs, and practical code or architecture examples when relevant. "
        "Avoid filler phrases, be confident, precise, and professional."
    )

    def __init__(self, base_url: str = DEFAULT_BASE_URL, model: str = DEFAULT_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def check_connection(self) -> Tuple[bool, str]:
        """
        Tests if the local Ollama server is running and reachable.
        Returns (is_connected: bool, message: str).
        """
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return True, f"Ollama is running ({len(models)} models available)."
            return False, f"Ollama responded with HTTP {resp.status_code}."
        except requests.exceptions.ConnectionError:
            return False, (
                "Ollama server is not running on http://localhost:11434.\n"
                "Please start Ollama by running 'ollama serve' in a terminal."
            )
        except requests.exceptions.Timeout:
            return False, "Connection to Ollama server timed out."
        except Exception as e:
            return False, f"Error communicating with Ollama: {str(e)}"

    def has_model(self, model_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Checks if the specified model (defaulting to self.model) exists locally in Ollama.
        """
        target = model_name or self.model
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.status_code != 200:
                return False, f"HTTP error {resp.status_code} querying models."

            data = resp.json()
            models = [m.get("name", "").lower() for m in data.get("models", [])]

            # Match exact or prefix (e.g. qwen2.5:3b or qwen2.5:3b-instruct-q4_0)
            target_lower = target.lower()
            matched = any(
                m == target_lower or m.startswith(f"{target_lower}:") or target_lower.startswith(m)
                for m in models
            )

            if matched:
                return True, f"Model '{target}' is installed."
            return False, f"Model '{target}' is not installed in Ollama. Run: ollama run {target}"
        except Exception as e:
            return False, f"Failed to check models: {str(e)}"

    def list_installed_models(self) -> list[str]:
        """Returns a list of model names installed locally in Ollama."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            pass
        return []

    def stream_chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """
        Streams AI response tokens chunk-by-chunk from local Ollama chat API.
        Yields string tokens.
        Raises RuntimeError on connection or model failures.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt question cannot be empty.")

        target_model = model or self.model
        sys_prompt = system_prompt or self.SYSTEM_PROMPT

        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt.strip()},
            ],
            "stream": True,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            },
        }

        url = f"{self.base_url}/api/chat"

        try:
            with requests.post(url, json=payload, stream=True, timeout=(5, 60)) as resp:
                if resp.status_code == 404:
                    raise RuntimeError(
                        f"Model '{target_model}' was not found in Ollama.\n"
                        f"Run in your terminal: ollama run {target_model}"
                    )
                if resp.status_code != 200:
                    raise RuntimeError(
                        f"Ollama returned error status {resp.status_code}: {resp.text}"
                    )

                for line in resp.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    try:
                        chunk_obj = json.loads(line)
                        if "message" in chunk_obj and "content" in chunk_obj["message"]:
                            content_piece = chunk_obj["message"]["content"]
                            if content_piece:
                                yield content_piece

                        if chunk_obj.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue

        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Could not connect to Ollama server at http://localhost:11434.\n"
                "Please make sure Ollama is installed and running."
            )
        except requests.exceptions.Timeout:
            raise RuntimeError("Request to local Ollama timed out.")

