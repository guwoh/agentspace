#!/usr/bin/env python3
"""AgentSpace Desktop: a local, file-based AI workspace."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, font
import webbrowser

from agentspace import initialize, verify
from desktop_core import (AI_LINKS, MODES, backup, make_prompt, project_files,
                          read_text, registry, restore, root_path, save_skill, skills)

VERSION = "0.2.0"


def open_folder(path):
    if sys.platform == "win32":
        os.startfile(str(path))
    else:
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(path)])


class Desktop:
    def __init__(self, window, initial_root=""):
        self.window = window
        self.root = tk.StringVar(value=initial_root)
        self.project_id = tk.StringVar()
        self.provider = tk.StringVar(value="ChatGPT")
        self.mode = tk.StringVar(value="Resume")
        self.new_root = tk.StringVar()
        self.status = tk.StringVar(value="Choose a private workspace to begin.")
        self.selected_file = None
        self.loaded_skill = None
        self.loaded_root = None
        self.projects = []
        self.skill_names = []
        self._setup_style()
        self._build()
        if initial_root:
            self.guard(self.refresh)

    def _setup_style(self):
        w = self.window
        w.title(f"AgentSpace Desktop · {VERSION}")
        w.geometry("1120x740")
        w.minsize(760, 500)
        w.configure(background="#eef2f6")
        style = ttk.Style(w)
        style.theme_use("clam")
        style.configure(".", font=("TkDefaultFont", 10), background="#eef2f6", foreground="#18273b")
        style.configure("TFrame", background="#eef2f6")
        style.configure("TNotebook", background="#eef2f6", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(14, 8))
        style.configure("TButton", padding=(10, 7))
        style.configure("Accent.TButton", background="#315fbd", foreground="white", padding=(12, 9))
        style.map("Accent.TButton", background=[("active", "#244b9a")])
        style.configure("Heading.TLabel", font=("TkDefaultFont", 17, "bold"))
        style.configure("Muted.TLabel", foreground="#52657b")
        style.configure("Treeview", rowheight=30, background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"))
        style.configure("TEntry", fieldbackground="white")
        style.configure("TCombobox", fieldbackground="white")
        self.text_widgets = []

    def guard(self, action):
        try:
            return action()
        except (OSError, ValueError, RuntimeError, tk.TclError) as exc:
            self.status.set("Operation not completed.")
            messagebox.showerror("AgentSpace", str(exc), parent=self.window)
        except Exception as exc:
            self.status.set("Operation not completed.")
            messagebox.showerror("AgentSpace", f"{type(exc).__name__}: {exc}", parent=self.window)

    def button(self, parent, label, callback, accent=False, **pack):
        widget = ttk.Button(parent, text=label, command=lambda: self.guard(callback),
                            style="Accent.TButton" if accent else "TButton")
        widget.pack(**pack)
        return widget

    def text_area(self, parent, readonly=False):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        widget = tk.Text(frame, wrap="word", undo=not readonly, font="TkFixedFont",
                         bg="white", fg="#18273b", insertbackground="#18273b",
                         padx=12, pady=10, relief="flat", borderwidth=0)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=widget.yview)
        widget.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        widget.pack(side="left", fill="both", expand=True)
        if readonly:
            widget.configure(state="disabled")
        self.text_widgets.append(widget)
        return widget

    def show_text(self, widget, content, readonly=True):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.configure(state="disabled" if readonly else "normal")

    def _build(self):
        top = ttk.Frame(self.window, padding=(18, 14))
        top.pack(fill="x")
        ttk.Label(top, text="AgentSpace", style="Heading.TLabel").pack(side="left")
        ttk.Label(top, text="  LOCAL WORKSPACE  /  AI HANDOFFS",
                  style="Muted.TLabel").pack(side="left", padx=8)
        self.button(top, "Open folder", self.open_workspace, side="right", padx=3)
        self.button(top, "Refresh", self.refresh, side="right", padx=3)
        bar = ttk.Frame(self.window, padding=(18, 0, 18, 12))
        bar.pack(fill="x")
        ttk.Label(bar, text="Workspace").pack(side="left", padx=(0, 8))
        ttk.Entry(bar, textvariable=self.root).pack(side="left", fill="x", expand=True)
        self.button(bar, "Browse", self.browse, side="left", padx=5)
        self.button(bar, "Initialize", self.init_workspace, side="left")
        tabs = self.tabs = ttk.Notebook(self.window)
        tabs.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        for label, builder in (("Projects", self.build_projects), ("Prompt studio", self.build_prompt),
                               ("Context & history", self.build_history), ("Skills", self.build_skills),
                               ("Connections", self.build_connections), ("Backup & settings", self.build_backup)):
            page = ttk.Frame(tabs, padding=14)
            tabs.add(page, text=label)
            builder(page)
        ttk.Label(self.window, textvariable=self.status, style="Muted.TLabel",
                  padding=(18, 5, 18, 12)).pack(fill="x")

    def build_projects(self, page):
        ttk.Label(page, text="Your projects", style="Heading.TLabel").pack(anchor="w")
        self.summary = ttk.Label(page, text="No workspace loaded.", style="Muted.TLabel")
        self.summary.pack(anchor="w", pady=(4, 14))
        columns = ("name", "session", "state")
        self.tree = ttk.Treeview(page, columns=columns, show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="Project ID")
        self.tree.column("#0", width=170, minwidth=100)
        for col, label, width in zip(columns, ("Name / scope", "Latest session", "Registry"),
                                     (230, 155, 100)):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, minwidth=80)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda _: self.guard(self.select_project))
        buttons = ttk.Frame(page)
        buttons.pack(fill="x", pady=(12, 0))
        self.button(buttons, "Start project", lambda: self.switch_prompt("Resume"), True, side="left", padx=(0, 6))
        self.button(buttons, "New project", self.new_project, side="left", padx=6)
        self.button(buttons, "Check context", self.check_context, side="left", padx=6)
        self.button(buttons, "View history", lambda: self.tabs.select(2), side="left", padx=6)

    def build_prompt(self, page):
        ttk.Label(page, text="Generate a prompt", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(page, text="Select a project and action. Copy the prompt into an authorized AI session.",
                  style="Muted.TLabel").pack(anchor="w", pady=(4, 12))
        row = ttk.Frame(page)
        row.pack(fill="x", pady=4)
        for label, var, values, width in (("Project ID", self.project_id, [], 24),
                                          ("AI", self.provider, list(AI_LINKS), 16),
                                          ("Action", self.mode, MODES, 20)):
            group = ttk.Frame(row)
            group.pack(side="left", fill="x", expand=True, padx=(0, 10))
            ttk.Label(group, text=label).pack(anchor="w")
            combo = ttk.Combobox(group, textvariable=var, values=values, width=width,
                                 state="normal" if var == self.project_id else "readonly")
            combo.pack(fill="x")
            combo.bind("<<ComboboxSelected>>", lambda _: self.guard(self.generate))
            if var == self.project_id:
                self.project_combo = combo
        new = ttk.Frame(page)
        new.pack(fill="x", pady=5)
        ttk.Label(new, text="Project root (new project only)").pack(side="left")
        ttk.Entry(new, textvariable=self.new_root).pack(side="left", fill="x", expand=True, padx=8)
        self.button(new, "Browse", self.browse_new_root, side="left")
        ttk.Label(page, text="Optional skills — select one or more in the Skills tab.",
                  style="Muted.TLabel").pack(anchor="w", pady=6)
        self.prompt_text = self.text_area(page, readonly=True)
        buttons = ttk.Frame(page)
        buttons.pack(fill="x", pady=(10, 0))
        self.button(buttons, "Generate & copy", self.copy_prompt, True, side="left", padx=(0, 6))
        self.button(buttons, "Generate preview", self.generate, side="left", padx=6)
        self.button(buttons, "Open selected AI", self.open_ai, side="left", padx=6)

    def build_history(self, page):
        ttk.Label(page, text="Context and session history", style="Heading.TLabel").pack(anchor="w", pady=(0, 12))
        paned = ttk.Panedwindow(page, orient="horizontal")
        paned.pack(fill="both", expand=True)
        left = ttk.Frame(paned)
        right = ttk.Frame(paned)
        paned.add(left, weight=1)
        paned.add(right, weight=4)
        self.history = tk.Listbox(left, exportselection=False, width=24, bg="white", relief="flat")
        self.history.pack(fill="both", expand=True)
        self.history.bind("<<ListboxSelect>>", lambda _: self.guard(self.view_history))
        self.context_text = self.text_area(right, readonly=True)
        ttk.Label(page, text="Saved snapshots are read-only here. Save through the AI workflow.",
                  style="Muted.TLabel").pack(anchor="w", pady=(10, 0))

    def build_skills(self, page):
        ttk.Label(page, text="Personal skills", style="Heading.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Label(page, text="Explicit selection adds skill file paths to generated prompts. No automatic execution.",
                  style="Muted.TLabel").pack(anchor="w", pady=(0, 12))
        paned = ttk.Panedwindow(page, orient="horizontal")
        paned.pack(fill="both", expand=True)
        left = ttk.Frame(paned)
        right = ttk.Frame(paned)
        paned.add(left, weight=1)
        paned.add(right, weight=4)
        self.skill_list = tk.Listbox(left, selectmode="extended", exportselection=False, bg="white", relief="flat")
        self.skill_list.pack(fill="both", expand=True)
        self.skill_list.bind("<Double-Button-1>", lambda _: self.guard(self.load_skill))
        self.skill_editor = self.text_area(right)
        self.skill_title = ttk.Label(right, text="No skill open.", style="Muted.TLabel")
        self.skill_title.pack(anchor="w", pady=5)
        buttons = ttk.Frame(page)
        buttons.pack(fill="x", pady=10)
        self.button(buttons, "Open selected", self.load_skill, side="left")
        self.button(buttons, "New skill", self.new_skill, side="left", padx=6)
        self.button(buttons, "Save skill", self.write_skill, True, side="left", padx=6)

    def build_connections(self, page):
        ttk.Label(page, text="AI connections", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(page, text="AgentSpace generates prompts locally. DevSpace or another authorized file tool provides access.",
                  style="Muted.TLabel", wraplength=690).pack(anchor="w", pady=(8, 18))
        for name in ("ChatGPT", "Claude", "Codex"):
            row = ttk.Frame(page, padding=(0, 6))
            row.pack(fill="x")
            ttk.Label(row, text=name, width=18).pack(side="left")
            self.button(row, "Open AI", lambda n=name: webbrowser.open(AI_LINKS[n]), side="left")
        self.button(page, "DevSpace setup guide",
                    lambda: webbrowser.open("https://github.com/Waishnav/devspace"), anchor="w", pady=10)
        self.button(page, "Check local DevSpace command", self.devspace_check, anchor="w")
        ttk.Label(page, text="A detected executable is not proof of an active MCP connection.\n"
                  "Connect and authenticate in your AI client; never paste credentials into prompts.",
                  style="Muted.TLabel", wraplength=690).pack(anchor="w", pady=12)

    def build_backup(self, page):
        ttk.Label(page, text="Backup and settings", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(page, text="Backups contain private Markdown context, protocol, skills and prompt files. "
                  "They are not encrypted and do not include project source or raw datasets.",
                  style="Muted.TLabel", wraplength=670).pack(anchor="w", pady=12)
        self.button(page, "Create private ZIP backup", self.create_backup, True, anchor="w", pady=4)
        self.button(page, "Restore into new folder", self.restore_backup, anchor="w", pady=4)
        ttk.Separator(page).pack(fill="x", pady=18)
        ttk.Label(page, text="Interface scale", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(page, text="Uses OS scaling at startup. Choose a font size for mixed-resolution displays.",
                  style="Muted.TLabel").pack(anchor="w", pady=8)
        scale = ttk.Frame(page)
        scale.pack(anchor="w")
        for size in (9, 10, 12, 14, 16):
            self.button(scale, str(size), lambda n=size: self.set_font(n), side="left", padx=3)
        ttk.Label(page, text=f"AgentSpace {VERSION} · Local files · MIT",
                  style="Muted.TLabel").pack(anchor="w", pady=20)

    def set_font(self, size):
        for name in ("TkDefaultFont", "TkTextFont", "TkFixedFont"):
            font.nametofont(name).configure(size=size)
        style = ttk.Style(self.window)
        style.configure(".", font=("TkDefaultFont", size))
        style.configure("Heading.TLabel", font=("TkDefaultFont", size + 7, "bold"))
        style.configure("Treeview", rowheight=max(30, int(size * 2.7)))
        style.configure("Treeview.Heading", font=("TkDefaultFont", size, "bold"))
        self.history.configure(font=("TkDefaultFont", size))
        self.skill_list.configure(font=("TkDefaultFont", size))
        self.status.set(f"Interface font size: {size} pt")

    def browse(self):
        chosen = filedialog.askdirectory(parent=self.window)
        if chosen:
            self.root.set(chosen)
            self.refresh()

    def browse_new_root(self):
        chosen = filedialog.askdirectory(parent=self.window)
        if chosen:
            self.new_root.set(chosen)

    def open_workspace(self):
        open_folder(root_path(self.root.get()))

    def init_workspace(self):
        chosen = self.root.get().strip()
        if not chosen:
            raise ValueError("Enter a private workspace path first.")
        if not messagebox.askyesno("Initialize", "Create missing starter files at this path? Existing files are preserved.",
                                   parent=self.window):
            return
        count, skipped = initialize(chosen)
        self.refresh()
        self.status.set(f"Initialized: {count} created, {skipped} existing files preserved.")

    def active_root(self):
        root = root_path(self.root.get())
        if self.loaded_root != root:
            raise ValueError("Workspace path changed. Click Refresh before using project actions.")
        return root

    def refresh(self):
        if not self.root.get().strip():
            raise ValueError("Choose a private workspace.")
        root = root_path(self.root.get())
        self.projects = registry(root)
        self.loaded_root = root
        self.tree.delete(*self.tree.get_children())
        for item in self.projects:
            self.tree.insert("", "end", iid=item["id"], text=item["id"],
                             values=(item["name"], item["session"],
                                     "Registered" if item["registered"] else "Folder only"))
        self.project_combo.configure(values=[p["id"] for p in self.projects])
        self.summary.configure(text=f"{len(self.projects)} projects · {root}")
        previous_skills = self.selected_skills()
        self.skill_names = skills(root)
        self.skill_list.delete(0, "end")
        for i, name in enumerate(self.skill_names):
            self.skill_list.insert("end", name)
            if name in previous_skills:
                self.skill_list.selection_set(i)
        # Never carry an editor buffer into a different workspace.
        self.loaded_skill = None
        self.show_text(self.skill_editor, "", readonly=False)
        self.skill_title.configure(text="No skill open.")
        if self.project_id.get() in self.tree.get_children():
            self.tree.selection_set(self.project_id.get())
        else:
            self.project_id.set("")
        self.refresh_history()
        self.show_text(self.prompt_text, "")
        self.status.set("Workspace refreshed. No context was changed.")

    def select_project(self):
        chosen = self.tree.selection()
        if chosen:
            self.project_id.set(chosen[0])
            self.refresh_history()

    def refresh_history(self):
        self.history.delete(0, "end")
        self.files = project_files(self.active_root(), self.project_id.get()) if self.project_id.get() else []
        for rel in self.files:
            self.history.insert("end", rel.split("/", 2)[-1])
        self.show_text(self.context_text, "")
        if self.files:
            self.history.selection_set(0)
            self.view_history()

    def view_history(self):
        chosen = self.history.curselection()
        if chosen:
            self.show_text(self.context_text, read_text(self.active_root(), self.files[chosen[0]]))

    def selected_skills(self):
        return [self.skill_names[i] for i in self.skill_list.curselection()
                if i < len(self.skill_names)]

    def switch_prompt(self, mode):
        self.mode.set(mode)
        self.tabs.select(1)
        self.generate()

    def new_project(self):
        pid = simpledialog.askstring("New project", "Project ID (lowercase, hyphens):", parent=self.window)
        if not pid:
            return
        self.project_id.set(pid)
        self.mode.set("New project")
        self.tabs.select(1)
        self.show_text(self.prompt_text, "")
        self.status.set("Enter the project root and generate a prompt. Registration happens on first explicit save.")

    def generate(self):
        result = make_prompt(self.active_root(), self.project_id.get().strip(), self.mode.get(),
                             self.selected_skills(), self.new_root.get())
        self.show_text(self.prompt_text, result)
        self.status.set("Prompt generated locally. No AI request sent.")
        return result

    def copy_prompt(self):
        result = self.generate()
        self.window.clipboard_clear()
        self.window.clipboard_append(result)
        self.status.set("Prompt copied. Paste into your authorized AI session.")

    def open_ai(self):
        url = AI_LINKS[self.provider.get()]
        if not url:
            self.status.set("Open your local AI client manually.")
        else:
            webbrowser.open(url)

    def check_context(self):
        errors, warnings = verify(self.active_root(), self.project_id.get())
        detail = "\n".join(["FAIL: " + e for e in errors] + ["WARN: " + w for w in warnings])
        if errors:
            messagebox.showwarning("Context check", detail, parent=self.window)
        else:
            messagebox.showinfo("Context check", "Saved files agree structurally.\n" + detail, parent=self.window)
        self.status.set("Context check complete; no files modified.")

    def load_skill(self):
        chosen = self.selected_skills()
        if len(chosen) != 1:
            raise ValueError("Select exactly one skill to edit.")
        name = chosen[0]
        content = read_text(self.active_root(), f"skills/{name}/SKILL.md")
        self.loaded_skill = (name, content, root_path(self.root.get()))
        self.show_text(self.skill_editor, content, readonly=False)
        self.skill_title.configure(text=f"Editing {name}")

    def new_skill(self):
        name = simpledialog.askstring("New skill", "Skill ID (lowercase, hyphens):", parent=self.window)
        if name:
            self.loaded_skill = (name, None, root_path(self.root.get()))
            self.show_text(self.skill_editor, f"# {name}\n\nDescribe when and how to use this skill.\n", readonly=False)
            self.skill_title.configure(text=f"New skill: {name}")

    def write_skill(self):
        if self.loaded_skill is None:
            raise ValueError("Open or create a skill first.")
        name, previous, loaded_root = self.loaded_skill
        if root_path(self.root.get()) != loaded_root:
            raise ValueError("Workspace changed; reopen the skill.")
        content = self.skill_editor.get("1.0", "end-1c")
        if not messagebox.askyesno("Save skill", f"Write skill {name} to your private workspace?",
                                   parent=self.window):
            return
        save_skill(loaded_root, name, content, previous)
        self.refresh()
        self.status.set(f"Saved skill: {name}")

    def create_backup(self):
        target = filedialog.asksaveasfilename(parent=self.window, defaultextension=".zip",
                                              filetypes=[("ZIP backup", "*.zip")])
        if target and messagebox.askyesno("Private backup",
                                          "Create an unencrypted archive of private context? Keep it confidential.",
                                          parent=self.window):
            count = backup(self.active_root(), target)
            self.status.set(f"Private backup created: {count} files.")

    def restore_backup(self):
        source = filedialog.askopenfilename(parent=self.window, filetypes=[("ZIP backup", "*.zip")])
        if not source:
            return
        parent = filedialog.askdirectory(parent=self.window, title="Choose parent folder for restored workspace")
        if not parent:
            return
        name = simpledialog.askstring("Restore", "New folder name:", parent=self.window)
        if not name:
            return
        if name in (".", "..") or any(c in name for c in ("/", "\\", ":")):
            raise ValueError("Enter a single folder name.")
        dest = Path(parent) / name
        count = restore(source, dest)
        self.root.set(str(dest))
        self.refresh()
        self.status.set(f"Restored {count} files. Review project root paths before reuse.")

    def devspace_check(self):
        path = shutil.which("devspace")
        messagebox.showinfo("DevSpace", "Executable found: " + path if path else
                            "DevSpace not found in this process's PATH.", parent=self.window)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default="")
    parser.add_argument("--smoke-test", action="store_true", help="create and destroy the GUI")
    args = parser.parse_args()
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            pass
    try:
        window = tk.Tk()
    except tk.TclError as exc:
        print(f"Cannot open desktop display: {exc}", file=sys.stderr)
        return 1
    if args.smoke_test:
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "private"
            initialize(root)
            app = Desktop(window, str(root))
            app.project_id.set("demo-site")
            assert "demo-site" in app.generate()
            app.copy_prompt()
            assert "demo-site" in window.clipboard_get()
            window.update_idletasks()
            window.update()
            window.destroy()
        return 0
    app = Desktop(window, args.workspace)
    window.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
