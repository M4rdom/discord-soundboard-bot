from pathlib import Path

from sound_library import (
    MAX_CATEGORIES_FULL_MESSAGE,
    MAX_CATEGORIES_PER_MESSAGE,
    MAX_OPTIONS_PER_CATEGORY,
    chunk_for_messages,
    scan_all_clips,
    scan_sounds,
)


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")


def test_scan_sounds_creates_missing_folder(tmp_path):
    missing = tmp_path / "sounds"
    assert scan_sounds(str(missing), max_messages=1) == {}
    assert missing.is_dir()


def test_scan_sounds_orders_categories_and_clips(tmp_path):
    _touch(tmp_path / "b" / "second.mp3")
    _touch(tmp_path / "b" / "first.ogg")
    _touch(tmp_path / "a" / "only.mp3")

    library = scan_sounds(str(tmp_path), max_messages=1)

    assert list(library.keys()) == ["a", "b"]
    assert [c.label for c in library["b"]] == ["first", "second"]


def test_scan_sounds_ignores_unsupported_files_and_non_directories(tmp_path):
    _touch(tmp_path / "not_a_category.mp3")
    _touch(tmp_path / "cat" / "notes.txt")
    _touch(tmp_path / "cat" / ".gitkeep")
    _touch(tmp_path / "cat" / "clip.mp3")

    library = scan_sounds(str(tmp_path), max_messages=1)

    assert list(library.keys()) == ["cat"]
    assert [c.label for c in library["cat"]] == ["clip"]


def test_scan_sounds_skips_categories_with_no_supported_clips(tmp_path):
    _touch(tmp_path / "empty" / "notes.txt")
    _touch(tmp_path / "full" / "clip.mp3")

    library = scan_sounds(str(tmp_path), max_messages=1)

    assert list(library.keys()) == ["full"]


def test_scan_sounds_caps_categories_to_one_message(tmp_path):
    category_names = [f"cat{i}" for i in range(MAX_CATEGORIES_PER_MESSAGE + 2)]
    for name in category_names:
        _touch(tmp_path / name / "clip.mp3")

    library = scan_sounds(str(tmp_path), max_messages=1)

    assert len(library) == MAX_CATEGORIES_PER_MESSAGE
    assert list(library.keys()) == sorted(category_names)[:MAX_CATEGORIES_PER_MESSAGE]


def test_scan_sounds_caps_categories_across_multiple_messages(tmp_path):
    max_messages = 3
    # Only the last message reserves a slot for the Stop button; earlier ones
    # use the full 5 rows.
    cap = MAX_CATEGORIES_FULL_MESSAGE * (max_messages - 1) + MAX_CATEGORIES_PER_MESSAGE
    category_names = [f"cat{i:02d}" for i in range(cap + 2)]
    for name in category_names:
        _touch(tmp_path / name / "clip.mp3")

    library = scan_sounds(str(tmp_path), max_messages=max_messages)

    assert len(library) == cap
    assert list(library.keys()) == sorted(category_names)[:cap]


def test_scan_sounds_caps_options_per_category(tmp_path):
    for i in range(MAX_OPTIONS_PER_CATEGORY + 5):
        _touch(tmp_path / "cat" / f"clip{i:02d}.mp3")

    library = scan_sounds(str(tmp_path), max_messages=1)

    assert len(library["cat"]) == MAX_OPTIONS_PER_CATEGORY


def test_scan_all_clips_is_not_capped(tmp_path):
    category_names = [f"cat{i}" for i in range(MAX_CATEGORIES_PER_MESSAGE + 2)]
    for name in category_names:
        for i in range(MAX_OPTIONS_PER_CATEGORY + 5):
            _touch(tmp_path / name / f"clip{i:02d}.mp3")

    clips = scan_all_clips(str(tmp_path))

    assert len(clips) == len(category_names) * (MAX_OPTIONS_PER_CATEGORY + 5)


def test_scan_all_clips_labels_are_prefixed_by_category(tmp_path):
    _touch(tmp_path / "memes" / "bruh.mp3")

    clips = scan_all_clips(str(tmp_path))

    assert clips[0].label == "memes/bruh"


def test_clip_id_is_short_and_stable(tmp_path):
    _touch(tmp_path / "cat" / ("a" * 150 + ".mp3"))  # deliberately long filename

    first_scan = scan_all_clips(str(tmp_path))[0]
    second_scan = scan_all_clips(str(tmp_path))[0]

    assert first_scan.id == second_scan.id
    assert len(first_scan.id) <= 100


def test_clip_id_differs_for_different_files(tmp_path):
    _touch(tmp_path / "cat" / "one.mp3")
    _touch(tmp_path / "cat" / "two.mp3")

    clips = scan_all_clips(str(tmp_path))

    assert clips[0].id != clips[1].id


def test_panel_and_flat_scan_share_ids_for_the_same_file(tmp_path):
    _touch(tmp_path / "cat" / "clip.mp3")

    library = scan_sounds(str(tmp_path), max_messages=1)
    flat = scan_all_clips(str(tmp_path))

    panel_clip = library["cat"][0]
    flat_clip = next(c for c in flat if c.path == panel_clip.path)
    assert panel_clip.id == flat_clip.id


def test_chunk_for_messages_single_message_when_it_fits(tmp_path):
    category_names = ["cat0", "cat1", "cat2"]
    for name in category_names:
        _touch(tmp_path / name / "clip.mp3")
    library = scan_sounds(str(tmp_path), max_messages=1)

    assert chunk_for_messages(library) == [library]


def test_chunk_for_messages_earlier_messages_use_all_five_slots(tmp_path):
    # 9 categories: message 1 uses all 5 slots (no button needed there),
    # message 2 gets the remaining 4 plus the Stop Audio button.
    category_names = [f"cat{i:02d}" for i in range(9)]
    for name in category_names:
        _touch(tmp_path / name / "clip.mp3")
    library = scan_sounds(str(tmp_path), max_messages=2)

    chunks = chunk_for_messages(library)

    assert [len(chunk) for chunk in chunks] == [5, 4]
    assert list(chunks[0].keys()) == sorted(category_names)[:5]
    assert list(chunks[1].keys()) == sorted(category_names)[5:9]


def test_chunk_for_messages_exact_multiple_of_five_leaves_last_message_button_only(tmp_path):
    category_names = [f"cat{i:02d}" for i in range(10)]
    for name in category_names:
        _touch(tmp_path / name / "clip.mp3")
    library = scan_sounds(str(tmp_path), max_messages=3)

    chunks = chunk_for_messages(library)

    assert [len(chunk) for chunk in chunks] == [5, 5, 0]


def test_chunk_for_messages_empty_library_returns_one_empty_chunk():
    assert chunk_for_messages({}) == [{}]
