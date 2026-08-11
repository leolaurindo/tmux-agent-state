A tmux indicator for agent activity.

It uses window-list styling to distinguish working from idle agents.
- pi: sets or clears `@agent_running` on `agent_start` and `agent_settled`.
- opencode: sets or clears `@agent_running` on `busy`, `retry` and `idle` session events.

## Setup

```sh
mkdir -p ~/.config
git clone https://github.com/leolaurindo/tmux-agent-state.git ~/.config/tmux-agent-state
cd ~/.config/tmux-agent-state

printf '\nsource-file %s/tmux/agent-state.conf\n' "$PWD" >> ~/.tmux.conf

# for pi
mkdir -p ~/.pi/agent/extensions 
ln -sfn "$PWD/pi/agent-state.ts" ~/.pi/agent/extensions/agent-state.ts

# for opencode
mkdir -p ~/.config/opencode/plugins
ln -sfn "$PWD/opencode/agent-state.js" ~/.config/opencode/plugins/agent-state.js


tmux source-file ~/.tmux.conf
# restart pi and/or opencode if they were running
```

## Configure styling

Styles are optional and apply only to window names in which the window contains at least one pi or opencode pane. With multiple agents on the same window, the last event wins. 

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

## Uninstall

Remove the `source-file .../tmux/agent-state.conf` line from `~/.tmux.conf`.

Remove the pi and/or opencode symlinks:

```sh
rm -f ~/.pi/agent/extensions/agent-state.ts
rm -f ~/.config/opencode/plugins/agent-state.js
tmux source-file ~/.tmux.conf
```
