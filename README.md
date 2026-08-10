Pi/OpenCode status indicator for tmux window names.

## Setup

From this repository:

```sh
printf '\nsource-file %s/tmux/agent-idle.conf\n' "$PWD" >> ~/.tmux.conf
mkdir -p ~/.pi/agent/extensions ~/.config/opencode/plugins
ln -sfn "$PWD/pi/agent-idle.ts" ~/.pi/agent/extensions/agent-idle.ts
ln -sfn "$PWD/opencode/agent-idle.js" ~/.config/opencode/plugins/agent-idle.js
tmux source-file ~/.tmux.conf
```

Restart Pi and OpenCode.

## Options

Highlight running agents:

```tmux
set -g @agent_accent "colour39"
set -g @agent_highlight_when "running"
```

If you want highlighting when idle:

```tmux
set -g @agent_highlight_when "idle"
```

The indicator is scoped to each tmux window.
