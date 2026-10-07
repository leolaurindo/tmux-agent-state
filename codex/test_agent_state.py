"""Real title events on isolated tmux servers; never touches the user's panes."""

import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
import uuid

SCRIPT = Path(__file__).with_name("agent-state.py").resolve()
# A temporary executable named codex emits the same native OSC title messages.
TUI = "import sys\nfor title in sys.stdin: print(chr(27)+']0;'+title.strip()+chr(7),end='',flush=True)"


class AgentStateTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        executable = Path(directory.name) / "codex"
        executable.symlink_to(sys.executable)
        self.tui_command = shlex.join([str(executable), "-u", "-c", TUI])
        self.socket = "agent-state-test-" + uuid.uuid4().hex
        self.addCleanup(subprocess.run, ["tmux", "-L", self.socket, "kill-server"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.tmux("-f", "/dev/null", "new-session", "-d", "-s", "test", self.tui_command)
        self.pane = self.tmux("display-message", "-p", "#{pane_id}")
        self.env = dict(os.environ, TMUX=self.tmux("display-message", "-p", "#{socket_path},#{pid},0"), TMUX_PANE=self.pane)
        self.wait_for(lambda: self.tmux("display-message", "-p", "#{pane_current_command}") == "codex")
        self.run_script("--install")

    def tmux(self, *args):
        return subprocess.check_output(["tmux", "-L", self.socket, *args], text=True).strip()

    def run_script(self, *args):
        subprocess.run(["python3", str(SCRIPT), *args], env=self.env, check=True, timeout=5)

    def option(self, scope, name, pane=None):
        return self.tmux("show-options", scope, "-v", "-q", "-t", pane or self.pane, name)

    def wait_for(self, predicate):
        deadline = time.monotonic() + 3
        while not predicate():
            if time.monotonic() >= deadline:
                self.fail("tmux state did not update after a native title event")
            time.sleep(0.02)

    def title(self, text, state, pane=None):
        target = pane or self.pane
        self.tmux("send-keys", "-t", target, "-l", text)
        self.tmux("send-keys", "-t", target, "Enter")
        self.wait_for(lambda: self.tmux("display-message", "-p", "-t", target, "#{pane_title}") == text)
        self.wait_for(lambda: self.option("-p", "@codex_title_state", target) == state)

    def test_unrecognized_startup_title_waits_for_codex_title(self):
        self.assertEqual(self.option("-p", "@agent_pane"), "")
        self.title("codex | Ready project", "idle")
        self.wait_for(lambda: self.option("-p", "@agent_pane") == "1")
        self.assertEqual(self.option("-p", "@agent_running_pane"), "")
        self.assertEqual(self.option("-w", "@agent_window"), "1")

    def test_working_idle_and_action_required_from_actual_title_events(self):
        self.title("codex | Working ⠙ project", "working")
        self.wait_for(lambda: self.option("-w", "@agent_running") == "1")
        # Both phases of the blink must stay waiting, covering approvals and asks.
        self.title("[ ! ] Action Required | codex | project", "waiting")
        self.wait_for(lambda: self.option("-w", "@agent_running") == "")
        self.title("[ . ] Action Required | codex | project", "waiting")
        self.assertEqual(self.option("-w", "@agent_running"), "")
        self.title("codex | Thinking ⠹ project", "working")
        self.wait_for(lambda: self.option("-w", "@agent_running") == "1")
        self.title("codex | Ready project", "idle")
        self.wait_for(lambda: self.option("-w", "@agent_running") == "")

    def test_current_default_titles_and_spinner_only_changes(self):
        self.title("⠙ Existing conversation | project", "working")
        self.wait_for(lambda: self.option("-w", "@agent_running") == "1")
        self.title("⠏ Existing conversation | project", "working")
        self.title("Existing conversation | project", "idle")
        self.wait_for(lambda: self.option("-w", "@agent_running") == "")
        self.title("[ ! ] Action Required | Existing conversation | project", "waiting")
        self.wait_for(lambda: self.option("-w", "@agent_running") == "")

    def test_window_aggregates_codex_and_other_agents_but_ignores_shells(self):
        other = self.tmux("split-window", "-d", "-P", "-F", "#{pane_id}", "sleep 300")
        self.title("codex | Working ⠙ project", "working")
        self.wait_for(lambda: self.option("-w", "@agent_running") == "1")
        self.tmux("set-option", "-p", "-t", other, "@agent_pane", "1")
        self.run_script(self.pane)
        self.assertEqual(self.option("-w", "@agent_running"), "")
        self.tmux("set-option", "-p", "-t", other, "@agent_running_pane", "1")
        self.run_script(self.pane)
        self.assertEqual(self.option("-w", "@agent_running"), "1")
        self.title("[ ! ] Action Required | codex | project", "waiting")
        self.wait_for(lambda: self.option("-w", "@agent_running") == "")
        self.assertEqual(self.option("-p", "@agent_running_pane", other), "1")

    def test_exit_cleanup_runs_when_title_leaves_codex_without_state_change(self):
        self.title("codex | Ready project", "idle")
        self.tmux("select-pane", "-T", "shell", "-t", self.pane)
        self.tmux("respawn-pane", "-k", "-t", self.pane, "sleep 300")
        self.wait_for(lambda: self.option("-p", "@codex_managed") == "")
        self.wait_for(lambda: self.option("-w", "@agent_window") == "")

    def test_exit_title_event_resyncs_after_command_changes(self):
        self.title("codex | Working ⠙ project", "working")
        self.title("codex | Ready project", "idle")
        self.assertEqual(self.option("-p", "@codex_managed"), "1")
        self.tmux("respawn-pane", "-k", "-t", self.pane, "sleep 300")
        self.wait_for(lambda: self.option("-p", "@codex_managed") == "")
        self.wait_for(lambda: self.option("-w", "@agent_window") == "")
        self.assertEqual(self.option("-p", "@agent_pane"), "")

    def test_exit_clears_owned_state_and_cannot_mark_an_unrelated_process(self):
        self.title("codex | Working ⠙ project", "working")
        self.wait_for(lambda: self.option("-w", "@agent_running") == "1")
        shell_title = "import time; print(chr(27)+']0;shell'+chr(7),end='',flush=True); time.sleep(300)"
        self.tmux("respawn-pane", "-k", "-t", self.pane, shlex.join(["python3", "-u", "-c", shell_title]))
        self.wait_for(lambda: self.option("-p", "@codex_managed") == "")
        self.assertEqual(self.option("-p", "@agent_pane"), "")
        self.wait_for(lambda: self.option("-w", "@agent_window") == "")
        self.assertEqual(self.option("-w", "@agent_running"), "")
        self.run_script(self.pane)
        self.assertEqual(self.option("-p", "@agent_pane"), "")

    def test_unrelated_node_title_does_not_overwrite_another_agents_state(self):
        node = Path(self.tui_command.split()[0]).with_name("node")
        node.symlink_to(sys.executable)
        self.tmux("respawn-pane", "-k", "-t", self.pane, shlex.join([str(node), "-u", "-c", TUI]))
        self.wait_for(lambda: self.tmux("display-message", "-p", "#{pane_current_command}") == "node")
        self.run_script(self.pane)
        self.tmux("set-option", "-p", "-t", self.pane, "@agent_pane", "1")
        self.tmux("set-option", "-p", "-t", self.pane, "@agent_running_pane", "1")
        self.title("[ ! ] Action Required | codex | unrelated node", "waiting")
        self.assertEqual(self.option("-p", "@codex_managed"), "")
        self.assertEqual(self.option("-p", "@agent_running_pane"), "1")
        self.assertEqual(self.option("-p", "@agent_pane"), "1")

    def test_events_target_the_emitting_pane_not_the_daemon_environment(self):
        other = self.tmux("split-window", "-d", "-P", "-F", "#{pane_id}", self.tui_command)
        self.wait_for(lambda: self.tmux("display-message", "-p", "-t", other, "#{pane_current_command}") == "codex")
        self.title("codex | Working ⠙ first", "working")
        self.wait_for(lambda: self.option("-p", "@agent_running_pane") == "1")
        self.title("[ ! ] Action Required | codex | second", "waiting", other)
        self.wait_for(lambda: self.option("-p", "@codex_managed", other) == "1")
        self.assertEqual(self.option("-p", "@agent_running_pane"), "1")
        self.assertEqual(self.option("-p", "@agent_running_pane", other), "")


if __name__ == "__main__":
    unittest.main()
