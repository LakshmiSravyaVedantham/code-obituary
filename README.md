# code-obituary

> Write AI-generated obituaries for deleted code. Because every function deserves a proper farewell.

[![CI](https://github.com/LakshmiSravyaVedantham/code-obituary/actions/workflows/ci.yml/badge.svg)](https://github.com/LakshmiSravyaVedantham/code-obituary/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/code-obituary.svg)](https://pypi.org/project/code-obituary/)

---

## What is this?

When you delete code, its history and purpose vanish forever. `code-obituary` solves this by
automatically generating a short, poetic obituary for every file you delete — and recording it
in a `GRAVEYARD.md` file in your repository.

Works as:
- A **CLI tool** you can run manually on any file
- A **git pre-commit hook** that triggers automatically on `git commit` when files are deleted

Optionally uses the **Anthropic Claude API** for AI-generated prose. Falls back gracefully
to a template-based obituary if no API key is set.

---

## Demo

```
$ code-obituary mourn legacy_oauth.py --reason "Twitter API v1 deprecated"

 Mourning legacy_oauth.py...
 Generating obituary...

 Obituary written:

## legacy_oauth.py
**Lived:** 2022-03-14 — 2024-11-01
**Cause of death:** Twitter API v1 deprecated
**Last words:** "def get_oauth_token(consumer_key, consumer_secret):..."

> legacy_oauth.py served faithfully as the OAuth 1.0 bridge for Twitter login.
> It handled token generation for 847 days before the API it depended on was
> deprecated. It is survived by oauth2_handler.py.

 Appended to GRAVEYARD.md
```

---

## Install

```bash
pip install code-obituary
```

Or for development:

```bash
git clone https://github.com/LakshmiSravyaVedantham/code-obituary
cd code-obituary
pip install -e ".[dev]"
```

---

## Quick Start

### 1. Mourn a file manually

```bash
code-obituary mourn path/to/old_file.py
code-obituary mourn path/to/old_file.py --reason "Replaced by new_auth.py"
```

### 2. Install the git hook (auto-mourn on delete)

```bash
cd your-project
code-obituary install
```

Now every `git commit` that deletes files will automatically write obituaries to `GRAVEYARD.md`.

### 3. View the graveyard

```bash
code-obituary view        # Pretty-print GRAVEYARD.md
code-obituary list        # Table view with dates
```

### 4. Enable AI obituaries

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
code-obituary mourn old_module.py
```

---

## How It Works

```
git commit (with deleted files)
       |
       v
 pre-commit hook
       |
       v
 git diff --cached --diff-filter=D  (find deleted files)
       |
       v
 git show HEAD:<filepath>            (get file content from last commit)
       |
       v
 analyzer.py                         (extract symbols, call Claude API or template)
       |
       v
 graveyard.py                        (append to GRAVEYARD.md)
       |
       v
 git add GRAVEYARD.md                (stage the updated graveyard)
```

---

## Commands

| Command | Description |
|---------|-------------|
| `code-obituary mourn <file>` | Write an obituary for a file |
| `code-obituary mourn <file> --reason "..."` | Specify cause of death |
| `code-obituary mourn <file> --from-git` | Read content from git HEAD |
| `code-obituary install` | Install pre-commit hook |
| `code-obituary view` | Pretty-print GRAVEYARD.md |
| `code-obituary list` | Table view of all obituaries |

---

## GRAVEYARD.md Format

```markdown
# GRAVEYARD.md

*Here lie the fallen code, remembered but no longer needed.*

---

## legacy_oauth.py
**Lived:** 2022-03-14 — 2024-11-01
**Cause of death:** Replaced by oauth2_handler.py after Twitter API v1 deprecation
**Last words:** "def get_oauth_token(consumer_key, consumer_secret)..."

> legacy_oauth.py served faithfully as the OAuth 1.0 bridge for Twitter login.
> It handled token generation for 847 days before the API it depended on was
> deprecated. It is survived by oauth2_handler.py.

---
```

---

## Configuration

| Environment Variable | Description |
|----------------------|-------------|
| `ANTHROPIC_API_KEY` | Enables AI-generated obituaries via Claude |

---

## Contributing

Contributions are welcome! Please:

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Run tests: `pytest`
4. Format code: `black . && isort .`
5. Open a pull request

---

## License

MIT License. See [LICENSE](LICENSE).
