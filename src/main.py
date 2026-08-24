"""Soundboard bot entry point: events, /panel and /sound commands, voice logic."""

import logging
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

import config
from audio_mixer import SoundMixer
from panel_view import SoundboardPanelView
from sound_library import SoundClip, chunk_for_messages, scan_all_clips, scan_sounds

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
log = logging.getLogger("soundboard")

# discord.Intents.default() already includes voice_states (not a privileged intent);
# it's kept explicit here just to make clear the bot depends on it.
intents = discord.Intents.default()
intents.voice_states = True

AUTOCOMPLETE_MAX_RESULTS = 25  # Discord's limit for autocomplete choices


class SoundboardBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)
        self.library: dict[str, list[SoundClip]] = {}
        self.all_clips: list[SoundClip] = []
        self.clip_by_id: dict[str, str] = {}
        self.mixers: dict[int, SoundMixer] = {}
        self.panel_message_ids: list[int] = []

    async def setup_hook(self) -> None:
        self.library = scan_sounds(config.SOUNDS_DIR, config.PANEL_MAX_MESSAGES)
        self.all_clips = scan_all_clips(config.SOUNDS_DIR)
        self.clip_by_id = {clip.id: clip.path for clip in self.all_clips}
        if not self.library:
            log.warning(
                "No sounds found in '%s'. Add subfolders with .mp3/.ogg files.",
                config.SOUNDS_DIR,
            )

        # Register each message's view with fixed custom_ids so they survive bot restarts.
        chunks = chunk_for_messages(self.library)
        last_index = len(chunks) - 1
        for index, chunk in enumerate(chunks):
            view = SoundboardPanelView(chunk, self, include_stop_button=(index == last_index))
            self.add_view(view)

        if config.GUILD_ID:
            guild = discord.Object(id=config.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self) -> None:
        assert self.user is not None  # always set once logged in
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id)

        channel = self.get_channel(config.PANEL_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            log.error(
                "PANEL_CHANNEL_ID=%s is not a text channel (or wasn't found). "
                "Check your .env and the bot's permissions.",
                config.PANEL_CHANNEL_ID,
            )
            return

        await self.send_panel(channel)

    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        assert self.user is not None
        if member.id == self.user.id:
            return

        voice_client = member.guild.voice_client
        if voice_client is None:
            return

        channel = voice_client.channel
        if before.channel != channel or after.channel == channel:
            return  # not someone leaving the bot's channel

        if not isinstance(channel, (discord.VoiceChannel, discord.StageChannel)):
            return

        if any(not m.bot for m in channel.members):
            return

        await voice_client.disconnect(force=True)
        mixer = self.mixers.pop(member.guild.id, None)
        if mixer is not None:
            mixer.cleanup()

    def build_panel_embed(self) -> discord.Embed:
        if self.library:
            description = (
                "Pick a sound from the categories below, or use `/sound` to search the "
                "whole library. Sounds overlap with each other."
            )
        else:
            description = f"No .mp3/.ogg files found in `{config.SOUNDS_DIR}/`."
        return discord.Embed(
            title="Sound Panel",
            description=description,
            color=discord.Color.blurple(),
        )

    async def send_panel(self, channel: discord.abc.Messageable) -> None:
        message_ids: list[int] = []
        chunks = chunk_for_messages(self.library)
        last_index = len(chunks) - 1
        for index, chunk in enumerate(chunks):
            view = SoundboardPanelView(chunk, self, include_stop_button=(index == last_index))
            if index == 0:
                # Only the first message carries the summary embed — repeating it on
                # every message would just be noise.
                message = await channel.send(embed=self.build_panel_embed(), view=view)
            else:
                message = await channel.send(view=view)
            message_ids.append(message.id)
        self.panel_message_ids = message_ids

    async def clear_panel_messages(self, channel: discord.TextChannel) -> None:
        for message_id in self.panel_message_ids:
            try:
                await channel.get_partial_message(message_id).delete()
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass
        self.panel_message_ids = []

    def get_mixer(self, guild_id: int) -> SoundMixer:
        mixer = self.mixers.get(guild_id)
        if mixer is None:
            mixer = SoundMixer()
            self.mixers[guild_id] = mixer
        return mixer

    def _in_panel_channel(self, interaction: discord.Interaction) -> bool:
        return interaction.channel_id == config.PANEL_CHANNEL_ID

    async def _ensure_voice_connection(
        self, interaction: discord.Interaction
    ) -> discord.VoiceClient | None:
        member = interaction.user
        if not isinstance(member, discord.Member):
            await interaction.followup.send(
                "❌ You must be connected to a voice channel to use the panel.", ephemeral=True
            )
            return None

        voice_state = member.voice
        if voice_state is None or voice_state.channel is None:
            await interaction.followup.send(
                "❌ You must be connected to a voice channel to use the panel.", ephemeral=True
            )
            return None

        assert interaction.guild is not None  # this command only runs inside a guild channel
        target_channel = voice_state.channel
        voice_client = interaction.guild.voice_client

        if voice_client is None:
            return await target_channel.connect(cls=discord.VoiceClient)

        assert isinstance(voice_client, discord.VoiceClient)
        if voice_client.channel.id != target_channel.id:
            await voice_client.move_to(target_channel)
        return voice_client

    async def _repost_panel(self, interaction: discord.Interaction) -> None:
        assert isinstance(interaction.channel, discord.TextChannel)
        await self.clear_panel_messages(interaction.channel)
        await self.send_panel(interaction.channel)

    async def handle_sound_id_selection(
        self, interaction: discord.Interaction, clip_id: str
    ) -> None:
        filepath = self.clip_by_id.get(clip_id)
        if filepath is None:
            await interaction.response.send_message(
                "❌ This sound is no longer available (the library may have changed). "
                "Try reposting the panel with `/panel`.",
                ephemeral=True,
            )
            return
        await self.handle_sound_selection(interaction, filepath)

    async def handle_sound_selection(self, interaction: discord.Interaction, filepath: str) -> None:
        if not self._in_panel_channel(interaction):
            await interaction.response.send_message(
                f"❌ This panel only works in <#{config.PANEL_CHANNEL_ID}>.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        voice_client = await self._ensure_voice_connection(interaction)
        if voice_client is None:
            return

        assert interaction.guild is not None
        mixer = self.get_mixer(interaction.guild.id)
        if not voice_client.is_playing():
            voice_client.play(mixer)
        mixer.add_source(filepath)

        sound_name = Path(filepath).stem
        await interaction.followup.send(f"▶️ Playing **{sound_name}**", ephemeral=True)
        await self._repost_panel(interaction)

    async def handle_stop_request(self, interaction: discord.Interaction) -> None:
        if not self._in_panel_channel(interaction):
            await interaction.response.send_message(
                f"❌ This panel only works in <#{config.PANEL_CHANNEL_ID}>.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        assert interaction.guild is not None
        mixer = self.mixers.get(interaction.guild.id)
        if mixer is not None:
            mixer.stop_all()

        await interaction.followup.send("🛑 Audio stopped.", ephemeral=True)
        await self._repost_panel(interaction)


bot = SoundboardBot()


@bot.tree.command(name="panel", description="Show the sound panel")
async def panel_command(interaction: discord.Interaction) -> None:
    if interaction.channel_id != config.PANEL_CHANNEL_ID:
        await interaction.response.send_message(
            f"❌ This command can only be used in <#{config.PANEL_CHANNEL_ID}>.", ephemeral=True
        )
        return
    assert isinstance(interaction.channel, discord.TextChannel)
    await bot.clear_panel_messages(interaction.channel)
    await interaction.response.send_message("🎛️ Panel reposted below.", ephemeral=True)
    await bot.send_panel(interaction.channel)


async def _sound_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    needle = current.lower()
    matches = [clip for clip in bot.all_clips if needle in clip.label.lower()]
    return [
        app_commands.Choice(name=clip.label[:100], value=clip.id)
        for clip in matches[:AUTOCOMPLETE_MAX_RESULTS]
    ]


@bot.tree.command(name="sound", description="Search and play any sound from the library")
@app_commands.describe(name="Type to search, then pick a sound from the suggestions")
@app_commands.autocomplete(name=_sound_autocomplete)
async def sound_command(interaction: discord.Interaction, name: str) -> None:
    if name not in bot.clip_by_id:
        await interaction.response.send_message(
            "❌ Pick one of the suggested sounds from the list instead of typing free text.",
            ephemeral=True,
        )
        return
    await bot.handle_sound_id_selection(interaction, name)


if __name__ == "__main__":
    bot.run(config.DISCORD_TOKEN)
