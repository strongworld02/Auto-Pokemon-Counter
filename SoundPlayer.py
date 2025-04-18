import threading
from pydub import AudioSegment
import pydub.playback

class SoundPlayer:
    _start_sound_path: str = "./Sounds/shiny_sound_effect.wav"
    _stop_sound_path: str = "./Sounds/escape_sound_effect.wav"

    _start_sound = None
    _stop_sound = None

    def __init__(self):
        self._start_sound = AudioSegment.from_wav(self._start_sound_path)
        self._stop_sound = AudioSegment.from_wav(self._stop_sound_path)

    def _play_start(self) -> None:
        pydub.playback.play(self._start_sound)
    
    def _play_stop(self) -> None:
        pydub.playback.play(self._stop_sound)

    def play_start_sound(self) -> None:
        threading.Thread(target=self._play_start, daemon=True).start()

    def play_stop_sound(self) -> None:
        threading.Thread(target=self._play_stop, daemon=True).start()