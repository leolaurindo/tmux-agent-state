#!/usr/bin/env bash

highlight='#{?@agent_window,#{?@agent_running,#{?@agent_running_style,#[#{E:@agent_running_style}],},#{?@agent_idle_style,#[#{E:@agent_idle_style}],}},}'

for option in window-status-format window-status-current-format; do
	format=$(tmux show-option -gv "$option")

	case "$format" in
		*@agent_running_style*|*@agent_idle_style*) continue ;;
	esac

	format=${format/\#W/$highlight#W}
	tmux set-option -g "$option" "$format"
done
