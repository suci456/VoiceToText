"""
Styles and Theme definitions for ParakeetAI Desktop Assistant.
Modern dark theme with blue and purple accent gradients, rounded cards, and clean typography.
"""

DARK_THEME_QSS = """
/* Global Application Style */
QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    selection-background-color: #6366f1;
    selection-color: #ffffff;
}

/* Main Window */
QMainWindow {
    background-color: #0b0f19;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #161b22;
    width: 8px;
    margin: 0px 0px 0px 0px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #30363d;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #6366f1;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Cards & Frames */
QFrame.card {
    background-color: #161b26;
    border: 1px solid #283042;
    border-radius: 12px;
    padding: 16px;
}

QFrame.card:hover {
    border: 1px solid #3d4a66;
}

/* Header Banner */
QFrame.header-frame {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a153a, stop:0.5 #1e1b4b, stop:1 #0f172a);
    border-bottom: 1px solid #3730a3;
    padding: 14px 20px;
}

QLabel.app-title {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 0.5px;
}

QLabel.app-subtitle {
    font-size: 12px;
    color: #a5b4fc;
    font-weight: 400;
}

/* Section Titles */
QLabel.section-title {
    font-size: 14px;
    font-weight: 600;
    color: #c7d2fe;
    margin-bottom: 6px;
}

/* Buttons */
QPushButton {
    background-color: #21283b;
    color: #f1f5f9;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #2e3852;
    border-color: #475569;
}

QPushButton:pressed {
    background-color: #1a2030;
}

QPushButton:disabled {
    background-color: #161c28;
    color: #475569;
    border-color: #1e293b;
}

/* Special Button Styles */
QPushButton.btn-primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed);
    color: #ffffff;
    border: 1px solid #6366f1;
}
QPushButton.btn-primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338ca, stop:1 #6d28d9);
    border-color: #818cf8;
}
QPushButton.btn-primary:pressed {
    background: #3730a3;
}

QPushButton.btn-record {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #dc2626, stop:1 #e11d48);
    color: #ffffff;
    border: 1px solid #f43f5e;
}
QPushButton.btn-record:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #b91c1c, stop:1 #be123c);
}

QPushButton.btn-stop {
    background-color: #334155;
    color: #f87171;
    border: 1px solid #475569;
}
QPushButton.btn-stop:hover {
    background-color: #475569;
    color: #ef4444;
}

QPushButton.btn-secondary {
    background-color: transparent;
    color: #94a3b8;
    border: 1px solid #334155;
    padding: 4px 10px;
    font-size: 11px;
}
QPushButton.btn-secondary:hover {
    background-color: #1e293b;
    color: #e2e8f0;
}

/* Text Editors */
QTextEdit, QPlainTextEdit {
    background-color: #0b0f19;
    color: #f8fafc;
    border: 1px solid #283042;
    border-radius: 8px;
    padding: 12px;
    font-size: 13px;
    line-height: 1.5;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #6366f1;
}

/* Badges and Indicators */
QLabel.badge {
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
}

QLabel.badge-online {
    background-color: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

QLabel.badge-offline {
    background-color: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

QLabel.badge-warning {
    background-color: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

QLabel.badge-recording {
    background-color: rgba(239, 68, 68, 0.2);
    color: #ff6b6b;
    border: 1px solid #ef4444;
}

/* Status Bar & Footer */
QStatusBar {
    background-color: #0a0d14;
    border-top: 1px solid #1e2536;
    color: #94a3b8;
    font-size: 11px;
    padding: 4px 8px;
}

/* Timer Display */
QLabel.timer-display {
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 22px;
    font-weight: 700;
    color: #38bdf8;
    background-color: #0b0f19;
    padding: 6px 14px;
    border-radius: 8px;
    border: 1px solid #1e293b;
}

/* Audio Level Progress Bar */
QProgressBar.audio-meter {
    border: 1px solid #1e293b;
    border-radius: 4px;
    background-color: #0b0f19;
    text-align: center;
    height: 8px;
}

QProgressBar.audio-meter::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:0.7 #f59e0b, stop:1 #ef4444);
    border-radius: 3px;
}
"""

