#!/usr/bin/env python3
"""Install repository-owned Codex/tmux integration without replacing other config."""

import json
import os
from pathlib import Path
import re
import subprocess
import tomllib

repo = Path(__file__).resolve().parent.parent
home = Path.home()
runtime = home / ".config/tmux-agent-state"
runtime.parent.mkdir(parents=True, exist_ok=True)
if not runtime.exists():
    runtime.symlink_to(repo)
if runtime.resolve() != repo:
    raise SystemExit(f"{runtime} must point to {repo}; refusing to replace it")

codex_home = Path(os.environ.get("CODEX_HOME", home / ".codex"))
codex_home.mkdir(parents=True, exist_ok=True)
config = codex_home / "config.toml"
original = config.read_text() if config.exists() else ""
tomllib.loads(original)
titles = tomllib.loads((repo / "codex/config.toml").read_text())["tui"]["terminal_title"]
setting = "terminal_title = " + json.dumps(titles)
section = re.search(r"(?m)^\[tui\][ \t]*(?:#.*)?\n(?:(?!^\[).)*", original, re.DOTALL)
if section:
    body = section.group()
    if re.search(r"(?m)^terminal_title\s*=", body):
        # Parse the existing assignment, including a multiline array, as one value.
        start = re.search(r"(?m)^terminal_title\s*=", body).start()
        end = start
        for line in body[start:].splitlines(keepends=True):
            end += len(line)
            try:
                tomllib.loads(body[start:end])
                break
            except tomllib.TOMLDecodeError:
                continue
        body = body[:start] + setting + "\n" + body[end:]
    else:
        body = body.rstrip() + "\n" + setting + "\n\n"
    updated = original[:section.start()] + body + original[section.end():]
else:
    updated = original.rstrip() + "\n\n[tui]\n" + setting + "\n"
expected = tomllib.loads(original)
expected.setdefault("tui", {})["terminal_title"] = titles
if tomllib.loads(updated) != expected:
    raise SystemExit("Title edit would change unrelated Codex config; refusing to write")
config.write_text(updated)

# Remove only the lifecycle-hook symlink installed by an earlier version.
hooks = codex_home / "hooks.json"
if hooks.is_symlink() and hooks.resolve() == repo / "codex/hooks.json":
    hooks.unlink()

tmux_config = home / ".tmux.conf"
text = tmux_config.read_text() if tmux_config.exists() else ""
source = "source-file ~/.config/tmux-agent-state/codex/agent-state.conf"
if source not in text.splitlines():
    tmux_config.write_text(text.rstrip() + "\n" + source + "\n")
if os.environ.get("TMUX"):
    subprocess.run(["tmux", "source-file", str(runtime / "codex/agent-state.conf")], check=True)
print("Installed Codex title tracking from", repo)
print("Existing Codex sessions keep working with their default titles.")
print("New Codex sessions use the configured app name, status, activity and project title.")
