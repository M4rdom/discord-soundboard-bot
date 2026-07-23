"""Audio source that lets several sounds overlap on the same voice connection."""

import audioop
import sys
import threading
from pathlib import Path

import discord

# 20 ms of stereo PCM at 48 kHz / 16 bit = 3840 bytes per frame.
FRAME_SIZE = discord.opus.Encoder.FRAME_SIZE
SILENT_FRAME = b"\x00" * FRAME_SIZE


def _ffmpeg_executable() -> str:
    # The Linux standalone executable (see .github/workflows/build.yml) bundles
    # its own ffmpeg binary next to the PyInstaller-extracted files, since it
    # can't assume the host has ffmpeg on PATH. Fall back to a plain "ffmpeg"
    # (resolved via PATH) everywhere else — normal `python src/main.py` runs,
    # Docker (which installs ffmpeg in the image), and the Windows executable.
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass is not None:
        bundled = Path(meipass) / "ffmpeg"
        if bundled.exists():
            return str(bundled)
    return "ffmpeg"


class SoundMixer(discord.AudioSource):
    """An "infinite" AudioSource that mixes the active tracks in real time.

    Never signals end of stream (always returns a frame, silence if nothing
    is playing), so it's played exactly once per voice connection and adding
    a new sound is just a matter of calling `add_source` to layer it on top
    of whatever is already playing.
    """

    def __init__(self) -> None:
        self._sources: list[discord.FFmpegPCMAudio] = []
        self._lock = threading.Lock()

    def add_source(self, filepath: str) -> None:
        source = discord.FFmpegPCMAudio(filepath, executable=_ffmpeg_executable())
        with self._lock:
            self._sources.append(source)

    def stop_all(self) -> None:
        with self._lock:
            for source in self._sources:
                source.cleanup()
            self._sources.clear()

    def read(self) -> bytes:
        with self._lock:
            if not self._sources:
                return SILENT_FRAME

            mixed = SILENT_FRAME
            still_playing = []
            for source in self._sources:
                chunk = source.read()
                if chunk:
                    mixed = audioop.add(mixed, chunk, 2)
                    still_playing.append(source)
                else:
                    source.cleanup()
            self._sources = still_playing
            return mixed

    def is_opus(self) -> bool:
        return False

    def cleanup(self) -> None:
        self.stop_all()
