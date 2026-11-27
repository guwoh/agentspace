#!/usr/bin/env python3
"""AgentSpace companion GUI for a separately installed DevSpace server.
Adapted from the local DevSpace GUI; configuration schema tested with 1.0.8.
No server, credentials, tunnel configuration or personal paths are bundled.
"""
import argparse
from hashlib import sha256
import json
import os
import queue
import re
import subprocess
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font, messagebox, ttk
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import webbrowser

CONFIG = Path.home() / ".devspace/config.json"
CLIENTS = {
    "ChatGPT": (
        "https://chatgpt.com/plugins",
        "Trong Plugins, chọn + → Add custom MCP server, dán URL và chọn OAuth.",
    ),
    "Claude": (
        "https://claude.ai/customize/connectors",
        "Trong Customize → Connectors, chọn Add → Custom → Web, dán URL và tiếp tục xác thực.",
    ),
}
SERVICE = ["systemctl", "--user"]
MCP_HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
INITIALIZE = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
    "protocolVersion": "2025-03-26", "capabilities": {},
    "clientInfo": {"name": "DevSpace GUI", "version": "1.0"},
}}


def read_config(path):
    config = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("Cấu hình DevSpace phải là một JSON object.")
    workspace = config.get("workspaces", {})
    if not isinstance(workspace, dict) or (
        "allowedRoots" in workspace and (
            not isinstance(workspace["allowedRoots"], list)
            or any(not isinstance(root, str) for root in workspace["allowedRoots"])
        )
    ):
        raise ValueError("Không đọc được workspaces.allowedRoots.")
    return config


def read_owner_password(path):
    try:
        auth = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ValueError("Không đọc được auth.json của DevSpace.") from None
    password = auth.get("ownerToken") if isinstance(auth, dict) else None
    if not isinstance(password, str) or not password.strip():
        raise ValueError("Không tìm thấy Owner password trong auth.json.")
    return password


def normalize_url(raw):
    value = raw.strip().rstrip("/")
    if not value:
        return ""
    url = urlsplit(value)
    if (url.scheme != "https" or not url.hostname or url.username is not None
            or url.password is not None or url.query or url.fragment
            or url.path not in ("", "/mcp") or re.search(r"[\s\\]", value)):
        raise ValueError("Nhập URL HTTPS của DevSpace. Có thể dán kèm /mcp.")
    _ = url.port
    return f"https://{url.netloc}"


def atomic_write(path, payload, mode=0o600):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as out:
            temporary = Path(out.name)
            if os.name != "nt":
                os.fchmod(out.fileno(), mode)
            out.write(payload)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def save_config(path, base, roots, original):
    if path.is_symlink():
        raise ValueError("Hãy dùng đường dẫn đến file cấu hình thực.")
    current = path.read_bytes()
    if current != original:
        raise ValueError("Cấu hình vừa thay đổi bên ngoài. Bấm Nạp lại trước khi lưu.")
    config = read_config(path)
    config["publicBaseUrl"] = normalize_url(base) or None
    if roots is not None:
        if not roots:
            raise ValueError("Hãy chọn ít nhất một thư mục.")
        paths = [Path(root).expanduser().resolve(strict=True) for root in roots]
        if any(not item.is_dir() for item in paths):
            raise ValueError("Mỗi đường dẫn phải là thư mục hiện có.")
        config.setdefault("workspaces", {})["allowedRoots"] = list(dict.fromkeys(map(str, paths)))
    backup = path.with_name(path.name + ".gui-backup")
    atomic_write(backup, current)
    atomic_write(path, (json.dumps(config, ensure_ascii=False, indent=2) + "\n").encode(), 0o600)
    return path.read_bytes()


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def probe(endpoint):
    request = Request(endpoint, json.dumps(INITIALIZE).encode(), MCP_HEADERS)
    try:
        with build_opener(NoRedirect()).open(request, timeout=4) as response:
            content_type = response.headers.get_content_type()
            if content_type not in ("application/json", "text/event-stream"):
                return f"HTTP {response.status}, nội dung trả về không phải MCP."
            return f"HTTP {response.status} · endpoint phản hồi ({content_type})."
    except HTTPError as exc:
        challenge = exc.headers.get("WWW-Authenticate", "")
        if 300 <= exc.code < 400:
            return "Endpoint chuyển hướng. Kiểm tra lại URL."
        if exc.code == 401 and ("resource_metadata" in challenge or challenge.lower().startswith("bearer")):
            return "HTTP 401 · endpoint yêu cầu OAuth/Bearer."
        return f"HTTP {exc.code} · chưa xác nhận được kết nối MCP."
    except (URLError, TimeoutError, ValueError):
        return "Không nhận được phản hồi trong thời gian kiểm tra."


