# Connect AgentSpace to DevSpace

[Tiếng Việt](DEVSPACE.vi.md) · [Desktop guide](DESKTOP.md) · [DevSpace upstream setup](https://github.com/Waishnav/devspace/blob/main/docs/setup.md)

AgentSpace manages project context and prompts. DevSpace is an independent self-hosted MCP server providing authorized file and command tools on your computer. The included DevSpace GUI is a companion configuration panel, not the server itself. It was adapted from our local panel for DevSpace 1.0.8; newer server schemas and non-Linux platforms require verification.

## 1. Prepare the computer

Install Git, Bash, Python 3.8+ with Tkinter, and a Node/npm version supported by DevSpace. The current upstream setup guide specifies Node >=22.19 and <27. On Ubuntu, use your distribution's Python Tk package if needed. Check current upstream requirements before installation. For Windows, consult upstream Bash/Git Bash/WSL setup; the companion GUI's systemd restart control is Linux-specific.

From the AgentSpace checkout:

```bash
python3 scripts/agentspace.py init ~/work/agentspace-private
python3 -B scripts/desktop.py --workspace ~/work/agentspace-private
npm install -g @waishnav/devspace
devspace init
devspace doctor
```

In DevSpace setup, select use with an MCP host. Allow only the private AgentSpace directory and project directories actually needed; avoid granting an entire home directory. Do not change an existing setup unless necessary. Never run this server as root.

## 2. Prepare an HTTPS endpoint

DevSpace needs a reachable HTTPS endpoint for remote cloud clients. Set up a tunnel you control using the provider's official instructions: [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/), [Tailscale Funnel](https://tailscale.com/kb/1223/funnel) or another suitable HTTPS reverse proxy. Forward to the configured local port (usually 7676), not an unrelated service. Do not disable authentication. AgentSpace does not create tunnels, DNS records or firewall rules. A temporary tunnel URL may change after restarting.

Start the server in a terminal with `devspace serve` (if already running, do not start a second copy). Keep the terminal/server and tunnel running. Use `devspace doctor` for diagnostics. For a preconfigured Linux user service only, use `systemctl --user status devspace.service`. The companion does not install a systemd unit. If you use a foreground server, restart it manually after saving changes. Do not restart a service during active work without permission.

## 3. Configure using the GUI

In AgentSpace, open **Connect → Open DevSpace GUI**, or run:

```bash
python3 -B scripts/devspace_gui.py
```

The GUI reads the installed DevSpace configuration locally (normally `~/.devspace/config.json`). If missing, finish `devspace init` and reload. Labels in this initial companion are Vietnamese.

| Control | Action |
|---|---|
| URL HTTPS | Enter your HTTPS base URL or the full endpoint ending in /mcp. |
| Thêm thư mục / Bỏ mục đã chọn | Add/remove permitted existing project directories. |
| Lưu cấu hình | Confirm saving. A local config backup is created; do not share it. |
| Nạp lại | Reload the file if it changed externally. |
| Khởi động lại (systemd) | Restart an existing Linux user service, only after confirmation. |
| Kiểm tra kết nối | Probe local and HTTPS endpoints. HTTP 401 with a Bearer/OAuth challenge can be expected before authentication. |
| Sao chép URL MCP | Copy the endpoint, e.g. `https://service.example.com/mcp`. |
| Mở thiết lập | Select ChatGPT or Claude, copy endpoint, open the host's connector page. |
| Sao chép mật khẩu | Optional explicit copy of local Owner password, for the genuine approval page only. |

A probe is not an authenticated session test. Copying the password does not send it to AI, and the GUI attempts to clear its clipboard copy after 60 seconds while it remains running; clipboard history/sync can retain it. Prefer entering the password directly on the verified approval page. Never paste it into chat, a prompt, a screenshot or Git.

## 4. Connect ChatGPT or Claude

Use the desktop web interface first, where your account supports custom remote MCP connectors. In the host's plugin/app/connector settings, add a custom MCP server using the copied URL and OAuth if offered. In Claude, use Settings/Customize → Connectors → Add custom connector; names and availability vary. Follow the DevSpace Owner approval page only after verifying its domain is your configured endpoint. Check the scopes and enable only the needed tools. For current details see [upstream setup](https://github.com/Waishnav/devspace/blob/main/docs/setup.md). Connector and account eligibility may differ; do not assume all mobile or free accounts support it.

## 5. First safe remote task

In the AgentSpace desktop app, select a project and copy a Resume prompt, or use [the startup prompt](../prompts/START.txt) with the private root substituted. Send it in a chat with DevSpace enabled. Ask it to read AGENTS.md, the selected project's brief, and the relevant feature map only; report what it can access, without editing. Confirm the response from real files. For a first test, use a disposable project, not sensitive data. The temporary Try demo workspace exists only while the desktop app is running.

When finished, explicitly ask to save context. In a new authorized chat, send the resume prompt again; no automatic migration of unsaved chats is implied.

## 6. Work from your phone

Keep the laptop awake, connected and running the server/tunnel. Configure the connector on a supported web client first. Open a chat from your phone under the authorized account and enable the connector if available on that client. Ask for a read-only status check before editing files. If the connector is absent or the client does not support custom MCP, use a supported web client instead. AgentSpace Desktop itself runs on the laptop; this setup does not install an Android app or grant remote desktop control.

## Troubleshooting and safety

- Missing command: check Node/npm PATH and upstream install; desktop launchers may not inherit shell PATH.
- Local endpoint down: check `devspace doctor`, server and configured port.
- Public endpoint down: check tunnel/HTTPS and target port. If URL changes, update DevSpace config and reconnect the host; do not bypass OAuth.
- OAuth callback failure: confirm the exact public base URL matches the active tunnel; remove/re-add a stale connector if needed.
- Workspace denied: confirm the intended allowed roots and project path; never broaden all permissions just to fix a connection.
- Read-only test succeeds but commands fail: verify the enabled tool set, host policy and shell environment.
- When done, disconnect/revoke unwanted clients and stop public exposure when no longer needed. Shell tools run with local-user authority; allowed roots are not a shell sandbox. Cloud AI can receive file contents through tool results. Keep credentials and live configuration outside the public repository.

Upstream: [Waishnav/devspace](https://github.com/Waishnav/devspace). AgentSpace distributes only its companion GUI; the DevSpace server is installed separately. Setup tested locally with server 1.0.8 configuration shape; real cross-account and mobile end-to-end verification remain user acceptance tasks.
