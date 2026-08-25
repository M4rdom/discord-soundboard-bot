import importlib
import sys

import pytest


@pytest.fixture
def reload_config(monkeypatch, tmp_path):
    # chdir to an empty tmp dir so config.py's load_dotenv() can't pick up
    # this machine's real .env (dotenv walks up from the cwd looking for one).
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DISCORD_TOKEN", "test-token")
    monkeypatch.setenv("PANEL_CHANNEL_ID", "123456789012345678")
    monkeypatch.delenv("GUILD_ID", raising=False)
    monkeypatch.delenv("SOUNDS_DIR", raising=False)
    monkeypatch.delenv("PANEL_MAX_MESSAGES", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    def _reload():
        sys.modules.pop("config", None)
        return importlib.import_module("config")

    yield _reload
    sys.modules.pop("config", None)


def test_panel_max_messages_defaults_to_three(reload_config):
    config = reload_config()
    assert config.PANEL_MAX_MESSAGES == 3


def test_panel_max_messages_reads_env_override(monkeypatch, reload_config):
    monkeypatch.setenv("PANEL_MAX_MESSAGES", "5")
    config = reload_config()
    assert config.PANEL_MAX_MESSAGES == 5


def test_panel_max_messages_rejects_non_integer(monkeypatch, reload_config):
    monkeypatch.setenv("PANEL_MAX_MESSAGES", "not-a-number")
    with pytest.raises(RuntimeError):
        reload_config()


def test_panel_max_messages_rejects_zero(monkeypatch, reload_config):
    monkeypatch.setenv("PANEL_MAX_MESSAGES", "0")
    with pytest.raises(RuntimeError):
        reload_config()


def test_log_level_defaults_to_info(reload_config):
    config = reload_config()
    assert config.LOG_LEVEL == "INFO"


def test_log_level_reads_env_override(monkeypatch, reload_config):
    monkeypatch.setenv("LOG_LEVEL", "debug")
    config = reload_config()
    assert config.LOG_LEVEL == "DEBUG"


def test_log_level_rejects_unknown_value(monkeypatch, reload_config):
    monkeypatch.setenv("LOG_LEVEL", "VERBOSE")
    with pytest.raises(RuntimeError):
        reload_config()
