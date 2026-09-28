function paneTarget() {
  const pane = process.env.TMUX_PANE;
  return process.env.TMUX && pane ? pane : null;
}

function setOption($, scope, option, value) {
  const pane = paneTarget();
  if (!pane) return Promise.resolve();

  if (value === undefined) {
    return $`tmux set-option ${scope} -u -t ${pane} ${option}`.quiet().nothrow();
  }
  return $`tmux set-option ${scope} -t ${pane} ${option} ${value}`.quiet().nothrow();
}

function setPaneOption($, option, value) {
  return setOption($, "-p", option, value);
}

function setWindowOption($, option, value) {
  return setOption($, "-w", option, value);
}

async function refreshWindow($) {
  const pane = paneTarget();
  if (!pane) return;

  const states = await $`tmux list-panes -t ${pane} -F '#{?@agent_pane,1,0}#{?@agent_running_pane,1,0}'`
    .quiet()
    .nothrow()
    .text();
  const agents = states.trim().split("\n").filter((line) => line[0] === "1");
  const hasAgent = agents.length > 0;
  const isRunning = hasAgent && agents.every((line) => line[1] === "1");
  await setWindowOption($, "@agent_window", hasAgent ? "1" : undefined);
  await setWindowOption($, "@agent_running", isRunning ? "1" : undefined);
}

export default async function ({ $ }) {
  await setPaneOption($, "@agent_pane", "1");
  await refreshWindow($);
  let activeSession;

  return {
    "chat.message": async (input) => {
      activeSession = input.sessionID;
    },

    event: async ({ event }) => {
      const sessionID = event.properties?.sessionID;
      if (!sessionID || sessionID !== activeSession) return;

      if (event.type === "session.status") {
        if (event.properties.status.type === "busy" || event.properties.status.type === "retry") {
          await setPaneOption($, "@agent_running_pane", "1");
          await refreshWindow($);
        } else if (event.properties.status.type === "idle") {
          await setPaneOption($, "@agent_running_pane");
          await refreshWindow($);
        }
      } else if (event.type === "session.idle") {
        await setPaneOption($, "@agent_running_pane");
        await refreshWindow($);
      } else if (event.type === "permission.updated") {
        await setPaneOption($, "@agent_running_pane");
        await refreshWindow($);
      } else if (event.type === "permission.replied") {
        await setPaneOption($, "@agent_running_pane", "1");
        await refreshWindow($);
      }
    },

    dispose: async () => {
      await setPaneOption($, "@agent_running_pane");
      await setPaneOption($, "@agent_pane");
      await refreshWindow($);
    },
  };
}
