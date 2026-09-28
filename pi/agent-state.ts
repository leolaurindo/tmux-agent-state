import { spawnSync } from "node:child_process";

function paneTarget() {
  const pane = process.env.TMUX_PANE;
  return process.env.TMUX && pane ? pane : null;
}

function tmux(args: string[]) {
  const result = spawnSync("tmux", args, { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
  return result.status === 0 ? result.stdout?.toString() ?? "" : null;
}

function setOption(scope: string, option: string, value?: string) {
  const pane = paneTarget();
  if (!pane) return;

  const args = ["set-option", scope, "-t", pane];
  if (value === undefined) args.push("-u");
  args.push(option);
  if (value !== undefined) args.push(value);
  tmux(args);
}

function refreshWindow() {
  const pane = paneTarget();
  if (!pane) return;

  const states = tmux([
    "list-panes",
    "-t",
    pane,
    "-F",
    "#{?@agent_pane,1,0}#{?@agent_running_pane,1,0}",
  ]);
  if (states === null) return;
  const agents = states.split("\n").filter((line) => line[0] === "1");
  const hasAgent = agents.length > 0;
  const isRunning = hasAgent && agents.every((line) => line[1] === "1");
  setOption("-w", "@agent_window", hasAgent ? "1" : undefined);
  setOption("-w", "@agent_running", isRunning ? "1" : undefined);
}

function setPaneOption(option: string, value?: string) {
  setOption("-p", option, value);
}

export default function (pi: {
  on: (event: string, handler: () => void) => void;
  events: { on: (channel: string, handler: (data: unknown) => void) => () => void };
}) {
  setPaneOption("@agent_pane", "1");
  refreshWindow();
  pi.events.on("pi-permission-system:permission-request", (data) => {
    if (!data || typeof data !== "object" || !("state" in data)) return;
    setPaneOption("@agent_running_pane", data.state === "waiting" ? undefined : "1");
    refreshWindow();
  });
  pi.on("session_start", () => {
    setPaneOption("@agent_pane", "1");
    refreshWindow();
  });
  pi.on("agent_start", () => {
    setPaneOption("@agent_running_pane", "1");
    refreshWindow();
  });
  pi.on("agent_settled", () => {
    setPaneOption("@agent_running_pane");
    refreshWindow();
  });
  pi.on("session_shutdown", () => {
    setPaneOption("@agent_running_pane");
    setPaneOption("@agent_pane");
    refreshWindow();
  });
}
