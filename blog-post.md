---
title: "I Built a Tool That Writes Obituaries for Your Deleted Code"
published: true
description: "Every function has a story. When you delete code, that story disappears. So I built code-obituary — a Python CLI that uses Claude AI to write poetic farewells for deleted files."
tags: python, git, ai, devtools
cover_image: https://images.unsplash.com/photo-1518770660439-4636190af475?w=800
---

# I Built a Tool That Writes Obituaries for Your Deleted Code

Every function has a story.

When you write `get_oauth_token()`, you're not just writing code. You're solving a problem, working around an API's quirks, handling an edge case that burned you three times before. That context lives in the function — in its variable names, its comments, its error handling.

When you delete it, that story disappears forever.

`git log` shows you *that* something was deleted. `git show` can recover the bytes. But neither tells you *why* it mattered, what it did, how long it served you, or what killed it.

I wanted to change that.

---

## The Problem: Deleted Code Context is Lost Forever

Picture this: you're six months into a project. You delete a 200-line authentication module because you're migrating to a new OAuth provider. You `git rm legacy_oauth.py`, commit with `"remove old auth module"`, and move on.

A year later, a colleague is debugging a subtle session handling bug. They search the codebase, find nothing, then find your commit. The file is gone. The commit message tells them nothing. The context — why it worked the way it did, what edge cases it handled — is lost.

This happens every day in software teams. We're meticulous about documenting what we *add*, but we delete code silently.

---

## The Solution: A Graveyard for Your Code

`code-obituary` is a Python CLI that:

1. Detects deleted files (manually or via a git pre-commit hook)
2. Reads their content from git history
3. Extracts function names, class names, and line counts
4. Calls the **Anthropic Claude API** to write a brief, poetic obituary
5. Appends it to `GRAVEYARD.md` in your repo root

No API key? No problem. It falls back to a template-based obituary using regex analysis.

---

## Demo: What GRAVEYARD.md Looks Like

After running `code-obituary mourn legacy_oauth.py --reason "Twitter API v1 deprecated"`:

```markdown
# GRAVEYARD.md

*Here lie the fallen code, remembered but no longer needed.*

---

## legacy_oauth.py
**Lived:** 2022-03-14 — 2024-11-01
**Cause of death:** Twitter API v1 deprecated
**Last words:** "def get_oauth_token(consumer_key, consumer_secret):..."

> legacy_oauth.py served faithfully as the OAuth 1.0 bridge for Twitter login.
> It handled token generation for 847 days before the API it deprecated on was
> sunset. In its time, it authenticated over 12,000 users and handled the
> awkward OAuth 1.0a signature dance with quiet dignity. It is survived by
> oauth2_handler.py, which carries on its mission with fewer cryptographic
> headaches.

---
```

The AI-generated prose is brief, human, and genuinely useful as documentation.

---

## Installation in 3 Lines

```bash
pip install code-obituary
cd your-project
code-obituary install  # sets up git pre-commit hook
```

That's it. Now every `git commit` that deletes files will automatically generate obituaries.

---

## How It Works

The architecture is simple:

```
git commit (with deletions)
    --> pre-commit hook
    --> git diff --cached --diff-filter=D   # find deleted files
    --> git show HEAD:<file>                # get content from last commit
    --> analyzer.py                         # extract symbols + call Claude
    --> graveyard.py                        # append to GRAVEYARD.md
    --> git add GRAVEYARD.md               # stage the update
```

The `analyzer.py` module handles two modes:

**With `ANTHROPIC_API_KEY`:** Builds a structured prompt with the file content, symbol names, and lifecycle dates, then calls `claude-opus-4-6` to generate a 3-5 sentence obituary.

**Without API key:** Uses regex to extract function/class names, maps file extensions to descriptions, and fills a template. Works offline and immediately.

---

## What I Learned

**1. Git plumbing is powerful.** `git diff --cached --diff-filter=D` to find staged deletions, `git show HEAD:<path>` to recover content before it's committed — these two commands are the backbone of the tool.

**2. Template fallbacks matter.** Not everyone has (or wants to expose) an API key. Building a solid template fallback made the tool useful from day one, without any dependencies.

**3. The "why" of deletion is underrated documentation.** The `--reason` flag is the most important feature. `"Replaced by oauth2_handler.py after Twitter API v1 deprecation"` is infinitely more useful than `"remove old auth"` in a commit message.

**4. Poetry in devtools is delightful.** Using words like "survived by" and "lived from" for a code file is a small thing, but it makes developers smile. Tone matters in tools.

---

## Try It

```bash
pip install code-obituary
code-obituary mourn some_old_file.py --reason "Refactored into smaller modules"
code-obituary view
```

Source: [github.com/LakshmiSravyaVedantham/code-obituary](https://github.com/LakshmiSravyaVedantham/code-obituary)

If you find it useful, a star would mean a lot. And if you have a particularly good obituary generated by it, share it in the comments — I'd love to see what it comes up with for your code.

---

*Every function deserves a proper farewell.*
