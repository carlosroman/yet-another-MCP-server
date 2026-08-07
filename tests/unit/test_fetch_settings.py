from __future__ import annotations

import os
from unittest.mock import patch

from yams.tools.fetch.settings import FetchSettings


class TestFetchSettingsDefaults:
    def test_default_timeout(self):
        assert FetchSettings().timeout == 30

    def test_default_max_size(self):
        assert FetchSettings().max_size == 1048576

    def test_default_follow_redirects(self):
        assert FetchSettings().follow_redirects is True

    def test_default_user_agent(self):
        assert FetchSettings().user_agent == "YAMS/1.0"


class TestFetchSettingsEnvVars:
    def test_timeout_from_env(self):
        with patch.dict(os.environ, {"YAMS_FETCH_TIMEOUT": "60"}):
            s = FetchSettings()
            assert s.timeout == 60

    def test_max_size_from_env(self):
        with patch.dict(os.environ, {"YAMS_FETCH_MAX_SIZE": "2097152"}):
            s = FetchSettings()
            assert s.max_size == 2097152

    def test_follow_redirects_from_env(self):
        with patch.dict(os.environ, {"YAMS_FETCH_FOLLOW_REDIRECTS": "false"}):
            s = FetchSettings()
            assert s.follow_redirects is False

    def test_user_agent_from_env(self):
        with patch.dict(os.environ, {"YAMS_FETCH_USER_AGENT": "TestBot/1.0"}):
            s = FetchSettings()
            assert s.user_agent == "TestBot/1.0"

    def test_constructor_overrides_env(self):
        with patch.dict(os.environ, {"YAMS_FETCH_TIMEOUT": "60"}):
            s = FetchSettings(timeout=10)
            assert s.timeout == 10


class TestFetchSettingsValidation:
    def test_ignores_extra_env_vars(self):
        with patch.dict(os.environ, {"YAMS_FETCH_UNKNOWN_VAR": "value"}):
            s = FetchSettings()
            assert s.timeout == 30

    def test_env_prefix_isolation(self):
        with patch.dict(os.environ, {"OTHER_TIMEOUT": "999"}):
            s = FetchSettings()
            assert s.timeout == 30
