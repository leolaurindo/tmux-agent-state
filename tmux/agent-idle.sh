#!/usr/bin/env bash

highlight='#{?@agent_window,#{?#{==:#{@agent_highlight_when},idle},#{?@agent_running,,#[fg=#{@agent_accent}]},#{?@agent_running,#[fg=#{@agent_accent}],}},}'

for option in window-status-format window-status-current-format; do
	format=$(tmux show-option -gv "$option")
	case "$format" in
		*@agent_running*) continue ;;
	esac

	format=${format/\#W/$highlight#W}
	tmux set-option -g "$option" "$format"
done
