# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/splash_screen.py — S.P.E.C.T.R.E. Video Splash Screen
Displays a video intro before loading the main interface.
"""

from PySide6.QtWidgets import QWidget, QApplication, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
import os

class SplashScreen(QWidget):
    finished = Signal()

    def __init__(self, duration_ms: int = 25000, video_path: str = "assets/intro.mp4"):
        super().__init__()
        # Frameless, always on top, black background
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: black;")
        
        # Make the splash screen 1280x720 or scale to screen
        self.resize(1280, 720)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_widget = QVideoWidget()
        layout.addWidget(self.video_widget)
        
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(1.0)
        
        self.media_player = QMediaPlayer()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        if os.path.exists(video_path):
            self.media_player.setSource(QUrl.fromLocalFile(video_path))
            self.media_player.playbackStateChanged.connect(self._on_playback_state)
            self.media_player.play()
            print(f"[Splash] Playing video from {video_path}")
        else:
            print(f"[Splash] Warning: Video not found at {video_path}. Screen will be blank.")
            # Trigger fallback immediately
            QTimer.singleShot(1000, self.close_splash)

        # Fallback timeout in case video hangs
        self.close_timer = QTimer(self)
        self.close_timer.singleShot(duration_ms, self.close_splash)

    def _on_playback_state(self, state):
        from PySide6.QtMultimedia import QMediaPlayer
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.close_splash()

    def close_splash(self):
        """Gracefully stop video, emit finished signal, then close."""
        self.media_player.stop()
        self.close()
        self.finished.emit()
