import audioop
from unittest.mock import MagicMock, patch

from audio_mixer import FRAME_SIZE, SILENT_FRAME, SoundMixer


def _frame(value: int) -> bytes:
    """A FRAME_SIZE-long PCM frame where every 16-bit sample equals `value`."""
    sample = value.to_bytes(2, byteorder="little", signed=True)
    return sample * (FRAME_SIZE // 2)


def _fake_source(chunks: list[bytes]):
    """A fake AudioSource: read() yields the given chunks, then b'' (finished)."""
    source = MagicMock()
    source.read.side_effect = [*chunks, b""]
    return source


def test_read_returns_silence_with_no_sources():
    assert SoundMixer().read() == SILENT_FRAME


def test_read_passes_through_a_single_source_unchanged():
    mixer = SoundMixer()
    frame = _frame(100)
    mixer._sources.append(_fake_source([frame]))

    assert mixer.read() == frame


def test_read_mixes_two_simultaneous_sources():
    mixer = SoundMixer()
    frame_a, frame_b = _frame(100), _frame(50)
    mixer._sources.append(_fake_source([frame_a]))
    mixer._sources.append(_fake_source([frame_b]))

    assert mixer.read() == audioop.add(frame_a, frame_b, 2)


def test_read_drops_and_cleans_up_a_finished_source():
    mixer = SoundMixer()
    finished = _fake_source([])
    mixer._sources.append(finished)

    result = mixer.read()

    assert result == SILENT_FRAME
    assert mixer._sources == []
    finished.cleanup.assert_called_once()


def test_read_keeps_active_sources_and_drops_finished_ones():
    mixer = SoundMixer()
    active = _fake_source([_frame(10), _frame(20)])
    finished = _fake_source([])
    mixer._sources.extend([active, finished])

    mixer.read()

    assert mixer._sources == [active]
    finished.cleanup.assert_called_once()
    active.cleanup.assert_not_called()


def test_stop_all_clears_and_cleans_up_every_source():
    mixer = SoundMixer()
    a, b = _fake_source([_frame(1)]), _fake_source([_frame(2)])
    mixer._sources.extend([a, b])

    mixer.stop_all()

    assert mixer._sources == []
    a.cleanup.assert_called_once()
    b.cleanup.assert_called_once()


def test_cleanup_stops_all_sources():
    mixer = SoundMixer()
    source = _fake_source([_frame(1)])
    mixer._sources.append(source)

    mixer.cleanup()

    assert mixer._sources == []
    source.cleanup.assert_called_once()


def test_is_opus_is_false():
    assert SoundMixer().is_opus() is False


def test_add_source_appends_an_ffmpeg_audio_source():
    with patch("audio_mixer.discord.FFmpegPCMAudio") as mock_ffmpeg:
        mixer = SoundMixer()
        mixer.add_source("sounds/cat/clip.mp3")

        mock_ffmpeg.assert_called_once_with("sounds/cat/clip.mp3")
        assert mixer._sources == [mock_ffmpeg.return_value]
