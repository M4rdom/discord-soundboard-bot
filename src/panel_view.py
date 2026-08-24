"""Soundboard panel UI components: per-category Select Menus + stop button."""

import discord

from sound_library import SoundClip

MAX_LABEL_LENGTH = 100  # Discord's limit for a SelectOption label


class CategorySelect(discord.ui.Select):
    def __init__(self, category: str, clips: list[SoundClip]):
        options = [
            discord.SelectOption(label=clip.label[:MAX_LABEL_LENGTH], value=clip.id)
            for clip in clips
        ]
        super().__init__(
            placeholder=f"🎵 {category}",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"panel_select_{category}",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        assert isinstance(self.view, SoundboardPanelView)
        await self.view.bot.handle_sound_id_selection(interaction, self.values[0])


class StopButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="🛑 Stop Audio",
            style=discord.ButtonStyle.danger,
            custom_id="btn_stop",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        assert isinstance(self.view, SoundboardPanelView)
        await self.view.bot.handle_stop_request(interaction)


class SoundboardPanelView(discord.ui.View):
    """Persistent view (timeout=None) rebuilt from a chunk_for_messages() chunk.

    Only the last message of a multi-message panel carries the Stop Audio
    button (see chunk_for_messages) — earlier ones use all 5 rows for
    category Select Menus instead.
    """

    def __init__(self, library: dict[str, list[SoundClip]], bot, *, include_stop_button: bool):
        super().__init__(timeout=None)
        self.bot = bot

        for category, clips in library.items():
            self.add_item(CategorySelect(category, clips))
        if include_stop_button:
            self.add_item(StopButton())
