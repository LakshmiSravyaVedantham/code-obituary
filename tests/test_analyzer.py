"""Tests for analyzer.py"""

from code_obituary.analyzer import (
    extract_symbols,
    generate_obituary,
    generate_template_obituary,
    get_file_description,
)

SAMPLE_PYTHON = """\
import os
import re

CONSTANT = "hello"


class OAuthHandler:
    \"\"\"Handles OAuth authentication.\"\"\"

    def __init__(self, consumer_key, consumer_secret):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

    def get_token(self):
        pass

    def refresh_token(self):
        pass


def get_user_profile(user_id):
    \"\"\"Fetches a user's profile from the API.\"\"\"
    return {}


def _internal_helper(data):
    return data
"""

SAMPLE_PYTHON_WITH_CLASS_AND_FUNCS = """\
class Router:
    def __init__(self):
        self.routes = {}

def handle_request(req, res):
    return 'OK'

async def get_user(user_id):
    return {}
"""

EMPTY_FILE = ""

SIMPLE_SCRIPT = """\
#!/usr/bin/env python3
print("Hello, world!")
"""


class TestExtractSymbols:
    def test_finds_python_functions(self):
        result = extract_symbols(SAMPLE_PYTHON)
        assert "get_user_profile" in result["functions"]
        assert "_internal_helper" in result["functions"]

    def test_finds_python_classes(self):
        result = extract_symbols(SAMPLE_PYTHON)
        assert "OAuthHandler" in result["classes"]

    def test_finds_python_methods(self):
        result = extract_symbols(SAMPLE_PYTHON)
        # Methods are also functions via regex
        assert "get_token" in result["functions"]
        assert "refresh_token" in result["functions"]

    def test_returns_empty_for_no_symbols(self):
        result = extract_symbols(EMPTY_FILE)
        assert result["functions"] == []
        assert result["classes"] == []

    def test_finds_async_functions(self):
        code = "async def fetch_data(url):\n    pass\n"
        result = extract_symbols(code)
        assert "fetch_data" in result["functions"]

    def test_finds_classes_in_mixed_file(self):
        result = extract_symbols(SAMPLE_PYTHON_WITH_CLASS_AND_FUNCS)
        assert "Router" in result["classes"]

    def test_finds_functions_in_mixed_file(self):
        result = extract_symbols(SAMPLE_PYTHON_WITH_CLASS_AND_FUNCS)
        assert "handle_request" in result["functions"]

    def test_returns_lists(self):
        result = extract_symbols(SAMPLE_PYTHON)
        assert isinstance(result["functions"], list)
        assert isinstance(result["classes"], list)

    def test_no_false_positives_in_strings(self):
        code = '# def not_a_function(x):\nresult = "class Fake:"\n'
        result = extract_symbols(code)
        # The string "class Fake:" should not produce a class
        assert "Fake" not in result["classes"]

    def test_finds_multiple_classes(self):
        code = "class Foo:\n    pass\n\nclass Bar:\n    pass\n"
        result = extract_symbols(code)
        assert "Foo" in result["classes"]
        assert "Bar" in result["classes"]

    def test_finds_multiple_functions(self):
        code = "def foo():\n    pass\n\ndef bar():\n    pass\n"
        result = extract_symbols(code)
        assert "foo" in result["functions"]
        assert "bar" in result["functions"]


class TestGetFileDescription:
    def test_includes_filename(self):
        desc = get_file_description("legacy_auth.py", SAMPLE_PYTHON)
        assert "legacy_auth.py" in desc

    def test_identifies_python_module(self):
        desc = get_file_description("module.py", SAMPLE_PYTHON)
        assert "Python module" in desc

    def test_includes_line_count(self):
        desc = get_file_description("module.py", SAMPLE_PYTHON)
        line_count = len(SAMPLE_PYTHON.splitlines())
        assert str(line_count) in desc

    def test_includes_class_names(self):
        desc = get_file_description("module.py", SAMPLE_PYTHON)
        assert "OAuthHandler" in desc

    def test_includes_function_names(self):
        desc = get_file_description("module.py", SAMPLE_PYTHON)
        assert "get_user_profile" in desc

    def test_unknown_extension(self):
        desc = get_file_description("Makefile", "all:\n\techo done\n")
        assert "source file" in desc

    def test_javascript_file_description(self):
        desc = get_file_description("app.js", "const x = 1;\n")
        assert "JavaScript module" in desc

    def test_shell_script_description(self):
        desc = get_file_description("deploy.sh", "#!/bin/bash\necho done\n")
        assert "Shell script" in desc


