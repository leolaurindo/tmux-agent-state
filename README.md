A tmux indicator for agent activity.

It uses window-list styling to distinguish working from idle agents.
- pi: reports pane state on `agent_start` and `agent_settled`, plus permission prompts from `pi-permission-system`.
- opencode: reports pane state on `busy`, `retry` and `idle` session events, and highlights pending permission requests.
- hax: uses its tmux BEL completion notification to apply the idle style silently.
- Codex CLI: uses each TUI pane's native title to highlight idle agents and pending permissions/questions.

## Setup

```sh
mkdir -p ~/projects ~/.config
git clone https://github.com/leolaurindo/tmux-agent-state.git ~/projects/tmux-agent-state
ln -s ~/projects/tmux-agent-state ~/.config/tmux-agent-state
cd ~/projects/tmux-agent-state

printf '\nsource-file %s/tmux/agent-state.conf\n' "$HOME/.config/tmux-agent-state" >> ~/.tmux.conf

# optional: for hax
printf '\nsource-file %s/hax/hax-agent-state.conf\n' "$HOME/.config/tmux-agent-state" >> ~/.tmux.conf

# for pi
mkdir -p ~/.pi/agent/extensions 
ln -sfn "$HOME/.config/tmux-agent-state/pi/agent-state.ts" ~/.pi/agent/extensions/agent-state.ts

# for opencode
mkdir -p ~/.config/opencode/plugins
ln -sfn "$HOME/.config/tmux-agent-state/opencode/agent-state.js" ~/.config/opencode/plugins/agent-state.js

# for Codex CLI (requires python3 3.11+, ps and tmux pane-title-changed support)
python3 codex/install.py

tmux source-file ~/.tmux.conf
# restart pi, opencode and/or hax if they were running
```

After the setup, configure the style (there's no default, you have to configure as you want).

## Codex CLI

Install and activate the integration with `python3 codex/install.py`.
The implementation, tmux hook, Codex title configuration and installer all live
in `codex/` in this repository. The installer preserves the other config values
and adds this line to `~/.tmux.conf`:

```tmux
source-file ~/.config/tmux-agent-state/codex/agent-state.conf
```

It also applies the setting from `codex/config.toml` to the existing `[tui]`
table in `~/.codex/config.toml`:

```toml
terminal_title = ["app-name", "status", "spinner", "project"]
```

The activity/spinner item is required: Codex uses it to publish `Action Required`
when a permission, question, MCP elicitation or other input needs a response.
New CLI sessions use this configured title. Already-running CLI sessions with
the standard spinner/thread/project title also work, without a restart.

| Codex title/state | tmux behavior |
| --- | --- |
| Working, Thinking, Starting, or a running spinner | Working; no idle highlight |
| Ready, or the standard title without a spinner | Idle highlight |
| `[ ! ] Action Required` / `[ . ] Action Required` | Idle highlight while waiting for permission or an answer |
| Back to working after approval/answer | Clear idle highlight immediately |
| Codex exits and the shell updates the title | Remove Codex's pane state |

`Waiting` for a background terminal is still working: it is not a request for
human input. Blink phases of `Action Required` both count as waiting. Optional
async questions also highlight the window even while the agent continues other
work, until the question is answered.

The integration registers a named `pane-title-changed[codex-agent-state]` hook
in tmux. It targets the pane that emitted the title and works with Codex's
shared app-server daemon. It does not use Codex lifecycle hooks, require `/hooks`
trust, wrap the CLI, make permission decisions, parse chat content or poll.
Changes that only animate a spinner or blink do not launch another script.
For the npm CLI launcher, `ps` confirms a Codex process on the pane's tty before
marking that pane as an agent; unrelated node processes are left alone.

The existing `@agent_idle_style` and multi-pane aggregation also apply to Codex.
This is a window-name highlight, not an audible or desktop notification.

Checked with Codex CLI 0.160.1 and tmux next-3.8 on Linux. The tmux build must
support `pane-title-changed`. This integration follows Codex's native title
format, so a future CLI format change may need an update. Custom titles that
omit the activity item cannot publish all waiting states. If an abrupt exit
leaves a title behind in a shell that does not update titles, reload the Codex
tmux config to resync. Destroying a pane can also require a resync to recalculate
its surviving window's agent state, as with pi/opencode.

See the [official terminal-title configuration](https://learn.chatgpt.com/docs/config-file/config-reference).
Run the checks against temporary, isolated tmux servers:

```sh
python3 -m unittest discover -s codex -p 'test_*.py' -v
```

## Configure styling

Styles are optional and apply only to window names in which the window contains at least one
configured agent. With multiple agents on the same window, one idle pane makes the whole window
idle; the window is running only while every agent pane is running.

You can configure styling for running state, idle, or both. They are independent.

You can set any valid tmux style. Examples:

```tmux
# configuring styles for both states 
set -g @agent_running_style "italics"
set -g @agent_idle_style "reverse"

# only for running
set -g @agent_running_style "fg=#a9b1d6, dim"

# only for idle
set -g @agent_idle_style "#{E:window-status-current-style},underscore,bold,italics"
```

Set these after the `source-file` line in `~/.tmux.conf`.

The hax config keeps tmux bell events enabled for status tracking but sets `bell-action none`, so
hax completion notifications do not make a sound. Selecting the hax window acknowledges the alert
and clears its style. The style is triggered only by a bell received from a pane whose foreground
command is `hax`; other panes' bells do not trigger it.

## Uninstall

Remove the `source-file .../tmux/agent-state.conf` line from `~/.tmux.conf`.
Remove the optional `source-file .../hax/hax-agent-state.conf` line too, if enabled.

The repository checkout is kept under `~/projects/tmux-agent-state`; `~/.config/tmux-agent-state`
is only its runtime symlink.

Remove the pi and/or opencode symlinks:

```sh
rm -f ~/.pi/agent/extensions/agent-state.ts
rm -f ~/.config/opencode/plugins/agent-state.js
tmux source-file ~/.tmux.conf
```

For Codex, remove its `source-file` line from `~/.tmux.conf` and unregister the
named hook:

```sh
tmux set-hook -gu 'pane-title-changed[codex-agent-state]'
```

For each surviving Codex pane, unset `@agent_pane`, `@agent_running_pane`,
`@codex_managed`, `@codex_title_state` and `@codex_command` with
`tmux set-option -pu -t <pane-id> <option>`; recalculate the window options if it
still has pi/opencode agent panes. If the window has no remaining agents, unset
`@agent_window` and `@agent_running` with `tmux set-option -wu -t <window-id> <option>`.
You can restore your preferred `tui.terminal_title` setting too.
