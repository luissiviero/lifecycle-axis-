"""Test harness for the PreToolUse/Stop hooks in .claude/hooks/.

Hooks live under a path protected by protect-paths.sh, so tests cannot live
next to them and cannot import them as Python modules: they are POSIX shell
scripts invoked by Claude Code as subprocesses, one JSON object piped in on
stdin. This module reproduces that invocation for tests.

Hook contract (see .claude/hooks/_lib.sh):
  - exit 0            -> allow. Stdout is normally empty, but a hook may
                          still emit an "ask" JSON payload with exit 0
                          (see below) -- 0 alone does not mean "no opinion".
  - exit 2            -> block. The reason is written to stderr.
  - stdout JSON        -> "ask": a hookSpecificOutput object with
                          permissionDecision == "ask", written with exit 0.

Two helpers:

  fake_repo(config_env=None, **files)
      Context manager. Creates a temp dir, `git init`s it, writes
      .sdlc/config.env (copied from this repo's own .sdlc/config.env unless
      `config_env` is given as a string of file content), and writes any
      extra `files` (relative-path -> content) into the tree. Yields the
      repo's absolute path.

  run_hook(hook_name, payload, root, env=None)
      Runs .claude/hooks/<hook_name> from the real repo (hooks are read from
      THIS repo, not the fake one -- that's the point: the fake repo only
      supplies the config/workspace the hook reads via CLAUDE_PROJECT_DIR;
      on Windows, through `bash`, which is the only way to run a shebang
      script there) with `payload` JSON-encoded and piped to stdin, CLAUDE_PROJECT_DIR set
      to `root`, and returns the completed subprocess (stdout/stderr as
      text). The environment starts as a copy of os.environ with every
      SDLC_* var and RELEASE_APPROVAL stripped out first, so ambient
      variables from the calling shell/session can't leak into a test's
      expectations; `env` overrides/adds on top of that clean base.
"""
from __future__ import annotations

import contextlib
import json
import os
import subprocess
import tempfile

# This repo's root (where .claude/hooks/ and .sdlc/config.env actually live),
# independent of any fake repo a test constructs.
REAL_ROOT = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True,
    text=True,
    check=True,
).stdout.strip()

HOOKS_DIR = os.path.join(REAL_ROOT, ".claude", "hooks")


@contextlib.contextmanager
def fake_repo(config_env: str | None = None, **files):
    """Yield a temp dir that is a git repo with .sdlc/config.env and `files` written."""
    with tempfile.TemporaryDirectory() as root:
        subprocess.run(["git", "init", "-q", root], check=True)
        # A committer identity, in case a test wants to `git commit` in the fake repo.
        subprocess.run(["git", "-C", root, "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", root, "config", "user.name", "Test"], check=True)

        os.makedirs(os.path.join(root, ".sdlc"), exist_ok=True)
        if config_env is None:
            with open(os.path.join(REAL_ROOT, ".sdlc", "config.env"), encoding="utf-8") as f:
                config_env = f.read()
        with open(os.path.join(root, ".sdlc", "config.env"), "w", encoding="utf-8") as f:
            f.write(config_env)

        for relpath, content in files.items():
            path = os.path.join(root, relpath)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

        yield root


def run_hook(hook_name: str, payload: dict, root: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Pipe json.dumps(payload) to .claude/hooks/<hook_name> with CLAUDE_PROJECT_DIR=root.

    Ambient SDLC_* and RELEASE_APPROVAL env vars are stripped from the
    base environment before `env` overrides are applied, so a test's
    expectations depend only on what it explicitly sets.
    """
    hook_path = os.path.join(HOOKS_DIR, hook_name)
    base_env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("SDLC_") and k != "RELEASE_APPROVAL"
    }
    base_env["CLAUDE_PROJECT_DIR"] = root
    if env:
        base_env.update(env)
    # Windows cannot exec a shebang script: CreateProcess raises WinError 193 on a .sh file.
    # Claude Code and Gemini CLI both run the hooks through a shell there, so the harness does
    # the same and the suite becomes runnable on a Windows checkout (roadmap item 19b).
    argv = ["bash", hook_path] if os.name == "nt" else [hook_path]
    return subprocess.run(
        argv,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=base_env,
    )
