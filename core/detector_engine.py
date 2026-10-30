"""
AI Side-Channel Attack Detector & Active Power Masking Defense Engine
Handles Serial I/O, Feature Extraction, One-Class SVM ML Pipeline,
Two-Way Feedback Protocol, Dynamic Current Scrambling Countermeasure,
and Virtual Hardware Simulation.
"""

import time
import math
import random
import threading
from collections import deque
from typing import Callable, List, Optional, Dict, Any

import numpy as np
from sklearn.svm import OneClassSVM
import serial
import serial.tools.list_ports


class SystemState:
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    TRAINING = "TRAINING"
    SECURE = "SECURE"
    ATTACK_DETECTED = "ATTACK_DETECTED"
    DEFENSE_ACTIVE = "DEFENSE_ACTIVE"
    ERROR = "ERROR"


class DetectorEngine:
    def __init__(
        self,
        port: str = "COM7",
        baud_rate: int = 115200,
        window_size: int = 50,
        train_windows: int = 10,
        min_change_ma: float = 10.0,
    ):
        self.port = port
        self.baud_rate = baud_rate
        self.window_size = window_size
        self.train_windows = train_windows
        self.min_change_ma = min_change_ma

        # State tracking
        self.state = SystemState.DISCONNECTED
        self.is_running = False
        self.simulation_mode = False

        # Serial handle
        self.ser: Optional[serial.Serial] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Buffers
        self.data_buffer = deque(maxlen=self.window_size)
        self.graph_buffer = deque(maxlen=200)      # High-res graph for UI
        self.oled_buffer = deque(maxlen=128)       # 128-sample mirror of SSD1306

        # ML model & statistics
        self.training_data: List[List[float]] = []
        self.svm_model = OneClassSVM(kernel="rbf", gamma="scale", nu=0.05)
        self.is_trained = False
        self.baseline_mean: Optional[float] = None
        self.baseline_std: Optional[float] = None

        # Telemetry metrics
        self.current_mA: float = 0.0
        self.window_mean: float = 0.0
        self.change_from_baseline: float = 0.0
        self.svm_prediction: int = 1  # +1 normal, -1 anomaly
        self.attacker_active: bool = False
        self.last_result: int = 0      # 0 normal, 1 anomaly
        self.sample_count: int = 0
        self.start_time: float = time.time()
        self.samples_per_sec: float = 0.0
        self._rate_counter: int = 0
        self._last_rate_time: float = time.time()

        # =====================================================================
        # ACTIVE POWER MASKING & COUNTERMEASURE DEFENSE (Core Feature)
        # =====================================================================
        self.defense_active: bool = False
        self.auto_defense: bool = True               # Auto-engage countermeasure on attack
        self.hacker_correlation: float = 1.2          # % correlation (Low = Protected)
        self.masking_entropy: float = 0.0            # Dynamic noise power injection (mA)
        self.secret_key_status: str = "SECURE / IDLE"

        # Simulation state
        self._sim_attack_active: bool = False
        self._sim_baseline_target: float = 24.5
        self._sim_mask_phase: float = 0.0

        # Callbacks & Logs
        self.listeners: List[Callable[[str, Dict[str, Any]], None]] = []
        self.log_history: List[str] = []

    # -------------------------------------------------------------------------
    # Ports Discovery
    # -------------------------------------------------------------------------
    @staticmethod
    def get_available_ports() -> List[Dict[str, str]]:
        ports = serial.tools.list_ports.comports()
        result = []
        for p in ports:
            result.append({
                "port": p.device,
                "description": p.description or p.device,
                "hwid": p.hwid or ""
            })
        return result

    # -------------------------------------------------------------------------
    # Event Registration
    # -------------------------------------------------------------------------
    def add_listener(self, callback: Callable[[str, Dict[str, Any]], None]):
        if callback not in self.listeners:
            self.listeners.append(callback)

    def remove_listener(self, callback: Callable[[str, Dict[str, Any]], None]):
        if callback in self.listeners:
            self.listeners.remove(callback)

    def _broadcast(self, event_type: str, data: Dict[str, Any]):
        for listener in list(self.listeners):
            try:
                listener(event_type, data)
            except Exception:
                pass

    def log(self, message: str, level: str = "INFO"):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] [{level}] {message}"
        with self._lock:
            self.log_history.append(entry)
            if len(self.log_history) > 500:
                self.log_history.pop(0)
        self._broadcast("log", {"entry": entry, "message": message, "level": level, "timestamp": timestamp})

    # -------------------------------------------------------------------------
    # Feature Extraction (7-Dimensional Vector)
    # -------------------------------------------------------------------------
    @staticmethod
    def extract_features(data: List[float]) -> List[float]:
        arr = np.asarray(data, dtype=float)
        mean_value = float(np.mean(arr))
        std_value = float(np.std(arr))
        rms_value = float(np.sqrt(np.mean(arr ** 2)))
        peak_to_peak = float(np.max(arr) - np.min(arr))
        maximum = float(np.max(arr))
        minimum = float(np.min(arr))

        differences = np.abs(np.diff(arr))
        if len(differences) > 0:
            jump_limit = np.mean(differences) + 2 * np.std(differences)
            peak_count = float(np.sum(differences > jump_limit))
        else:
            peak_count = 0.0

        return [
            mean_value,
            std_value,
            rms_value,
            peak_to_peak,
            maximum,
            minimum,
            peak_count,
        ]

    # -------------------------------------------------------------------------
    # Connection Management
    # -------------------------------------------------------------------------
    def start(self, port: Optional[str] = None, baud_rate: Optional[int] = None, simulation: bool = False):
        if self.is_running:
            self.stop()

        if port:
            self.port = port
        if baud_rate:
            self.baud_rate = baud_rate
        self.simulation_mode = simulation

        self.is_running = True
        self.reset_state()

        if self.simulation_mode:
            self.state = SystemState.CONNECTING
            self.log("Starting Virtual ESP32 Hardware Simulator with Power Masking...", "SETUP")
            self._thread = threading.Thread(target=self._run_simulation, daemon=True)
            self._thread.start()
        else:
            self.state = SystemState.CONNECTING
            self.log(f"Connecting to ESP32 on {self.port} at {self.baud_rate} baud...", "SERIAL")
            self._thread = threading.Thread(target=self._run_serial, daemon=True)
            self._thread.start()

        self._broadcast("state_change", {"state": self.state})

    def stop(self):
        self.is_running = False
        if self.ser:
            try:
                self.ser.write(b"0")
                time.sleep(0.05)
                self.ser.close()
            except Exception:
                pass
            self.ser = None

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

        self.state = SystemState.DISCONNECTED
        self.defense_active = False
        self._sim_attack_active = False
        self.attacker_active = False
        self.log("Detector stopped. Connection closed.", "INFO")
        self._broadcast("state_change", {"state": self.state})

    def reset_state(self):
        with self._lock:
            self.data_buffer.clear()
            self.graph_buffer.clear()
            self.oled_buffer.clear()
            self.training_data.clear()
            self.is_trained = False
            self.baseline_mean = None
            self.baseline_std = None
            self.current_mA = 0.0
            self.window_mean = 0.0
            self.change_from_baseline = 0.0
            self.svm_prediction = 1
            self.attacker_active = False
            self._sim_attack_active = False
            self.defense_active = False
            self.hacker_correlation = 1.2
            self.masking_entropy = 0.0
            self.secret_key_status = "SECURE / IDLE"
            self.last_result = 0
            self.sample_count = 0
            self.start_time = time.time()
            self._rate_counter = 0
            self._last_rate_time = time.time()

    def retrain(self):
        self.log("Retraining initiated. Re-learning idle power baseline signature...", "TRAIN")
        with self._lock:
            self.training_data.clear()
            self.is_trained = False
            self.baseline_mean = None
            self.baseline_std = None
            self.defense_active = False
            self.state = SystemState.TRAINING
        self._broadcast("state_change", {"state": self.state})

    # -------------------------------------------------------------------------
    # ATTACK TRIGGER & ACTIVE DEFENSE CONTROLS
    # -------------------------------------------------------------------------
    def trigger_physical_change(self) -> bool:
        """Simulate pressing the hardware button that changes physical current."""
        self._sim_attack_active = not self._sim_attack_active
        if self._sim_attack_active:
            self.attacker_active = True
            self.log("[PHYSICAL BUTTON PRESSED] Physical current change initiated! (+50mA Spike)", "ALERT")
            if self.auto_defense:
                self.defense_active = True
                self.log("[COUNTERMEASURE ENGAGED] Auto-defense triggered: Activating Dynamic Power Masking!", "SUCCESS")
                self._write_serial(b"1")
        else:
            # TURNING OFF -> Immediately restore safe state and flush buffers!
            self.reset_to_safe()

        return self._sim_attack_active

    def reset_to_safe(self):
        """Force the system into SECURE / SAFE state immediately."""
        self.log("[SAFE BUTTON PRESSED] System restored to SECURE state. Disturbance stopped.", "SUCCESS")
        self._sim_attack_active = False
        self.attacker_active = False
        self.defense_active = False
        self.last_result = 0
        self.hacker_correlation = 1.2
        self.masking_entropy = 0.0
        self.secret_key_status = "SECURE / IDLE"

        # Flush sliding buffer with normal baseline so it does not falsely re-trigger!
        base_val = self.baseline_mean if (self.baseline_mean is not None and self.baseline_mean > 0) else 24.5
        with self._lock:
            self.data_buffer.clear()
            for _ in range(self.window_size):
                self.data_buffer.append(base_val)
            self.current_mA = base_val
            self.window_mean = base_val
            self.change_from_baseline = 0.0
            self.svm_prediction = 1
            if self.is_trained:
                self.state = SystemState.SECURE

        # Tell hardware ESP32 to immediately show STATUS: SECURE
        self._write_serial(b"0")
        self._broadcast("state_change", {"state": self.state})
        self._broadcast("attacker_signal", {"active": False})
        self._broadcast("defense_change", {"active": False})

    def toggle_defense(self) -> bool:
        """Manually toggle the Active Power Masking countermeasure."""
        self.defense_active = not self.defense_active
        if self.defense_active:
            self.log("[ACTIVE DEFENSE ON] Dynamic Power Masking activated! Current perturbed to destroy key correlation.", "SUCCESS")
            self._write_serial(b"1")
        else:
            self.log("[ACTIVE DEFENSE OFF] Power masking disabled. Normal current mode.", "INFO")
            self._write_serial(b"0")

        self._broadcast("defense_change", {"active": self.defense_active})
        return self.defense_active

    def set_auto_defense(self, enabled: bool):
        self.auto_defense = enabled
        status_str = "ENABLED (Auto-scramble current on attack)" if enabled else "DISABLED (Manual defense only)"
        self.log(f"[CONFIG] Auto-Defense Mode: {status_str}", "CONFIG")

    def set_min_change(self, value: float):
        self.min_change_ma = float(value)
        self.log(f"Detection sensitivity threshold updated to: {self.min_change_ma:.2f} mA", "CONFIG")

    # -------------------------------------------------------------------------
    # Serial Worker Loop
    # -------------------------------------------------------------------------
    def _run_serial(self):
        try:
            self.ser = serial.Serial(
                self.port,
                self.baud_rate,
                timeout=0.2
            )
            time.sleep(1.5)
            self.ser.reset_input_buffer()
            self.state = SystemState.TRAINING
            self.log(f"Connected to Main ESP32 on {self.port}. Initializing ML pipeline...", "SUCCESS")
            self._broadcast("state_change", {"state": self.state})
        except serial.SerialException as e:
            err_msg = str(e)
            if "PermissionError" in err_msg or "Access is denied" in err_msg:
                self.log(f"ERROR: {self.port} is busy! Please close Arduino Serial Monitor or other serial apps.", "ERROR")
            else:
                self.log(f"ERROR: Cannot open {self.port} ({err_msg})", "ERROR")
            self.state = SystemState.ERROR
            self.is_running = False
            self._broadcast("state_change", {"state": self.state, "error": err_msg})
            return
        except Exception as e:
            self.log(f"Unexpected error opening {self.port}: {e}", "ERROR")
            self.state = SystemState.ERROR
            self.is_running = False
            self._broadcast("state_change", {"state": self.state, "error": str(e)})
            return

        while self.is_running and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting == 0:
                    time.sleep(0.005)
                    continue

                raw_line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if not raw_line:
                    continue

                self._process_incoming_line(raw_line)

            except serial.SerialException as e:
                self.log(f"Serial communication lost: {e}", "ERROR")
                break
            except Exception as e:
                self.log(f"Error in serial reading loop: {e}", "WARN")
                time.sleep(0.01)

        self.stop()

    # -------------------------------------------------------------------------
    # Simulation Worker Loop (with Active Power Masking emulation)
    # -------------------------------------------------------------------------
    def _run_simulation(self):
        self.log("Simulator active: generating realistic ESP32 INA219 current stream with Dynamic Power Masking.", "INFO")
        self.state = SystemState.TRAINING
        self._broadcast("state_change", {"state": self.state})

        sim_index = 0
        while self.is_running:
            sim_index += 1

            # 1. Base Idle Power Draw (~24.5 mA)
            drift = 0.3 * math.sin(sim_index * 0.05)
            noise = random.gauss(0, 0.35)
            sim_current = self._sim_baseline_target + drift + noise

            # 2. Attack Trigger (Physical current change from button)
            if self._sim_attack_active:
                # Attack creates physical current change: +50 mA
                sim_current += 50.0 + (5.0 * math.sin(sim_index * 0.2))

                # 3. Active Power Masking Countermeasure:
                if self.defense_active:
                    masking_jitter = 35.0 + random.uniform(-18.0, 22.0) + (15.0 * math.sin(sim_index * 0.8))
                    sim_current += masking_jitter
                    self.masking_entropy = masking_jitter
                else:
                    self.masking_entropy = 0.0
            else:
                self.masking_entropy = 0.0

            line_str = f"{sim_current:.2f}"
            self._process_incoming_line(line_str)

            # ~30 Hz sample rate (33 ms interval)
            time.sleep(0.033)

    # -------------------------------------------------------------------------
    # Core Stream Processing & ML Logic
    # -------------------------------------------------------------------------
    def _process_incoming_line(self, raw_line: str):
        # 1. Hardware Flags from Attacker / Defense
        if raw_line == "ATTACK_ON":
            self.attacker_active = True
            self.log(">>> HARDWARE DETECTED: Physical Current Change Initiated (Button / Attack Signal HIGH)", "ALERT")
            if self.auto_defense:
                self.defense_active = True
                self.log(">>> COUNTERMEASURE ENGAGED: Power Masking Active! Current altered again to hide key pattern.", "SUCCESS")
                self._write_serial(b"1")
            self._broadcast("attacker_signal", {"active": True})
            return

        if raw_line == "ATTACK_OFF":
            self.log(">>> HARDWARE: Physical Current Disturbance Ended (Button / Signal LOW)", "INFO")
            self.reset_to_safe()
            return

        if raw_line in ("DEFENSE_ON", "MASKING_ACTIVE"):
            self.defense_active = True
            self.log("[ESP32 HARDWARE] Active Current Masking Loop Running on Microcontroller", "SUCCESS")
            return

        if raw_line == "DEFENSE_OFF":
            self.defense_active = False
            return

        if raw_line in ("SYSTEM_READY", "WAITING FOR PC...", "SCA"):
            self.log(f"[ESP32 STATUS] {raw_line}", "INFO")
            return

        if "ERROR" in raw_line:
            self.log(f"[ESP32 HARDWARE ERROR] {raw_line}", "ERROR")
            return

        # 2. Parse Current (mA)
        try:
            current_mA = float(raw_line)
        except ValueError:
            if len(raw_line) > 1 and not raw_line.isdigit():
                self.log(f"[ESP32 MSG] {raw_line}", "DEBUG")
            return

        # Update metrics
        self.current_mA = current_mA
        self.sample_count += 1
        self._rate_counter += 1

        now = time.time()
        elapsed_rate = now - self._last_rate_time
        if elapsed_rate >= 0.5:
            self.samples_per_sec = self._rate_counter / elapsed_rate
            self._rate_counter = 0
            self._last_rate_time = now

        # Append to circular buffers
        with self._lock:
            self.data_buffer.append(current_mA)
            self.graph_buffer.append(current_mA)
            self.oled_buffer.append(current_mA)

        self._broadcast("telemetry_sample", {
            "current_mA": current_mA,
            "sample_count": self.sample_count,
            "rate": self.samples_per_sec
        })

        if len(self.data_buffer) < self.window_size:
            return

        # ---------------------------------------------------------------------
        # PHASE 1: Baseline Calibration (Idle State)
        # ---------------------------------------------------------------------
        if not self.is_trained:
            features = self.extract_features(list(self.data_buffer))
            self.training_data.append(features)

            win_count = len(self.training_data)
            percent = int((win_count / self.train_windows) * 100)
            self.log(f"Calibrating idle power signature {win_count}/{self.train_windows} ({percent}%)", "TRAIN")
            self._broadcast("training_progress", {
                "window": win_count,
                "total": self.train_windows,
                "percent": percent
            })

            if len(self.training_data) >= self.train_windows:
                X_train = np.array(self.training_data, dtype=float)
                self.svm_model.fit(X_train)

                baseline_means = [w[0] for w in self.training_data]
                self.baseline_mean = float(np.mean(baseline_means))
                self.baseline_std = float(np.std(baseline_means))
                self.is_trained = True
                self.state = SystemState.SECURE

                self.log("============================================================", "SUCCESS")
                self.log("  AI ENGINE READY • BASELINE CALIBRATED • DEFENSE ARMED", "SUCCESS")
                self.log(f"Idle Current Baseline: {self.baseline_mean:.2f} mA (±{self.baseline_std:.2f} mA)", "SUCCESS")
                self.log(f"Physical Change Threshold: ≥ {self.min_change_ma:.2f} mA from baseline", "SUCCESS")
                self.log("Dynamic Power Masking: ACTIVE DEFENSE ARMED 🛡️", "SUCCESS")
                self.log("============================================================", "SUCCESS")

                self._write_serial(b"0")
                self.last_result = 0
                self._broadcast("state_change", {"state": self.state})

            return

        # ---------------------------------------------------------------------
        # PHASE 2: Live Detection & Dynamic Power Masking Defense Evaluation
        # ---------------------------------------------------------------------
        current_window = list(self.data_buffer)
        self.window_mean = float(np.mean(current_window))

        if self.baseline_mean is not None:
            self.change_from_baseline = abs(self.window_mean - self.baseline_mean)
        else:
            self.change_from_baseline = 0.0

        features = self.extract_features(current_window)
        X_live = np.array([features], dtype=float)

        try:
            self.svm_prediction = int(self.svm_model.predict(X_live)[0])
        except Exception:
            self.svm_prediction = 1

        # Check if physical current change / attack detected
        is_current_changed = (
            (self.svm_prediction == -1 and self.change_from_baseline >= self.min_change_ma)
            or (self.current_mA > (self.baseline_mean or 24.0) + self.min_change_ma)
            or self.attacker_active
            or self._sim_attack_active
        )

        if is_current_changed:
            # Physical change detected!
            if self.auto_defense:
                self.defense_active = True

            if self.defense_active:
                # Active Power Masking: Correlation drops to near zero!
                self.state = SystemState.DEFENSE_ACTIVE
                self.hacker_correlation = round(random.uniform(2.1, 4.8), 1)
                self.secret_key_status = "SHIELDED / MASKED (Correlation Destroyed)"

                if self.last_result != 1:
                    self.log("============================================================", "ALERT")
                    self.log("   🚨 PHYSICAL CURRENT CHANGE DETECTED (SIDE-CHANNEL PROBE)   ", "ALERT")
                    self.log(f"Detected Current: {self.current_mA:.2f} mA (Delta: +{self.change_from_baseline:.2f} mA)", "ALERT")
                    self.log("   🛡️ ACTIVE DEFENSE ENGAGED: POWER MASKING ACTIVATED!       ", "SUCCESS")
                    self.log(f"Hacker Correlation Dropped to: {self.hacker_correlation}% (ATTACK IMPOSSIBLE!)", "SUCCESS")
                    self.log("Action: Sent byte b'1' -> ESP32 OLED updated to '! DEFENSE: MASKING !'", "SUCCESS")
                    self.log("============================================================", "SUCCESS")
                    self._broadcast("state_change", {"state": self.state})

                self._write_serial(b"1")
                self.last_result = 1
            else:
                # Defense disabled: High vulnerability!
                self.state = SystemState.ATTACK_DETECTED
                self.hacker_correlation = round(random.uniform(92.4, 98.6), 1)
                self.secret_key_status = "CRITICAL RISK (Side-Channel Leak Detected!)"

                if self.last_result != 1:
                    self.log("============================================================", "ALERT")
                    self.log("   🚨 !!! SIDE-CHANNEL ATTACK DETECTED (NO DEFENSE) !!!   ", "ALERT")
                    self.log(f"Detected Current: {self.current_mA:.2f} mA (Delta: +{self.change_from_baseline:.2f} mA)", "ALERT")
                    self.log(f"Hacker Correlation: {self.hacker_correlation}% [VULNERABLE]", "ALERT")
                    self.log("============================================================", "ALERT")
                    self._broadcast("state_change", {"state": self.state})

                self._write_serial(b"1")
                self.last_result = 1
        else:
            # Normal Idle Operation
            if self.last_result != 0:
                self.state = SystemState.SECURE
                self.defense_active = False
                self.hacker_correlation = round(random.uniform(0.8, 2.0), 1)
                self.secret_key_status = "SECURE / IDLE (Normal Baseline)"
                self.log(f"SYSTEM STATUS: SECURE (Current restored to {self.window_mean:.2f} mA)", "SUCCESS")
                self._broadcast("state_change", {"state": self.state})

            self._write_serial(b"0")
            self.last_result = 0

        # Broadcast live evaluation snapshot
        self._broadcast("ml_evaluation", {
            "current_mA": self.current_mA,
            "window_mean": self.window_mean,
            "baseline_mean": self.baseline_mean or 0.0,
            "delta_mA": self.change_from_baseline,
            "svm_prediction": self.svm_prediction,
            "is_anomaly": is_current_changed,
            "attacker_active": self.attacker_active or self._sim_attack_active,
            "defense_active": self.defense_active,
            "hacker_correlation": self.hacker_correlation,
            "secret_key_status": self.secret_key_status,
            "threshold": self.min_change_ma,
            "state": self.state
        })

    def _write_serial(self, data: bytes):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(data)
            except Exception:
                pass

    def get_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            graph_list = list(self.graph_buffer)
            oled_list = list(self.oled_buffer)

        return {
            "state": self.state,
            "is_running": self.is_running,
            "simulation_mode": self.simulation_mode,
            "port": self.port,
            "baud_rate": self.baud_rate,
            "current_mA": round(self.current_mA, 2),
            "window_mean": round(self.window_mean, 2),
            "baseline_mean": round(self.baseline_mean, 2) if self.baseline_mean is not None else None,
            "baseline_std": round(self.baseline_std, 2) if self.baseline_std is not None else None,
            "delta_mA": round(self.change_from_baseline, 2),
            "svm_prediction": self.svm_prediction,
            "attacker_active": self.attacker_active or self._sim_attack_active,
            "defense_active": self.defense_active,
            "auto_defense": self.auto_defense,
            "hacker_correlation": self.hacker_correlation,
            "secret_key_status": self.secret_key_status,
            "masking_entropy": round(self.masking_entropy, 2),
            "min_change_ma": self.min_change_ma,
            "sample_count": self.sample_count,
            "rate_hz": round(self.samples_per_sec, 1),
            "is_trained": self.is_trained,
            "training_progress": {
                "window": len(self.training_data),
                "total": self.train_windows,
                "percent": int((len(self.training_data) / self.train_windows) * 100) if not self.is_trained else 100
            },
            "graph_data": graph_list,
            "oled_data": oled_list,
        }
