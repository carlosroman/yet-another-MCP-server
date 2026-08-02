from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from yams.config.settings import SearchSettings


class TestSearchSettingsDefaults:
    def test_default_values(self):
        with patch.dict(os.environ, {"BRAVE_API_KEY": "test-key"}):
            settings = SearchSettings()
            assert settings.provider == "brave"
            assert settings.count == 10
            assert settings.country == "us"
            assert settings.language == "en"


class TestSearchSettingsEnvVars:
    def test_provider_from_env(self, tmp_path: Path):
        env_file = tmp_path / ".env"
        env_file.write_text("YAMS_SEARCH_PROVIDER=brave\n")
        with patch.dict(os.environ, {"YAMS_SEARCH_PROVIDER": "brave", "BRAVE_API_KEY": "test-key"}):
            settings = SearchSettings()
            assert settings.provider == "brave"

    def test_count_from_env(self):
        with patch.dict(os.environ, {"YAMS_SEARCH_COUNT": "15", "BRAVE_API_KEY": "test-key"}):
            settings = SearchSettings()
            assert settings.count == 15

    def test_country_from_env(self):
        with patch.dict(os.environ, {"YAMS_SEARCH_COUNTRY": "gb", "BRAVE_API_KEY": "test-key"}):
            settings = SearchSettings()
            assert settings.country == "gb"

    def test_language_from_env(self):
        with patch.dict(os.environ, {"YAMS_SEARCH_LANGUAGE": "es", "BRAVE_API_KEY": "test-key"}):
            settings = SearchSettings()
            assert settings.language == "es"

    def test_brave_api_key_from_env(self):
        with patch.dict(os.environ, {"BRAVE_API_KEY": "test-key-123"}):
            settings = SearchSettings()
            assert settings.brave_api_key == "test-key-123"


class TestSearchSettingsValidation:
    def test_count_too_low(self):
        with pytest.raises(ValidationError):
            SearchSettings(count=0)

    def test_count_too_high(self):
        with pytest.raises(ValidationError):
            SearchSettings(count=21)

    def test_invalid_provider(self):
        with pytest.raises(ValidationError):
            SearchSettings(provider="google")  # type: ignore  # intentional invalid value


class TestSearchSettingsBraveKeyRequired:
    def test_brave_key_required_for_brave_provider(self):
        with (
            patch.dict(os.environ, {"BRAVE_API_KEY": ""}),
            pytest.raises(ValidationError, match="BRAVE_API_KEY"),
        ):
            SearchSettings(provider="brave", brave_api_key="")

    def test_brave_key_not_required_for_searxng(self):
        settings = SearchSettings(provider="searxng", brave_api_key="")
        assert settings.provider == "searxng"

    def test_brave_key_provided(self):
        settings = SearchSettings(provider="brave", brave_api_key="my-key")
        assert settings.brave_api_key == "my-key"


class TestSearchSettingsEnvFile:
    def test_env_file_loading(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("BRAVE_API_KEY", raising=False)
        monkeypatch.delenv("YAMS_SEARCH_COUNT", raising=False)
        monkeypatch.delenv("YAMS_SEARCH_PROVIDER", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text(
            "BRAVE_API_KEY=file-key\nYAMS_SEARCH_COUNT=5\nYAMS_SEARCH_PROVIDER=brave\n"
        )
        settings = SearchSettings(_env_file=str(env_file))
        assert settings.brave_api_key == "file-key"
        assert settings.count == 5
