# 🎛️ Discord Soundboard Bot

Soundboard panel bot for a private Discord server. It scans a local `sounds/` folder and exposes a panel with dropdown menus (one per category) to play sound effects in the user's voice channel, with overlapping audio and a button to stop everything.

![Sound panel posted by the bot](.github/assets/Control_Panel_View_Example.png)

## Features

- Automatic scan of `sounds/<category>/` on startup (`.mp3` and `.ogg` formats).
- `/panel` command that posts the panel (also posted automatically on bot startup).
- One native Discord `Select Menu` per category (max. 4 categories / 25 sounds each, Discord's limit).
- `/sound <name>` command with autocomplete to search and play **any** sound in the library, not limited by the panel's 4-category / 25-sound cap.
- Red **🛑 Stop Audio** button.
- The bot automatically joins or moves to the voice channel of the user interacting with it.
- Sounds **overlap** with each other (playing a new one doesn't cut off the previous one).
- After every action (play or stop), the panel is reposted at the bottom of the channel so it stays visible.
- The bot only responds inside the text channel configured in `.env`.

## Project structure

```
.
├── .devcontainer/
│   ├── Dockerfile          # VS Code / Codespaces dev environment (Python + ffmpeg)
│   └── devcontainer.json
├── .container/
│   ├── Dockerfile          # Standalone runtime image (docker build / docker compose)
│   └── docker-compose.yml   # Runs .container/Dockerfile with sounds/ bind-mounted
├── .github/
│   └── workflows/
│       └── build.yml       # Builds the Windows/Linux standalone executables (see below)
├── sounds/                # Sound categories (one subfolder = one category = one menu)
│   ├── memes/*.mp3
│   ├── games/*.mp3
│   └── reactions/*.mp3
├── src/
│   ├── main.py            # Bot entry point: events, /panel and /sound commands, voice logic
│   ├── config.py           # Loads and validates .env
│   ├── sound_library.py    # Scans sounds/ -> clip catalog (capped for the panel, and a flat/full one for /sound)
│   ├── audio_mixer.py      # AudioSource that mixes several .mp3/.ogg files in parallel (overlap)
│   └── panel_view.py        # Select Menus + "Stop Audio" button
├── tests/                # pytest suite (src/sound_library.py)
├── .dockerignore           # Applies to .container/Dockerfile's build context (repo root)
├── pyproject.toml          # pytest / ruff / pyright configuration
├── requirements.txt        # Runtime deps only (used by .container/Dockerfile)
├── requirements-dev.txt    # requirements.txt + pytest/ruff/pyright, for local dev
├── requirements-build.txt  # requirements.txt + pyinstaller, for packaging the executables
└── .env.example
```

## 1. Create the Discord application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and create a **New Application**.
2. On the **Bot** tab, click **Reset Token** and copy the token (you'll need it for `DISCORD_TOKEN`).
3. Under **Privileged Gateway Intents**, this bot **doesn't need any privileged intent enabled**:
   - ❌ Presence Intent — not used.
   - ❌ Server Members Intent — not used.
   - ❌ Message Content Intent — not used (everything runs on Slash Commands and component interactions, not text messages).
   - Access to users' voice state (`member.voice`) uses the **`voice_states`** intent, which is **not privileged** and is already included in `discord.Intents.default()`. No toggle needed in the portal.
4. Under **OAuth2 → URL Generator**, check the scopes:
   - `bot`
   - `applications.commands`

   And under **Bot Permissions**, at minimum:
   - `View Channels`, `Send Messages`, `Manage Messages` (needed to delete the previous panel when reposting), `Embed Links`
   - `Connect`, `Speak` (voice)
5. Open the generated URL and invite the bot to your server.

## 2. Configure the project

```bash
cp .env.example .env
```

Edit `.env`:

```env
DISCORD_TOKEN=your_token_here
PANEL_CHANNEL_ID=123456789012345678   # text channel where the panel will live
GUILD_ID=123456789012345678           # optional, syncs /panel instantly during development
SOUNDS_DIR=sounds                     # optional
```

To get the IDs, enable **Developer Mode** in Discord (Settings → Advanced) and right-click the channel/server → **Copy ID**.

## 3. Add sounds

Place your `.mp3` or `.ogg` files inside subfolders of `sounds/` (no need to convert anything: `ffmpeg` decodes both formats equally well). Each subfolder becomes a category (a dropdown menu):

```
sounds/
├── memes/
│   ├── bruh.mp3
│   └── vine-boom.ogg
├── games/
│   └── minecraft-hurt.mp3
└── reactions/
    └── applause.ogg
```

> ⚠️ Discord allows a maximum of 5 component rows per message. Since the stop button takes up one, the **panel** supports **up to 4 categories**, with **up to 25 sounds** each. Anything beyond that is skipped for the panel (logged on startup) — but it's still reachable through `/sound`, which searches the full, uncapped library.
>
> ⚠️ If the same category has both `bruh.mp3` and `bruh.ogg`, they'll show up as two options with the same name (not deduplicated).

![sounds/ folder structure example](.github/assets/Folder_Extructure_Example.png)

## 4. Run the bot

There are four ways to run this; which one to pick depends on your OS and what you're doing:

| Environment | Recommended option | Why |
|---|---|---|
| **Windows** | [Option C: Docker](#option-c-plain-docker-with-sounds-mounted-as-a-volume-windows) | No native Windows executable bundles `ffmpeg` (see Option D) — Docker sidesteps installing it separately, and `restart: unless-stopped` keeps the bot up. |
| **Linux** | [Option D: standalone executable](#option-d-standalone-executable-recommended-for-linux-desktops) | The Linux build bundles `ffmpeg` — download it and run it, nothing else to install. |
| **Developing/contributing** (either OS) | [Option A: Dev Container](#option-a-dev-container-recommended) | Reproducible environment with the test/lint/type-check tooling already installed. |
| **Anything without Docker or a downloaded binary** | [Option B: local Python environment](#option-b-local-environment) | Manual fallback — needs Python and `ffmpeg` installed yourself. |

### Option A: Dev Container (recommended)

With the **Dev Containers** VS Code extension installed, open the project folder and choose **Reopen in Container**. This builds an image with Python 3.12 and `ffmpeg` already installed and runs `pip install -r requirements-dev.txt` automatically (includes the runtime deps plus `pytest`/`ruff`/`pyright`).

Then, inside the container:

```bash
python src/main.py
```

### Option B: Local environment

Requirements: Python 3.11+ and [ffmpeg](https://ffmpeg.org/download.html) installed and available on your `PATH`.

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

### Option C: Plain Docker, with sounds/ mounted as a volume (Windows)

Use this if you just want to run the bot with Docker Desktop on Windows — without VS Code — and keep your sound files on the host so you can drag-and-drop new ones without rebuilding the image. This uses `.container/Dockerfile` (a lean runtime image), not `.devcontainer/Dockerfile` (which is only for the VS Code dev environment) — they live in separate folders since they serve different purposes.

> 💡 On a tagged release, `.github/workflows/build.yml` also publishes a ready-to-run image to `ghcr.io/m4rdom/discord-soundboard-bot:latest`. That skips the build step entirely — handy on a Linux VPS, where you can just `docker pull` instead of cloning the repo:
> ```bash
> docker run -d --name soundboard --env-file .env -v "$(pwd)/sounds:/app/sounds" ghcr.io/m4rdom/discord-soundboard-bot:latest
> ```
> The rest of this section builds the image from source instead, which is what you want on Windows/Docker Desktop while you're still adding/changing sounds locally.

1. Make sure [Docker Desktop](https://www.docker.com/products/docker-desktop/) is installed and running (WSL2 backend recommended).
2. Copy `.env.example` to `.env` and fill it in, same as above. **Don't** put `.env` inside `sounds/`, and never commit it — it's already gitignored and excluded from the image via `.dockerignore`.
3. Put your `.mp3`/`.ogg` files in `sounds/<category>/` on your Windows machine, exactly as described in [section 3](#3-add-sounds).

**Using `docker compose` (recommended — avoids Windows path-quoting issues)**, from PowerShell in the project root:

```powershell
docker compose -f .container/docker-compose.yml up -d --build
```

This builds the image and starts the bot with `sounds/` bind-mounted read-write from the project folder (see `.container/docker-compose.yml`), so adding/removing files under `sounds/` on Windows is picked up the next time the bot restarts (`docker compose restart`) — no rebuild needed, since sounds aren't baked into the image.

View logs / stop:

```powershell
docker compose -f .container/docker-compose.yml logs -f
docker compose -f .container/docker-compose.yml down
```

**Using plain `docker run` instead**, from PowerShell in the project root:

```powershell
docker build -f .container/Dockerfile -t discord-soundboard-bot .
docker run -d --name soundboard --env-file .env -v ${PWD}\sounds:/app/sounds discord-soundboard-bot
```

From `cmd.exe`, replace `${PWD}` with `%cd%`. If your sounds live elsewhere, use the full Windows path, e.g. `-v C:\Users\you\Desktop\sounds:/app/sounds`. Note the build context is still the project root (`.`) — only the Dockerfile itself lives under `.container/`, so `requirements.txt` and `src/` resolve correctly.

> ⚠️ The container only ever gets your Discord token via `--env-file .env` / `env_file:` (an environment variable at runtime) — `.env` itself is never copied into the image, so it can't leak through a shared image layer.

### Option D: Standalone executable (recommended for Linux desktops)

Download the ready-made `soundboard` executable and just run it — no Python, no Docker, no build step on your end. It's produced by `.github/workflows/build.yml` with [PyInstaller](https://pyinstaller.org/), which bundles the Python runtime and all pip dependencies (`discord.py`, `PyNaCl`, `python-dotenv`) into that single file. (If you're the one maintaining the bot and want to build it yourself instead of downloading it, see [Building the standalone executables](#building-the-standalone-executables) under Development.)

> ⚠️ **This is the recommended option on Linux, but not on Windows.** The Linux build also bundles `ffmpeg` itself — nothing else to install. The Windows build does **not** bundle `ffmpeg` (see the note below), which is exactly why [Option C (Docker)](#option-c-plain-docker-with-sounds-mounted-as-a-volume-windows) is the recommended path on Windows instead — its image already installs `ffmpeg` for you.

**1. Download it:**

- Go to the repo's **Actions** tab → **Build standalone executables** → open the latest successful run → download `soundboard-linux` (or `soundboard-windows`) from **Artifacts**.
- Or, if a version tag was pushed (e.g. `v1.0.0`), grab it directly from that tag's **Release** page instead.

**2. Set it up:** put the executable in its own folder, alongside a `.env` (copied from `.env.example` and filled in) and a `sounds/` folder with your categories — same layout as [section 3](#3-add-sounds).

**3. `ffmpeg`, if you're on Windows** — the Linux build bundles it, so this step is Linux-only... except it isn't needed there. On Windows, the executable doesn't bundle it: there's no first-party source of a portable `ffmpeg.exe` the CI could pull from without depending on a third-party download, so download a portable build yourself (e.g. from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or [BtbN's builds](https://github.com/BtbN/FFmpeg-Builds/releases)) and drop `ffmpeg.exe` in the same folder as `soundboard.exe` (or anywhere on `PATH`) — or just use Option C instead, which doesn't require this step.

**4. Run it:** `./soundboard` from a terminal on Linux (`chmod +x soundboard` first if it lost its executable bit, e.g. after unzipping), or double-click `soundboard.exe` on Windows.

The `--collect-all nacl --hidden-import _cffi_backend` flags are required on both platforms, not optional: PyNaCl's compiled `_sodium` extension is loaded through `cffi`, which PyInstaller's static analysis doesn't detect on its own — without these flags the executable builds fine but silently loses voice support (logs `PyNaCl is not installed` at startup instead of failing loudly).

> This is the right tool for "double-click and it runs" on a single desktop machine. It's not a service: closing the window/terminal stops the bot, and there's no auto-restart-on-crash like `.container/docker-compose.yml`'s `restart: unless-stopped` gives you — for an always-on deployment on a server, Option C (Docker) or a `systemd` unit is a better fit.

## 5. Usage

1. The bot posts the panel automatically in `PANEL_CHANNEL_ID` on startup. You can also repost it with `/panel` (only works inside that channel).
2. Join a voice channel.
3. Pick a sound from any of the dropdown menus, or type `/sound <name>` and choose from the autocomplete suggestions: the bot joins (or moves to) your voice channel and plays it.

   ![Picking a sound from a category dropdown](.github/assets/Control_Panel_Options_Selector_Example.png)

   ![Searching a sound with /sound's autocomplete](.github/assets/Sound_Search_Example.png)

4. You can pick another sound while one is already playing: they'll **overlap**.
5. Press **🛑 Stop Audio** to stop everything that's playing.
6. After every action, the bot deletes the panel it used and posts a new one at the bottom of the channel.
7. If everyone leaves the voice channel, the bot automatically disconnects instead of sitting there alone.

## Development

Install dev dependencies (adds `pytest`, `ruff` and `pyright` on top of the runtime requirements):

```bash
pip install -r requirements-dev.txt
```

Run the test suite (covers `src/sound_library.py`, the module most likely to break when the sound collection changes):

```bash
pytest
```

Lint and format:

```bash
ruff check .
ruff format .
```

Type-check (same engine as the Pylance extension already configured in `.devcontainer/devcontainer.json`, so editor and CLI agree):

```bash
pyright
```

`requirements.txt` and `requirements-dev.txt` pin exact versions rather than `>=` ranges, so `pip install` always reproduces the versions this project was last tested against. When you deliberately want to upgrade a dependency, bump its pin by hand and re-run the checks above.

### Building the standalone executables

Regular users don't need this — see [Option D](#option-d-standalone-executable-recommended-for-linux-desktops) to just download and run one. This is only for building them yourself instead of using CI: needs Python 3.11+ on the machine doing the *building* (the resulting executable itself needs nothing, that's the whole point). PyInstaller doesn't cross-compile, so build on Linux to get the Linux binary, and on Windows to get the `.exe` — `.github/workflows/build.yml` does both by running on a `ubuntu-latest`/`windows-latest` matrix.

On Linux:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-build.txt
pyinstaller --onefile --name soundboard --collect-all nacl --hidden-import _cffi_backend src/main.py
```

The binary is written to `dist/soundboard`.

On Windows (PowerShell):

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements-build.txt
pyinstaller --onefile --name soundboard --collect-all nacl --hidden-import _cffi_backend src/main.py
```

The executable is written to `dist\soundboard.exe`.

The `--collect-all nacl --hidden-import _cffi_backend` flags are required on both platforms, not optional: PyNaCl's compiled `_sodium` extension is loaded through `cffi`, which PyInstaller's static analysis doesn't detect on its own — without these flags the executable builds fine but silently loses voice support (logs `PyNaCl is not installed` at startup instead of failing loudly).

## Technical notes

- Audio overlap is implemented in `src/audio_mixer.py`: `SoundMixer` is a `discord.AudioSource` that keeps a list of active `FFmpegPCMAudio` sources and mixes their PCM frames (`audioop.add`) on every 20 ms tick. It's played exactly once per voice connection; adding a new sound just adds another source to the mix.
- Each `SoundClip` gets a short, stable `id` (a hash of its file path, see `src/sound_library.py`) used as the `SelectOption`/autocomplete `value` instead of the raw path — Discord caps those values at 100 characters, which long filenames can exceed.
- `on_voice_state_update` in `src/main.py` disconnects the bot from a voice channel once no non-bot members remain in it, freeing the connection and its `SoundMixer`.
- The panel's `View` is registered as persistent (`timeout=None` + fixed `custom_id`s via `bot.add_view(...)` in `setup_hook`), so buttons/menus keep working after the bot restarts, even on older panel messages.
- `sound_library.py` exposes two catalogs: `scan_sounds()` (capped to fit the panel's Select Menus) and `scan_all_clips()` (the full, uncapped flat list used by `/sound`'s autocomplete, which isn't bound by Discord's 5-row limit).
