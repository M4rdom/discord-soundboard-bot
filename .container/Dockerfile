# Standalone runtime image for deploying the bot outside VS Code (docker build / docker compose).
# Not used by devcontainer.json — that one uses .devcontainer/Dockerfile for the interactive dev environment.
FROM python:3.12-slim

# ffmpeg is required: discord.py uses it (FFmpegPCMAudio) to decode .mp3/.ogg files
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Fixed UID so it lines up predictably with host-side sounds/ permissions
# (see README's Option C) instead of whatever useradd would pick otherwise.
RUN useradd --uid 1000 --no-create-home --shell /bin/false appuser

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser src/ ./src/

USER appuser

# sounds/ is deliberately not copied here: it's meant to be bind-mounted at
# runtime (see docker-compose.yml), so adding sounds never requires a rebuild.
CMD ["python", "src/main.py"]
