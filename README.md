A tmux indicator for agent activity.

It uses window-list styling to distinguish working from idle agents.
- pi: reports pane state on `agent_start` and `agent_settled`, plus permission prompts from `pi-permission-system`.
- opencode: reports pane state on `busy`, `retry` and `idle` session events, and highlights pending permission requests.
- hax: uses its tmux BEL completion notification to apply the idle style silently.

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


tmux source-file ~/.tmux.conf
# restart pi, opencode and/or hax if they were running
```

After the setup, configure the style (there's no default, you have to configure as you want).

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
