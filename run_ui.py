"""
AI-SCA Side-Channel Attack Detector - Unified Launcher
Allows running either the Cyberpunk Desktop GUI or Cyberpunk Web Dashboard.
Usage:
  python run_ui.py          # Launches Desktop GUI (Default)
  python run_ui.py --web    # Launches Browser Web Dashboard (FastAPI + WebSockets)
  python run_ui.py --cli    # Runs Terminal ML Detector
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description="AI Side-Channel Attack Detector UI Launcher")
    parser.add_argument("--web", action="store_true", help="Launch Cyberpunk Web Dashboard in browser")
    parser.add_argument("--cli", action="store_true", help="Launch Terminal Command-Line Detector")
    parser.add_argument("--port", type=str, default="COM7", help="Serial COM Port (default: COM7)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")

    args = parser.parse_args()

    if args.web:
        print("[LAUNCHER] Launching Cyberpunk Web Dashboard on http://localhost:8000 ...")
        from web_app import run_web
        run_web()
    elif args.cli:
        print(f"[LAUNCHER] Launching Terminal ML Detector on {args.port}...")
        from run_side_channel_detector import run_cli
        run_cli(port=args.port, baud=args.baud)
    else:
        print("[LAUNCHER] Launching Cyberpunk Black & Green Desktop GUI (Tkinter)...")
        import tkinter as tk
        from desktop_gui import CyberpunkGUI
        root = tk.Tk()
        app = CyberpunkGUI(root)
        root.mainloop()


if __name__ == "__main__":
    main()
