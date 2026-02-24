"""Tests for graveyard.py"""

from datetime import date

import pytest

from code_obituary.graveyard import (
    append_obituary,
    ensure_graveyard,
    get_graveyard_path,
    list_obituaries,
    read_graveyard,
)


@pytest.fixture
def tmp_repo(tmp_path):
    """Create a temporary directory to act as a fake repo root."""
    return str(tmp_path)


class TestEnsureGraveyard:
    def test_creates_graveyard_if_missing(self, tmp_repo):
        path = get_graveyard_path(tmp_repo)
        assert not __import__("os").path.exists(path)
        ensure_graveyard(tmp_repo)
        assert __import__("os").path.exists(path)

    def test_graveyard_has_correct_header(self, tmp_repo):
        ensure_graveyard(tmp_repo)
        with open(get_graveyard_path(tmp_repo), "r") as f:
            content = f.read()
        assert "GRAVEYARD.md" in content
        assert "fallen code" in content

    def test_does_not_overwrite_existing(self, tmp_repo):
        path = get_graveyard_path(tmp_repo)
        with open(path, "w") as f:
            f.write("existing content")
        ensure_graveyard(tmp_repo)
        with open(path, "r") as f:
            content = f.read()
        assert content == "existing content"


class TestAppendObituary:
    def test_creates_graveyard_and_appends(self, tmp_repo):
        import os

        path = get_graveyard_path(tmp_repo)
        assert not os.path.exists(path)

        entry = append_obituary(
            tmp_repo,
            "legacy_oauth.py",
            "It served the Twitter API for 847 days.",
            {
                "born": "2022-03-14",
                "died": "2024-11-01",
                "reason": "Twitter API v1 deprecation",
                "last_words": "def get_oauth_token(consumer_key, consumer_secret):",
            },
        )

        assert os.path.exists(path)
        assert "legacy_oauth.py" in entry
        assert "2022-03-14" in entry
        assert "2024-11-01" in entry
        assert "Twitter API v1 deprecation" in entry

    def test_appends_multiple_obituaries(self, tmp_repo):
        append_obituary(tmp_repo, "file1.py", "First obituary text.", {})
        append_obituary(tmp_repo, "file2.py", "Second obituary text.", {})

        with open(get_graveyard_path(tmp_repo), "r") as f:
            content = f.read()

        assert "file1.py" in content
        assert "file2.py" in content
        assert "First obituary text." in content
        assert "Second obituary text." in content

    def test_obituary_uses_blockquote_format(self, tmp_repo):
        append_obituary(
            tmp_repo,
            "old_module.py",
            "It was a brave little module.",
            {},
        )
        with open(get_graveyard_path(tmp_repo), "r") as f:
            content = f.read()
        assert "> It was a brave little module." in content

    def test_metadata_defaults_to_today(self, tmp_repo):
        append_obituary(tmp_repo, "file.py", "Some text.", {})
        with open(get_graveyard_path(tmp_repo), "r") as f:
            content = f.read()
        today = str(date.today())
        assert today in content

    def test_returns_formatted_entry(self, tmp_repo):
        entry = append_obituary(
            tmp_repo,
            "utils.py",
            "It was a utility module.",
            {"reason": "Replaced by helpers.py"},
        )
        assert isinstance(entry, str)
        assert "utils.py" in entry
        assert "Replaced by helpers.py" in entry

    def test_last_words_are_included(self, tmp_repo):
        entry = append_obituary(
            tmp_repo,
            "config.py",
            "A config file lived and died.",
            {"last_words": "DATABASE_URL = 'sqlite:///app.db'"},
        )
        assert "DATABASE_URL" in entry


class TestListObituaries:
    def test_returns_empty_list_if_no_graveyard(self, tmp_repo):
        result = list_obituaries(tmp_repo)
        assert result == []

    def test_returns_correct_count(self, tmp_repo):
        append_obituary(tmp_repo, "alpha.py", "Alpha obit.", {"reason": "Reason A"})
        append_obituary(tmp_repo, "beta.py", "Beta obit.", {"reason": "Reason B"})
        result = list_obituaries(tmp_repo)
        assert len(result) == 2

    def test_parses_filename_correctly(self, tmp_repo):
        append_obituary(tmp_repo, "legacy_auth.py", "Auth module obit.", {})
        result = list_obituaries(tmp_repo)
        assert result[0]["filename"] == "legacy_auth.py"

    def test_parses_lived_dates(self, tmp_repo):
        append_obituary(
            tmp_repo,
            "old.py",
            "Old module.",
            {"born": "2020-01-01", "died": "2024-12-31"},
        )
        result = list_obituaries(tmp_repo)
        assert "2020-01-01" in result[0]["lived"]
        assert "2024-12-31" in result[0]["lived"]

    def test_parses_cause_of_death(self, tmp_repo):
        append_obituary(
            tmp_repo,
            "module.py",
            "Module obit.",
            {"reason": "Replaced by new_module.py"},
        )
        result = list_obituaries(tmp_repo)
        assert "Replaced by new_module.py" in result[0]["cause"]

    def test_parses_body_text(self, tmp_repo):
        append_obituary(tmp_repo, "x.py", "It served well for many years.", {})
        result = list_obituaries(tmp_repo)
        assert "It served well for many years." in result[0]["body"]


class TestReadGraveyard:
    def test_returns_message_if_no_graveyard(self, tmp_repo):
        result = read_graveyard(tmp_repo)
        assert "No GRAVEYARD.md found" in result

    def test_returns_content_if_exists(self, tmp_repo):
        append_obituary(tmp_repo, "file.py", "An obituary.", {})
        result = read_graveyard(tmp_repo)
        assert "file.py" in result
        assert "An obituary." in result
