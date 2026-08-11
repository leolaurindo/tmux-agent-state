import { spawn } from "node:child_process";

function setWindowOption(option: string, value?: string) {
	const pane = process.env.TMUX_PANE;
	if (!process.env.TMUX || !pane) return;

	const args = ["set-option", "-w", "-t", pane];
	if (value === undefined) args.push("-u");
	args.push(option);
	if (value !== undefined) args.push(value);
	spawn("tmux", args, { stdio: "ignore" }).unref();
}

export default function (pi: { on: (event: string, handler: () => void) => void }) {
	setWindowOption("@agent_window", "1");
	pi.on("session_start", () => setWindowOption("@agent_window", "1"));
	pi.on("agent_start", () => setWindowOption("@agent_running", "1"));
	pi.on("agent_settled", () => setWindowOption("@agent_running"));
	pi.on("session_shutdown", () => {
		setWindowOption("@agent_running");
		setWindowOption("@agent_window");
	});
}
