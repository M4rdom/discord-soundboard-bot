from pathlib import Path

from sound_library import MAX_CATEGORIES, MAX_OPTIONS_PER_CATEGORY, scan_all_clips, scan_sounds


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")


def test_scan_sounds_creates_missing_folder(tmp_path):
    missing = tmp_path / "sounds"
    assert scan_sounds(str(missing)) == {}
    assert missing.is_dir()


def test_scan_sounds_orders_categories_and_clips(tmp_path):
    _touch(tmp_path / "b" / "second.mp3")
    _touch(tmp_path / "b" / "first.ogg")
    _touch(tmp_path / "a" / "only.mp3")

    library = scan_sounds(str(tmp_path))

    assert list(library.keys()) == ["a", "b"]
    assert [c.label for c in library["b"]] == ["first", "second"]


def test_scan_sounds_ignores_unsupported_files_and_non_directories(tmp_path):
    _touch(tmp_path / "not_a_category.mp3")
    _touch(tmp_path / "cat" / "notes.txt")
    _touch(tmp_path / "cat" / ".gitkeep")
    _touch(tmp_path / "cat" / "clip.mp3")

    library = scan_sounds(str(tmp_path))

    assert list(library.keys()) == ["cat"]
    assert [c.label for c in library["cat"]] == ["clip"]


def test_scan_sounds_skips_categories_with_no_supported_clips(tmp_path):
    _touch(tmp_path / "empty" / "notes.txt")
    _touch(tmp_path / "full" / "clip.mp3")

    library = scan_sounds(str(tmp_path))

    assert list(library.keys()) == ["full"]


def test_scan_sounds_caps_categories(tmp_path):
    category_names = [f"cat{i}" for i in range(MAX_CATEGORIES + 2)]
    for name in category_names:
        _touch(tmp_path / name / "clip.mp3")

    library = scan_sounds(str(tmp_path))

    assert len(library) == MAX_CATEGORIES
    assert list(library.keys()) == sorted(category_names)[:MAX_CATEGORIES]


def test_scan_sounds_caps_options_per_category(tmp_path):
    for i in range(MAX_OPTIONS_PER_CATEGORY + 5):
        _touch(tmp_path / "cat" / f"clip{i:02d}.mp3")

    library = scan_sounds(str(tmp_path))

    assert len(library["cat"]) == MAX_OPTIONS_PER_CATEGORY


def test_scan_all_clips_is_not_capped(tmp_path):
    category_names = [f"cat{i}" for i in range(MAX_CATEGORIES + 2)]
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

    library = scan_sounds(str(tmp_path))
    flat = scan_all_clips(str(tmp_path))

    panel_clip = library["cat"][0]
    flat_clip = next(c for c in flat if c.path == panel_clip.path)
    assert panel_clip.id == flat_clip.id
