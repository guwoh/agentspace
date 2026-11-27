#!/usr/bin/env python3
"""AgentSpace Desktop: a local, file-based AI workspace."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, font
import webbrowser

from agentspace import initialize, verify
from desktop_core import (AI_LINKS, MODES, backup, create_demo, filter_projects, make_prompt, project_files,
                          load_feature_map, check_feature_map, find_features, feature_routes, make_feature_prompt,
                          read_text, registry, restore, root_path, save_skill, skills)

VERSION = "0.3.0-dev"


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
        self.demo_dir = None
        self.return_root = ""
        self.demo_active = False
        self.search = tk.StringVar()
        self.show_unregistered = tk.BooleanVar(value=False)
        self.font_size = 10
        self._setup_style()
        self._build()
        self.window.update_idletasks()
        self.fit_initial_window()
        self.search.trace_add("write", lambda *_: self.guard(self.render_projects))
        self.window.bind("<Control-plus>", lambda _: self.change_font(1))
        self.window.bind("<Control-equal>", lambda _: self.change_font(1))
        self.window.bind("<Control-minus>", lambda _: self.change_font(-1))
        self.window.bind("<Control-0>", lambda _: self.set_font(10))
        self.window.bind("<Control-f>", lambda _: self.focus_search())
        if initial_root:
            self.guard(self.refresh)

    def _setup_style(self):
        w = self.window
        w.title(f"AgentSpace Desktop · {VERSION}")
        w.geometry("1120x740")
        w.minsize(800, 540)
        w.configure(background="#eef2f6")
        style = ttk.Style(w)
        style.theme_use("clam")
        # Use app-owned named fonts: desktop settings can change TkDefaultFont
        # after startup, otherwise manual zoom is silently overridden.
        self.body_font = font.Font(root=w, font="TkDefaultFont")
        self.body_font.configure(size=self.font_size)
        self.mono_font = font.Font(root=w, font="TkFixedFont")
        self.mono_font.configure(size=self.font_size)
        self.heading_font = font.Font(root=w, font=self.body_font)
        self.heading_font.configure(size=17, weight="bold")
        self.bold_font = font.Font(root=w, font=self.body_font)
        self.bold_font.configure(weight="bold")
        style.configure(".", font=self.body_font, background="#eef2f6", foreground="#18273b")
        style.configure("TFrame", background="#eef2f6")
        style.configure("TNotebook", background="#eef2f6", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(14, 8))
        style.configure("TButton", padding=(10, 7))
        style.configure("Accent.TButton", background="#315fbd", foreground="white", padding=(12, 9))
        style.map("Accent.TButton", background=[("active", "#244b9a")])
        style.configure("Heading.TLabel", font=self.heading_font)
        style.configure("Muted.TLabel", foreground="#52657b")
        style.configure("Treeview", rowheight=30, background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=self.bold_font)
        style.configure("TEntry", fieldbackground="white")
        style.configure("TCombobox", fieldbackground="white")
        self.text_widgets = []

    def fit_initial_window(self):
        # The window manager may apply a larger text scale than tk scaling reports.
        # Size the initial window from measured font pixels, bounded by the screen.
        ratio = max(1.0, min(2.2, self.body_font.metrics("linespace") / 18))
        width = min(int(1120 * ratio), int(self.window.winfo_screenwidth() * .88))
        height = min(int(740 * ratio), int(self.window.winfo_screenheight() * .85))
        self.window.geometry(f"{max(800, width)}x{max(540, height)}")

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
        widget = tk.Text(frame, wrap="word", undo=not readonly, font=self.mono_font, width=1, height=4,
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
        self.tagline = ttk.Label(top, text="Switch AI. Keep your progress.", style="Muted.TLabel")
        self.tagline.pack(side="left", padx=8)
        self.button(top, "Open folder", self.open_workspace, side="right", padx=3)
        self.demo_button = self.button(top, "Try demo", self.toggle_demo, side="right", padx=3)
        self.button(top, "Refresh", self.refresh, side="right", padx=3)
        bar = ttk.Frame(self.window, padding=(18, 0, 18, 12))
        bar.pack(fill="x")
        ttk.Label(bar, text="Workspace").pack(side="left", padx=(0, 8))
        ttk.Entry(bar, textvariable=self.root).pack(side="left", fill="x", expand=True)
        self.button(bar, "Browse", self.browse, side="left", padx=5)
        self.button(bar, "Initialize", self.init_workspace, side="left")
        tabs = self.tabs = ttk.Notebook(self.window, width=1, height=1)
        tabs.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        self.page_views = []
        for label, builder in (("Projects", self.build_projects), ("Prompts", self.build_prompt),
                               ("History", self.build_history), ("Skills", self.build_skills),
                               ("Connect", self.build_connections), ("Settings", self.build_backup),
                               ("Feature map", self.build_features)):
            shell = ttk.Frame(tabs)
            tabs.add(shell, text=label)
            canvas = tk.Canvas(shell, bg="#eef2f6", highlightthickness=0, borderwidth=0)
            scroll = ttk.Scrollbar(shell, orient="vertical", command=canvas.yview)
            horizontal = ttk.Scrollbar(shell, orient="horizontal", command=canvas.xview)
            canvas.configure(yscrollcommand=scroll.set, xscrollcommand=horizontal.set)
            shell.rowconfigure(0, weight=1)
            shell.columnconfigure(0, weight=1)
            canvas.grid(row=0, column=0, sticky="nsew")
            scroll.grid(row=0, column=1, sticky="ns")
            horizontal.grid(row=1, column=0, sticky="ew")
            page = ttk.Frame(canvas, padding=14)
            handle = canvas.create_window((0, 0), window=page, anchor="nw")
            builder(page)
            self.page_views.append((canvas, page, handle))
            canvas.bind("<Configure>", lambda _, c=canvas, p=page, h=handle: self.fit_page(c, p, h))
            page.bind("<Configure>", lambda _, c=canvas, p=page, h=handle: self.fit_page(c, p, h))
            canvas.bind("<MouseWheel>", lambda e, c=canvas: c.yview_scroll(-1 if e.delta > 0 else 1, "units"))
            canvas.bind("<Button-4>", lambda e, c=canvas: c.yview_scroll(-1, "units"))
            canvas.bind("<Button-5>", lambda e, c=canvas: c.yview_scroll(1, "units"))
        self.tabs.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self.status_label = ttk.Label(self.window, textvariable=self.status, style="Muted.TLabel",
                                      padding=(18, 5, 18, 12))
        self.status_label.pack(side="bottom", fill="x", before=tabs)
        self.window.bind("<Configure>", self.on_resize, add="+")

    def fit_page(self, canvas, page, handle):
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if width < 2 or height < 2:
            return
        needed = max(height, page.winfo_reqheight())
        needed_width = max(width, page.winfo_reqwidth())
        if int(float(canvas.itemcget(handle, "width") or 0)) != needed_width:
            canvas.itemconfigure(handle, width=needed_width)
        if int(float(canvas.itemcget(handle, "height") or 0)) != needed:
            canvas.itemconfigure(handle, height=needed)
        canvas.configure(scrollregion=(0, 0, needed_width, needed))

    def on_resize(self, event):
        if event.widget != self.window:
            return
        width = event.width
        if width < 1000 or self.font_size >= 14:
            self.tagline.pack_forget()
        elif not self.tagline.winfo_manager():
            self.tagline.pack(side="left", padx=8)
        self.guide.configure(wraplength=max(250, width - 100))
        self.summary.configure(wraplength=max(250, width - 100))
        self.status_label.configure(wraplength=max(250, width - 70))
        for canvas, page, handle in self.page_views:
            self.fit_page(canvas, page, handle)

    def build_projects(self, page):
        ttk.Label(page, text="Your projects", style="Heading.TLabel").pack(anchor="w")
        self.summary = ttk.Label(page, text="No workspace loaded.", style="Muted.TLabel")
        self.summary.pack(anchor="w", pady=(4, 8))
        self.guide = ttk.Label(page, text="1. Choose or initialize a private workspace.  2. Try demo or start a project.\n3. Copy the prompt into an AI with authorized file access.",
                               style="Muted.TLabel", wraplength=720)
        self.guide.pack(anchor="w", pady=(0, 10))
        search_row = ttk.Frame(page)
        search_row.pack(fill="x", pady=(0, 8))
        ttk.Label(search_row, text="Find project").pack(side="left")
        self.search_entry = ttk.Entry(search_row, textvariable=self.search)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=8)
        self.button(search_row, "Clear", lambda: self.search.set(""), side="left")
        ttk.Checkbutton(search_row, text="Show folder-only", variable=self.show_unregistered,
                        command=lambda: self.guard(self.render_projects)).pack(side="right", padx=6)
        self.project_count = ttk.Label(page, text="", style="Muted.TLabel")
        self.project_count.pack(anchor="w", pady=(0, 4))
        tree_frame = ttk.Frame(page)
        tree_frame.pack(fill="both", expand=True)
        columns = ("name", "session", "state")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings", selectmode="browse", height=5)
        self.tree.heading("#0", text="Project ID")
        self.tree.column("#0", width=170, minwidth=100)
        for col, label, width in zip(columns, ("Name / scope", "Latest session", "Registry"),
                                     (230, 155, 100)):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, minwidth=80)
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-Button-1>", lambda _: self.guard(lambda: self.switch_prompt("Resume")))
        self.tree.bind("<<TreeviewSelect>>", lambda _: self.guard(self.select_project))
        buttons = ttk.Frame(page)
        buttons.pack(fill="x", pady=(12, 0))
        actions = (("Copy resume prompt", self.quick_resume, True),
                   ("Start project", lambda: self.switch_prompt("Resume"), False),
                   ("New project", self.new_project, False),
                   ("Check context", self.check_context, False),
                   ("View history", lambda: self.tabs.select(2), False))
        for i, (label, callback, accent) in enumerate(actions):
            ttk.Button(buttons, text=label, command=lambda cb=callback: self.guard(cb),
                       style="Accent.TButton" if accent else "TButton").grid(
                           row=i // 3, column=i % 3, sticky="ew", padx=3, pady=3)
        for i in range(3):
            buttons.columnconfigure(i, weight=1)

    def build_prompt(self, page):
        ttk.Label(page, text="Generate a prompt", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(page, text="Select a project and action. Copy into an authorized AI session.",
                  style="Muted.TLabel", wraplength=620).pack(anchor="w", pady=(4, 8))
        row = ttk.Frame(page)
        row.pack(fill="x", pady=4)
        for label, var, values, width in (("Project ID", self.project_id, [], 12),
                                          ("AI", self.provider, list(AI_LINKS), 10),
                                          ("Action", self.mode, MODES, 12)):
            group = ttk.Frame(row)
            group.pack(side="left", fill="x", expand=True, padx=(0, 10))
            ttk.Label(group, text=label).pack(anchor="w")
            combo = ttk.Combobox(group, textvariable=var, values=values, width=width,
                                 state="normal" if var == self.project_id else "readonly")
            combo.pack(fill="x")
            if var == self.project_id:
                self.project_combo = combo
                combo.bind("<<ComboboxSelected>>", lambda _: self.guard(self.choose_prompt_project))
            else:
                combo.bind("<<ComboboxSelected>>", lambda _: self.guard(self.generate))
        new = ttk.Frame(page)
        new.pack(fill="x", pady=5)
        ttk.Label(new, text="Project root (new project only)").pack(side="left")
        ttk.Entry(new, textvariable=self.new_root).pack(side="left", fill="x", expand=True, padx=8)
        self.button(new, "Browse", self.browse_new_root, side="left")
        ttk.Label(page, text="Optional skills — select one or more in the Skills tab.",
                  style="Muted.TLabel").pack(anchor="w", pady=6)
        buttons = ttk.Frame(page)
        buttons.pack(side="bottom", fill="x", pady=(8, 0))
        self.prompt_text = self.text_area(page, readonly=True)
        for i, (label, callback) in enumerate((("Generate & copy", self.copy_prompt),
                                                ("Preview", self.generate), ("Open AI", self.open_ai))):
            ttk.Button(buttons, text=label, command=lambda cb=callback: self.guard(cb),
                       style="Accent.TButton" if i == 0 else "TButton").grid(
                           row=0, column=i, sticky="ew", padx=3, pady=3)
            buttons.columnconfigure(i, weight=1)

    def build_history(self, page):
        ttk.Label(page, text="Context and session history", style="Heading.TLabel").pack(anchor="w", pady=(0, 12))
        paned = ttk.Panedwindow(page, orient="horizontal")
        paned.pack(fill="both", expand=True)
        left = ttk.Frame(paned)
        right = ttk.Frame(paned)
        paned.add(left, weight=1)
        paned.add(right, weight=4)
        self.history = tk.Listbox(left, exportselection=False, width=20, height=4, font=self.body_font, bg="white", relief="flat")
        self.history.pack(fill="both", expand=True)
        self.history.bind("<<ListboxSelect>>", lambda _: self.guard(self.view_history))
        self.context_text = self.text_area(right, readonly=True)
        ttk.Label(page, text="Saved snapshots are read-only here. Save through the AI workflow.",
                  style="Muted.TLabel").pack(anchor="w", pady=(10, 0))

    def build_skills(self, page):
        ttk.Label(page, text="Personal skills", style="Heading.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Label(page, text="Explicit selection adds skill file paths to generated prompts. No automatic execution.",
                  style="Muted.TLabel", wraplength=620).pack(anchor="w", pady=(0, 8))
        paned = ttk.Panedwindow(page, orient="horizontal")
        paned.pack(fill="both", expand=True)
        left = ttk.Frame(paned)
        right = ttk.Frame(paned)
        paned.add(left, weight=1)
        paned.add(right, weight=4)
        self.skill_list = tk.Listbox(left, selectmode="extended", exportselection=False, width=20, height=4, font=self.body_font, bg="white", relief="flat")
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

    def build_features(self, page):
        ttk.Label(page, text="Feature map", style="Heading.TLabel").pack(anchor="w")
        self.map_status = ttk.Label(page, text="Select a project first.", wraplength=620, style="Muted.TLabel")
        self.map_status.pack(anchor="w", pady=6)
        self.feature_query = tk.StringVar()
        search = ttk.Entry(page, textvariable=self.feature_query)
        search.pack(fill="x", pady=4)
        self.feature_query.trace_add("write", lambda *_: self.guard(self.render_features))
        self.feature_list = tk.Listbox(page, height=4, exportselection=False, font=self.body_font)
        self.feature_list.pack(fill="x", pady=5)
        self.feature_list.bind("<<ListboxSelect>>", lambda _: self.guard(self.show_feature))
        actions = ttk.Frame(page)
        actions.pack(fill="x", pady=5)
        self.button(actions, "Validate / reload", self.reload_features, side="left")
        self.button(actions, "Copy focused prompt", self.copy_feature, True, side="left", padx=6)
        self.feature_detail = self.text_area(page, readonly=True)
        self.feature_info = None
        self.feature_rows = []
        self.feature_key = None

    def on_tab_changed(self, event):
        if self.tabs.index(self.tabs.select()) == 6:
            self.guard(self.reload_features)

    def reload_features(self):
        self.feature_info = None
        self.feature_key = None
        self.render_features()
        pid = self.project_id.get().strip()
        if not pid or not self.loaded_root:
            self.map_status.configure(text="Select a project first.")
            return
        root = self.active_root()
        info = load_feature_map(root, pid)
        self.feature_key = (root, pid)
        self.feature_info = info
        errors, warnings = check_feature_map(root, pid, info)
        self.map_status.configure(text=f"{pid}: " + ("; ".join(errors + warnings) if errors or warnings
                                   else "Map session and paths agree. Symbols and source facts are not checked."))
        self.render_features()

    def render_features(self):
        self.feature_rows = find_features(self.feature_info, self.feature_query.get())
        self.feature_list.delete(0, "end")
        self.show_text(self.feature_detail, "")
        for row in self.feature_rows:
            self.feature_list.insert("end", f"{row['id']} — {row['name']}")

    def show_feature(self):
        selected = self.feature_list.curselection()
        if not selected:
            return
        row = self.feature_rows[selected[0]]
        routes = feature_routes(self.feature_info, row["id"])
        self.show_text(self.feature_detail, "\n\n".join(
            r["name"] + " [" + r["status"] + "]\n" + "\n".join(r["sources"]) for r in routes))

    def copy_feature(self):
        selected = self.feature_list.curselection()
        if not selected or self.feature_key != (self.active_root(), self.project_id.get().strip()):
            raise ValueError("Reload the map and select a feature.")
        prompt = make_feature_prompt(self.active_root(), self.project_id.get().strip(),
                                     self.feature_rows[selected[0]]["id"])
        self.window.clipboard_clear()
        self.window.clipboard_append(prompt)
        self.status.set("Focused read-only prompt copied.")

    def build_connections(self, page):
        ttk.Label(page, text="AI connections", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(page, text="AgentSpace generates prompts locally. DevSpace or another authorized file tool provides access.",
                  style="Muted.TLabel", wraplength=690).pack(anchor="w", pady=(8, 18))
        for name in ("ChatGPT", "Claude", "Codex"):
            row = ttk.Frame(page, padding=(0, 6))
            row.pack(fill="x")
            ttk.Label(row, text=name, width=18).pack(side="left")
            self.button(row, "Open AI", lambda n=name: webbrowser.open(AI_LINKS[n]), side="left")
        self.button(page, "Open DevSpace GUI", self.open_devspace_gui, True, anchor="w", pady=6)
        self.button(page, "DevSpace setup guide",
                    lambda: webbrowser.open("https://github.com/guwoh/agentspace/blob/main/docs/DEVSPACE.md"), anchor="w", pady=10)
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
        ttk.Label(page, text="Uses OS scaling at startup. Adjust text with Ctrl + / − or Ctrl + 0 to reset. Per-monitor scaling is not guaranteed.",
                  style="Muted.TLabel", wraplength=620).pack(anchor="w", pady=8)
        scale = ttk.Frame(page)
        scale.pack(anchor="w")
        for size in (9, 10, 12, 14, 16):
            self.button(scale, str(size), lambda n=size: self.set_font(n), side="left", padx=3)
        ttk.Label(page, text=f"AgentSpace {VERSION} · Local files · MIT",
                  style="Muted.TLabel").pack(anchor="w", pady=20)

    def change_font(self, delta):
        self.set_font(max(8, min(18, self.font_size + delta)))
        return "break"

    def set_font(self, size):
        self.font_size = size
        self.body_font.configure(size=size)
        self.mono_font.configure(size=size)
        style = ttk.Style(self.window)
        self.heading_font.configure(size=size + 7)
        self.bold_font.configure(size=size)
        style.configure(".", font=self.body_font)
        style.configure("Treeview", rowheight=max(26, int(self.body_font.metrics("linespace") * 1.7)))
        self.history.configure(font=self.body_font)
        self.skill_list.configure(font=self.body_font)
        self.feature_list.configure(font=self.body_font)
        self.status.set(f"Interface font size: {size} pt")
        self.window.update_idletasks()
        for canvas, page, handle in self.page_views:
            self.fit_page(canvas, page, handle)

    def toggle_demo(self):
        if self.demo_active:
            self.root.set(self.return_root)
            self.demo_active = False
            self.demo_button.configure(text="Try demo")
            if self.return_root:
                self.refresh()
            else:
                self.loaded_root = None
                self.projects = []
                self.tree.delete(*self.tree.get_children())
                self.search.set("")
                self.project_count.configure(text="")
                self.project_id.set("")
                self.project_combo.configure(values=[])
                self.skill_names = []
                self.skill_list.delete(0, "end")
                self.loaded_skill = None
                self.show_text(self.skill_editor, "", readonly=False)
                self.skill_title.configure(text="No skill open.")
                self.refresh_history()
                self.show_text(self.prompt_text, "")
                self.summary.configure(text="No workspace loaded.")
                self.guide.configure(text="Choose a private workspace, or try the fictional demo.")
            self.status.set("Exited demo. Your private workspace was not changed.")
            return
        if self.demo_dir is None:
            self.demo_dir = tempfile.TemporaryDirectory(prefix="agentspace-demo-")
            try:
                self.demo_root = create_demo(Path(self.demo_dir.name) / "workspace")
            except Exception:
                self.demo_dir.cleanup()
                self.demo_dir = None
                raise
        self.return_root = str(self.loaded_root) if self.loaded_root is not None else ""
        self.root.set(str(self.demo_root))
        self.demo_active = True
        self.demo_button.configure(text="Exit demo")
        self.refresh()
        self.tree.selection_set("demo-robot")
        self.select_project()
        self.mode.set("Resume")
        self.tabs.select(0)
        self.status.set("Fictional demo. No AI connection needed; no private files changed.")

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
        changed_workspace = self.loaded_root != root
        if self.demo_active and root != self.demo_root:
            self.demo_active = False
            self.demo_button.configure(text="Try demo")
        self.loaded_root = root
        if changed_workspace:
            self.project_id.set("")
            self.new_root.set("")
            self.mode.set("Resume")
        self.guide.configure(text=("DEMO • Fictional robot project. Try Start project, Generate & copy, history and context check. "
                                   "No AI connection needed for this preview." if self.demo_active else
                                   "Select a project and click Start project. Copy the prompt into an authorized AI session."))
        if changed_workspace:
            self.show_unregistered.set(False)
            self.search.set("")
        self.render_projects()
        self.summary.configure(text=f"{sum(p['registered'] for p in self.projects)} registered projects · {root}")
        previous_skills = [] if changed_workspace else self.selected_skills()
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

    def focus_search(self):
        self.tabs.select(0)
        self.search_entry.focus_set()
        return "break"

    def render_projects(self):
        visible = filter_projects(self.projects, self.search.get(), self.show_unregistered.get())
        # Preserve a selected row if it remains visible. Never silently select another.
        previous = self.tree.selection()
        selected_id = self.project_id.get()
        self.tree.delete(*self.tree.get_children())
        for item in visible:
            self.tree.insert("", "end", iid=item["id"], text=item["id"],
                             values=(item["name"], item["session"],
                                     "Registered" if item["registered"] else "Folder only"))
        allowed = filter_projects(self.projects, "", self.show_unregistered.get())
        self.project_combo.configure(values=[p["id"] for p in allowed])
        self.project_count.configure(text=f"{len(visible)} shown · {len(self.projects) - sum(p['registered'] for p in self.projects)} folder-only")
        if previous and previous[0] == selected_id and selected_id in self.tree.get_children():
            self.tree.selection_set(selected_id)
        elif previous and previous[0] == selected_id:
            self.project_id.set("")
            self.refresh_history()
            self.show_text(self.prompt_text, "")

    def quick_resume(self):
        self.active_root()
        selected = self.tree.selection()
        if not selected:
            raise ValueError("Select a visible project first.")
        self.project_id.set(selected[0])
        self.mode.set("Resume")
        self.copy_prompt()
        self.tabs.select(1)

    def choose_prompt_project(self):
        pid = self.project_id.get().strip()
        if pid in self.tree.get_children():
            self.tree.selection_set(pid)
        else:
            self.tree.selection_remove(*self.tree.selection())
        if self.mode.get() == "New project":
            self.mode.set("Resume")
        self.refresh_history()
        self.generate()

    def select_project(self):
        chosen = self.tree.selection()
        if chosen and chosen[0] != self.project_id.get():
            self.project_id.set(chosen[0])
            self.mode.set("Resume")
            self.show_text(self.prompt_text, "")
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
        if not self.project_id.get():
            self.status.set("Choose a project, or use New project to begin.")
            return
        self.generate()

    def new_project(self):
        pid = simpledialog.askstring("New project", "Project ID (lowercase, hyphens):", parent=self.window)
        if not pid:
            return
        if any(p["id"] == pid for p in self.projects):
            raise ValueError("Project ID already exists. Select it and use Start project.")
        self.project_id.set(pid)
        self.new_root.set("")
        self.mode.set("New project")
        self.tabs.select(1)
        self.show_text(self.prompt_text, "")
        self.status.set("Enter the project root and generate a prompt. Registration happens on first explicit save.")

    def generate(self):
        result = make_prompt(self.active_root(), self.project_id.get().strip(), self.mode.get(),
                             self.selected_skills(), self.new_root.get())
        self.show_text(self.prompt_text, result)
        self.status.set("Demo prompt only. No AI request sent." if self.demo_active else "Prompt generated locally. No AI request sent.")
        return result

    def copy_prompt(self):
        result = self.generate()
        self.window.clipboard_clear()
        self.window.clipboard_append(result)
        self.status.set("Fictional demo prompt copied. No AI connection needed to try the app." if self.demo_active else "Prompt copied. Paste into your authorized AI session.")

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

    def open_devspace_gui(self):
        if getattr(sys, "frozen", False):
            command = [sys.executable, "--devspace-gui"]
        else:
            command = [sys.executable, "-B", str(Path(__file__).with_name("devspace_gui.py"))]
        subprocess.Popen(command)
        self.status.set("DevSpace configuration GUI opened separately. No connection or settings changed automatically.")

    def devspace_check(self):
        path = shutil.which("devspace")
        messagebox.showinfo("DevSpace", "Executable found: " + path if path else
                            "DevSpace not found in this process's PATH.", parent=self.window)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--devspace-gui":
        from devspace_gui import main as devspace_main
        return devspace_main(sys.argv[2:])
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
            app.toggle_demo()
            assert app.demo_active and app.project_id.get() == "demo-robot"
            assert verify(app.active_root(), "demo-robot") == ([], [])
            app.skill_list.selection_set(0)
            app.quick_resume()
            assert "demo-robot" in window.clipboard_get()
            assert "demo-review" in window.clipboard_get()
            app.tabs.select(0)
            app.search.set("missing")
            window.update()
            assert not app.tree.get_children()
            assert not app.project_id.get()
            app.search.set("ROBOT")
            assert app.tree.get_children() == ("demo-robot",)
            app.tree.selection_set("demo-robot")
            app.select_project()
            app.quick_resume()
            assert "demo-robot" in window.clipboard_get()
            window.geometry("800x540")
            for size in (10, 12, 16):
                app.set_font(size)
                for index in (0, 1):
                    app.tabs.select(index)
                    window.update()
                    canvas, page, handle = app.page_views[index]
                    assert canvas.winfo_width() > 10 and canvas.winfo_height() > 10
                    assert int(float(canvas.itemcget(handle, "height"))) >= page.winfo_reqheight()
                    assert int(float(canvas.itemcget(handle, "width"))) >= page.winfo_reqwidth()
                    widget = app.tree if index == 0 else app.prompt_text
                    assert widget.winfo_width() > 10 and widget.winfo_height() > 10
            app.set_font(10)
            app.tabs.select(6)
            window.update()
            app.feature_query.set("driver")
            assert len(app.feature_rows) == 1
            app.feature_list.selection_set(0)
            app.show_feature()
            app.copy_feature()
            assert "Focus only on feature driver" in window.clipboard_get()
            app.toggle_demo()
            assert app.active_root() == root
            assert not app.selected_skills()
            app.demo_dir.cleanup()
            window.update_idletasks()
            window.update()
            window.destroy()
        return 0
    app = Desktop(window, args.workspace)
    try:
        window.mainloop()
    finally:
        if app.demo_dir is not None:
            app.demo_dir.cleanup()
    return 0


if __name__ == "__main__":
    sys.exit(main())
