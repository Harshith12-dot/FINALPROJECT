"""
AI Side-Channel Attack Detector & Active Power Masking Desktop GUI
Cyberpunk Black & Neon Green Aesthetic with Dynamic Current Scrambling Defense.
"""

import sys
import os
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, List

from core.detector_engine import DetectorEngine, SystemState


# =============================================================================
# THEME COLOR CONSTANTS (CYBERPUNK BLACK & NEON GREEN)
# =============================================================================
BG_DEEP = "#050806"         # Pitch black obsidian
BG_PANEL = "#0B150F"        # Dark charcoal emerald
BG_PANEL_ALT = "#0E1C14"    # Elevated panel card
BORDER_GREEN = "#184227"    # Dark green border
BORDER_GLOW = "#00FF66"     # Bright neon green border
NEON_GREEN = "#00FF66"      # Primary matrix neon green
NEON_GREEN_HOVER = "#33FF88"# Hover green
NEON_MINT = "#80FFB8"       # Soft matrix green
TEXT_WHITE = "#E6FFF0"      # Bright text
TEXT_MUTED = "#3D7A55"      # Subdued green labels
GRID_COLOR = "#0D2418"      # Oscilloscope grid line
ALERT_RED = "#FF2244"       # Alert anomaly red
ALERT_BG = "#2B060B"        # Alert container
WARN_YELLOW = "#FFBB00"     # Warning amber
CYAN_LINE = "#00E5FF"       # Baseline reference cyan & defense shield
DEFENSE_PURPLE = "#BB55FF"  # Masking indicator


class CyberpunkGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AI-SCA // Side-Channel Attack Detector & Dynamic Power Masking Defense")
        self.root.geometry("1380x880")
        self.root.minsize(1120, 760)
        self.root.configure(bg=BG_DEEP)

        # Detector backend engine
        self.engine = DetectorEngine()
        self.engine.add_listener(self._on_engine_event)

        # UI State variables
        self.selected_port = tk.StringVar(value="COM7")
        self.selected_baud = tk.StringVar(value="115200")
        self.is_sim_mode = tk.BooleanVar(value=False)
        self.auto_defense_var = tk.BooleanVar(value=True)
        self.threshold_var = tk.DoubleVar(value=10.0)
        self.autoscroll_var = tk.BooleanVar(value=True)

        # Cached display metrics
        self.current_state = SystemState.DISCONNECTED
        self.cached_current = 0.0
        self.cached_mean = 0.0
        self.cached_baseline = 0.0
        self.cached_delta = 0.0
        self.cached_prediction = 1
        self.cached_attacker = False
        self.cached_defense = False
        self.cached_correlation = 1.2
        self.cached_key_status = "SECURE / IDLE"
        self.cached_entropy = 0.0
        self.cached_rate = 0.0
        self.cached_samples = 0
        self.is_trained = False
        self.train_progress_text = "0/10 (0%)"

        # UI build
        self._init_styles()
        self._build_header()
        self._build_toolbar()
        self._build_main_grid()
        self._build_status_footer()

        # Initial ports population
        self._refresh_ports()

        # Periodic GUI update timer (~30 FPS)
        self.root.after(33, self._gui_tick)

        # Protocol on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # -------------------------------------------------------------------------
    # STYLES & SETUP
    # -------------------------------------------------------------------------
    def _init_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Cyber.TCombobox",
            fieldbackground=BG_PANEL,
            background=BG_PANEL_ALT,
            foreground=NEON_GREEN,
            bordercolor=BORDER_GREEN,
            arrowcolor=NEON_GREEN,
            darkcolor=BG_PANEL,
            lightcolor=BORDER_GREEN,
        )
        style.map(
            "Cyber.TCombobox",
            fieldbackground=[("readonly", BG_PANEL)],
            foreground=[("readonly", NEON_GREEN)],
            selectbackground=[("readonly", BG_PANEL_ALT)],
            selectforeground=[("readonly", NEON_GREEN)]
        )

    # -------------------------------------------------------------------------
    # HEADER SECTION
    # -------------------------------------------------------------------------
    def _build_header(self):
        header_frame = tk.Frame(self.root, bg=BG_PANEL, height=76, highlightbackground=BORDER_GREEN, highlightthickness=1)
        header_frame.pack(fill=tk.X, padx=14, pady=(12, 6))

        # Title block
        title_box = tk.Frame(header_frame, bg=BG_PANEL)
        title_box.pack(side=tk.LEFT, padx=16, pady=10)

        main_title = tk.Label(
            title_box,
            text="⚡ AI SIDE-CHANNEL ATTACK DETECTOR & POWER MASKING DEFENSE",
            font=("Consolas", 14, "bold"),
            fg=NEON_GREEN,
            bg=BG_PANEL
        )
        main_title.pack(anchor=tk.W)

        subtitle = tk.Label(
            title_box,
            text="Core Idea: Detect Physical Current Changes → Actively Change Current Again to Destroy Hacker Key Pattern",
            font=("Consolas", 9),
            fg=NEON_MINT,
            bg=BG_PANEL
        )
        subtitle.pack(anchor=tk.W)

        # Status Pill (Right side)
        self.status_pill = tk.Label(
            header_frame,
            text="● SYSTEM OFFLINE",
            font=("Consolas", 11, "bold"),
            fg="#77887E",
            bg="#0B150F",
            padx=18,
            pady=8,
            relief=tk.FLAT,
            highlightbackground=BORDER_GREEN,
            highlightthickness=1
        )
        self.status_pill.pack(side=tk.RIGHT, padx=16, pady=12)

    # -------------------------------------------------------------------------
    # TOOLBAR CONTROLS
    # -------------------------------------------------------------------------
    def _build_toolbar(self):
        bar = tk.Frame(self.root, bg=BG_PANEL, highlightbackground=BORDER_GREEN, highlightthickness=1)
        bar.pack(fill=tk.X, padx=14, pady=4)

        # Port Selector
        lbl_port = tk.Label(bar, text="PORT:", font=("Consolas", 9, "bold"), fg=TEXT_MUTED, bg=BG_PANEL)
        lbl_port.pack(side=tk.LEFT, padx=(14, 4), pady=8)

        self.port_combo = ttk.Combobox(
            bar,
            textvariable=self.selected_port,
            style="Cyber.TCombobox",
            width=18,
            state="readonly"
        )
        self.port_combo.pack(side=tk.LEFT, padx=4, pady=8)

        btn_refresh = tk.Button(
            bar,
            text="⟳ SCAN",
            font=("Consolas", 8, "bold"),
            fg=NEON_GREEN,
            bg=BG_PANEL_ALT,
            activebackground=NEON_GREEN,
            activeforeground=BG_DEEP,
            relief=tk.FLAT,
            highlightbackground=BORDER_GREEN,
            highlightthickness=1,
            padx=8,
            pady=2,
            command=self._refresh_ports
        )
        btn_refresh.pack(side=tk.LEFT, padx=(2, 8), pady=8)

        # Baud Rate
        lbl_baud = tk.Label(bar, text="BAUD:", font=("Consolas", 9, "bold"), fg=TEXT_MUTED, bg=BG_PANEL)
        lbl_baud.pack(side=tk.LEFT, padx=(6, 4), pady=8)

        self.baud_combo = ttk.Combobox(
            bar,
            textvariable=self.selected_baud,
            values=["115200", "9600", "57600", "230400"],
            style="Cyber.TCombobox",
            width=8,
            state="readonly"
        )
        self.baud_combo.pack(side=tk.LEFT, padx=4, pady=8)

        # Connect / Disconnect Button
        self.btn_connect = tk.Button(
            bar,
            text="CONNECT ESP32",
            font=("Consolas", 9, "bold"),
            fg=BG_DEEP,
            bg=NEON_GREEN,
            activebackground=NEON_GREEN_HOVER,
            activeforeground=BG_DEEP,
            relief=tk.FLAT,
            padx=12,
            pady=3,
            command=self._toggle_connect
        )
        self.btn_connect.pack(side=tk.LEFT, padx=10, pady=8)

        # Simulation Mode Toggle Checkbox
        chk_sim = tk.Checkbutton(
            bar,
            text="🧪 SIMULATOR MODE",
            variable=self.is_sim_mode,
            font=("Consolas", 9, "bold"),
            fg=WARN_YELLOW,
            bg=BG_PANEL,
            activebackground=BG_PANEL,
            activeforeground=WARN_YELLOW,
            selectcolor=BG_PANEL_ALT,
            command=self._on_sim_mode_toggle
        )
        chk_sim.pack(side=tk.LEFT, padx=8, pady=8)

        # Physical Attack Button (Current Change Trigger)
        self.btn_attack = tk.Button(
            bar,
            text="⚡ INJECT ATTACK (CHANGE CURRENT)",
            font=("Consolas", 9, "bold"),
            fg="#FFAAAA",
            bg="#3D0B12",
            activebackground=ALERT_RED,
            activeforeground=TEXT_WHITE,
            relief=tk.FLAT,
            highlightbackground=ALERT_RED,
            highlightthickness=1,
            padx=10,
            pady=3,
            command=self._toggle_physical_change
        )
        self.btn_attack.pack(side=tk.LEFT, padx=6, pady=8)

        # Force Safe Mode Button (Always cleanly turns off disturbance & restores safe state)
        self.btn_safe = tk.Button(
            bar,
            text="🛡️ SAFE MODE (TURN OFF)",
            font=("Consolas", 9, "bold"),
            fg="#050806",
            bg="#00FF66",
            activebackground="#33FF88",
            activeforeground="#050806",
            relief=tk.FLAT,
            padx=10,
            pady=3,
            command=self._force_safe_mode
        )
        self.btn_safe.pack(side=tk.LEFT, padx=6, pady=8)

        # Active Power Masking Countermeasure Toggle
        self.btn_defense = tk.Button(
            bar,
            text="🛡️ MASKING: ON",
            font=("Consolas", 9, "bold"),
            fg=BG_DEEP,
            bg=CYAN_LINE,
            activebackground=NEON_GREEN,
            activeforeground=BG_DEEP,
            relief=tk.FLAT,
            padx=10,
            pady=3,
            command=self._toggle_defense
        )
        self.btn_defense.pack(side=tk.LEFT, padx=6, pady=8)

        # Auto-Defense Checkbox
        chk_auto = tk.Checkbutton(
            bar,
            text="Auto-Mask Current on Attack",
            variable=self.auto_defense_var,
            font=("Consolas", 8),
            fg=NEON_MINT,
            bg=BG_PANEL,
            activebackground=BG_PANEL,
            activeforeground=NEON_GREEN,
            selectcolor=BG_PANEL_ALT,
            command=self._on_auto_defense_toggle
        )
        chk_auto.pack(side=tk.LEFT, padx=6, pady=8)

        # Retrain Button
        self.btn_retrain = tk.Button(
            bar,
            text="↺ RETRAIN",
            font=("Consolas", 8),
            fg=TEXT_MUTED,
            bg=BG_PANEL_ALT,
            relief=tk.FLAT,
            padx=8,
            pady=3,
            command=self._retrain_baseline
        )
        self.btn_retrain.pack(side=tk.RIGHT, padx=12, pady=8)

    # -------------------------------------------------------------------------
    # MAIN GRID LAYOUT
    # -------------------------------------------------------------------------
    def _build_main_grid(self):
        container = tk.Frame(self.root, bg=BG_DEEP)
        container.pack(fill=tk.BOTH, expand=True, padx=14, pady=6)

        # Top section: Oscilloscope (Left 66%) + Telemetry & Defense HUD (Right 34%)
        top_frame = tk.Frame(container, bg=BG_DEEP)
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self._build_oscilloscope_panel(top_frame)
        self._build_telemetry_hud(top_frame)

        # Bottom section: SSD1306 OLED Mirror (Left 32%) + Terminal Console (Right 68%)
        bottom_frame = tk.Frame(container, bg=BG_DEEP, height=260)
        bottom_frame.pack(fill=tk.X, pady=(0, 4))

        self._build_oled_mirror(bottom_frame)
        self._build_terminal_console(bottom_frame)

    # -------------------------------------------------------------------------
    # OSCILLOSCOPE PANEL
    # -------------------------------------------------------------------------
    def _build_oscilloscope_panel(self, parent):
        panel = tk.Frame(parent, bg=BG_PANEL, highlightbackground=BORDER_GREEN, highlightthickness=1)
        panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        # Panel Header
        hdr = tk.Frame(panel, bg=BG_PANEL)
        hdr.pack(fill=tk.X, padx=12, pady=6)

        title = tk.Label(
            hdr,
            text="POWER TRACE OSCILLOSCOPE [PHYSICAL CURRENT vs ACTIVE MASKING]",
            font=("Consolas", 9, "bold"),
            fg=NEON_GREEN,
            bg=BG_PANEL
        )
        title.pack(side=tk.LEFT)

        # Legend
        legend_box = tk.Frame(hdr, bg=BG_PANEL)
        legend_box.pack(side=tk.RIGHT)

        tk.Label(legend_box, text="■ Normal Waveform", font=("Consolas", 8), fg=NEON_GREEN, bg=BG_PANEL).pack(side=tk.LEFT, padx=4)
        tk.Label(legend_box, text="■ Attack Spike", font=("Consolas", 8), fg=ALERT_RED, bg=BG_PANEL).pack(side=tk.LEFT, padx=4)
        tk.Label(legend_box, text="■ Dynamic Masking Wave", font=("Consolas", 8), fg=CYAN_LINE, bg=BG_PANEL).pack(side=tk.LEFT, padx=4)
        tk.Label(legend_box, text="-- Baseline μ", font=("Consolas", 8), fg=TEXT_MUTED, bg=BG_PANEL).pack(side=tk.LEFT, padx=4)

        # Oscilloscope Canvas
        self.osc_canvas = tk.Canvas(
            panel,
            bg="#020603",
            highlightthickness=1,
            highlightbackground=BORDER_GREEN
        )
        self.osc_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    # -------------------------------------------------------------------------
    # TELEMETRY & ACTIVE DEFENSE HUD
    # -------------------------------------------------------------------------
    def _build_telemetry_hud(self, parent):
        hud = tk.Frame(parent, bg=BG_PANEL, width=410, highlightbackground=BORDER_GREEN, highlightthickness=1)
        hud.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(6, 0))
        hud.pack_propagate(False)

        hdr = tk.Frame(hud, bg=BG_PANEL)
        hdr.pack(fill=tk.X, padx=12, pady=6)
        tk.Label(
            hdr,
            text="ACTIVE POWER MASKING & TELEMETRY HUD",
            font=("Consolas", 9, "bold"),
            fg=NEON_GREEN,
            bg=BG_PANEL
        ).pack(side=tk.LEFT)

        # Card 1: LIVE CURRENT POWER DRAW
        c1 = self._create_card(hud, "LIVE POWER DRAW (mA)")
        self.lbl_curr_val = tk.Label(c1, text="0.00 mA", font=("Consolas", 24, "bold"), fg=NEON_GREEN, bg=BG_PANEL_ALT)
        self.lbl_curr_val.pack(anchor=tk.W, padx=10, pady=(2, 0))

        self.bar_canvas = tk.Canvas(c1, height=10, bg="#07120B", highlightthickness=0)
        self.bar_canvas.pack(fill=tk.X, padx=10, pady=(4, 6))

        # Card 2: CORE COUNTERMEASURE: POWER MASKING & SECRET KEY SECURITY
        c2 = self._create_card(hud, "SIDE-CHANNEL DEFENSE: ACTIVE POWER MASKING")
        grid_c2 = tk.Frame(c2, bg=BG_PANEL_ALT)
        grid_c2.pack(fill=tk.X, padx=10, pady=4)

        tk.Label(grid_c2, text="DEFENSE COUNTERMEASURE:", font=("Consolas", 8), fg=TEXT_MUTED, bg=BG_PANEL_ALT).grid(row=0, column=0, sticky=tk.W)
        self.lbl_defense_status = tk.Label(grid_c2, text="ARMED (STANDBY)", font=("Consolas", 9, "bold"), fg=CYAN_LINE, bg=BG_PANEL_ALT)
        self.lbl_defense_status.grid(row=0, column=1, sticky=tk.E, padx=10)

        tk.Label(grid_c2, text="HACKER KEY CORRELATION:", font=("Consolas", 8), fg=TEXT_MUTED, bg=BG_PANEL_ALT).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.lbl_correlation_val = tk.Label(grid_c2, text="1.2% (SAFE)", font=("Consolas", 9, "bold"), fg=NEON_GREEN, bg=BG_PANEL_ALT)
        self.lbl_correlation_val.grid(row=1, column=1, sticky=tk.E, padx=10, pady=2)

        tk.Label(grid_c2, text="SECRET KEY SECURITY:", font=("Consolas", 8), fg=TEXT_MUTED, bg=BG_PANEL_ALT).grid(row=2, column=0, sticky=tk.W)
        self.lbl_key_val = tk.Label(grid_c2, text="SECURE & SHIELDED 🛡️", font=("Consolas", 9, "bold"), fg=NEON_MINT, bg=BG_PANEL_ALT)
        self.lbl_key_val.grid(row=2, column=1, sticky=tk.E, padx=10)

        # Card 3: BASELINE & CURRENT DRIFT
        c3 = self._create_card(hud, "BASELINE TELEMETRY & JITTER")
        grid_c3 = tk.Frame(c3, bg=BG_PANEL_ALT)
        grid_c3.pack(fill=tk.X, padx=10, pady=4)

        tk.Label(grid_c3, text="IDLE BASELINE (μ):", font=("Consolas", 8), fg=TEXT_MUTED, bg=BG_PANEL_ALT).grid(row=0, column=0, sticky=tk.W)
        self.lbl_base_val = tk.Label(grid_c3, text="-- mA", font=("Consolas", 9, "bold"), fg=CYAN_LINE, bg=BG_PANEL_ALT)
        self.lbl_base_val.grid(row=0, column=1, sticky=tk.E, padx=10)

        tk.Label(grid_c3, text="CURRENT SHIFT (Δ):", font=("Consolas", 8), fg=TEXT_MUTED, bg=BG_PANEL_ALT).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.lbl_delta_val = tk.Label(grid_c3, text="0.00 mA", font=("Consolas", 9, "bold"), fg=TEXT_WHITE, bg=BG_PANEL_ALT)
        self.lbl_delta_val.grid(row=1, column=1, sticky=tk.E, padx=10, pady=2)

        tk.Label(grid_c3, text="MASKING CURRENT INJECTED:", font=("Consolas", 8), fg=TEXT_MUTED, bg=BG_PANEL_ALT).grid(row=2, column=0, sticky=tk.W)
        self.lbl_entropy_val = tk.Label(grid_c3, text="0.00 mA (Idle)", font=("Consolas", 9, "bold"), fg=CYAN_LINE, bg=BG_PANEL_ALT)
        self.lbl_entropy_val.grid(row=2, column=1, sticky=tk.E, padx=10)

        # Card 4: AI & 2-WAY PROTOCOL
        c4 = self._create_card(hud, "AI MODEL & 2-WAY SERIAL FEEDBACK")
        grid_c4 = tk.Frame(c4, bg=BG_PANEL_ALT)
        grid_c4.pack(fill=tk.X, padx=10, pady=4)

        tk.Label(grid_c4, text="ONE-CLASS SVM INFERENCE:", font=("Consolas", 8), fg=TEXT_MUTED, bg=BG_PANEL_ALT).grid(row=0, column=0, sticky=tk.W)
        self.lbl_svm_val = tk.Label(grid_c4, text="NORMAL (+1)", font=("Consolas", 9, "bold"), fg=NEON_GREEN, bg=BG_PANEL_ALT)
        self.lbl_svm_val.grid(row=0, column=1, sticky=tk.E, padx=10)

        tk.Label(grid_c4, text="2-WAY PROTOCOL OUT:", font=("Consolas", 8), fg=TEXT_MUTED, bg=BG_PANEL_ALT).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.lbl_serial_feed = tk.Label(grid_c4, text="Sent: b'0' (Secure)", font=("Consolas", 9, "bold"), fg=NEON_GREEN, bg=BG_PANEL_ALT)
        self.lbl_serial_feed.grid(row=1, column=1, sticky=tk.E, padx=10, pady=2)

        tk.Label(grid_c4, text="TELEMETRY SAMPLING:", font=("Consolas", 8), fg=TEXT_MUTED, bg=BG_PANEL_ALT).grid(row=2, column=0, sticky=tk.W)
        self.lbl_rate_val = tk.Label(grid_c4, text="0.0 Hz (0 pkts)", font=("Consolas", 9), fg=TEXT_MUTED, bg=BG_PANEL_ALT)
        self.lbl_rate_val.grid(row=2, column=1, sticky=tk.E, padx=10)

    def _create_card(self, parent, title_text: str) -> tk.Frame:
        card = tk.Frame(parent, bg=BG_PANEL_ALT, highlightbackground=BORDER_GREEN, highlightthickness=1)
        card.pack(fill=tk.X, padx=10, pady=3)
        tk.Label(
            card,
            text=f"// {title_text}",
            font=("Consolas", 8, "bold"),
            fg=TEXT_MUTED,
            bg=BG_PANEL_ALT
        ).pack(anchor=tk.W, padx=8, pady=(4, 2))
        return card

    # -------------------------------------------------------------------------
    # OLED MIRROR (REPLICATING SSD1306 128x64 DISPLAY)
    # -------------------------------------------------------------------------
    def _build_oled_mirror(self, parent):
        frame = tk.Frame(parent, bg=BG_PANEL, width=360, highlightbackground=BORDER_GREEN, highlightthickness=1)
        frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        frame.pack_propagate(False)

        hdr = tk.Frame(frame, bg=BG_PANEL)
        hdr.pack(fill=tk.X, padx=10, pady=6)
        tk.Label(
            hdr,
            text="HARDWARE OLED MIRROR [SSD1306 128x64]",
            font=("Consolas", 8, "bold"),
            fg=NEON_GREEN,
            bg=BG_PANEL
        ).pack(side=tk.LEFT)

        # OLED Display Bezel Canvas (Scaled 2x: 256 x 128)
        self.oled_canvas = tk.Canvas(
            frame,
            width=256,
            height=128,
            bg="#020402",
            highlightthickness=2,
            highlightbackground="#142B1C"
        )
        self.oled_canvas.pack(padx=10, pady=(2, 6))

        tk.Label(
            frame,
            text="Physical ESP32 I2C Display (Shows Active Power Masking)",
            font=("Consolas", 7),
            fg=TEXT_MUTED,
            bg=BG_PANEL
        ).pack(pady=(0, 4))

    # -------------------------------------------------------------------------
    # TERMINAL CONSOLE
    # -------------------------------------------------------------------------
    def _build_terminal_console(self, parent):
        frame = tk.Frame(parent, bg=BG_PANEL, highlightbackground=BORDER_GREEN, highlightthickness=1)
        frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(6, 0))

        hdr = tk.Frame(frame, bg=BG_PANEL)
        hdr.pack(fill=tk.X, padx=10, pady=4)

        tk.Label(
            hdr,
            text="SERIAL & POWER MASKING EVENT STREAM CONSOLE",
            font=("Consolas", 9, "bold"),
            fg=NEON_GREEN,
            bg=BG_PANEL
        ).pack(side=tk.LEFT)

        btn_box = tk.Frame(hdr, bg=BG_PANEL)
        btn_box.pack(side=tk.RIGHT)

        tk.Checkbutton(
            btn_box,
            text="Autoscroll",
            variable=self.autoscroll_var,
            font=("Consolas", 8),
            fg=TEXT_MUTED,
            bg=BG_PANEL,
            activebackground=BG_PANEL,
            activeforeground=NEON_GREEN,
            selectcolor=BG_PANEL_ALT
        ).pack(side=tk.LEFT, padx=6)

        tk.Button(
            btn_box,
            text="Clear",
            font=("Consolas", 8),
            fg=TEXT_MUTED,
            bg=BG_PANEL_ALT,
            relief=tk.FLAT,
            command=self._clear_terminal
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            btn_box,
            text="Export Log",
            font=("Consolas", 8),
            fg=NEON_MINT,
            bg=BG_PANEL_ALT,
            relief=tk.FLAT,
            command=self._export_log
        ).pack(side=tk.LEFT, padx=4)

        self.term_text = tk.Text(
            frame,
            bg="#030804",
            fg=NEON_GREEN,
            insertbackground=NEON_GREEN,
            font=("Consolas", 8),
            wrap=tk.WORD,
            highlightthickness=0,
            borderwidth=0,
            height=9
        )
        scroll = tk.Scrollbar(frame, command=self.term_text.yview, bg=BG_PANEL)
        self.term_text.configure(yscrollcommand=scroll.set)

        scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 4), pady=4)
        self.term_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=4)

        self.term_text.tag_config("ALERT", foreground=ALERT_RED)
        self.term_text.tag_config("SUCCESS", foreground="#33FF88")
        self.term_text.tag_config("TRAIN", foreground=CYAN_LINE)
        self.term_text.tag_config("WARN", foreground=WARN_YELLOW)
        self.term_text.tag_config("ERROR", foreground="#FF5555")
        self.term_text.tag_config("DEFAULT", foreground=NEON_GREEN)

    # -------------------------------------------------------------------------
    # FOOTER BAR
    # -------------------------------------------------------------------------
    def _build_status_footer(self):
        footer = tk.Frame(self.root, bg=BG_PANEL, height=24)
        footer.pack(fill=tk.X, side=tk.BOTTOM, padx=14, pady=(2, 6))

        self.lbl_foot_info = tk.Label(
            footer,
            text="Ready. When current changes (via button), the system activates dynamic current masking to prevent attack.",
            font=("Consolas", 8),
            fg=TEXT_MUTED,
            bg=BG_PANEL
        )
        self.lbl_foot_info.pack(side=tk.LEFT, padx=6)

        lbl_foot_credit = tk.Label(
            footer,
            text="AI-SCA Dynamic Power Masking Engine v2.1",
            font=("Consolas", 8),
            fg=BORDER_GREEN,
            bg=BG_PANEL
        )
        lbl_foot_credit.pack(side=tk.RIGHT, padx=6)

    # -------------------------------------------------------------------------
    # EVENT HANDLERS & ENGINE LISTENER
    # -------------------------------------------------------------------------
    def _on_engine_event(self, event_type: str, data: dict):
        self.root.after(0, self._process_event, event_type, data)

    def _process_event(self, event_type: str, data: dict):
        if event_type == "state_change":
            self.current_state = data.get("state", SystemState.DISCONNECTED)
            self._update_status_pill()

        elif event_type == "telemetry_sample":
            self.cached_current = data.get("current_mA", 0.0)
            self.cached_samples = data.get("sample_count", 0)
            self.cached_rate = data.get("rate", 0.0)

        elif event_type == "training_progress":
            win = data.get("window", 0)
            tot = data.get("total", 10)
            pct = data.get("percent", 0)
            self.train_progress_text = f"{win}/{tot} ({pct}%)"

        elif event_type == "ml_evaluation":
            self.cached_current = data.get("current_mA", 0.0)
            self.cached_mean = data.get("window_mean", 0.0)
            self.cached_baseline = data.get("baseline_mean", 0.0)
            self.cached_delta = data.get("delta_mA", 0.0)
            self.cached_prediction = data.get("svm_prediction", 1)
            self.cached_attacker = data.get("attacker_active", False)
            self.cached_defense = data.get("defense_active", False)
            self.cached_correlation = data.get("hacker_correlation", 1.2)
            self.cached_key_status = data.get("secret_key_status", "SECURE")
            self.is_trained = True

        elif event_type == "attacker_signal":
            self.cached_attacker = data.get("active", False)

        elif event_type == "defense_change":
            self.cached_defense = data.get("active", False)

        elif event_type == "log":
            entry = data.get("entry", "")
            level = data.get("level", "DEFAULT")
            self._append_terminal(entry, level)

    def _append_terminal(self, text: str, level: str = "DEFAULT"):
        tag = level if level in ("ALERT", "SUCCESS", "TRAIN", "WARN", "ERROR") else "DEFAULT"
        self.term_text.insert(tk.END, text + "\n", tag)
        try:
            line_count = int(self.term_text.index('end-1c').split('.')[0])
            if line_count > 250:
                self.term_text.delete('1.0', '50.0')
        except Exception:
            pass
        if self.autoscroll_var.get():
            self.term_text.see(tk.END)

    def _clear_terminal(self):
        self.term_text.delete("1.0", tk.END)

    def _export_log(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Log", "*.txt"), ("CSV Log", "*.csv"), ("All Files", "*.*")]
        )
        if path:
            try:
                content = self.term_text.get("1.0", tk.END)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("Export Successful", f"Log saved to:\n{path}")
            except Exception as e:
                messagebox.showerror("Export Failed", str(e))

    # -------------------------------------------------------------------------
    # USER ACTIONS
    # -------------------------------------------------------------------------
    def _refresh_ports(self):
        ports = DetectorEngine.get_available_ports()
        device_names = [f"{p['port']} - {p['description']}" for p in ports]
        raw_ports = [p["port"] for p in ports]

        if not raw_ports:
            raw_ports = ["COM7 (Virtual/Manual)"]
            device_names = ["COM7 - Virtual / Not Connected"]

        self.port_combo["values"] = device_names
        for i, p in enumerate(raw_ports):
            if "COM7" in p.upper():
                self.port_combo.current(i)
                break
        else:
            self.port_combo.current(0)

    def _toggle_connect(self):
        if self.engine.is_running:
            self.engine.stop()
            self.btn_connect.configure(text="CONNECT ESP32", bg=NEON_GREEN, fg=BG_DEEP)
            self.lbl_foot_info.configure(text="Disconnected from ESP32.")
        else:
            selected_str = self.selected_port.get()
            port = selected_str.split(" ")[0] if " " in selected_str else selected_str
            baud = int(self.selected_baud.get())
            sim = self.is_sim_mode.get()

            self.engine.start(port=port, baud_rate=baud, simulation=sim)
            self.btn_connect.configure(text="DISCONNECT", bg=ALERT_RED, fg=TEXT_WHITE)
            mode_str = "Virtual Simulation" if sim else f"Hardware ({port})"
            self.lbl_foot_info.configure(text=f"Connected in {mode_str} mode. Press button to test current change & defense!")

    def _on_sim_mode_toggle(self):
        if self.engine.is_running:
            self._toggle_connect()
            self._toggle_connect()

    def _retrain_baseline(self):
        if self.engine.is_running:
            self.engine.retrain()
        else:
            messagebox.showinfo("Not Connected", "Please connect to ESP32 or enable Simulation Mode first.")

    def _toggle_physical_change(self):
        """Simulate pressing the hardware button that changes physical current."""
        if not self.engine.is_running:
            messagebox.showinfo("Not Connected", "Please connect to ESP32 or start Simulation Mode to test.")
            return

        is_active = self.engine.trigger_physical_change()
        self._sync_attack_button(is_active)

    def _force_safe_mode(self):
        """Force the system into safe / secure mode and turn off disturbance."""
        if not self.engine.is_running:
            messagebox.showinfo("Not Connected", "Please connect to ESP32 or start Simulation Mode first.")
            return

        self.engine.reset_to_safe()
        self._sync_attack_button(False)

    def _sync_attack_button(self, is_active: bool):
        if is_active:
            self.btn_attack.configure(
                text="⚡ TURN OFF ATTACK (RESTORE NORMAL)",
                bg=ALERT_RED,
                fg=TEXT_WHITE
            )
        else:
            self.btn_attack.configure(
                text="⚡ INJECT ATTACK (CHANGE CURRENT)",
                bg="#3D0B12",
                fg="#FFAAAA"
            )

    def _toggle_defense(self):
        """Manually toggle dynamic power masking defense."""
        if not self.engine.is_running:
            messagebox.showinfo("Not Connected", "Please connect or start simulation mode first.")
            return

        active = self.engine.toggle_defense()
        self.cached_defense = active
        if active:
            self.btn_defense.configure(text="🛡️ POWER MASKING: ON", bg=CYAN_LINE, fg=BG_DEEP)
        else:
            self.btn_defense.configure(text="🛡️ POWER MASKING: OFF", bg=BG_PANEL_ALT, fg=TEXT_MUTED)

    def _on_auto_defense_toggle(self):
        enabled = self.auto_defense_var.get()
        self.engine.set_auto_defense(enabled)

    # -------------------------------------------------------------------------
    # PERIODIC GUI TICK & RENDERING (30 FPS)
    # -------------------------------------------------------------------------
    def _gui_tick(self):
        try:
            self._update_hud()
            self._draw_oscilloscope()
            self._draw_oled_mirror()
        except Exception:
            pass
        finally:
            self.root.after(33, self._gui_tick)

    def _update_status_pill(self):
        if self.current_state == SystemState.DISCONNECTED:
            self.status_pill.configure(text="● SYSTEM OFFLINE", fg="#77887E", bg="#0B150F")
            self.btn_connect.configure(text="CONNECT ESP32", bg=NEON_GREEN, fg=BG_DEEP)
        elif self.current_state == SystemState.CONNECTING:
            self.status_pill.configure(text="◌ CONNECTING...", fg=WARN_YELLOW, bg="#1F1705")
        elif self.current_state == SystemState.TRAINING:
            self.status_pill.configure(text=f"⚙ BASELINE CALIBRATION [{self.train_progress_text}]", fg=CYAN_LINE, bg="#061D24")
        elif self.current_state == SystemState.SECURE:
            self.status_pill.configure(text="🛡️ SYSTEM SECURE • KEY PROTECTED", fg=NEON_GREEN, bg="#072412")
        elif self.current_state == SystemState.DEFENSE_ACTIVE:
            self.status_pill.configure(text="🛡️ DEFENSE ACTIVE: POWER MASKING ON (KEY SHIELDED)", fg=BG_DEEP, bg=CYAN_LINE)
        elif self.current_state == SystemState.ATTACK_DETECTED:
            self.status_pill.configure(text="🚨 ATTACK DETECTED: PHYSICAL CURRENT CHANGE!", fg=TEXT_WHITE, bg=ALERT_RED)
        elif self.current_state == SystemState.ERROR:
            self.status_pill.configure(text="✕ COM ERROR / PORT BUSY", fg="#FFAAAA", bg="#330A0E")
            self.btn_connect.configure(text="CONNECT ESP32", bg=NEON_GREEN, fg=BG_DEEP)

    def _update_hud(self):
        # 1. Live Current
        self.lbl_curr_val.configure(text=f"{self.cached_current:.2f} mA")
        if self.current_state == SystemState.ATTACK_DETECTED:
            self.lbl_curr_val.configure(fg=ALERT_RED)
        elif self.current_state == SystemState.DEFENSE_ACTIVE:
            self.lbl_curr_val.configure(fg=CYAN_LINE)
        else:
            self.lbl_curr_val.configure(fg=NEON_GREEN)

        self.bar_canvas.delete("all")
        w = self.bar_canvas.winfo_width()
        if w > 10:
            ratio = min(max(self.cached_current / 220.0, 0.0), 1.0)
            fill_w = int(w * ratio)
            if self.current_state == SystemState.DEFENSE_ACTIVE:
                bar_color = CYAN_LINE
            elif self.current_state == SystemState.ATTACK_DETECTED:
                bar_color = ALERT_RED
            else:
                bar_color = NEON_GREEN
            self.bar_canvas.create_rectangle(0, 0, fill_w, 10, fill=bar_color, width=0)

        # 2. Defense Status & Correlation
        if self.cached_defense or self.current_state == SystemState.DEFENSE_ACTIVE:
            self.lbl_defense_status.configure(text="MASKING ACTIVE 🛡️", fg=CYAN_LINE)
            self.lbl_correlation_val.configure(text=f"{self.cached_correlation}% (UNBREAKABLE)", fg=NEON_GREEN)
            self.lbl_key_val.configure(text="SHIELDED / MASKED 🛡️", fg=CYAN_LINE)
            self.lbl_entropy_val.configure(text="+35 mA Jitter Noise", fg=CYAN_LINE)
        elif self.current_state == SystemState.ATTACK_DETECTED:
            self.lbl_defense_status.configure(text="ALERT: NO MASKING", fg=ALERT_RED)
            self.lbl_correlation_val.configure(text=f"{self.cached_correlation}% (CRITICAL LEAK!)", fg=ALERT_RED)
            self.lbl_key_val.configure(text="VULNERABLE TO SNOOPING!", fg=ALERT_RED)
            self.lbl_entropy_val.configure(text="0.00 mA (Unprotected)", fg=TEXT_MUTED)
        else:
            self.lbl_defense_status.configure(text="ARMED (STANDBY)", fg=NEON_MINT)
            self.lbl_correlation_val.configure(text="1.2% (IDLE / SAFE)", fg=NEON_GREEN)
            self.lbl_key_val.configure(text="SECURE & SAFE", fg=NEON_MINT)
            self.lbl_entropy_val.configure(text="0.00 mA (Idle)", fg=TEXT_MUTED)

        # 3. Baseline & Delta
        self._sync_attack_button(self.cached_attacker)
        if self.cached_baseline > 0.0:
            self.lbl_base_val.configure(text=f"{self.cached_baseline:.2f} mA")
        else:
            self.lbl_base_val.configure(text="Calibrating...")

        sign = "+" if self.cached_delta >= 0 else ""
        self.lbl_delta_val.configure(text=f"{sign}{self.cached_delta:.2f} mA")

        # 4. SVM & Protocol
        if not self.is_trained:
            self.lbl_svm_val.configure(text="TRAINING BASELINE...", fg=CYAN_LINE)
        else:
            if self.cached_prediction == -1:
                self.lbl_svm_val.configure(text="SVM: ANOMALY (-1)", fg=ALERT_RED)
            else:
                self.lbl_svm_val.configure(text="SVM: NORMAL (+1)", fg=NEON_GREEN)

        if self.cached_defense or self.current_state in (SystemState.DEFENSE_ACTIVE, SystemState.ATTACK_DETECTED):
            self.lbl_serial_feed.configure(text="Sent: b'1' (Defense ON)", fg=CYAN_LINE)
        else:
            self.lbl_serial_feed.configure(text="Sent: b'0' (Secure)", fg=NEON_GREEN)

        self.lbl_rate_val.configure(text=f"{self.cached_rate:.1f} Hz ({self.cached_samples} samples)")

    # -------------------------------------------------------------------------
    # OSCILLOSCOPE DRAWING ROUTINE
    # -------------------------------------------------------------------------
    def _draw_oscilloscope(self):
        c = self.osc_canvas
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 50 or h < 50:
            return

        c.delete("all")

        margin_left = 55
        margin_right = 15
        margin_top = 20
        margin_bottom = 25
        plot_w = w - margin_left - margin_right
        plot_h = h - margin_top - margin_bottom

        max_y_ma = 200.0
        y_steps = [0, 50, 100, 150, 200]

        # Horizontal Grid
        for ma in y_steps:
            norm_y = 1.0 - (ma / max_y_ma)
            y_pos = margin_top + (norm_y * plot_h)
            c.create_line(margin_left, y_pos, w - margin_right, y_pos, fill=GRID_COLOR, width=1, dash=(3, 5))
            c.create_text(margin_left - 8, y_pos, text=f"{ma} mA", fill=TEXT_MUTED, font=("Consolas", 8), anchor=tk.E)

        # Baseline Reference Line
        if self.cached_baseline > 0:
            norm_base = 1.0 - (self.cached_baseline / max_y_ma)
            y_base = margin_top + (norm_base * plot_h)
            c.create_line(margin_left, y_base, w - margin_right, y_base, fill=CYAN_LINE, width=1, dash=(5, 3))
            c.create_text(w - margin_right - 4, y_base - 8, text=f"Baseline {self.cached_baseline:.1f}mA", fill=CYAN_LINE, font=("Consolas", 7), anchor=tk.E)

        snapshot = self.engine.get_snapshot()
        data = snapshot["graph_data"]

        if len(data) >= 2:
            num_points = len(data)
            dx = plot_w / (max(num_points - 1, 1))

            # Dynamic color coding:
            # - DEFENSE_ACTIVE: Vibrant Cyan / Neon Green masked wave
            # - ATTACK_DETECTED: Alert Red spike
            # - SECURE: Pure Neon Green
            if self.current_state == SystemState.DEFENSE_ACTIVE or self.cached_defense:
                trace_color = CYAN_LINE
                glow_color = "#07333B"
            elif self.current_state == SystemState.ATTACK_DETECTED:
                trace_color = ALERT_RED
                glow_color = "#4D0A14"
            else:
                trace_color = NEON_GREEN
                glow_color = "#083318"

            coords = []
            for i, val in enumerate(data):
                px = margin_left + (i * dx)
                clamped_val = min(max(val, 0.0), max_y_ma)
                py = margin_top + (plot_h * (1.0 - (clamped_val / max_y_ma)))
                coords.append((px, py))

            # Fill under waveform
            fill_poly = [margin_left, margin_top + plot_h]
            for px, py in coords:
                fill_poly.extend([px, py])
            fill_poly.extend([margin_left + plot_w, margin_top + plot_h])
            c.create_polygon(fill_poly, fill=glow_color, outline="")

            # Glowing trace line
            for i in range(len(coords) - 1):
                p1 = coords[i]
                p2 = coords[i + 1]
                c.create_line(p1[0], p1[1], p2[0], p2[1], fill=trace_color, width=3, capstyle=tk.ROUND)

            # Center crisp trace line
            for i in range(len(coords) - 1):
                p1 = coords[i]
                p2 = coords[i + 1]
                c.create_line(p1[0], p1[1], p2[0], p2[1], fill=TEXT_WHITE if (self.current_state in (SystemState.DEFENSE_ACTIVE, SystemState.ATTACK_DETECTED)) else NEON_GREEN, width=1.5, capstyle=tk.ROUND)

            last_p = coords[-1]
            c.create_oval(last_p[0] - 4, last_p[1] - 4, last_p[0] + 4, last_p[1] + 4, fill=trace_color, outline=TEXT_WHITE, width=1)

        # Header readout overlay
        status_banner = "DYNAMIC POWER MASKING ENGAGED [KEY SAFE]" if (self.cached_defense or self.current_state == SystemState.DEFENSE_ACTIVE) else ("PHYSICAL SNOOPING SPIKE" if self.current_state == SystemState.ATTACK_DETECTED else "STEADY IDLE CURRENT")
        c.create_text(
            margin_left + 10,
            margin_top + 12,
            text=f"LIVE CURRENT: {self.cached_current:.2f} mA  |  STATUS: {status_banner}",
            fill=CYAN_LINE if (self.cached_defense or self.current_state == SystemState.DEFENSE_ACTIVE) else NEON_MINT,
            font=("Consolas", 8, "bold"),
            anchor=tk.W
        )

    # -------------------------------------------------------------------------
    # HARDWARE SSD1306 OLED MIRROR
    # -------------------------------------------------------------------------
    def _draw_oled_mirror(self):
        c = self.oled_canvas
        c.delete("all")

        is_defending = (self.cached_defense or self.current_state in (SystemState.DEFENSE_ACTIVE, SystemState.ATTACK_DETECTED))

        # Status Header
        if is_defending:
            c.create_rectangle(0, 0, 256, 28, fill="#FFFFFF", outline="")
            c.create_text(128, 14, text="! DEFENSE: MASKING !", fill="#000000", font=("Consolas", 10, "bold"))
        else:
            c.create_rectangle(0, 0, 256, 28, fill="#020804", outline="#1F4D2A")
            c.create_text(70, 14, text="ML STATUS: SECURE", fill="#FFFFFF", font=("Consolas", 9, "bold"))
            c.create_text(220, 14, text=f"{int(self.cached_current)}mA", fill="#FFFFFF", font=("Consolas", 9, "bold"))

        # Key & Attack State
        key_text = "KEY: PROTECTED 🛡️" if is_defending else "KEY: IDLE"
        c.create_text(60, 42, text=key_text, fill="#FFFFFF", font=("Consolas", 8, "bold"))

        att_str = "ATTACK: ON [PROBE]" if self.cached_attacker else "ATTACK: OFF"
        c.create_text(190, 42, text=att_str, fill="#FFFFFF", font=("Consolas", 8))

        # Mini OLED Waveform
        snapshot = self.engine.get_snapshot()
        oled_data = snapshot["oled_data"]

        graph_top = 56
        graph_bottom = 122
        graph_h = graph_bottom - graph_top

        if len(oled_data) >= 2:
            max_oled_ma = 200.0
            scale_x = 256.0 / 128.0

            for i in range(len(oled_data) - 1):
                v1 = min(max(oled_data[i], 0.0), max_oled_ma)
                v2 = min(max(oled_data[i + 1], 0.0), max_oled_ma)

                y1 = graph_bottom - ((v1 / max_oled_ma) * graph_h)
                y2 = graph_bottom - ((v2 / max_oled_ma) * graph_h)

                x1 = i * scale_x
                x2 = (i + 1) * scale_x

                c.create_line(x1, y1, x2, y2, fill="#FFFFFF", width=1.5)

    # -------------------------------------------------------------------------
    # CLEANUP
    # -------------------------------------------------------------------------
    def _on_close(self):
        if self.engine.is_running:
            self.engine.stop()
        self.root.destroy()
        sys.exit(0)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
def main():
    root = tk.Tk()
    app = CyberpunkGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
