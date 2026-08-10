function setWindowOption($, option, value) {
  const pane = process.env.TMUX_PANE;
  if (!process.env.TMUX || !pane) return Promise.resolve();

  if (value === undefined) {
    return $`tmux set-option -w -u -t ${pane} ${option}`.quiet().nothrow();
  }
  return $`tmux set-option -w -t ${pane} ${option} ${value}`.quiet().nothrow();
}

export default async function ({ $ }) {
  await setWindowOption($, "@agent_window", "1");
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
          await setWindowOption($, "@agent_running", "1");
        } else if (event.properties.status.type === "idle") {
          await setWindowOption($, "@agent_running");
        }
      } else if (event.type === "session.idle") {
        await setWindowOption($, "@agent_running");
      }
    },

    dispose: async () => {
      await setWindowOption($, "@agent_running");
      await setWindowOption($, "@agent_window");
    },
  };
}
