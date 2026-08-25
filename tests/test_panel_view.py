import discord

from panel_view import CategorySelect, SoundboardPanelView, StopButton
from sound_library import SoundClip


def _clip(label: str, clip_id: str = "abc123") -> SoundClip:
    return SoundClip(id=clip_id, label=label, path=f"sounds/cat/{label}.mp3")


def test_category_select_options_match_clips():
    clips = [_clip("bruh", "id1"), _clip("vine-boom", "id2")]
    select = CategorySelect("memes", clips)

    assert select.placeholder == "🎵 memes"
    assert select.custom_id == "panel_select_memes"
    assert [(o.label, o.value) for o in select.options] == [
        ("bruh", "id1"),
        ("vine-boom", "id2"),
    ]


def test_category_select_truncates_long_labels():
    clip = _clip("a" * 150, "id1")
    select = CategorySelect("cat", [clip])

    assert len(select.options[0].label) == 100
    assert select.options[0].value == "id1"  # the id itself isn't truncated


def test_category_select_custom_id_is_unique_per_category():
    a = CategorySelect("memes", [_clip("x")])
    b = CategorySelect("games", [_clip("y")])

    assert a.custom_id != b.custom_id


def test_stop_button_has_fixed_custom_id_and_danger_style():
    button = StopButton()

    assert button.custom_id == "btn_stop"
    assert button.style == discord.ButtonStyle.danger


def test_view_builds_one_select_per_category_plus_button():
    library = {"memes": [_clip("bruh")], "games": [_clip("gg")]}
    view = SoundboardPanelView(library, bot=None, include_stop_button=True)

    assert len(view.children) == 3
    assert isinstance(view.children[-1], StopButton)
    assert all(isinstance(child, CategorySelect) for child in view.children[:-1])


def test_view_omits_button_when_not_requested():
    library = {"memes": [_clip("bruh")]}
    view = SoundboardPanelView(library, bot=None, include_stop_button=False)

    assert len(view.children) == 1
    assert isinstance(view.children[0], CategorySelect)


def test_view_with_empty_library_and_button_has_only_the_button():
    view = SoundboardPanelView({}, bot=None, include_stop_button=True)

    assert len(view.children) == 1
    assert isinstance(view.children[0], StopButton)
