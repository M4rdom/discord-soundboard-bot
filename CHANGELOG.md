# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `PANEL_MAX_MESSAGES` (`.env`, default `3`) lets the panel spread across
  several messages instead of being capped at 4 categories total.

### Changed

- Only the last panel message carries the 🛑 Stop Audio button; earlier
  messages use all 5 Select Menu rows for categories instead of reserving
  one for a repeated button.
- The category count is no longer treated as a fixed limitation — it's
  configurable via `PANEL_MAX_MESSAGES` with no upper bound of its own. Only
  the 25-sounds-per-category Select Menu cap remains fixed.
- Released executable is named `soundboard-linux` instead of a bare
  `soundboard`, so the filename itself says which environment it's for.
- Simplified the panel's summary embed: no emoji, no per-category field
  listing (redundant with the Select Menu placeholders).
- The `ghcr.io` image now builds and publishes on every push to `main`
  (tagged `:latest` and `:sha-<commit>`), not just on tagged releases.

### Removed

- Dropped the Windows executable build — it was never bundling `ffmpeg`
  anyway, and Docker (Option C) is the supported path on Windows. The
  workflow now only builds `soundboard-linux`.

### Fixed

- Added `docker/setup-buildx-action` to the `ghcr.io` publish job so
  `docker/build-push-action` uses a proper Buildx builder.

## [1.0.0] - 2026-07-23

### Added

- Sound panel (category Select Menus + Stop Audio button), posted
  automatically on startup and repostable with `/panel`.
- `/sound <name>` command with autocomplete to search and play any sound in
  the library, not bound by the panel's Select Menu limits.
- Overlapping audio playback (`SoundMixer`) so a new sound doesn't cut off
  ones already playing.
- Automatic voice disconnect when everyone leaves the channel.
- `pytest` / `ruff` / `pyright` tooling and a test suite for the sound
  scanner.
- Standalone Docker runtime image (`.container/`) with a compose file for
  bind-mounting `sounds/`, separate from the VS Code dev container.
- GitHub Actions workflow building standalone executables for Linux
  (with `ffmpeg` bundled) and Windows, publishing them to Releases, plus a
  Docker image published to `ghcr.io`.
- README documentation covering setup, all ways to run the bot, and
  per-OS recommendations.
