import sys
import json
import os
import subprocess
import re
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QProgressBar, QSlider, QHBoxLayout
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import QTimer, Qt
import pygame

class AlbumPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Album Player")
        self.setGeometry(100, 100, 800, 600)
        
        self.layout = QVBoxLayout()
        
        # Fon rasmi
        self.image_label = QLabel(self)
        self.image_label.setScaledContents(True)
        self.layout.addWidget(self.image_label)
        
        # Qo'shiq nomi
        self.song_title = QLabel("Qo'shiq nomi", self)
        self.song_title.setFont(QFont("Arial", 16))
        self.layout.addWidget(self.song_title)
        
        # Musiqa progress
        self.music_progress = QProgressBar(self)
        self.music_progress.setMinimum(0)
        self.music_progress.setMaximum(100)
        self.music_progress.setValue(0)
        self.layout.addWidget(self.music_progress)
        
        # Tugmalar
        btn_layout = QHBoxLayout()
        self.prev_btn = QPushButton("◄◄ Previous")
        self.prev_btn.clicked.connect(self.prev_song)
        btn_layout.addWidget(self.prev_btn)
        
        self.play_pause_btn = QPushButton("Play")
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        btn_layout.addWidget(self.play_pause_btn)
        
        self.next_btn = QPushButton("Next ►►")
        self.next_btn.clicked.connect(self.next_song)
        btn_layout.addWidget(self.next_btn)
        
        self.layout.addLayout(btn_layout)
        
        # Volume
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self.set_volume)
        vol_layout.addWidget(self.volume_slider)
        self.layout.addLayout(vol_layout)
        
        # Zaps tugmasi
        self.zaps_btn = QPushButton("Zaps (Video yaratish)")
        self.zaps_btn.clicked.connect(self.create_video)
        self.layout.addWidget(self.zaps_btn)
        
        # Zaps progress va label
        self.zaps_label = QLabel("Zaps jarayoni: Tayyor emas")
        self.zaps_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.zaps_label)
        
        self.zaps_progress = QProgressBar(self)
        self.zaps_progress.setMinimum(0)
        self.zaps_progress.setMaximum(100)
        self.zaps_progress.setValue(0)
        self.zaps_progress.setVisible(False)
        self.layout.addWidget(self.zaps_progress)
        
        self.setLayout(self.layout)
        
        # Ma'lumotlar
        self.songs = self.load_songs()
        self.current_song_index = 0
        self.is_playing = False
        self.song_duration = 0.0
        self.current_pos = 0
        
        pygame.mixer.init()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_music_progress)
        self.timer.start(1000)
        
        self.load_current_song()
        self.set_volume(70)

    def load_songs(self):
        try:
            with open('songs.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def load_current_song(self):
        if not self.songs:
            self.song_title.setText("songs.json topilmadi yoki bo'sh")
            self.image_label.clear()
            return
            
        song = self.songs[self.current_song_index]
        self.song_title.setText(f"{self.current_song_index + 1}/{len(self.songs)} - {song['name']}")
        
        image_path = f"assets/image_{song['id']}.jpg"
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.image_label.setPixmap(pixmap.scaled(800, 400, Qt.KeepAspectRatio))
        else:
            self.image_label.clear()
        
        music_path = f"assets/song_{song['id']}.mp3"
        if os.path.exists(music_path):
            self.song_duration = self.get_audio_duration(music_path)
            self.music_progress.setMaximum(int(self.song_duration))
            self.music_progress.setValue(0)
        else:
            self.song_duration = 0.0

    def toggle_play_pause(self):
        if not self.songs:
            return
        if not self.is_playing:
            self.play_song()
            self.play_pause_btn.setText("Pause")
        else:
            pygame.mixer.music.pause()
            self.play_pause_btn.setText("Play")
        self.is_playing = not self.is_playing

    def play_song(self):
        song = self.songs[self.current_song_index]
        music_path = f"assets/song_{song['id']}.mp3"
        if os.path.exists(music_path):
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play()
            self.current_pos = 0
        else:
            self.song_title.setText(f"Musiqa topilmadi: {music_path}")

    def update_music_progress(self):
        if self.is_playing:
            if pygame.mixer.music.get_busy():
                self.current_pos += 1
                self.music_progress.setValue(min(self.current_pos, int(self.song_duration)))
            else:
                self.next_song()

    def prev_song(self):
        if not self.songs:
            return
        self.current_song_index = (self.current_song_index - 1) % len(self.songs)
        self.load_current_song()
        if self.is_playing:
            self.play_song()

    def next_song(self):
        if not self.songs:
            return
        self.current_song_index = (self.current_song_index + 1) % len(self.songs)
        self.load_current_song()
        if self.is_playing:
            self.play_song()

    def set_volume(self, value):
        pygame.mixer.music.set_volume(value / 100.0)

    def create_video(self):
        if not self.songs:
            self.zaps_label.setText("Hech qanday qo'shiq yo'q")
            return

        self.zaps_btn.setEnabled(False)
        self.zaps_label.setText("Zaps boshlandi... bitta buyruq bilan")
        self.zaps_progress.setValue(0)
        self.zaps_progress.setVisible(True)
        QApplication.processEvents()

        cmd = ['ffmpeg', '-y']
        filter_parts = []
        video_labels = []
        audio_labels = []
        total_duration = 0.0
        valid_count = 0

        for i, song in enumerate(self.songs):
            img = f"assets/image_{song['id']}.jpg"
            mp3 = f"assets/song_{song['id']}.mp3"

            if not (os.path.exists(img) and os.path.exists(mp3)):
                continue

            dur = self.get_audio_duration(mp3)
            if dur <= 0:
                continue

            total_duration += dur
            valid_count += 1

            cmd.extend(['-loop', '1', '-t', str(dur), '-i', img])
            cmd.extend(['-i', mp3])

            v = f"v{i}"
            a = f"a{i}"

            filter_parts.append(
                f"[{i*2}:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
                f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,setsar=1,setpts=PTS-STARTPTS[{v}];"
            )
            filter_parts.append(f"[{i*2+1}:a]anull[a{i}];")  # oddiyroq, kerak bo'lsa aformat qo'shsa bo'ladi

            video_labels.append(f"[{v}]")
            audio_labels.append(f"[{a}]")

        if valid_count == 0:
            self.zaps_label.setText("Hech qanday mos rasm+musiqa topilmadi")
            self.zaps_btn.setEnabled(True)
            self.zaps_progress.setVisible(False)
            return

        filter_complex = (
            "".join(filter_parts) +
            "".join(video_labels) + f"concat=n={valid_count}:v=1:a=0[v];" +
            "".join(audio_labels) + f"concat=n={valid_count}:v=0:a=1[a]"
        )

        cmd.extend([
            '-filter_complex', filter_complex,
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            'album_video.mp4'
        ])

        self.zaps_label.setText(f"{valid_count} ta trek → video yaratilmoqda...")
        QApplication.processEvents()

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )

            percent = 0
            while True:
                line = process.stderr.readline()
                if not line and process.poll() is not None:
                    break
                if "time=" in line:
                    match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d{2})', line)
                    if match:
                        h, m, s = map(float, match.groups())
                        current_time = h*3600 + m*60 + s
                        if total_duration > 0:
                            percent = min(int((current_time / total_duration) * 100), 98)
                            self.zaps_progress.setValue(percent)
                            QApplication.processEvents()

            process.wait()
            if process.returncode == 0:
                self.zaps_label.setText("Muvaffaqiyat! Video: album_video.mp4")
                self.zaps_progress.setValue(100)
            else:
                _, err = process.communicate()
                self.zaps_label.setText(f"FFmpeg xatosi: {err[:300]}...")
        except Exception as e:
            self.zaps_label.setText(f"Xato: {str(e)}")

        self.zaps_btn.setEnabled(True)
        QTimer.singleShot(6000, lambda: self.zaps_progress.setVisible(False))

    def get_audio_duration(self, path):
        try:
            cmd = [
                'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', path
            ]
            output = subprocess.check_output(cmd).decode().strip()
            return float(output)
        except:
            return 0.0

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = AlbumPlayer()
    player.show()
    sys.exit(app.exec_())
