#!/usr/bin/env bash

set -u

if [ "${1-}" = "--pane" ]; then
	shift
	pane=${1-}
	shift
	bell_script=${1-}
	[ -n "$pane" ] && [ -n "$bell_script" ] || exit 0

	quoted_script=$(printf '%q' "$bell_script")
	hook="run-shell -b 'bash $quoted_script #{hook_pane}'"
	tmux set-hook -p -t "$pane" 'pane-bell[hax-agent-state]' "$hook"
	exit 0
fi

bell_script=${1-}
[ -n "$bell_script" ] || exit 0

quoted_script=$(printf '%q' "$bell_script")
quoted_installer=$(printf '%q' "$0")
created_hook="run-shell -b 'bash $quoted_installer --pane #{hook_pane} $quoted_script'"
tmux set-hook -g 'pane-created[hax-agent-state]' "$created_hook"

while IFS= read -r pane; do
	[ -n "$pane" ] || continue
	bash "$0" --pane "$pane" "$bell_script"
done < <(tmux list-panes -a -F '#{pane_id}')
