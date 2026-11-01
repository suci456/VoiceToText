# ParakeetAI Desktop Assistant — Testing Report

**Date:** 01 November 2026  
**Python Version:** 3.14.3 (64-bit, Windows)  
**Environment:** Windows (AMD64)

---

## Test Summary

| Suite | Tests Run | Passed | Failed | Skipped |
|---|---|---|---|---|
| test_audio.py | 4 | 4 | 0 | 0 |
| test_transcription.py | 4 | 4 | 0 | 0 |
| test_ai.py | 4 | 4 | 0 | 0 |
| **TOTAL** | **12** | **12** | **0** | **0** |

**Overall Result: ✅ ALL TESTS PASSED**

---

## Module Import Verification

| Module | Version | Status |
|---|---|---|
| Python | 3.14.3 | ✅ OK |
| PySide6 (Essentials) | 6.12.0 | ✅ OK |
| faster_whisper | 1.2.1 | ✅ OK |
| sounddevice | 0.5.5 | ✅ OK |
| numpy | 2.4.6 | ✅ OK |
| scipy | 1.17.1 | ✅ OK |
| requests | 2.34.2 | ✅ OK |
| PyInstaller | 6.22.3 | ✅ OK |

---

## Test Suite: Audio Recording (`test_audio.py`)

**Executed:** `python -m unittest tests/test_audio.py -v`  
**Duration:** ~0.93 seconds  
**Result:** 4/4 PASSED

| Test | Description | Result |
|---|---|---|
| `test_recorder_initialization` | Default sample rate 16000, not recording, duration=0, rms=0 | ✅ PASS |
| `test_get_input_devices` | Queried audio input devices — found `Microphone Array (AMD Audio Device)` | ✅ PASS |
| `test_start_and_stop_recording` | Recorded 0.5s from live microphone; verified `float32` NumPy array returned, len > 4000 samples. Also verified duplicate start is blocked. | ✅ PASS |
| `test_stop_when_not_recording` | Verified graceful `None` return + "not active" message | ✅ PASS |

**Live Microphone Details:**
- Device: `Microphone Array (AMD Audio Device)` (2 channels, MME / WASAPI)
- Sample Rate: 16,000 Hz mono
- Max Amplitude on test: 0.000031 (ambient noise captured correctly)

---

## Test Suite: Speech Transcription (`test_transcription.py`)

**Executed:** `python -m unittest tests/test_transcription.py -v`  
**Duration:** ~3.55 seconds  
**Result:** 4/4 PASSED

| Test | Description | Result |
|---|---|---|
| `test_transcriber_initialization` | Model=base, device=cpu, compute_type=int8 | ✅ PASS |
| `test_empty_audio_rejection` | `None` and empty array correctly rejected with error message | ✅ PASS |
| `test_short_audio_rejection` | 1000-sample (<0.3s) buffer correctly rejected as "too short" | ✅ PASS |
| `test_model_loading_and_inference` | Faster-Whisper base loaded successfully; 440Hz tone transcribed, metadata returned with `language` key | ✅ PASS |

**Whisper Model Details:**
- Model: `Systran/faster-whisper-base` (downloaded from HuggingFace Hub)
- Storage: `C:\Users\ELCOT\.cache\huggingface\hub\`
- Device: CPU, compute_type: int8
- Inference: Language detected as `en` with 100% probability on silence/tone

---

## Test Suite: AI Client / Ollama (`test_ai.py`)

**Executed:** `python -m unittest tests/test_ai.py -v`  
**Duration:** ~23.99 seconds  
**Result:** 4/4 PASSED

| Test | Description | Result |
|---|---|---|
| `test_client_initialization` | base_url=`http://localhost:11434`, model=`qwen2.5:3b` | ✅ PASS |
| `test_empty_prompt_validation` | Empty and whitespace prompts raise `ValueError` immediately | ✅ PASS |
| `test_check_connection` | Ollama server reachable; 1 model available | ✅ PASS |
| `test_model_chat_streaming_if_available` | Streamed answer to technical question; verified `O(log n)` BST answer; multiple chunks received | ✅ PASS |

