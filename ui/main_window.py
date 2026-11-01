"""
Main Window for ParakeetAI Desktop Assistant.
Implements modern UI with PySide6, real-time audio visualization,
Faster-Whisper local transcription, and Ollama streaming responses.
"""

import os
import sys
from typing import Optional
import numpy as np

from PySide6.QtCore import Qt, QThread, Signal, QTimer, QTime
from PySide6.QtGui import QIcon, QFont, QTextCursor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QPlainTextEdit, QProgressBar,
    QFrame, QSplitter, QMessageBox, QStatusBar, QApplication
)

from audio.recorder import AudioRecorder
from speech.transcriber import SpeechTranscriber
from ai.ollama_client import OllamaClient
from ui.styles import DARK_THEME_QSS


class TranscribeWorker(QThread):
    """Worker thread for offline Faster-Whisper speech transcription."""
    finished = Signal(bool, str, dict)
    status_updated = Signal(str)

    def __init__(self, transcriber: SpeechTranscriber, audio_data: np.ndarray):
        super().__init__()
        self.transcriber = transcriber
        self.audio_data = audio_data

    def run(self):
        self.status_updated.emit("Transcribing audio locally with Faster-Whisper (base, int8)...")
        success, text, metadata = self.transcriber.transcribe(self.audio_data)
        self.finished.emit(success, text, metadata)


class AiAnswerWorker(QThread):
    """Worker thread for local streaming LLM inference via Ollama."""
    chunk_received = Signal(str)
    finished = Signal(bool, str)
    status_updated = Signal(str)

    def __init__(self, client: OllamaClient, prompt: str):
        super().__init__()
        self.client = client
        self.prompt = prompt
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        self.status_updated.emit("Connecting to local Ollama (qwen2.5:3b)...")
        full_response = []
        try:
            for chunk in self.client.stream_chat(self.prompt):
                if self._is_cancelled:
                    break
                full_response.append(chunk)
                self.chunk_received.emit(chunk)

            if not self._is_cancelled:
                self.finished.emit(True, "".join(full_response))
            else:
                self.finished.emit(False, "Generation cancelled by user.")
        except Exception as e:
            self.finished.emit(False, str(e))


