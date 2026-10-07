#!/usr/bin/env python3
"""Sync a Codex TUI pane's native title into the shared tmux agent state."""

import shlex
import subprocess
import sys
import time
from pathlib import Path

SPINNERS = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
# The same three buckets are used by tmux to ignore spinner/blink-only changes.
WAITING = r"^[[] [!.] []] Action Required"
WORKING = rf"(^codex [|] (Starting|Working|Thinking|Waiting))|(^[{SPINNERS}])"
STATE_FORMAT = "#{?#{m/r:" + WAITING + ",#{pane_title}},waiting,#{?#{m/r:" + WORKING + ",#{pane_title}},working,idle}}"


def tmux(*args):
    return subprocess.run(
        ["tmux", *args], check=True, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, timeout=2,
    ).stdout.strip()


def set_option(pane, scope, option, value=None):
    args = ["set-option", scope, "-t", pane]
    if value is None:
        args.append("-u")
    args.append(option)
    if value is not None:
        args.append(value)
    tmux(*args)


def refresh_window(pane):
    states = tmux("list-panes", "-t", pane, "-F",
                  "#{?@agent_pane,1,0}#{?@agent_running_pane,1,0}").splitlines()
    agents = [state for state in states if state.startswith("1")]
    set_option(pane, "-w", "@agent_window", "1" if agents else None)
    running = bool(agents) and all(state == "11" for state in agents)
    set_option(pane, "-w", "@agent_running", "1" if running else None)


def sync(pane):
    info = tmux(
        "display-message", "-p", "-t", pane,
        "#{pane_current_command}\t#{pane_tty}\t#{@codex_managed}\t#{@codex_title_known}\t"
        + STATE_FORMAT + "\t#{pane_title}",
    )
    command, tty, managed, title_known, state, title = info.split("\t", 5)
    is_codex = command == "codex"
    if command == "node":
        # The npm launcher is node; confirm the Codex executable on the same tty.
        names = subprocess.check_output(["ps", "-t", tty, "-o", "comm="], text=True).split()
        is_codex = "codex" in names
    title_has_codex = "codex" in title.lower()
    recognized = title_has_codex or state != "idle"
    known = title_known == "1" or recognized
    set_option(pane, "-p", "@codex_title_state", state)
    set_option(pane, "-p", "@codex_command", command)
    if is_codex:
        set_option(pane, "-p", "@codex_managed", "1")
        set_option(pane, "-p", "@codex_title_known", "1" if known else None)
        set_option(pane, "-p", "@codex_title_has_app", "1" if title_has_codex else None)
        set_option(pane, "-p", "@agent_pane", "1" if known else None)
        set_option(pane, "-p", "@agent_running_pane", "1" if known and state == "working" else None)
        refresh_window(pane)
    elif managed:
        for option in (
            "@codex_managed", "@codex_title_known", "@codex_title_has_app",
            "@agent_pane", "@agent_running_pane",
        ):
            set_option(pane, "-p", option)
        refresh_window(pane)


def install():
    # Target the pane that emitted the title, not the app-server daemon's TMUX_PANE.
    candidate = "#{||:#{m/r:^(codex|node)$,#{pane_current_command}},#{@codex_managed}}"
    title_has_codex = "#{m/r:codex,#{pane_title}}"
    newly_identified = "#{&&:#{@codex_managed},#{!=:#{@codex_title_known},1}," + title_has_codex + "}"
    left_codex_title = "#{&&:#{@codex_managed},#{==:#{@codex_title_has_app},1},#{!=:" + title_has_codex + ",1}}"
    state_changed = "#{!=:#{@codex_title_state}," + STATE_FORMAT + "}"
    command_changed = "#{!=:#{@codex_command},#{pane_current_command}}"
    changed = "#{||:" + state_changed + ",#{||:" + command_changed + ",#{||:" + newly_identified + "," + left_codex_title + "}}}"
    condition = "#{&&:" + candidate + "," + changed + "}"
    command = shlex.join(["python3", str(Path(__file__).resolve())]) + " --settle #{hook_pane}"
    hook = "if-shell -F " + shlex.quote(condition) + " " + shlex.quote("run-shell -b " + shlex.quote(command))
    tmux("set-hook", "-g", "pane-title-changed[codex-agent-state]", hook)
    for pane in tmux("list-panes", "-a", "-F", "#{pane_id}").splitlines():
        sync(pane)


if __name__ == "__main__":
    if sys.argv[1:] == ["--install"]:
        install()
    elif len(sys.argv) == 3 and sys.argv[1] == "--settle":
        try:
            sync(sys.argv[2])
            time.sleep(0.2)
            sync(sys.argv[2])
        except (ValueError, OSError, subprocess.SubprocessError):
            # A pane can disappear while a title hook is running.
            pass
    elif len(sys.argv) == 2:
        try:
            sync(sys.argv[1])
        except (ValueError, OSError, subprocess.SubprocessError):
            # A pane can disappear while a title hook is running.
            pass