def service_action(action):
    result = subprocess.run([*SERVICE, action, "devspace.service"], capture_output=True,
                            text=True, timeout=20)
    if result.returncode:
        raise ValueError(f"systemd không hoàn thành thao tác {action}. Kiểm tra dịch vụ devspace.service.")


def status(config, base):
    try:
        state = subprocess.run([*SERVICE, "is-active", "devspace.service"], capture_output=True,
                               text=True, timeout=4).stdout.strip() or "không xác định"
    except (OSError, subprocess.SubprocessError):
        state = "manual / systemd unavailable"
    port = config.get("port", 7676)
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("Cổng trong file cấu hình không hợp lệ.")
    local = probe(f"http://127.0.0.1:{port}/mcp")
    public = probe(base + "/mcp") if base else "Chưa có URL HTTPS."
    return f"Dịch vụ  {state}\nMáy này  {local}\nHTTPS    {public}"


class App:
    def __init__(self, root, path):
        self.root, self.path = root, path
        self.busy = False
        self.events = queue.Queue()
        self.config, self.original = {}, None
        self.roots_changed = False
        root.title("DevSpace · Kết nối AI")
        root.geometry(f"{min(800, root.winfo_screenwidth()-60)}x{min(630, root.winfo_screenheight()-105)}")
        root.minsize(450, 400)
        root.configure(bg="#eef3f5")
        self.action_rows = []
        self.layout_size = None
        self.zoom_offset = 0
        self.password_timer = None
        self.password_fingerprint = None
        self.poll_timer = None
        root.bind("<Destroy>", self.on_destroy, add="+")
        self.fonts = {
            "body": font.Font(root, family="Sans", size=15),
            "section": font.Font(root, family="Sans", size=16, weight="bold"),
            "title": font.Font(root, family="Sans", size=30, weight="bold"),
        }
        theme = self.theme = ttk.Style(root)
        theme.theme_use("clam")
        theme.configure(".", font=self.fonts["body"])
        theme.configure("TFrame", background="#eef3f5")
        theme.configure("TLabel", background="#eef3f5", foreground="#172b35")
        theme.configure("TButton", font=self.fonts["body"], padding=(10, 6))
        theme.configure("TEntry", padding=(5, 5))
        theme.configure("TCombobox", padding=(5, 4))
        root.option_add("*TCombobox*Listbox.font", str(self.fonts["body"]))
        theme.configure("Accent.TButton", background="#0d675f", foreground="white")
        theme.map("Accent.TButton", background=[("active", "#14776b")])

        surface = ttk.Frame(root)
        surface.pack(fill="both", expand=True)
        surface.columnconfigure(0, weight=1)
        surface.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(surface, bg="#eef3f5", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar = ttk.Scrollbar(surface, command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        body = self.body = ttk.Frame(self.canvas, padding=20)
        self.body_item = self.canvas.create_window(0, 0, window=body, anchor="n")
        self.canvas.bind("<Configure>", lambda event: self.layout(event.width, event.height))
        body.bind("<Configure>", self.update_scroll_region)
        root.bind("<Button-4>", lambda event: self.scroll(event, -3))
        root.bind("<Button-5>", lambda event: self.scroll(event, 3))
        root.bind("<MouseWheel>", lambda event: self.scroll(event, -3 if event.delta > 0 else 3))

        ttk.Label(body, text="DevSpace", font=self.fonts["title"]).pack(anchor="w")
        ttk.Label(body, text="Kết nối AI với thư mục dự án trên máy").pack(anchor="w", pady=(0, 5))
        self.action_row(body, [
            ("Cỡ chữ −", lambda: self.zoom(-2)),
            ("Cỡ chữ +", lambda: self.zoom(2)),
            ("Tự động", lambda: self.zoom()),
        ], gap=(0, 12))
        for key, change in (("plus", 2), ("equal", 2), ("minus", -2), ("0", None)):
            root.bind(f"<Control-{key}>", lambda event, delta=change: self.zoom(delta))
        ttk.Label(body, text="URL HTTPS của DevSpace", font=self.fonts["section"]).pack(anchor="w")
        self.base = tk.StringVar()
        ttk.Entry(body, textvariable=self.base, font=self.fonts["body"]).pack(fill="x", pady=(4, 8))
        client_row = ttk.Frame(body)
        client_row.pack(fill="x", pady=(0, 5))
        ttk.Label(client_row, text="Ứng dụng AI").pack(side="left", padx=(0, 10))
        self.client = tk.StringVar(value="ChatGPT")
        ttk.Combobox(client_row, textvariable=self.client, values=tuple(CLIENTS),
                     state="readonly", width=12, font=self.fonts["body"]).pack(side="left")
        self.action_row(body, [
            ("Kiểm tra kết nối", self.check),
            ("Sao chép URL MCP", self.copy),
            ("Mở thiết lập", self.connect, "Accent.TButton"),
        ])
        self.client_hint = ttk.Label(body, text=CLIENTS["ChatGPT"][1], justify="left")
        self.client_hint.pack(anchor="w", pady=(4, 5))
        self.action_row(body, [("Sao chép mật khẩu", self.copy_owner_password)], gap=(0, 12))
        self.client.trace_add("write", lambda *_: self.client_hint.configure(text=CLIENTS[self.client.get()][1]))
        ttk.Label(body, text="Thư mục được phép", font=self.fonts["section"]).pack(anchor="w")
        list_frame = ttk.Frame(body)
        list_frame.pack(fill="x", pady=(5, 5))
        self.list = tk.Listbox(list_frame, height=4, selectmode="extended", relief="flat",
                               font=self.fonts["body"], bg="white", fg="#172b35",
                               selectbackground="#0d675f")
        self.list.grid(row=0, column=0, sticky="ew")
        list_frame.columnconfigure(0, weight=1)
        scroll_y = ttk.Scrollbar(list_frame, command=self.list.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x = ttk.Scrollbar(list_frame, orient="horizontal", command=self.list.xview)
        scroll_x.grid(row=1, column=0, sticky="ew")
        self.list.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.root_hint = ttk.Label(body, justify="left")
        self.root_hint.pack(anchor="w")
        self.action_row(body, [
            ("Thêm thư mục…", self.add),
            ("Bỏ mục đã chọn", self.remove),
            ("Nạp lại", self.load),
        ], gap=(5, 9))
        self.action_row(body, [
            ("Lưu cấu hình", self.save, "Accent.TButton"),
            ("Khởi động lại (systemd)", self.restart),
        ])
        self.action_row(body, [("Hướng dẫn cài đặt", lambda: webbrowser.open("https://github.com/guwoh/agentspace/blob/main/docs/DEVSPACE.md"))])
        self.result = tk.StringVar(value="Sẵn sàng.")
        self.status_label = ttk.Label(body, textvariable=self.result, justify="left")
        self.status_label.pack(anchor="w", pady=(8, 0))
        self.load()
        self.poll_timer = root.after(80, self.poll)

    def action_row(self, parent, actions, gap=(0, 0)):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=gap)
        buttons = [ttk.Button(row, text=label, command=action,
                              style=styles[0] if styles else "TButton")
                   for label, action, *styles in actions]
        self.action_rows.append(buttons)

    def zoom(self, delta=None):
        self.zoom_offset = 0 if delta is None else min(10, max(-6, self.zoom_offset + delta))
        self.layout(self.canvas.winfo_width(), self.canvas.winfo_height())
        return "break"

    def layout(self, window_width, window_height):
        width = min(1120, window_width - 16, max(530, int(window_width * 0.82)))
        if width < 40:
            return
        automatic = min(22, max(15, round(window_width / 142 + 8)))
        size = min(30, max(12, automatic + self.zoom_offset))
        rows = min(7, max(3, (window_height - 380) // 112))
        key = width, size, rows
        self.canvas.coords(self.body_item, window_width // 2, 0)
        if self.layout_size == key:
            return
        self.layout_size = key
        self.canvas.itemconfigure(self.body_item, width=width)
        self.fonts["body"].configure(size=size)
        self.fonts["section"].configure(size=size + 1)
        self.fonts["title"].configure(size=size + 15)
        self.list.configure(height=rows)
        available = width - 40
        for label in (self.client_hint, self.root_hint, self.status_label):
            label.configure(wraplength=available)
        self.body.update_idletasks()
        for buttons in self.action_rows:
            fits = sum(button.winfo_reqwidth() + 8 for button in buttons) <= available
            for index, button in enumerate(buttons):
                button.grid(row=0 if fits else index, column=index if fits else 0,
                            sticky="w", padx=(0, 8), pady=(0, 4))

    def update_scroll_region(self, _event):
        self.canvas.configure(scrollregion=(0, 0, self.canvas.winfo_width(), self.body.winfo_height()))

    def scroll(self, event, delta):
        if event.widget == self.list or self.body.winfo_height() <= self.canvas.winfo_height():
            return
        self.canvas.yview_scroll(delta, "units")

    def load(self):
        try:
            self.config = read_config(self.path)
            self.original = self.path.read_bytes()
        except (OSError, ValueError):
            self.original = None
            self.config = {}
            self.base.set("")
            self.list.delete(0, "end")
            self.roots_changed = False
            self.result.set("Chưa có cấu hình hợp lệ. Chạy devspace init trong terminal, rồi bấm Nạp lại. Xem hướng dẫn AgentSpace.")
            return
        self.base.set(self.config.get("publicBaseUrl") or "")
        roots = self.config.get("workspaces", {}).get("allowedRoots")
        self.list.delete(0, "end")
        for item in roots or []:
            self.list.insert("end", item)
        self.roots_changed = False
        self.root_hint.configure(text="Đang dùng thư mục mặc định của dịch vụ. Thêm thư mục để đặt danh sách riêng."
                                 if roots is None else "Chỉ cấp quyền cho thư mục cần dùng với AI. Đây không phải sandbox cho lệnh shell.")
        self.result.set("Đã nạp cấu hình.")

    def add(self):
        folder = filedialog.askdirectory(mustexist=True)
        if folder and folder not in self.list.get(0, "end"):
            self.list.insert("end", folder)
            self.roots_changed = True
            self.root_hint.configure(text="Danh sách này sẽ thay thế phạm vi mặc định khi lưu.")

    def remove(self):
        for index in reversed(self.list.curselection()):
            self.list.delete(index)
            self.roots_changed = True

    def copy(self):
        try:
            base = normalize_url(self.base.get())
            if not base:
                raise ValueError("Nhập URL HTTPS trước khi sao chép.")
            self.root.clipboard_clear()
            self.root.clipboard_append(base + "/mcp")
            self.result.set("Đã sao chép URL MCP.")
            return True
        except ValueError as exc:
            messagebox.showerror("URL MCP", str(exc))
            return False

    def copy_owner_password(self):
        if not messagebox.askokcancel("Owner password", "Chỉ dán vào trang xác thực DevSpace chính thức. Clipboard có thể được lưu bởi clipboard manager. Tiếp tục?"):
            return
        try:
            password = read_owner_password(self.path.with_name("auth.json"))
            self.root.clipboard_clear()
            self.root.clipboard_append(password)
        except (ValueError, tk.TclError) as exc:
            message = str(exc) if isinstance(exc, ValueError) else "Không truy cập được clipboard."
            messagebox.showerror("Owner password", message)
            return
        if self.password_timer is not None:
            self.root.after_cancel(self.password_timer)
        fingerprint = sha256(password.encode()).digest()
        self.password_fingerprint = fingerprint
        self.password_timer = self.root.after(60000, self.clear_owner_password, fingerprint)
        self.result.set("Đã sao chép Owner password. Dán vào trang DevSpace trong 60 giây.")

    def clear_owner_password(self, fingerprint):
        self.password_timer = None
        self.password_fingerprint = None
        try:
            current = self.root.clipboard_get()
            if sha256(current.encode()).digest() == fingerprint:
                self.root.clipboard_clear()
        except tk.TclError:
            pass

    def connect(self):
        if self.copy():
            webbrowser.open(CLIENTS[self.client.get()][0])

    def save(self):
        try:
            if self.original is None:
                raise ValueError("Hãy nạp cấu hình hợp lệ trước khi lưu.")
            if not messagebox.askokcancel("Save configuration", "Lưu cấu hình DevSpace? Thay đổi URL có thể ảnh hưởng kết nối hiện tại."):
                return
            if self.roots_changed and not messagebox.askokcancel(
                "Lưu danh sách thư mục", "Danh sách mới sẽ thay thế phạm vi đang dùng. Tiếp tục?"):
                return
            roots = list(self.list.get(0, "end")) if self.roots_changed else None
            self.original = save_config(self.path, self.base.get(), roots, self.original)
            self.load()
            self.result.set("Đã lưu và tạo bản sao lưu. Bấm khởi động lại để dịch vụ áp dụng thay đổi.")
        except (OSError, ValueError) as exc:
            messagebox.showerror("Không lưu được", str(exc))

    def background(self, message, task):
        if self.busy:
            return
        self.busy = True
        self.result.set(message)
        def run():
            try:
                self.events.put(task())
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                self.events.put(str(exc))
        threading.Thread(target=run, daemon=True).start()

    def check(self):
        try:
            base = normalize_url(self.base.get())
        except ValueError as exc:
            messagebox.showerror("URL MCP", str(exc))
            return
        config = self.config.copy()
        self.background("Đang kiểm tra dịch vụ và endpoint…", lambda: status(config, base))

    def restart(self):
        if self.busy or not messagebox.askokcancel(
                "Khởi động lại", "Các phiên DevSpace đang dùng có thể bị ngắt trong chốc lát. Tiếp tục?"):
            return
        def task():
            service_action("restart")
            return "Đã khởi động lại DevSpace. Bấm Kiểm tra kết nối để xem trạng thái."
        self.background("Đang khởi động lại…", task)

    def poll(self):
        try:
            result = self.events.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            self.result.set(result)
        self.poll_timer = self.root.after(80, self.poll)

    def on_destroy(self, event):
        if event.widget != self.root:
            return
        for timer in (self.poll_timer, self.password_timer):
            if timer is not None:
                try:
                    self.root.after_cancel(timer)
                except tk.TclError:
                    pass
        if self.password_fingerprint is not None:
            self.clear_owner_password(self.password_fingerprint)


def smoke_ui():
    # Disposable configuration only. No server, tunnel or credentials are touched.
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "config.json"
        path.write_text(json.dumps({"publicBaseUrl": "https://service.example.com",
                                   "workspaces": {"allowedRoots": [folder]}}), encoding="utf-8")
        root = tk.Tk()
        try:
            app = App(root, path)
            root.update()
            assert app.copy()
            assert root.clipboard_get() == "https://service.example.com/mcp"
            app.client.set("Claude")
            root.update()
            assert "Connectors" in app.client_hint.cget("text")
            app.path = path.with_name("missing.json")
            app.load()
            assert app.original is None and app.base.get() == ""
        finally:
            root.destroy()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--smoke-ui", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        config = read_config(args.config)
        print(status(config, normalize_url(config.get("publicBaseUrl") or "")))
        return
    if args.smoke_ui:
        return smoke_ui()
    root = tk.Tk()
    App(root, args.config)
    root.mainloop()


if __name__ == "__main__":
    main()
