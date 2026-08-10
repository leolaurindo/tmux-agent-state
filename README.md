# tmux agent idle


Small Pi/OpenCode indicator for tmux window names.

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

## Customize

The default only underlines the window name while the agent is running:

```tmux
set -g @agent_highlight_when "running"
set -g @agent_highlight_style "underscore"
```

Set these after the `source-file` line in `~/.tmux.conf`. The style is applied
only to the window name; the rest of your theme format is preserved.

Use a hardcoded color:

```tmux
set -g @agent_highlight_style "fg=#a9b1d6"
```

Use a tmux theme color:

```tmux
set -g @agent_highlight_style "fg=themegreen"
```

Use the theme's current-window style with a small tweak:

```tmux
set -g @agent_highlight_style "#{E:window-status-current-style},underscore"
```

Other useful tweaks include `bold`, `reverse`, `italics` and `underscore,bold`.
Use `idle` instead of `running` to highlight waiting agents.
