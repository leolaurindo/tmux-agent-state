#!/usr/bin/env bash

pane=${1-}
[ -n "$pane" ] || exit 0

command=$(tmux display-message -p -t "$pane" '#{pane_current_command}') || exit 0
if [ "$command" = hax ]; then
	tmux set-option -w -t "$pane" @hax_window 1
else
	tmux set-option -w -u -t "$pane" @hax_window
fi
