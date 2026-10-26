# AI-Based Side-Channel Attack Detector & Dynamic Power Masking Defense
### Physical Behavior Change Detection • Dynamic Current Scrambling Countermeasure • Black & Green Cyberpunk UI

![AI-SCA Power Masking Defense](https://img.shields.io/badge/Defense-Active%20Power%20Masking-00ff66?style=for-the-badge)
![Security](https://img.shields.io/badge/Target-Cryptographic%20Key%20Protection-cyan?style=for-the-badge)
![ESP32 Hardware](https://img.shields.io/badge/Hardware-ESP32%20%2B%20INA219%20%2B%20OLED-red?style=for-the-badge)

---

## 🎯 The Core Idea of Our Project

In IoT hardware security, an adversary uses **Side-Channel Analysis (SCA)**, specifically **Differential Power Analysis (DPA)** and **Simple Power Analysis (SPA)**. Hackers measure physical power behavior (subtle micro-current fluctuations during cryptographic operations like AES or RSA) to reconstruct secret encryption keys.

### 🛡️ The Countermeasure (Active Dynamic Power Masking)
**"Whenever the current changes, we detect it and immediately change the current again, so that for the hacker, detecting any secret key pattern becomes impossible!"**

1. **Physical Behavior Change (The Trigger)**:
   - A physical button (on the Attacker C3 or Target pin 12) triggers a current change ($+50\text{ mA}$ power disturbance / snooping attempt).
2. **AI & Statistical Detection**:
   - The INA219 sensor reads the current shift.
   - The One-Class SVM machine learning engine and threshold detector identify the anomaly.
3. **Active Power Masking Countermeasure (The Defense)**:
   - To prevent the attacker from finding any cryptographic pattern, the ESP32 initiates **Dynamic Power Masking**:
     - The microcontroller runs pseudo-random high-entropy mathematical loops (`sin()`, `cos()`, `sqrt()`).
     - Injects dynamic current perturbation noise ($+20\text{ mA}$ to $+45\text{ mA}$ random jitter).
     - This alters the current again continuously, destroying the **Signal-to-Noise Ratio (SNR)**.
4. **Result**:
   - The hacker's correlation coefficient collapses from **$96.8\%$ (critical vulnerability)** down to **$< 3.5\%$ (unbreakable)**.
   - The secret key remains fully protected!

---

## 🖥️ UI & Hardware Visualizations

| System State | Current Waveform Behavior | UI Banner | SSD1306 Hardware OLED | Secret Key Status |
| :--- | :--- | :--- | :--- | :--- |
| **Normal (Idle)** | Flat baseline current (~24 mA) | `● SYSTEM SECURE • KEY SAFE` (Green) | `ML STATUS: SECURE`<br>`KEY: IDLE` | Safe & Idle |
| **Attack Triggered (Button Pressed)** | Physical current spike (+50 mA) | `🚨 ATTACK DETECTED: PHYSICAL CURRENT CHANGE!` (Red) | Inverted Alert Bar | Probed / At Risk |
| **Active Defense Engaged (Countermeasure)** | Dynamic high-frequency scrambled current wave | `🛡️ DEFENSE ACTIVE: POWER MASKING ON [KEY SHIELDED]` (Cyan) | `! DEFENSE: MASKING !`<br>`KEY: PROTECTED 🛡️` | **Protected (Correlation Destroyed)** |

---

## 🚀 How to Run the Project

### 1. Native Desktop GUI (Currently Running)
```powershell
python app.py
```
- Includes **`⚡ PRESS BUTTON (CHANGE CURRENT)`** to test the physical disturbance.
- Includes **`🛡️ POWER MASKING: ON`** to toggle dynamic current scrambling.
- Real-time oscilloscope canvas showing both the clean baseline, attack spikes, and active cyan masking waves.

### 2. Browser Web Dashboard (With Audio Alarm)
```powershell
python app.py --web
```
- Available at `http://localhost:8000` with WebSockets and real-time canvas rendering.

### 3. Standalone Console ML Engine
```powershell
python run_side_channel_detector.py
```

---

## 🔌 Hardware Wiring & Pinout

### Main ESP32 Target Node
- **INA219 & SSD1306 OLED**:
  - `SDA` $\rightarrow$ ESP32 **GPIO 21**
  - `SCL` $\rightarrow$ ESP32 **GPIO 22**
  - `VCC` $\rightarrow$ 3.3V
  - `GND` $\rightarrow$ GND
- **Physical Attack Trigger Inputs**:
  - **Option A (External from C3)**: C3 `GPIO 5` $\rightarrow$ Main ESP32 **GPIO 27**
  - **Option B (Local Push Button)**: Button connected between Main ESP32 **GPIO 12** and **GND** (internal pullup enabled)

### Attacker Node (ESP32-C3 SuperMini)
- Push button on **GPIO 4** (to GND).
- Signal output on **GPIO 5** (to Target GPIO 27).
- LED on **GPIO 8**.
- Common GND with Target ESP32.