class TestGenerateTemplateObituary:
    def test_includes_filename(self):
        obit = generate_template_obituary("legacy_oauth.py", SAMPLE_PYTHON)
        assert "legacy_oauth.py" in obit

    def test_includes_line_count(self):
        obit = generate_template_obituary("module.py", SAMPLE_PYTHON)
        line_count = len(SAMPLE_PYTHON.splitlines())
        assert str(line_count) in obit

    def test_includes_reason_when_provided(self):
        obit = generate_template_obituary(
            "file.py", SAMPLE_PYTHON, reason="Replaced by new_auth.py"
        )
        assert "Replaced by new_auth.py" in obit

    def test_generic_cause_when_no_reason(self):
        obit = generate_template_obituary("file.py", SAMPLE_PYTHON)
        assert "refactoring" in obit.lower() or "deleted" in obit.lower()

    def test_includes_dates_when_provided(self):
        obit = generate_template_obituary(
            "file.py", SAMPLE_PYTHON, born="2021-01-01", died="2024-06-15"
        )
        assert "2021-01-01" in obit
        assert "2024-06-15" in obit

    def test_handles_empty_content(self):
        obit = generate_template_obituary("empty.py", EMPTY_FILE)
        assert isinstance(obit, str)
        assert len(obit) > 0

    def test_includes_survivor_symbols(self):
        obit = generate_template_obituary("module.py", SAMPLE_PYTHON)
        # Should mention at least one class or function name
        symbols_mentioned = any(
            name in obit for name in ["OAuthHandler", "get_user_profile", "_internal_helper"]
        )
        assert symbols_mentioned

    def test_includes_last_words_for_non_empty_file(self):
        obit = generate_template_obituary("script.py", SAMPLE_PYTHON)
        # Last words snippet is added for non-empty files
        assert "Last words" in obit or "import" in obit or "CONSTANT" in obit

    def test_returns_string(self):
        obit = generate_template_obituary("file.py", SIMPLE_SCRIPT)
        assert isinstance(obit, str)

    def test_only_died_date(self):
        obit = generate_template_obituary("file.py", SAMPLE_PYTHON, died="2024-01-15")
        assert "2024-01-15" in obit

    def test_born_and_died_both_present(self):
        obit = generate_template_obituary(
            "file.py", SAMPLE_PYTHON, born="2019-06-01", died="2025-01-01"
        )
        assert "2019-06-01" in obit
        assert "2025-01-01" in obit


class TestGenerateObituary:
    def test_uses_template_when_no_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        obit = generate_obituary("test.py", SAMPLE_PYTHON)
        assert isinstance(obit, str)
        assert len(obit) > 10

    def test_accepts_reason_parameter(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        obit = generate_obituary("test.py", SAMPLE_PYTHON, reason="Replaced by better_module.py")
        assert "Replaced by better_module.py" in obit

    def test_accepts_born_and_died_parameters(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        obit = generate_obituary(
            "test.py",
            SAMPLE_PYTHON,
            born="2020-05-01",
            died="2024-10-15",
        )
        assert "2020-05-01" in obit
        assert "2024-10-15" in obit

    def test_filename_in_output(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        obit = generate_obituary("my_special_module.py", SIMPLE_SCRIPT)
        assert "my_special_module.py" in obit

    def test_handles_various_file_types(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        for ext, content in [
            (".py", SAMPLE_PYTHON),
            (".sql", "SELECT * FROM users;"),
            (".sh", "#!/bin/bash\necho hello"),
            (".md", "# Title\nSome content."),
        ]:
            obit = generate_obituary(f"file{ext}", content)
            assert isinstance(obit, str)
            assert len(obit) > 5
