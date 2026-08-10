Implement a minimal tmux busy indicator for Pi and OpenCode.

Goal:

* No sidebars, wrappers, daemons, polling, or screen scraping. No clown fiesta in my screen.
* Keep normal tmux footer/window list.
* When Pi or OpenCode is actively running a task, change that tmux window name to a different color. Use, preferrably, a theme related accent.
* When the agent is done and waiting for input, restore the normal color.
* Alternatively, the opposite should be configurable too: make it change color when idle, and move to normal when running. Thus should be true only for windows with pi and opencode.
Implementation:
* If possible, expand this to sessions too. 
* Use a tmux window option like `@agent_running`.
* Agent starts working:
  `tmux set-option -w @agent_running 1`
* Agent settles/returns to waiting:
  `tmux set-option -w -u @agent_running`
* Modify existing `window-status-format` and `window-status-current-format` so `@agent_running=1` changes only the window-name color while preserving the current tmux theme.

Pi:

* Add a tiny Pi extension.
* Use lifecycle events, ideally `agent_start` to set running and `agent_settled` to clear it.
* Verify exact event/API names against the installed Pi version.

OpenCode:

* Add a tiny OpenCode plugin.
* Use its session lifecycle/status events.
* Set running when the session is actually busy.
* Clear it on `session.idle`.
* Verify the actual status payload against the installed OpenCode version.

Requirements:

* Works when I switch to another tmux window.
* Multiple agent windows can be highlighted independently.
* Safely does nothing outside tmux.
* Keep the code as small as possible.

Show me the exact files/config changes and commands to reload them.

Deliverable:
* A tiny, organized repo (this one) with all necessary to configure.
* A nice document teaching how to setup, with non destructive/invasive installation scripts if needed, otherwise only guide through instructions.
