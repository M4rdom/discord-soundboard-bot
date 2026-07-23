FROM mcr.microsoft.com/devcontainers/python:1-3.12-bullseye

# The base image ships a Yarn APT repository with an expired GPG key
# (NO_PUBKEY), which breaks "apt-get update". We don't use Node/Yarn, so
# that source is removed before updating.
RUN rm -f /etc/apt/sources.list.d/yarn.list

# ffmpeg is required: discord.py uses it (FFmpegPCMAudio) to decode .mp3/.ogg files
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
