# Using AgentSpace with DevSpace
DevSpace is a separate self-hosted MCP tool server. It gives an AI host file and command tools; AgentSpace supplies the handoff convention.

## Setup
Consult [upstream installation](https://github.com/Waishnav/devspace#installation) for current prerequisites and platform support. For an existing compatible Node installation:

```bash
npm install -g @waishnav/devspace
devspace init
```

Choose ChatGPT/MCP-host use. Configure allowed roots for your private AgentSpace folder and selected projects. Configure your own HTTPS tunnel/reverse proxy to the local server (default port 7676).

```bash
devspace serve
devspace doctor
```

Connect the host to your public endpoint, for example:
```text
https://service.example.com/mcp
```

Approve the connection using your Owner password. Never include it in a prompt or repository. Host connector availability and UI depend on your account/client.

## Start work
Send [the startup prompt](../prompts/START.txt) with your private root substituted. Ask the AI to read the index, select a project, and restore its handoff. Reuse the workspace handle returned by DevSpace.

## Boundaries
The machine, server, and tunnel must remain reachable. File content returned to a cloud AI can enter its conversation. Shell tools have local-user authority; allowed roots alone are not a shell sandbox.

[Upstream README](https://github.com/Waishnav/devspace), checked 2026-11-10. AgentSpace bundles no DevSpace code.