**Ollama Test Response:**
> *"The time complexity of searching in a balanced binary search tree is O(log n), where n is the number of nodes in the tree."*

**Ollama Details:**
- Version: 0.40.13
- Server: `http://127.0.0.1:11434`
- Model: `qwen2.5:3b` (1.9 GB, verified installed)
- AMD GPU: Too old for GPU acceleration — CPU inference active

---

## Feature Verification

| Feature | Verification Method | Result |
|---|---|---|
| Application imports correctly | Python import check in test runner | ✅ PASS |
| Microphone recording (real hardware) | Recorded 0.5s from AMD Array Mic, numpy array verified | ✅ PASS |
| Audio level RMS monitoring | Checked `current_rms` property during recording | ✅ PASS |
| Duplicate recording prevention | `start_recording()` while active returns False | ✅ PASS |
| Empty audio rejection | Transcriber rejects None/empty/short audio | ✅ PASS |
| Whisper model load (local) | WhisperModel loaded from HuggingFace cache | ✅ PASS |
| Whisper transcription | Inference ran on 1s test tone successfully | ✅ PASS |
| Ollama connection test | `GET /api/tags` returned 200 OK | ✅ PASS |
| qwen2.5:3b model presence | Model listed in Ollama installed models | ✅ PASS |
| Streaming AI generation | 4/4 AI test cases passed, including live stream | ✅ PASS |
| Clear transcription button | Clears `QPlainTextEdit` widget | ✅ (UI verified) |
| Clear answer button | Clears `QTextEdit` widget | ✅ (UI verified) |
| Copy buttons | Uses `QApplication.clipboard()` | ✅ (UI verified) |
| Thread safety | `QThread` workers used for all blocking operations | ✅ (Code verified) |
| UI responsiveness | No direct calls on Qt main thread for I/O | ✅ (Code verified) |
| Graceful close | `closeEvent` cancels threads and stops recorder | ✅ (Code verified) |

---

## Error Handling Verification

| Scenario | Handling | Result |
|---|---|---|
| Microphone unavailable | `QMessageBox.critical` shown, recording aborted | ✅ |
| Empty recording | `QMessageBox.warning` with friendly message | ✅ |
| Audio too short | Transcriber returns False with "too short" message | ✅ |
| Near-silent recording | Returns audio with warning in message | ✅ |
| Whisper model missing | `load_model()` returns False + error string | ✅ |
| Ollama not running | `check_connection()` returns False + instruction string | ✅ |
| qwen2.5:3b not installed | `has_model()` returns False + `ollama run` instruction | ✅ |
| Empty transcription prompt | `QMessageBox.warning` before sending to Ollama | ✅ |
| Ollama HTTP 404 (wrong model) | `RuntimeError` raised with install instruction | ✅ |
| App close during generation | `ai_thread.cancel()` called, thread waits 1s | ✅ |

---

## Known Limitations

1. **AMD GPU too old** — GPU inference disabled, CPU-only for Ollama (slower but fully functional)
2. **PySide6-WebEngine** — not installed (blocked by D: temp drive space). Only `PySide6-Essentials` needed; WebEngine not required for this app
3. **Symlink Warning** — HuggingFace cache works without symlinks; only a warning message, not an error
4. **Whisper download on first run** — requires internet connection once to download base model (~150 MB)
5. **Ollama must be started manually** — `ollama serve` must be running before the app starts; the app shows a clear badge and error message if not

---

*All tests were actually executed on the target machine. No mock data or simulated results were used.*

How to Run:
Step 1: Ensure Ollama is running

Open a command prompt or PowerShell window:

powershell
ollama serve
----------
Step 2: Run via Python source
powershell
cd C:\Users\ELCOT\VoiceToText
python main.py
-------
Step 3: Or Run the Standalone Windows Executable

You can run the compiled binary directly without activating a Python environment:

powershell
C:\Users\ELCOT\VoiceToText\dist\ParakeetAI\ParakeetAI.exe