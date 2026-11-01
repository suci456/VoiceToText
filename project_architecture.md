# ParakeetAI Desktop Assistant — Project Architecture

---

## Overview

ParakeetAI is a modular, event-driven Windows desktop application built with a strict separation of concerns across four distinct layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                     │
│     PySide6 MainWindow + QSS Dark Theme + QThread Workers   │
└────────────────────────┬────────────────────────────────────┘
                         │  Signals & Slots (non-blocking)
┌────────────────────────▼────────────────────────────────────┐
│                  BUSINESS LOGIC LAYER                       │
│     AudioRecorder · SpeechTranscriber · OllamaClient        │
└────────────────────────┬────────────────────────────────────┘
                         │  Native APIs
┌────────────────────────▼────────────────────────────────────┐
│                    RUNTIME LAYER                            │
│   SoundDevice → WASAPI/MME   │   Faster-Whisper (CPU int8)  │
│   Ollama REST API (local)    │   qwen2.5:3b (GGUF)          │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Descriptions

### `main.py`
Application entry point. Configures High-DPI scaling, sets application metadata (name, icon), creates `QApplication` and launches `MainWindow`.

### `ui/styles.py`
Contains `DARK_THEME_QSS` — a full Qt Style Sheet string implementing the dark colour theme with:
- Background: `#0d1117` (GitHub dark)
- Card frames: `#161b26` with `#283042` borders
- Accent gradients: `#4f46e5` → `#7c3aed` (indigo → violet)
- Recording indicator: `#dc2626` → `#e11d48` (red)
- Monospace timer display with `#38bdf8` (sky blue)

### `ui/main_window.py`
The central GUI module. Contains:

| Class | Role |
|---|---|
| `MainWindow(QMainWindow)` | Main window, layout builder, signal handler |
| `TranscribeWorker(QThread)` | Background Faster-Whisper transcription |
| `AiAnswerWorker(QThread)` | Background Ollama streaming inference |

**Widget Hierarchy:**
```
QMainWindow
├── Header QFrame (gradient banner + status badges)
└── QSplitter (50/50 horizontal)
    ├── Left Panel (QVBoxLayout)
    │   ├── Recording Card (Start/Stop buttons, timer, RMS meter)
    │   └── Transcription Card (QPlainTextEdit + Copy/Clear)
    └── Right Panel (QFrame card)
        └── AI Answer (QTextEdit + streaming, QProgressBar spinner)
```

### `audio/recorder.py`
`AudioRecorder` class provides:
- `start_recording()` → opens `sd.InputStream` with callback
- `stop_recording()` → closes stream, concatenates frames into `float32 np.ndarray`
- `current_rms` property → thread-safe live amplitude level (0.0–1.0)
- `duration` property → elapsed recording seconds
- Thread safety via `threading.Lock()` around shared state

### `speech/transcriber.py`
`SpeechTranscriber` class:
- Lazy-loads `WhisperModel("base", device="cpu", compute_type="int8")`
- Validates audio length (min 4800 samples = 0.3s) and amplitude
- Uses VAD filter (`min_silence_duration_ms=500`) to skip long pauses
- Returns `(success: bool, text: str, metadata: dict)`

### `ai/ollama_client.py`
`OllamaClient` class:
- `check_connection()` → `GET /api/tags` with 3s timeout
- `has_model(name)` → checks installed model list by name prefix
- `stream_chat(prompt)` → `POST /api/chat` with `stream=True`, yields token strings via `Generator`
- System prompt configures the model as a "Senior Staff Software Engineer" interview assistant

---

## Data Flow

```
Microphone Hardware
       │  (16kHz, mono, float32)
       ▼
AudioRecorder.start_recording()
  └── sd.InputStream callback → frames list
       │
AudioRecorder.stop_recording()
  └── np.concatenate(frames) → audio_array: float32[N]
       │
       ▼ (emitted via QThread signal)
TranscribeWorker.run()
  └── SpeechTranscriber.transcribe(audio_array)
       └── WhisperModel.transcribe() → segments + metadata
       │
       ▼ (finished signal → main thread)
MainWindow._on_transcribe_finished()
  └── transcription_text.setPlainText(text)
       │
       ▼ (user clicks "Suggest Answer")
AiAnswerWorker.run()
  └── OllamaClient.stream_chat(prompt)
       └── requests.post("/api/chat", stream=True)
           └── for chunk in response.iter_lines(): yield chunk.content
       │
       ▼ (chunk_received signal → main thread, per token)
MainWindow._on_ai_chunk_received(chunk)
  └── answer_text.insertText(chunk)  ← progressive display
```

---

## Threading Architecture

```
Main Thread (Qt Event Loop)
│
├── QTimer (100ms) → update timer display + RMS meter bar
├── QTimer (15s)  → periodic system status check
│
├── TranscribeWorker (QThread)
│     signals: status_updated(str), finished(bool, str, dict)
│     runs: faster-whisper inference
│
└── AiAnswerWorker (QThread)
      signals: chunk_received(str), finished(bool, str)
      runs: HTTP streaming to Ollama REST API
```

**Key principle:** All `sounddevice`, Faster-Whisper, and HTTP operations run off the main thread. UI updates only happen via `Signal` → `Slot` connections across thread boundaries.

---

## Error Propagation

```
Component         Error Type            UI Response
─────────────────────────────────────────────────────────────
AudioRecorder     PortAudioError        QMessageBox.critical
                  No input devices      QMessageBox.critical

SpeechTranscriber Empty audio           QMessageBox.warning
                  Model load failure    Displayed in status label

OllamaClient      ConnectionError       QMessageBox.critical
                  HTTP 404 (no model)   QMessageBox.critical (with install cmd)
                  Timeout               QMessageBox.critical
```

---

## Configuration

All parameters are set at instantiation time in `MainWindow.__init__()`:

| Parameter | Value | Location |
|---|---|---|
| Sample Rate | 16,000 Hz | `AudioRecorder(sample_rate=16000)` |
| Whisper Model | base, CPU, int8 | `SpeechTranscriber(model_size_or_path="base", device="cpu", compute_type="int8")` |
| Ollama URL | http://localhost:11434 | `OllamaClient(base_url="http://localhost:11434")` |
| AI Model | qwen2.5:3b | `OllamaClient(model="qwen2.5:3b")` |
| Temperature | 0.7 | `stream_chat()` options |

---

## File Tree (Complete)

```
C:\Users\ELCOT\VoiceToText\
├── main.py
├── requirements.txt
├── README.md
├── testing_report.md
├── project_architecture.md
│
├── audio/
│   ├── __init__.py
│   └── recorder.py
│
├── speech/
│   ├── __init__.py
│   └── transcriber.py
│
├── ai/
│   ├── __init__.py
│   └── ollama_client.py
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   └── styles.py
│
├── assets/
│   ├── app_icon.ico
│   └── app_icon.png
│
└── tests/
    ├── __init__.py
    ├── test_audio.py
    ├── test_transcription.py
    └── test_ai.py
```

