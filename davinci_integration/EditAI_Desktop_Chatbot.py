"""
=============================================================================
EditAI Desktop Companion — Floating DaVinci Resolve 21 Chatbot
=============================================================================
A modern dark-themed desktop assistant that connects to DaVinci Resolve 21
via the official Blackmagic Design Python Scripting API.
"""

import os
import sys
import threading
import time
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# Ensure paths
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from davinci_controller import DaVinciController
from davinci_nlp_engine import DaVinciNLPEngine

RESOLVE_EXE_PATH = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe"

class DaVinciDesktopChatbot(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EditAI • DaVinci Resolve 21 Chatbot")
        self.geometry("720x760")
        self.minsize(580, 600)

        # Apply dark theme styling
        self.configure(bg="#0f141c")
        
        # Initialize backend
        self.controller = DaVinciController()
        self.nlp_engine = DaVinciNLPEngine(self.controller)
        self.is_connected = False

        self._build_ui()
        self._start_connection_monitor()

    def _build_ui(self):
        # 1. Header Frame
        header_frame = tk.Frame(self, bg="#161d28", bd=1, relief="ridge", padx=14, pady=10)
        header_frame.pack(fill="x", padx=12, pady=(10, 6))

        title_lbl = tk.Label(
            header_frame, text="EDITMIND AI", font=("Segoe UI", 16, "bold"),
            fg="#38bdf8", bg="#161d28"
        )
        title_lbl.pack(side="left")

        subtitle_lbl = tk.Label(
            header_frame, text=" |  DaVinci Resolve 21 Co-Pilot", font=("Segoe UI", 12),
            fg="#cbd5e1", bg="#161d28"
        )
        subtitle_lbl.pack(side="left")

        self.status_badge = tk.Label(
            header_frame, text="● Disconnected", font=("Segoe UI", 10, "bold"),
            fg="#ef4444", bg="#161d28"
        )
        self.status_badge.pack(side="right")

        # 2. Project Info Bar
        info_frame = tk.Frame(self, bg="#1e2634", padx=14, pady=6)
        info_frame.pack(fill="x", padx=12, pady=(0, 8))

        self.proj_info_lbl = tk.Label(
            info_frame, text="Project: Checking connection...", font=("Segoe UI", 9),
            fg="#94a3b8", bg="#1e2634"
        )
        self.proj_info_lbl.pack(side="left")

        self.btn_launch_resolve = tk.Button(
            info_frame, text="🚀 Launch Resolve", font=("Segoe UI", 8, "bold"),
            bg="#2563eb", fg="white", activebackground="#1d4ed8", bd=0, padx=8, pady=2,
            command=self._launch_resolve
        )
        self.btn_launch_resolve.pack(side="right")

        # 3. Quick Action Buttons Bar
        quick_frame = tk.Frame(self, bg="#0f141c")
        quick_frame.pack(fill="x", padx=12, pady=(0, 6))

        quick_buttons = [
            ("🎬 Edit", lambda: self._quick_action("switch_page", {"page": "edit"})),
            ("🎨 Color", lambda: self._quick_action("switch_page", {"page": "color"})),
            ("📦 Deliver", lambda: self._quick_action("switch_page", {"page": "deliver"})),
            ("✂️ Detect Cuts", lambda: self._quick_action("detect_scene_cuts", {})),
            ("💬 AI Subtitles", lambda: self._quick_action("create_subtitles_from_audio", {})),
            ("🎙️ Voice Iso", lambda: self._quick_action("enable_voice_isolation", {"track_index": 1})),
            ("💾 Save", lambda: self._quick_action("save_project", {})),
        ]

        for text, cmd in quick_buttons:
            b = tk.Button(
                quick_frame, text=text, font=("Segoe UI", 8, "bold"),
                bg="#1e293b", fg="#f1f5f9", activebackground="#334155", activeforeground="white",
                bd=1, relief="solid", padx=6, pady=3, command=cmd
            )
            b.pack(side="left", padx=2)

        # 4. Chat History View
        chat_container = tk.Frame(self, bg="#0f141c")
        chat_container.pack(fill="both", expand=True, padx=12, pady=4)

        self.chat_display = scrolledtext.ScrolledText(
            chat_container, bg="#131922", fg="#f1f5f9",
            insertbackground="#38bdf8", font=("Consolas", 10),
            padx=12, pady=10, wrap="word", bd=1, relief="solid"
        )
        self.chat_display.pack(fill="both", expand=True)

        self.chat_display.tag_configure("user", foreground="#38bdf8", font=("Consolas", 10, "bold"))
        self.chat_display.tag_configure("assistant", foreground="#f8fafc")
        self.chat_display.tag_configure("system", foreground="#94a3b8", font=("Consolas", 9, "italic"))
        self.chat_display.tag_configure("error", foreground="#f87171", font=("Consolas", 10, "bold"))

        self._append_message("system", "Welcome to EditAI Assistant for DaVinci Resolve 21!")
        self._append_message("system", "Enter any natural language command below to control your active project.")

        # 5. Input Area
        input_container = tk.Frame(self, bg="#161d28", bd=1, relief="ridge", padx=10, pady=8)
        input_container.pack(fill="x", padx=12, pady=10)

        self.prompt_entry = tk.Entry(
            input_container, bg="#0b0f15", fg="#f8fafc",
            insertbackground="#38bdf8", font=("Segoe UI", 11),
            bd=1, relief="solid"
        )
        self.prompt_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=4)
        self.prompt_entry.bind("<Return>", lambda e: self._send_prompt())

        send_btn = tk.Button(
            input_container, text="Send ➔", font=("Segoe UI", 10, "bold"),
            bg="#0284c7", fg="white", activebackground="#0369a1", bd=0, padx=14, pady=4,
            command=self._send_prompt
        )
        send_btn.pack(side="right")

    def _append_message(self, tag, text):
        self.chat_display.insert(tk.END, f"\n[{tag.upper()}]\n" if tag != "system" else "\n", tag)
        self.chat_display.insert(tk.END, f"{text}\n", tag)
        self.chat_display.see(tk.END)

    def _send_prompt(self):
        prompt = self.prompt_entry.get().strip()
        if not prompt:
            return

        self._append_message("user", prompt)
        self.prompt_entry.delete(0, tk.END)

        def runner():
            res = self.nlp_engine.execute_prompt(prompt)
            tag = "assistant" if res.get("success") else "error"
            msg = res.get("message") or res.get("error", "Unknown result")
            self.after(0, lambda: self._append_message(tag, msg))
            self.after(0, self._update_status)

        threading.Thread(target=runner, daemon=True).start()

    def _quick_action(self, action, params):
        def runner():
            res = self.nlp_engine._dispatch_action(action, params)
            tag = "assistant" if res.get("success") else "error"
            msg = res.get("message") or res.get("error", "Action completed")
            self.after(0, lambda: self._append_message(tag, msg))
            self.after(0, self._update_status)

        threading.Thread(target=runner, daemon=True).start()

    def _launch_resolve(self):
        if os.path.exists(RESOLVE_EXE_PATH):
            subprocess.Popen([RESOLVE_EXE_PATH])
            self._append_message("system", f"Launching DaVinci Resolve from: {RESOLVE_EXE_PATH}")
        else:
            messagebox.showerror("Error", f"Resolve executable not found at: {RESOLVE_EXE_PATH}")

    def _update_status(self):
        if self.controller.is_connected():
            self.is_connected = True
            self.status_badge.config(text="● Connected", fg="#22c55e")
            summary = self.controller.get_project_summary()
            proj = summary.get("project_name", "No Project Open")
            tl = summary.get("timeline_name", "None")
            tc = summary.get("timeline_timecode", "N/A")
            self.proj_info_lbl.config(text=f"Project: {proj} | Timeline: {tl} | TC: {tc}")
        else:
            self.is_connected = False
            self.status_badge.config(text="● Disconnected", fg="#ef4444")
            self.proj_info_lbl.config(text="Project: DaVinci Resolve not detected. Click 'Launch Resolve'.")

    def _start_connection_monitor(self):
        def poll():
            while True:
                time.sleep(3)
                try:
                    self.controller.is_connected()
                    self.after(0, self._update_status)
                except Exception:
                    pass

        threading.Thread(target=poll, daemon=True).start()

if __name__ == "__main__":
    app = DaVinciDesktopChatbot()
    app.mainloop()
