"""Scans the sounds folder and builds the category -> clips catalog."""

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

# Limits imposed by the Discord API (Message Components v1):
# a message supports 5 action rows; each Select Menu takes up a whole row,
# so we reserve one row for the "Stop Audio" button.
MAX_CATEGORIES = 4
MAX_OPTIONS_PER_CATEGORY = 25

# ffmpeg decodes both formats equally well; no conversion needed.
SUPPORTED_EXTENSIONS = (".mp3", ".ogg")


@dataclass(frozen=True)
class SoundClip:
    id: str  # short stable id, safe to use as a SelectOption/Choice 'value' (100 char limit)
    label: str  # display name (filename without extension, or "category/filename")
    path: str  # local path to the file


def _make_clip(path: Path, label: str) -> SoundClip:
    # Discord's component/choice values are capped at 100 chars, but full file
    # paths (especially long, descriptive filenames) can easily exceed that.
    # A hash of the path is always short and stable across scans.
    clip_id = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:16]
    return SoundClip(id=clip_id, label=label, path=str(path))


def _iter_categories(sounds_dir: str) -> list[Path]:
    root = Path(sounds_dir)
    if not root.is_dir():
        log.info("Folder '%s' does not exist, creating it empty.", sounds_dir)
        root.mkdir(parents=True, exist_ok=True)
        return []
    return sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: p.name)


def _iter_clips(category: Path) -> list[Path]:
    return sorted(
        (p for ext in SUPPORTED_EXTENSIONS for p in category.glob(f"*{ext}")),
        key=lambda p: p.name,
    )


def scan_sounds(sounds_dir: str) -> dict[str, list[SoundClip]]:
    """Walks sounds/<category>/ (.mp3/.ogg) and returns a dict ordered by category.

    Capped to MAX_CATEGORIES / MAX_OPTIONS_PER_CATEGORY so the result fits in
    the panel's Select Menus. For the full, uncapped library see scan_all_clips.
    """
    categories = _iter_categories(sounds_dir)
    library: dict[str, list[SoundClip]] = {}

    if len(categories) > MAX_CATEGORIES:
        omitted = [c.name for c in categories[MAX_CATEGORIES:]]
        log.warning(
            "Found %d categories but the panel only supports %d (Discord's 5-row limit). "
            "Omitted: %s",
            len(categories),
            MAX_CATEGORIES,
            omitted,
        )
        categories = categories[:MAX_CATEGORIES]

    for category in categories:
        clips = _iter_clips(category)

        if len(clips) > MAX_OPTIONS_PER_CATEGORY:
            log.warning(
                "Category '%s' has %d sounds, only the first %d are loaded (Discord limit).",
                category.name,
                len(clips),
                MAX_OPTIONS_PER_CATEGORY,
            )
            clips = clips[:MAX_OPTIONS_PER_CATEGORY]

        if not clips:
            continue

        library[category.name] = [_make_clip(clip, label=clip.stem) for clip in clips]

    return library


def scan_all_clips(sounds_dir: str) -> list[SoundClip]:
    """Flat list of every clip in every category, with no panel component limits.

    Used by the /sound autocomplete command, which isn't bound by Discord's
    5-action-row limit the way the panel's category Select Menus are.
    """
    clips: list[SoundClip] = []
    for category in _iter_categories(sounds_dir):
        for clip_path in _iter_clips(category):
            clips.append(_make_clip(clip_path, label=f"{category.name}/{clip_path.stem}"))
    return clips