class MainWindow(QMainWindow):
    """Main desktop application window for ParakeetAI Desktop Assistant."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ParakeetAI Desktop Assistant")
        self.setMinimumSize(960, 680)
        self.resize(1100, 760)

        # Set application icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "app_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Core logic components
        self.recorder = AudioRecorder(sample_rate=16000)
        self.transcriber = SpeechTranscriber(model_size_or_path="base", device="cpu", compute_type="int8")
        self.ollama_client = OllamaClient(model="qwen2.5:3b")

        # Runtime state
        self.current_audio: Optional[np.ndarray] = None
        self.transcribe_thread: Optional[TranscribeWorker] = None
        self.ai_thread: Optional[AiAnswerWorker] = None

        # Live Recording Timer
        self.recording_timer = QTimer(self)
        self.recording_timer.setInterval(100)  # 10 Hz
        self.recording_timer.timeout.connect(self._on_recording_timer_tick)

        # Periodic status check timer
        self.status_check_timer = QTimer(self)
        self.status_check_timer.setInterval(15000)  # Check every 15s
        self.status_check_timer.timeout.connect(self.check_system_status)

        # Initialize GUI
        self._init_ui()
        self.setStyleSheet(DARK_THEME_QSS)

        # Initial hardware & service status verification
        QTimer.singleShot(200, self.check_system_status)

    def _init_ui(self):
        """Constructs the responsive desktop interface."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)

        # Header Section
        header_frame = self._build_header()
        main_layout.addWidget(header_frame)

        # Main Split Content (Left: Recording & Transcription, Right: AI Answer)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(8)

        left_panel = self._build_left_panel()
        right_panel = self._build_right_panel()

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter, 1)

        # Status Bar / Footer
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_msg_label = QLabel("Ready")
        self.status_msg_label.setStyleSheet("color: #94a3b8;")
        self.status_bar.addWidget(self.status_msg_label, 1)

    def _build_header(self) -> QFrame:
        frame = QFrame()
        frame.setProperty("class", "header-frame")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(14, 8, 14, 8)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)

        title_label = QLabel("ParakeetAI Desktop Assistant")
        title_label.setProperty("class", "app-title")
        subtitle_label = QLabel("Local & Offline Speech Recognition | Qwen2.5 Local AI Interview Assistant")
        subtitle_label.setProperty("class", "app-subtitle")

        title_vbox.addWidget(title_label)
        title_vbox.addWidget(subtitle_label)
        layout.addLayout(title_vbox)

        layout.addStretch()

        # Badges row
        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(8)

        self.mic_badge = QLabel("Mic: Checking...")
        self.mic_badge.setProperty("class", "badge badge-warning")

        self.whisper_badge = QLabel("Whisper: base (int8)")
        self.whisper_badge.setProperty("class", "badge badge-online")

        self.ollama_badge = QLabel("Ollama: Checking...")
        self.ollama_badge.setProperty("class", "badge badge-warning")

        badges_layout.addWidget(self.mic_badge)
        badges_layout.addWidget(self.whisper_badge)
        badges_layout.addWidget(self.ollama_badge)

        self.btn_refresh = QPushButton("Refresh Status")
        self.btn_refresh.setProperty("class", "btn-secondary")
        self.btn_refresh.clicked.connect(self.check_system_status)
        badges_layout.addWidget(self.btn_refresh)

        layout.addLayout(badges_layout)
        return frame

    def _build_left_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(12)

        # 1. Recording Card
        rec_card = QFrame()
        rec_card.setProperty("class", "card")
        rec_layout = QVBoxLayout(rec_card)
        rec_layout.setSpacing(10)

        rec_header = QLabel("Audio Recording")
        rec_header.setProperty("class", "section-title")
        rec_layout.addWidget(rec_header)

        # Controls & Timer Row
        controls_row = QHBoxLayout()
        controls_row.setSpacing(10)

        self.btn_start_record = QPushButton("Start Recording")
        self.btn_start_record.setProperty("class", "btn-record")
        self.btn_start_record.clicked.connect(self.on_start_recording)

        self.btn_stop_record = QPushButton("Stop Recording")
        self.btn_stop_record.setProperty("class", "btn-stop")
        self.btn_stop_record.setEnabled(False)
        self.btn_stop_record.clicked.connect(self.on_stop_recording)

        self.timer_label = QLabel("00:00.0")
        self.timer_label.setProperty("class", "timer-display")
        self.timer_label.setAlignment(Qt.AlignCenter)

        controls_row.addWidget(self.btn_start_record, 1)
        controls_row.addWidget(self.btn_stop_record, 1)
        controls_row.addWidget(self.timer_label)
        rec_layout.addLayout(controls_row)

        # Audio Level meter
        meter_row = QHBoxLayout()
        meter_label = QLabel("Mic Level:")
        meter_label.setStyleSheet("color: #64748b; font-size: 11px;")
        self.audio_meter = QProgressBar()
        self.audio_meter.setProperty("class", "audio-meter")
        self.audio_meter.setRange(0, 100)
        self.audio_meter.setValue(0)
        self.audio_meter.setTextVisible(False)
        meter_row.addWidget(meter_label)
        meter_row.addWidget(self.audio_meter, 1)
        rec_layout.addLayout(meter_row)

        # Recording Status message
        self.rec_status_label = QLabel("Ready to capture microphone audio.")
        self.rec_status_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        rec_layout.addWidget(self.rec_status_label)

        layout.addWidget(rec_card)

        # 2. Transcription Card
        trans_card = QFrame()
        trans_card.setProperty("class", "card")
        trans_layout = QVBoxLayout(trans_card)
        trans_layout.setSpacing(10)

        trans_header_row = QHBoxLayout()
        trans_title = QLabel("Recognized Speech (Transcription)")
        trans_title.setProperty("class", "section-title")

        self.btn_clear_trans = QPushButton("Clear")
        self.btn_clear_trans.setProperty("class", "btn-secondary")
        self.btn_clear_trans.clicked.connect(self.on_clear_transcription)

        self.btn_copy_trans = QPushButton("Copy")
        self.btn_copy_trans.setProperty("class", "btn-secondary")
        self.btn_copy_trans.clicked.connect(self.on_copy_transcription)

        trans_header_row.addWidget(trans_title)
        trans_header_row.addStretch()
        trans_header_row.addWidget(self.btn_copy_trans)
        trans_header_row.addWidget(self.btn_clear_trans)
        trans_layout.addLayout(trans_header_row)

        self.transcription_text = QPlainTextEdit()
        self.transcription_text.setPlaceholderText(
            "Speak your interview question into the microphone and click 'Stop Recording'...\n\n"
            "Transcription will appear here automatically using local Faster-Whisper."
        )
        trans_layout.addWidget(self.transcription_text, 1)

        self.trans_meta_label = QLabel("")
        self.trans_meta_label.setStyleSheet("color: #64748b; font-size: 11px;")
        trans_layout.addWidget(self.trans_meta_label)

        layout.addWidget(trans_card, 1)
        return container

    def _build_right_panel(self) -> QWidget:
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        title = QLabel("AI Interview Answer Suggestion")
        title.setProperty("class", "section-title")

        self.btn_suggest_answer = QPushButton("Suggest Answer")
        self.btn_suggest_answer.setProperty("class", "btn-primary")
        self.btn_suggest_answer.clicked.connect(self.on_suggest_answer)

        self.btn_copy_answer = QPushButton("Copy")
        self.btn_copy_answer.setProperty("class", "btn-secondary")
        self.btn_copy_answer.clicked.connect(self.on_copy_answer)

        self.btn_clear_answer = QPushButton("Clear")
        self.btn_clear_answer.setProperty("class", "btn-secondary")
        self.btn_clear_answer.clicked.connect(self.on_clear_answer)

        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(self.btn_suggest_answer)
        header_row.addWidget(self.btn_copy_answer)
        header_row.addWidget(self.btn_clear_answer)
        layout.addLayout(header_row)

        # AI Answer Text Area
        self.answer_text = QTextEdit()
        self.answer_text.setReadOnly(True)
        self.answer_text.setPlaceholderText(
            "Click 'Suggest Answer' once a question is transcribed.\n\n"
            "The answer will stream progressively in real time from local Ollama (qwen2.5:3b)."
        )
        layout.addWidget(self.answer_text, 1)

        # AI Status / Progress Bar
        self.ai_progress = QProgressBar()
        self.ai_progress.setRange(0, 0)  # Indeterminate spinner
        self.ai_progress.setFixedHeight(4)
        self.ai_progress.setTextVisible(False)
        self.ai_progress.hide()
        layout.addWidget(self.ai_progress)

        self.ai_status_label = QLabel("Ollama Qwen2.5:3b Assistant ready.")
        self.ai_status_label.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(self.ai_status_label)

        return card

    # =========================================================================
    # Hardware & Service Status Checks
    # =========================================================================

    def check_system_status(self):
        """Verifies microphone hardware and Ollama server status."""
        # 1. Microphone Check
        try:
            devices = self.recorder.get_input_devices()
            if devices:
                self.mic_badge.setText(f"Mic: {devices[0]['name'][:16]}...")
                self.mic_badge.setProperty("class", "badge badge-online")
            else:
                self.mic_badge.setText("Mic: None Found")
                self.mic_badge.setProperty("class", "badge badge-offline")
        except Exception:
            self.mic_badge.setText("Mic: Error")
            self.mic_badge.setProperty("class", "badge badge-offline")

        # 2. Whisper Model Status
        self.whisper_badge.setText("Whisper: base (int8)")
        self.whisper_badge.setProperty("class", "badge badge-online")

        # 3. Ollama Server Status
        is_ollama_ok, ollama_msg = self.ollama_client.check_connection()
        if is_ollama_ok:
            has_qwen, qwen_msg = self.ollama_client.has_model("qwen2.5:3b")
            if has_qwen:
                self.ollama_badge.setText("Ollama: qwen2.5:3b Ready")
                self.ollama_badge.setProperty("class", "badge badge-online")
                self.ai_status_label.setText("Ollama connected (qwen2.5:3b ready).")
            else:
                self.ollama_badge.setText("Ollama: Missing qwen2.5:3b")
                self.ollama_badge.setProperty("class", "badge badge-warning")
                self.ai_status_label.setText("Ollama running, but qwen2.5:3b is missing. Run: ollama run qwen2.5:3b")
        else:
            self.ollama_badge.setText("Ollama: Offline")
            self.ollama_badge.setProperty("class", "badge badge-offline")
            self.ai_status_label.setText("Ollama offline. Run 'ollama serve' locally.")

        self.style().unpolish(self.mic_badge)
        self.style().polish(self.mic_badge)
        self.style().unpolish(self.whisper_badge)
        self.style().polish(self.whisper_badge)
        self.style().unpolish(self.ollama_badge)
        self.style().polish(self.ollama_badge)

    # =========================================================================
    # Audio Recording Logic
    # =========================================================================

    def on_start_recording(self):
        """Starts real microphone recording."""
        if self.recorder.is_recording:
            return

        success, msg = self.recorder.start_recording()
        if not success:
            QMessageBox.critical(self, "Recording Error", f"Unable to start microphone:\n{msg}")
            self.rec_status_label.setText(f"Error: {msg}")
            return

        self.btn_start_record.setEnabled(False)
        self.btn_stop_record.setEnabled(True)
        self.btn_suggest_answer.setEnabled(False)
        self.rec_status_label.setText("Recording in progress... Speak into microphone.")
        self.status_msg_label.setText("Recording audio...")

        self.mic_badge.setText("Mic: RECORDING")
        self.mic_badge.setProperty("class", "badge badge-recording")
        self.style().unpolish(self.mic_badge)
        self.style().polish(self.mic_badge)

        self.recording_timer.start()

    def _on_recording_timer_tick(self):
        """Updates elapsed timer and microphone live RMS meter."""
        elapsed = self.recorder.duration
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        millis = int((elapsed * 10) % 10)
        self.timer_label.setText(f"{mins:02d}:{secs:02d}.{millis:01d}")

        # Update audio meter level (0-100)
        rms = self.recorder.current_rms
        meter_val = int(min(100, max(0, rms * 100)))
        self.audio_meter.setValue(meter_val)

    def on_stop_recording(self):
        """Stops microphone recording and initiates local Faster-Whisper transcription."""
        if not self.recorder.is_recording:
            return

        self.recording_timer.stop()
        self.audio_meter.setValue(0)

        self.btn_start_record.setEnabled(True)
        self.btn_stop_record.setEnabled(False)

        audio_data, msg = self.recorder.stop_recording()
        self.check_system_status()

        if audio_data is None or len(audio_data) == 0:
            self.rec_status_label.setText(f"Recording stopped: {msg}")
            QMessageBox.warning(self, "Empty Recording", msg)
            return

        self.current_audio = audio_data
        duration = len(audio_data) / 16000.0
        self.rec_status_label.setText(f"Captured {duration:.1f}s of audio. Starting local transcription...")
        self.status_msg_label.setText("Transcribing speech locally...")

        # Start background transcription thread
        self.transcribe_thread = TranscribeWorker(self.transcriber, audio_data)
        self.transcribe_thread.status_updated.connect(self._on_transcribe_status)
        self.transcribe_thread.finished.connect(self._on_transcribe_finished)
        self.transcribe_thread.start()

    def _on_transcribe_status(self, status: str):
        self.status_msg_label.setText(status)
        self.trans_meta_label.setText(status)

    def _on_transcribe_finished(self, success: bool, text: str, metadata: dict):
        self.btn_suggest_answer.setEnabled(True)
        if success:
            self.transcription_text.setPlainText(text)
            lang = metadata.get("language", "en")
            prob = metadata.get("language_probability", 1.0)
            duration = metadata.get("duration", 0.0)
            self.trans_meta_label.setText(
                f"Transcribed locally in {duration:.1f}s | Language: {lang.upper()} ({prob:.0%})"
            )
            self.status_msg_label.setText("Transcription complete.")
            self.rec_status_label.setText("Transcription complete. Ready to suggest answer.")
        else:
            self.trans_meta_label.setText(f"Transcription failed: {text}")
            self.status_msg_label.setText("Transcription failed.")
            QMessageBox.warning(self, "Transcription Notice", text)

    # =========================================================================
    # AI Answer Generation (Streaming)
    # =========================================================================

    def on_suggest_answer(self):
        """Initiates streaming answer generation from Ollama Qwen2.5:3b."""
        question = self.transcription_text.toPlainText().strip()
        if not question or question.startswith("(No clear speech"):
            QMessageBox.warning(
                self,
                "No Question Provided",
                "Please record or enter a technical question in the transcription area before requesting an answer."
            )
            return

        # Check Ollama connection first
        is_ok, msg = self.ollama_client.check_connection()
        if not is_ok:
            QMessageBox.critical(
                self,
                "Ollama Not Running",
                f"{msg}\n\nMake sure Ollama is installed and running on http://localhost:11434."
            )
            self.ai_status_label.setText("Ollama connection failed.")
            return

        # Prepare UI for progressive streaming
        self.answer_text.clear()
        self.btn_suggest_answer.setEnabled(False)
        self.ai_progress.show()
        self.ai_status_label.setText("Generating Answer progressively from Qwen2.5:3b...")
        self.status_msg_label.setText("Streaming AI answer...")

        # Launch streaming worker thread
        self.ai_thread = AiAnswerWorker(self.ollama_client, question)
        self.ai_thread.chunk_received.connect(self._on_ai_chunk_received)
        self.ai_thread.finished.connect(self._on_ai_finished)
        self.ai_thread.start()

    def _on_ai_chunk_received(self, chunk: str):
        """Appends streaming text chunk-by-chunk to the QTextEdit view."""
        cursor = self.answer_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(chunk)
        self.answer_text.setTextCursor(cursor)
        self.answer_text.ensureCursorVisible()

    def _on_ai_finished(self, success: bool, message: str):
        self.ai_progress.hide()
        self.btn_suggest_answer.setEnabled(True)
        if success:
            self.ai_status_label.setText("Answer generated successfully.")
            self.status_msg_label.setText("AI answer complete.")
        else:
            self.ai_status_label.setText(f"Error: {message}")
            self.status_msg_label.setText("AI generation failed.")
            QMessageBox.critical(
                self,
                "AI Generation Error",
                f"Failed to generate answer:\n\n{message}"
            )

    # =========================================================================
    # Quality of Life Actions
    # =========================================================================

    def on_clear_transcription(self):
        self.transcription_text.clear()
        self.trans_meta_label.clear()
        self.rec_status_label.setText("Transcription cleared.")

    def on_copy_transcription(self):
        text = self.transcription_text.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)
            self.status_msg_label.setText("Transcription copied to clipboard.")

    def on_clear_answer(self):
        self.answer_text.clear()
        self.ai_status_label.setText("Answer cleared.")

    def on_copy_answer(self):
        text = self.answer_text.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)
            self.status_msg_label.setText("AI answer copied to clipboard.")

    def closeEvent(self, event):
        """Safely terminates active background threads before application closes."""
        if self.recorder.is_recording:
            self.recorder.stop_recording()

        if self.ai_thread and self.ai_thread.isRunning():
            self.ai_thread.cancel()
            self.ai_thread.wait(1000)

        if self.transcribe_thread and self.transcribe_thread.isRunning():
            self.transcribe_thread.wait(1000)

        event.accept()

