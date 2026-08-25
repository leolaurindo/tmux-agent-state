#!/usr/bin/env bash

highlight='#{?@hax_window,#{?window_bell_flag,#{?@hax_idle_style,#[#{E:@hax_idle_style}],},},}'

for option in window-status-format window-status-current-format; do
	format=$(tmux show-option -gv "$option")

	case "$format" in
		*@hax_window*|*window_bell_flag*) continue ;;
	esac

	format=${format/\#W/$highlight#W}
	tmux set-option -g "$option" "$format"
done
