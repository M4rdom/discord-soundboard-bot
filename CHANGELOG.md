# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- Stopped bundling `ffmpeg` into the Linux standalone executable. It worked
  on the exact machine it was built on but failed elsewhere — Ubuntu's
  `ffmpeg` links against ~100 shared libraries (video/audio backends), and a
  minimal target system (e.g. a fresh LXC container) is missing most of
  them, causing silent playback failures (`OpusNotLoaded`, then
  `error while loading shared libraries`). Installing `ffmpeg`/`libopus0`
  via the system package manager resolves the full dependency chain
  correctly for that specific system, which bundling a single binary can't.
  Docker was never affected, since it installs `ffmpeg` via `apt` inside
  the image itself. See Option D in the README.

## [1.0.0] - 2026-08-24

### Added

- Sound panel (category Select Menus + Stop Audio button), posted
  automatically on startup and repostable with `/panel`. Spreads across
  multiple messages via `PANEL_MAX_MESSAGES` (`.env`, default `3`) to fit
  more than 4 categories — only the 25-sounds-per-category Select Menu cap
  is fixed; only the last message carries the Stop Audio button, earlier
  ones use all 5 rows for category menus.
- `/sound <name>` command with autocomplete to search and play any sound in
  the library, not bound by the panel's Select Menu limits.
- Overlapping audio playback (`SoundMixer`) so a new sound doesn't cut off
  ones already playing.
- Automatic voice disconnect when everyone leaves the channel.
- `pytest` / `ruff` / `pyright` tooling and a test suite for the sound
  scanner and config parsing.
- Standalone Docker runtime image (`.container/`) with a compose file for
  bind-mounting `sounds/`, separate from the VS Code dev container.
- GitHub Actions workflow building a Linux standalone executable (`ffmpeg`
  bundled in) on tagged releases, plus a Docker image published to
  `ghcr.io` on every push to `main` (tags `:latest` and `:sha-<commit>`,
  plus the version tag on releases), authenticated with a PAT (`GHCR_PAT`)
  since `GITHUB_TOKEN` alone denies the first package push on personal
  accounts.
- README and CHANGELOG documentation covering setup, all ways to run the
  bot, and per-OS recommendations (Docker on Windows, the standalone
  executable on Linux).
