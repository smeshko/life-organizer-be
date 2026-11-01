"""Tests for Claude model and effort settings."""

import pytest
from pydantic import ValidationError

from life_organizer.config import Settings


def _settings() -> Settings:
    return Settings(api_key="k", claude_api_key="k", _env_file=None)  # type: ignore[call-arg]


def test_claude_model_defaults_to_opus(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_MODEL", raising=False)
    assert _settings().claude_model == "claude-opus-5-5"


def test_claude_effort_defaults_to_low(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_EFFORT", raising=False)
    assert _settings().claude_effort == "low"


def test_claude_model_and_effort_read_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_MODEL", "claude-haiku-4-5")
    monkeypatch.setenv("CLAUDE_EFFORT", "medium")
    settings = _settings()
    assert settings.claude_model == "claude-haiku-4-5"
    assert settings.claude_effort == "medium"


def test_invalid_claude_effort_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_EFFORT", "turbo")
    with pytest.raises(ValidationError):
        _settings()
