"""
PDF Generator for Presentation Script & Defense Guide
Generates an executive, publication-grade PDF using ReportLab.
"""

import os
import re
import html
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# ----------------------------------------------------------------------
# COLOR PALETTE (Executive Cyber / Clean Engineering)
# ----------------------------------------------------------------------
PRIMARY = colors.HexColor("#0f172a")        # Slate 900
PRIMARY_TINT = colors.HexColor("#1e293b")   # Slate 800
TEAL_DARK = colors.HexColor("#0f766e")      # Teal 700
TEAL_MID = colors.HexColor("#0d9488")       # Teal 600
EMERALD_GREEN = colors.HexColor("#059669")  # Emerald 600
NEON_CYAN = colors.HexColor("#0284c7")      # Cyan / Sky
ALERT_RED = colors.HexColor("#b91c1c")      # Crimson Red
TEXT_DARK = colors.HexColor("#1e293b")      # Body Slate
TEXT_MUTED = colors.HexColor("#64748b")     # Slate 500
BORDER_LIGHT = colors.HexColor("#cbd5e1")   # Slate 300
BORDER_TEAL = colors.HexColor("#99f6e4")    # Mint Teal Border
BG_LIGHT = colors.HexColor("#f8fafc")       # Light Slate Tint
BG_SCRIPT = colors.HexColor("#f0fdf4")      # Light Mint Script Tint
BG_CODE = colors.HexColor("#0b1120")        # Console Dark
BG_HEADER = colors.HexColor("#0f172a")      # Title Header Dark

# ----------------------------------------------------------------------
# NUMBERED CANVAS (Two-Pass for 'Page X of Y' + Running Headers/Footers)
# ----------------------------------------------------------------------
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_decorations(self, page_count):
        self.saveState()
        page_w, page_h = A4
        left_m = 36
        right_m = page_w - 36

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(TEAL_DARK)
            self.drawString(left_m, page_h - 26, "AI SIDE-CHANNEL DETECTOR & DYNAMIC POWER MASKING DEFENSE")
            self.setFont("Helvetica", 7.5)
            self.setFillColor(TEXT_MUTED)
            self.drawRightString(right_m, page_h - 26, "Final Presentation Script & Defense Guide")
            self.setStrokeColor(BORDER_LIGHT)
            self.setLineWidth(0.6)
            self.line(left_m, page_h - 30, right_m, page_h - 30)

        # Running Footer (all pages)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(TEXT_MUTED)
        self.drawString(left_m, 20, "IoT Physical Security • Unsupervised Anomaly Detection & Active Power Masking")
        self.drawRightString(right_m, 20, f"Page {self._pageNumber} of {page_count}")
        self.setStrokeColor(BORDER_LIGHT)
        self.setLineWidth(0.6)
        self.line(left_m, 30, right_m, 30)

        self.restoreState()


# ----------------------------------------------------------------------
# TEXT SANITIZER & STYLES
# ----------------------------------------------------------------------
def md_to_flowable_xml(text):
    """Safely escapes HTML and transforms markdown tags into ReportLab XML."""
    if not text:
        return ""
    
    # Mathematical and symbol replacements
    math_map = [
        (r'\\mu_{\\Delta}', 'μ_Δ'),
        (r'\\sigma_{\\Delta}', 'σ_Δ'),
        (r'\\mu_{\\text{base}}', 'μ_base'),
        (r'\\mu', 'μ'),
        (r'\\sigma', 'σ'),
        (r'\\gamma', 'γ'),
        (r'\\nu', 'ν'),
        (r'\\alpha_i', 'α_i'),
        (r'\\alpha', 'α'),
        (r'\\rho', 'ρ'),
        (r'\\Delta', 'Δ'),
        (r'\\Omega', 'Ω'),
        (r'\\propto', '∝'),
        (r'\\oplus', '⊕'),
        (r'\\approx', '≈'),
        (r'\\le', '≤'),
        (r'\\ge', '≥'),
        (r'\\pm', '±'),
        (r'\\to', '→'),
        (r'\\lim', 'lim'),
        (r'\\infty', '∞'),
        (r'\\sum', '∑'),
        (r'\\sqrt', '√'),
        (r'\\mathbf{F}', '<b>F</b>'),
        (r'\\mathbf{x}', '<b>x</b>'),
        (r'\\text{S-Box}', 'S-Box'),
        (r'\\text{HW}', 'HW'),
        (r'\\text{RMS}', 'RMS'),
        (r'\\text{P-P}', 'P-P'),
        (r'\\text{sign}', 'sign'),
        (r'\\text{Anomaly}', 'Anomaly'),
        (r'\\text{Signal}', 'Signal'),
        (r'\\text{Hardware}', 'Hardware'),
        (r'\\text{MIN_CHANGE}', 'MIN_CHANGE'),
        (r'\\text{Cov}', 'Cov'),
        (r'\\text{device}', 'device'),
        (r'\\text{crypto}', 'crypto'),
        (r'\\text{attack}', 'attack'),
        (r'\\text{mask}', 'mask'),
        (r'\\text{total}', 'total'),
        (r'\\text{base}', 'base'),
        (r'\\text{ mA}', ' mA'),
        (r'\\text{--}', '–'),
        (r'\\land', 'AND'),
        (r'\\lor', 'OR'),
        (r'\\cdot', '·'),
        (r'\\dots', '...'),
        (r'\\exp', 'exp'),
        (r'\\left(', '('),
        (r'\\right)', ')'),
        (r'\\|', '|'),
        ('$$', ''),
    ]
    for old, new in math_map:
        text = text.replace(old, new)
        
    # Strip remaining $ delimiters from inline math
    text = re.sub(r'\$([^$]+)\$', r'<i>\1</i>', text)
    
    # HTML escape ampersand, less than, greater than
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    # Restore markdown bold **text** -> <b>text</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Restore markdown italic *text* -> <i>text</i>
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', text)
    # Restore markdown code `code` -> Courier monospace
    text = re.sub(r'`(.+?)`', r"<font face='Courier' color='#0f766e'><b>\1</b></font>", text)
    
    return text


def build_styles():
    ss = getSampleStyleSheet()
    
    styles = {
        'Title': ParagraphStyle(
            'DocTitle',
            parent=ss['Title'],
            fontName='Helvetica-Bold',
            fontSize=15,
            leading=19,
            textColor=colors.white,
            alignment=1, # Center
            spaceAfter=4
        ),
        'Subtitle': ParagraphStyle(
            'DocSubtitle',
            parent=ss['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=12.5,
            textColor=colors.HexColor("#99f6e4"),
            alignment=1,
            spaceAfter=5
        ),
        'Badge': ParagraphStyle(
            'DocBadge',
            parent=ss['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor("#e2e8f0"),
            alignment=1,
        ),
        'H1': ParagraphStyle(
            'Heading1_Custom',
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=15,
            textColor=PRIMARY,
            spaceBefore=12,
            spaceAfter=5,
            keepWithNext=True
        ),
        'H2': ParagraphStyle(
            'Heading2_Custom',
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=TEAL_DARK,
            spaceBefore=9,
            spaceAfter=4,
            keepWithNext=True
        ),
        'H3': ParagraphStyle(
            'Heading3_Custom',
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11.5,
            textColor=PRIMARY_TINT,
            spaceBefore=5,
            spaceAfter=3,
            keepWithNext=True
        ),
        'Body': ParagraphStyle(
            'Body_Custom',
            parent=ss['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11.5,
            textColor=TEXT_DARK,
            spaceAfter=4
        ),
        'BodyItalic': ParagraphStyle(
            'BodyItalic_Custom',
            parent=ss['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=10.5,
            textColor=TEXT_MUTED,
            spaceAfter=3
        ),
        'ScriptSpoken': ParagraphStyle(
            'ScriptSpoken_Custom',
            parent=ss['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            textColor=PRIMARY,
            spaceAfter=3
        ),
        'FormulaText': ParagraphStyle(
            'Formula_Custom',
            parent=ss['Normal'],
            fontName='Courier-Bold',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#0369a1"),
            alignment=1, # Center
            spaceBefore=3,
            spaceAfter=3
        ),
        'CodeConsole': ParagraphStyle(
            'CodeConsole_Custom',
            fontName='Courier',
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#80ffb8"),
            spaceBefore=1,
            spaceAfter=1
        ),
        'TableCell': ParagraphStyle(
            'TableCell_Custom',
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=TEXT_DARK
        ),
        'TableHeader': ParagraphStyle(
            'TableHeader_Custom',
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.white
        ),
        'QuestionTitle': ParagraphStyle(
            'QuestionTitle_Custom',
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=TEAL_DARK,
            keepWithNext=True
        ),
        'AnswerText': ParagraphStyle(
            'AnswerText_Custom',
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=TEXT_DARK,
            leftIndent=4
        )
    }
    return styles


def create_callout_box(content_flowables, bg_color=BG_SCRIPT, border_color=EMERALD_GREEN, border_width=3, width=523.28):
    """Wraps flowables into a styled card with a colored left accent border."""
    cell_data = [[content_flowables]]
    t = Table(cell_data, colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_color),
        ('LINEBEFORE', (0,0), (0,0), border_width, border_color),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 9),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    return t


def create_code_box(code_lines, width=523.28, styles=None):
    """Wraps code / ASCII diagram in a dark cyberpunk console box."""
    flowables = []
    for line in code_lines:
        safe_line = html.escape(line)
        flowables.append(Paragraph(safe_line, styles['CodeConsole']))
        
    t = Table([[flowables]], colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_CODE),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#0284c7")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    return t


def generate_pdf(output_path="Presentation_Script_and_Defense_Guide.pdf"):
    print(f"Building presentation PDF: {output_path}")
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=40,
        bottomMargin=40,
        title="AI Side-Channel Attack Detector & Dynamic Power Masking Defense - Presentation Script & Defense Guide",
        author="Harshith • Final Project Defense",
        subject="AI Side-Channel Attack Detection and Dynamic Power Masking Defense for IoT Microcontrollers"
    )
    
    styles = build_styles()
    story = []
    w = 523.28 # Printable width
    
    # ------------------------------------------------------------------
    # HEADER BANNER (Executive Slate Header Card)
    # ------------------------------------------------------------------
    banner_content = [
        Paragraph("AI SIDE-CHANNEL ATTACK DETECTOR &amp; DYNAMIC POWER MASKING DEFENSE", styles['Title']),
        Paragraph("Official Final Presentation Script &amp; Comprehensive Oral Defense Guide", styles['Subtitle']),
        Spacer(1, 2),
        Paragraph("<b>CORE PRINCIPLE:</b> Physical Behavior Change Detection → Dynamic Current Scrambling to Prevent Secret Key Extraction", styles['Badge']),
        Paragraph("<b>HARDWARE:</b> ESP32 DevKit V1 + INA219 Sensor + SSD1306 OLED + ESP32-C3 Attacker Probe | <b>MODEL:</b> Unsupervised One-Class SVM", styles['Badge'])
    ]
    t_banner = Table([[banner_content]], colWidths=[w])
    t_banner.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_HEADER),
        ('BOX', (0,0), (-1,-1), 1.5, TEAL_MID),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(t_banner)
    story.append(Spacer(1, 6))
    
    # ------------------------------------------------------------------
    # TABLE OF CONTENTS GRID
    # ------------------------------------------------------------------
    toc_data = [
        [
            Paragraph("<b>1. Strategy &amp; Timing Breakdown</b>", styles['TableCell']),
            Paragraph("<b>4. Mathematical Formulations &amp; Proofs</b>", styles['TableCell']),
            Paragraph("<b>7. Step-by-Step Live Demo Script</b>", styles['TableCell'])
        ],
        [
            Paragraph("<b>2. Introduction &amp; The Core Problem</b>", styles['TableCell']),
            Paragraph("<b>5. Hardware &amp; Two-Way Closed Loop</b>", styles['TableCell']),
            Paragraph("<b>8. Conclusion &amp; Key Takeaways</b>", styles['TableCell'])
        ],
        [
            Paragraph("<b>3. Side-Channel Attacks Real Example</b>", styles['TableCell']),
            Paragraph("<b>6. Dual-Condition Decision Trigger</b>", styles['TableCell']),
            Paragraph("<b>9. Viva &amp; Examiner Q&amp;A (20 Answers)</b>", styles['TableCell'])
        ]
    ]
    t_toc = Table(toc_data, colWidths=[w/3.0, w/3.0, w/3.0])
    t_toc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_LIGHT),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_toc)
    story.append(Spacer(1, 8))
    
    # ------------------------------------------------------------------
    # 1. PRESENTATION STRATEGY & TIMING BREAKDOWN
    # ------------------------------------------------------------------
    story.append(Paragraph("1. PRESENTATION STRATEGY &amp; TIMING BREAKDOWN (15 MINUTES)", styles['H1']))
    story.append(Paragraph("Structured timeline ensuring optimal pacing across the problem, mathematical innovation, hardware demo, and evaluation:", styles['Body']))
    
    timing_table_data = [
        [
            Paragraph("Segment", styles['TableHeader']),
            Paragraph("Time", styles['TableHeader']),
            Paragraph("Presentation Objective", styles['TableHeader']),
            Paragraph("Key Visual / Physical Action", styles['TableHeader'])
        ],
        [
            Paragraph("<b>1. Hook &amp; Problem</b>", styles['TableCell']),
            Paragraph("2.0 min", styles['TableCell']),
            Paragraph("Introduce why mathematical AES-128 is virtually unbreakable, but CMOS silicon hardware physically leaks keys via dynamic current.", styles['TableCell']),
            Paragraph("Title Slide &amp; Hardware Setup View", styles['TableCell'])
        ],
        [
            Paragraph("<b>2. SCA Attack Example</b>", styles['TableCell']),
            Paragraph("2.5 min", styles['TableCell']),
            Paragraph("Explain DPA/SPA on AES S-Box bit-flips and how Pearson correlation isolates the key using Hamming Weight model.", styles['TableCell']),
            Paragraph("Hamming Weight &amp; Correlation Diagram", styles['TableCell'])
        ],
        [
            Paragraph("<b>3. Core Innovation</b>", styles['TableCell']),
            Paragraph("2.0 min", styles['TableCell']),
            Paragraph("Introduce Active Power Masking: <i>'Whenever current changes, change current again!'</i> Destroy the hacker's SNR.", styles['TableCell']),
            Paragraph("Closed-Loop Architecture Flowchart", styles['TableCell'])
        ],
        [
            Paragraph("<b>4. Math &amp; ML Models</b>", styles['TableCell']),
            Paragraph("2.5 min", styles['TableCell']),
            Paragraph("Explain 7D sliding window feature vectors, One-Class SVM RBF hyper-sphere, and mathematical correlation collapse limit.", styles['TableCell']),
            Paragraph("SVM Formula &amp; Hyper-Sphere Plot", styles['TableCell'])
        ],
        [
            Paragraph("<b>5. Hardware Setup</b>", styles['TableCell']),
            Paragraph("2.0 min", styles['TableCell']),
            Paragraph("Show ESP32, INA219, SSD1306 OLED, ESP32-C3 Attacker Probe, and two-way 115200 baud serial command downlink.", styles['TableCell']),
            Paragraph("Physical Hardware Demonstration", styles['TableCell'])
        ],
        [
            Paragraph("<b>6. Live Demonstration</b>", styles['TableCell']),
            Paragraph("3.0 min", styles['TableCell']),
            Paragraph("Execute live: Baseline calibration → Attack button press → Auto-masking engagement → Safe mode recovery.", styles['TableCell']),
            Paragraph("Live Oscilloscope &amp; Physical OLED", styles['TableCell'])
        ],
        [
            Paragraph("<b>7. Conclusion</b>", styles['TableCell']),
            Paragraph("1.0 min", styles['TableCell']),
            Paragraph("Summarize results: Correlation collapsed from 96.8% to &lt; 3.5%, sub-50ms latency, zero false positives.", styles['TableCell']),
            Paragraph("Final Metric Summary Card", styles['TableCell'])
        ],
        [
            Paragraph("<b>8. Viva &amp; Q&amp;A</b>", styles['TableCell']),
            Paragraph("5-10 min", styles['TableCell']),
            Paragraph("Defend system design, algorithmic selection, hardware latency, and security trade-offs against examiner queries.", styles['TableCell']),
            Paragraph("Viva Master Cheat-Sheet (20 Q&amp;As)", styles['TableCell'])
        ]
    ]
    t_timing = Table(timing_table_data, colWidths=[90, 48, 225, 160.28])
    t_timing.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), TEAL_DARK),
        ('ALIGN', (1,1), (1,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT]),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_timing)
    story.append(Spacer(1, 8))
    
    # ------------------------------------------------------------------
    # 2. SECTION 1: INTRODUCTION & THE CORE PROBLEM
    # ------------------------------------------------------------------
    story.append(Paragraph("2. SECTION 1: INTRODUCTION &amp; THE CORE PROBLEM (0:00 - 2:00)", styles['H1']))
    sec1_spoken = [
        Paragraph("<b>🎤 Spoken Presentation Script — Deliver clearly with high authority:</b>", styles['BodyItalic']),
        Spacer(1, 2),
        Paragraph(md_to_flowable_xml(
            "\"Respected evaluators, professors, and colleagues, good morning.\n\n"
            "Today, billions of Internet-of-Things (IoT) devices—from automotive ECUs and smart medical implants to connected smart-locks—rely on advanced cryptographic algorithms like AES-128 and RSA to protect sensitive user data.\n\n"
            "Mathematically, AES-128 is virtually unbreakable; a supercomputer would require billions of years to brute-force a 128-bit key.\n\n"
            "<b>However, there is a fatal physical blind spot:</b> While the mathematical algorithm is provably secure, the <b>silicon chip executing it is a physical entity</b>.\n\n"
            "When CMOS transistors switch states from 0 to 1, they draw physical current from the power supply rail. By simply placing an inexpensive current probe or shunt resistor on the supply line, an attacker can record power fluctuations and reconstruct the secret key in minutes without breaking a single line of math!\n\n"
            "This physical vulnerability is known as a <b>Side-Channel Attack (SCA)</b>.\n\n"
            "In this project, we have designed and built a complete <b>AI-Based Side-Channel Attack Detector and Dynamic Power Masking Defense System</b>. We monitor real-time physical current telemetry using machine learning, detect snooping attempts, and immediately execute an active countermeasure: <b>whenever the current changes, we automatically change the current again, completely scrambling the power signature so that recovering the secret key becomes statistically impossible.</b>\""
        ), styles['ScriptSpoken'])
    ]
    story.append(create_callout_box(sec1_spoken, bg_color=BG_SCRIPT, border_color=EMERALD_GREEN))
    story.append(Spacer(1, 8))
    
    # ------------------------------------------------------------------
    # 3. SECTION 2: WHAT IS A SIDE-CHANNEL ATTACK? REAL-WORLD EXAMPLE
    # ------------------------------------------------------------------
    story.append(Paragraph("3. SECTION 2: WHAT IS A SIDE-CHANNEL ATTACK? REAL-WORLD EXAMPLE (2:00 - 4:30)", styles['H1']))
    sec2_spoken = [
        Paragraph("<b>🎤 Spoken Script — Explaining the physical mechanism:</b>", styles['BodyItalic']),
        Spacer(1, 2),
        Paragraph(md_to_flowable_xml(
            "\"To understand why physical current leaks secrets, let us look at how an actual <b>Differential Power Analysis (DPA)</b> attack works on an IoT chip.\n\n"
            "In AES-128 encryption, a plaintext byte <i>P</i> is XORed with a secret key byte <i>K</i>: <b>Z = P ⊕ K</b>. This intermediate value is passed into the non-linear Substitution Box: <b>Y = S-Box(P ⊕ K)</b>.\n\n"
            "When the microcontroller writes <i>Y</i> onto its internal 8-bit CMOS data bus:\n"
            "• If <i>Y = 00000000_2</i>, zero transistors switch → minimal current is drawn.\n"
            "• If <i>Y = 11111111_2</i>, eight transistors switch simultaneously → causing a massive <b>current spike</b>!\n\n"
            "This relationship is modeled by the <b>Hamming Weight Model</b>: <i>I_device(t) ∝ HW(Y) = ∑ y_j</i>.\n\n"
            "An attacker captures power traces across multiple plaintexts and calculates the <b>Pearson Correlation Coefficient</b> between measured power traces and hypothetical key guesses. The true key generates a massive correlation spike (~96.8%), exposing the key in plain sight.\""
        ), styles['ScriptSpoken'])
    ]
    story.append(create_callout_box(sec2_spoken, bg_color=BG_SCRIPT, border_color=TEAL_MID))
    story.append(Spacer(1, 8))
    
    # ------------------------------------------------------------------
    # 4. SECTION 3: OUR CORE INNOVATION — DYNAMIC POWER MASKING
    # ------------------------------------------------------------------
    story.append(Paragraph("4. SECTION 3: OUR CORE INNOVATION — DYNAMIC POWER MASKING (4:30 - 6:30)", styles['H1']))
    sec3_content = [
        Paragraph(md_to_flowable_xml(
            "Conventional IoT devices have zero awareness of physical power tampering; they continue executing normally while leaking data. Our project introduces an <b>Active Dual-Stage Closed-Loop Defense</b>:"
        ), styles['Body']),
        Spacer(1, 2),
        Paragraph(md_to_flowable_xml(
            "<b>Phase 1 — AI Telemetry &amp; Behavior Detection:</b><br/>"
            "An on-chip <b>INA219 High-Side Power Monitor</b> samples the supply line at high frequency. An unsupervised <b>One-Class Support Vector Machine (One-Class SVM)</b> with an RBF kernel evaluates 7-dimensional statistical feature vectors in real time, detecting anomalies when current deviations exceed our calibrated threshold (Δ ≥ 10.0 mA)."
        ), styles['Body']),
        Spacer(1, 2),
        Paragraph(md_to_flowable_xml(
            "<b>Phase 2 — Active Dynamic Power Masking (The Countermeasure):</b><br/>"
            "Our core philosophy is: <b>'Whenever the current changes, change the current again!'</b><br/>"
            "The instant an attack is detected, the defense engine commands the microcontroller to execute randomized, non-linear mathematical operations (<code>sin</code>, <code>cos</code>, <code>sqrt</code>) in high-frequency bursts, injecting +20 mA to +45 mA dynamic jitter noise.<br/>"
            "<b>Why does this neutralize the hacker?</b> DPA attacks depend entirely on a clean Signal-to-Noise Ratio (SNR). By injecting dynamic perturbation noise, the correlation coefficient collapses from <b>96.8% (vulnerable)</b> down to <b>&lt; 3.5% (unreadable noise)</b>, making key extraction impossible!"
        ), styles['Body'])
    ]
    story.append(create_callout_box(sec3_content, bg_color=BG_LIGHT, border_color=PRIMARY))
    story.append(Spacer(1, 8))
    
    # ------------------------------------------------------------------
    # 5. SECTION 4: MATHEMATICAL MODELS & FORMULAS USED
    # ------------------------------------------------------------------
    story.append(PageBreak()) # Clean page break for math
    story.append(Paragraph("5. SECTION 4: MATHEMATICAL MODELS &amp; FORMULAS USED", styles['H1']))
    story.append(Paragraph("Our system relies on four rigorous mathematical formulations to govern detection and defense:", styles['Body']))
    
    # Formula 1
    f1_content = [
        Paragraph("<b>Formula 1: 7-Dimensional Sliding Window Feature Vector</b>", styles['H3']),
        Paragraph(md_to_flowable_xml(
            "Rather than evaluating noisy instantaneous points, the engine partitions current into rolling windows of <i>N = 50</i> samples (<i>X = [x_1, ..., x_N]</i>) and computes a 7D vector:"
        ), styles['Body']),
        Paragraph("F = [ μ,  σ,  RMS,  P-P,  x_max,  x_min,  J ]^T", styles['FormulaText']),
        Paragraph(md_to_flowable_xml(
            "1. <b>Mean (μ):</b>  <i>μ = (1/N) ∑ x_i</i>  (Tracks steady-state power draw)<br/>"
            "2. <b>Standard Deviation (σ):</b>  <i>σ = √[ (1/N) ∑ (x_i - μ)^2 ]</i>  (Measures current spread)<br/>"
            "3. <b>RMS Energy:</b>  <i>RMS = √[ (1/N) ∑ x_i^2 ]</i>  (Captures total power dissipation)<br/>"
            "4. <b>Peak-to-Peak Range (P-P):</b>  <i>P-P = x_max - x_min</i>  (Reflects maximum dynamic excursion)<br/>"
            "5. <b>Jump Count (J):</b> Transitions where adjacent differences exceed <i>|x_i - x_{i-1}| &gt; μ_Δ + 2σ_Δ</i>"
        ), styles['Body'])
    ]
    story.append(create_callout_box(f1_content, bg_color=BG_LIGHT, border_color=TEAL_MID))
    story.append(Spacer(1, 6))
    
    # Formula 2
    f2_content = [
        Paragraph("<b>Formula 2: One-Class SVM Anomaly Detection Model</b>", styles['H3']),
        Paragraph(md_to_flowable_xml(
            "Normal idle power is well-defined, but attack profiles take infinite arbitrary forms. We employ an unsupervised <b>One-Class SVM</b> with a <b>Radial Basis Function (RBF) Kernel</b>:"
        ), styles['Body']),
        Paragraph("K(x, x') = exp( -γ · ||x - x'||^2 )", styles['FormulaText']),
        Paragraph(md_to_flowable_xml(
            "During calibration (500 idle samples), the model fits a bounding hyper-sphere with outlier fraction <i>ν = 0.05</i>. The decision function is:<br/>"
            "<b>f(x) = sign( ∑ α_i · K(x_i, x) - ρ )</b><br/>"
            "• If <b>f(x) = +1</b> → Current vector is inside the sphere: <b>Normal Baseline (Idle)</b>.<br/>"
            "• If <b>f(x) = -1</b> → Current vector lies outside the sphere: <b>Disturbance / Anomaly</b>."
        ), styles['Body'])
    ]
    story.append(create_callout_box(f2_content, bg_color=BG_LIGHT, border_color=PRIMARY_TINT))
    story.append(Spacer(1, 6))
    
    # Formula 3 & 4
    f34_content = [
        Paragraph("<b>Formula 3: Dual-Condition Decision Trigger (Zero False Positives)</b>", styles['H3']),
        Paragraph(md_to_flowable_xml(
            "To prevent false positives from power supply ripple, an attack is declared if and only if:"
        ), styles['Body']),
        Paragraph("Anomaly = [ ( f(x) == -1  AND  |μ - μ_base| ≥ MIN_CHANGE )  OR  Hardware_Signal ]", styles['FormulaText']),
        Paragraph(md_to_flowable_xml("Where <b>MIN_CHANGE = 10.0 mA</b> (calibrated sensitivity barrier)."), styles['Body']),
        Spacer(1, 3),
        Paragraph("<b>Formula 4: Dynamic Power Masking &amp; Pearson Correlation Collapse</b>", styles['H3']),
        Paragraph(md_to_flowable_xml(
            "Total current during active defense is: <i>I_total(t) = I_crypto(t) + I_attack(t) + J_mask(t)</i>.<br/>"
            "The adversary extracts keys via the Pearson correlation between measured power <i>P</i> and key hypothesis <i>H</i>:"
        ), styles['Body']),
        Paragraph("r_{P, H} = Cov(P, H) / [ σ_P · σ_H ]", styles['FormulaText']),
        Paragraph(md_to_flowable_xml(
            "Injecting high-entropy masking noise increases the power variance: <i>σ_P^2 = σ_crypto^2 + σ_mask^2</i>.<br/>"
            "As <i>σ_mask → ∞</i>, the denominator dominates, driving <b>lim r_{P, H} → 0</b>.<br/>"
            "<b>Empirical Result:</b> Correlation drops from <b>0.968 (96.8%)</b> down to <b>0.028 (2.8%)</b>!"
        ), styles['Body'])
    ]
    story.append(create_callout_box(f34_content, bg_color=BG_LIGHT, border_color=ALERT_RED))
    story.append(Spacer(1, 8))
    
    # ------------------------------------------------------------------
    # 6. SECTION 5: HARDWARE & TWO-WAY CLOSED-LOOP ARCHITECTURE
    # ------------------------------------------------------------------
    story.append(Paragraph("6. SECTION 5: HARDWARE &amp; TWO-WAY CLOSED-LOOP ARCHITECTURE", styles['H1']))
    hw_content = [
        Paragraph(md_to_flowable_xml(
            "Our physical experimental testbed comprises four tightly coupled hardware modules:<br/>"
            "1. <b>Main Target Node (ESP32 DevKit V1):</b> Executes core tasks, reads telemetry, drives the 0.96\" SSD1306 OLED display over I2C (SDA: GPIO 21, SCL: GPIO 22), and streams UART telemetry at 115200 baud.<br/>"
            "2. <b>High-Side Power Monitor (INA219 Module):</b> Measures voltage drop across a 0.1 Ω precision shunt on the positive rail, streaming digital mA telemetry.<br/>"
            "3. <b>Attacker Probe Node (ESP32-C3 SuperMini):</b> Connected via push button (GPIO 4) and hardware attack trigger line (GPIO 5 → Main ESP32 GPIO 27). Pressing the button induces a physical +50 mA current surge.<br/>"
            "4. <b>Two-Way Closed Loop Feedback:</b><br/>"
            "   • <b>Uplink:</b> ESP32 streams live current readings to Python.<br/>"
            "   • <b>Downlink:</b> Upon anomaly detection, Python sends byte <code>b'1'</code> over Serial. The ESP32 immediately flips its OLED to <code>! DEFENSE: MASKING !</code> and triggers local current scrambling. When safe, Python sends byte <code>b'0'</code>, returning OLED to <code>STATUS: SECURE</code>."
        ), styles['Body'])
    ]
    story.append(create_callout_box(hw_content, bg_color=BG_LIGHT, border_color=TEAL_DARK))
    story.append(Spacer(1, 8))
    
    # ------------------------------------------------------------------
    # 7. SECTION 6: LIVE DEMONSTRATION SCRIPT (STEP-BY-STEP)
    # ------------------------------------------------------------------
    story.append(PageBreak()) # New page for demo script
    story.append(Paragraph("7. SECTION 6: LIVE DEMONSTRATION SCRIPT (STEP-BY-STEP)", styles['H1']))
    story.append(Paragraph("Follow this sequential procedure during the viva to demonstrate the live closed-loop defense:", styles['Body']))
    
    demo_flow_lines = [
        "                 +----------------------------------------------------+",
        "                 |           CLOSED-LOOP DEMO EXECUTION FLOW          |",
        "                 +----------------------------------------------------+",
        "                                           |",
        "     [Step 1] Baseline Calibration   --> Idle 24.5 mA, One-Class SVM Fits Hyper-Sphere",
        "                                           v",
        "     [Step 2] Press Attack Button    --> Current Spikes +50 mA, Anomaly Declared",
        "                                           v",
        "     [Step 3] Auto-Masking Engaged   --> Cyan Waveform, Noise Injected, Correlation < 3%",
        "                                           v",
        "     [Step 4] Press Safe Mode Button --> Buffer Flushed, Baseline Restored, OLED Secure"
    ]
    story.append(create_code_box(demo_flow_lines, width=w, styles=styles))
    story.append(Spacer(1, 6))
    
    # Step 1
    s1_box = [
        Paragraph("<b>Step 1: System Launch &amp; Normal Baseline Calibration</b>", styles['H3']),
        Paragraph("<b>Action:</b> Run <code>python app.py</code> (or Web UI). Click <b>CONNECT ESP32</b> (or enable <b>SIMULATOR MODE</b>).", styles['Body']),
        Paragraph(md_to_flowable_xml(
            "<b>What to Say:</b> \"Notice that upon connection, the system initiates the 10-window (500 sample) Baseline Calibration Phase. The One-Class SVM models the idle current distribution: 24.7 mA with tight standard deviation (±0.4 mA). Once calibrated, the HUD shows <b>SYSTEM SECURE • KEY SAFE</b>. The oscilloscope displays a calm, steady neon green trace, the physical OLED reads <code>ML STATUS: SECURE</code>, and hacker correlation is baseline 1.2% (zero key leakage).\""
        ), styles['ScriptSpoken'])
    ]
    story.append(create_callout_box(s1_box, bg_color=BG_LIGHT, border_color=EMERALD_GREEN))
    story.append(Spacer(1, 5))
    
    # Step 2
    s2_box = [
        Paragraph("<b>Step 2: Triggering the Physical Disturbance / Attack</b>", styles['H3']),
        Paragraph("<b>Action:</b> Press the physical button on the ESP32-C3 Attacker (or click <b>INJECT ATTACK (CHANGE CURRENT)</b> on the UI).", styles['Body']),
        Paragraph(md_to_flowable_xml(
            "<b>What to Say:</b> \"Now, an attacker initiates a side-channel snooping attempt by pressing the attack button. Look at the screen: current spikes by +50 mA, jumping into the 75–85 mA range. The One-Class SVM instantly determines that this 7D feature vector violates the trained hyper-sphere (f(x) = -1) and the shift exceeds our 10.0 mA threshold.\""
        ), styles['ScriptSpoken'])
    ]
    story.append(create_callout_box(s2_box, bg_color=BG_LIGHT, border_color=ALERT_RED))
    story.append(Spacer(1, 5))
    
    # Step 3
    s3_box = [
        Paragraph("<b>Step 3: Observing the Active Power Masking Countermeasure</b>", styles['H3']),
        Paragraph("<b>Action:</b> Point to the vibrant <b>Cyan Masking Waveform</b> on the oscilloscope and the HUD telemetry cards.", styles['Body']),
        Paragraph(md_to_flowable_xml(
            "<b>What to Say:</b> \"Rather than remaining vulnerable at fixed higher current, our Active Power Masking countermeasure engages automatically! <b>It changes the current again!</b> Notice how the oscilloscope shifts into a dynamic cyan trace with +35 mA randomized jitter noise. In the HUD, Secret Key Security switches to <b>SHIELDED / MASKED</b> and correlation collapses from 96.8% to <b>2.8%</b>! Simultaneously, Python sends byte <code>b'1'</code> over Serial, and the physical OLED display immediately updates to <code>! DEFENSE: MASKING !</code>. Any power trace the hacker captures is pure mathematical noise!\""
        ), styles['ScriptSpoken'])
    ]
    story.append(create_callout_box(s3_box, bg_color=BG_LIGHT, border_color=NEON_CYAN))
    story.append(Spacer(1, 5))
    
    # Step 4
    s4_box = [
        Paragraph("<b>Step 4: Restoring Normal Operation (Safe Mode / Turn Off)</b>", styles['H3']),
        Paragraph("<b>Action:</b> Click the <b>🛡️ SAFE MODE (TURN OFF)</b> button (or release the physical button).", styles['Body']),
        Paragraph(md_to_flowable_xml(
            "<b>What to Say:</b> \"When the disturbance terminates or when we click <b>SAFE MODE</b>, the circular buffer flushes previous attack samples, current immediately returns to the normal 24.5 mA baseline, Python writes <code>b'0'</code> over Serial, the OLED flips back to <code>ML STATUS: SECURE</code>, and the oscilloscope returns to a calm neon green wave with zero lag and zero freezing.\""
        ), styles['ScriptSpoken'])
    ]
    story.append(create_callout_box(s4_box, bg_color=BG_LIGHT, border_color=EMERALD_GREEN))
    story.append(Spacer(1, 8))
    
    # ------------------------------------------------------------------
    # 8. SECTION 7: CONCLUSION & KEY TAKEAWAYS
    # ------------------------------------------------------------------
    story.append(Paragraph("8. SECTION 7: CONCLUSION &amp; KEY TAKEAWAYS (14:00 - 15:00)", styles['H1']))
    concl_content = [
        Paragraph(md_to_flowable_xml(
            "<b>Deliver these four core conclusions with confidence:</b><br/>"
            "1. <b>Physical Vulnerability Proven:</b> Mathematically secure ciphers (AES-128) inherently leak keys through CMOS dynamic power draw (Hamming Weight model).<br/>"
            "2. <b>Lightweight Unsupervised ML:</b> By computing 7D feature vectors over sliding windows, our One-Class SVM detects novel disturbances in under 1.2 ms without requiring prior attack labels.<br/>"
            "3. <b>Active Power Masking Defense:</b> Actively scrambling current upon anomaly detection collapses Pearson correlation from <b>96.8% down to 2.8%</b>, destroying the attacker's Signal-to-Noise Ratio.<br/>"
            "4. <b>Complete Two-Way Closed Loop:</b> Seamless hardware-software integration across ESP32, INA219, OLED display, and real-time visualization dashboards."
        ), styles['Body'])
    ]
    story.append(create_callout_box(concl_content, bg_color=BG_SCRIPT, border_color=PRIMARY))
    story.append(Spacer(1, 8))
    
    # ------------------------------------------------------------------
    # 9. VIVA & EXAMINER Q&A MASTER CHEAT-SHEET (20 ANSWERS)
    # ------------------------------------------------------------------
    story.append(PageBreak()) # New page for Q&A
    story.append(Paragraph("9. VIVA &amp; EXAMINER Q&amp;A MASTER CHEAT-SHEET (20 TOUGH QUESTIONS)", styles['H1']))
    story.append(Paragraph("Authoritative, technically rigorous answers organized into five key evaluation domains:", styles['Body']))
    
    qas = [
        # Domain 1
        ("Domain A: Core Concepts & Attack Theory", [
            ("Q1: What is the fundamental difference between standard cryptanalysis and a Side-Channel Attack?",
             "Standard cryptanalysis treats the cipher as a mathematical black box and attacks the algorithm itself (e.g., trying to invert AES or factor RSA primes). A Side-Channel Attack attacks the physical implementation on silicon by measuring physical emissions like power consumption, electromagnetic radiation, or execution timing."),
            ("Q2: What is the difference between SPA (Simple Power Analysis) and DPA (Differential Power Analysis)?",
             "SPA directly inspects a single power trace visually to infer operations (e.g., distinguishing an RSA modular multiplication from a squaring step). DPA is statistical: it captures hundreds or thousands of power traces across varying plaintexts, applies a hypothetical power model (like Hamming Weight), and uses Pearson correlation to isolate the exact secret key byte."),
            ("Q3: Why does CMOS hardware leak power when processing data?",
             "In CMOS circuits, static leakage is minimal. Power is primarily consumed when charging and discharging parasitic gate capacitances during logic bit transitions (0 → 1 or 1 → 0). The total current drawn is directly proportional to the number of bits switching (Hamming Distance) or total high bits on the bus (Hamming Weight).")
        ]),
        # Domain 2
        ("Domain B: Machine Learning & Mathematics", [
            ("Q4: Why choose One-Class SVM over supervised classifiers like Random Forest or CNNs?",
             "In IoT physical security, we have abundant baseline data of normal idle operation, but an attacker can construct infinite, unpredictable disturbance profiles. Supervised models require labeled examples of every attack type and fail when encountering zero-day attacks. One-Class SVM is an unsupervised novelty detector that models normal behavior and flags any outward deviation."),
            ("Q5: What is the purpose of the RBF Kernel in your One-Class SVM?",
             "Real-world current draw exhibits non-linear thermal drift and power supply ripple. The Radial Basis Function (RBF) kernel maps 7D feature vectors into an infinite-dimensional Hilbert space, allowing the SVM to compute a non-linear bounding hyper-sphere that encloses normal idle behavior without overfitting."),
            ("Q6: Why extract 7 statistical features instead of feeding raw current samples to the SVM?",
             "Raw ADC samples suffer from high-frequency noise and temporal jitter. Extracting statistical features (μ, σ, RMS, P-P, max, min, Jump Count) condenses 50 temporal samples into structural metrics representing power magnitude, energy, and transient edges, making detection invariant to minor clock drift."),
            ("Q7: How does your formula mathematically prove that Pearson Correlation drops during masking?",
             "Pearson correlation is r_{P, H} = Cov(P, H) / (σ_P · σ_H). By adding independent pseudo-random masking noise J_mask, the covariance Cov(P, H) remains constant while power variance σ_P^2 = σ_crypto^2 + σ_mask^2 increases substantially. As σ_mask increases, the denominator dominates, driving r_{P, H} → 0.")
        ]),
        # Domain 3
        ("Domain C: Hardware, Protocol & Countermeasure", [
            ("Q8: How does your physical button represent a real-world side-channel attack?",
             "In a laboratory attack, an adversary uses clock glitchers, power modulators, or triggers high-frequency RF bursts to induce power anomalies. Our ESP32-C3 Attacker node simulates this physical behavior: pressing the button initiates high-power computation loops and Wi-Fi RF power draw, causing an instantaneous physical +50 mA disturbance on the shared supply rail."),
            ("Q9: What is the INA219 sensor's role and how does it measure current?",
             "The INA219 is a high-side current and power monitor. It contains an internal 12-bit ADC that measures the small differential voltage drop across a 0.1 Ω, 1% precision shunt resistor on the positive power rail (V_in+ - V_in-) and transmits calculated current over I2C using Ohm's law: I = V_shunt / R_shunt."),
            ("Q10: What is the Two-Way Closed-Loop protocol between Python and the ESP32?",
             "Telemetry Uplink: The ESP32 continuously transmits ASCII current readings over 115200 baud serial. Control Downlink: Python continuously evaluates telemetry. If an anomaly is confirmed, Python writes byte b'1' back over serial. The ESP32 UART interrupt receives '1', flips its OLED to '! DEFENSE: MASKING !', and executes local current scrambling. When normal, Python sends byte b'0' to restore OLED to 'STATUS: SECURE'."),
            ("Q11: What is the difference between Hardware Power Masking and Software Power Masking?",
             "Software Power Masking (algorithmic) XORs cryptographic intermediate values with random masks inside the code (Z' = Z ⊕ M). Hardware Power Masking (our system) dynamically alters power on the supply rail by activating concurrent randomized arithmetic ALU operations and current injection, physically obscuring the power profile."),
            ("Q12: Why did you implement a 'Safe Mode' button?",
             "In sliding-window detection, when an attack ends, the circular buffer retains historical high-current samples for a short duration. The Safe Mode button immediately flushes the rolling buffer with trained baseline values, resets the state to SECURE, and transmits b'0' to the hardware, preventing residual false alarm loops.")
        ]),
        # Domain 4
        ("Domain D: Performance & Edge Feasibility", [
            ("Q13: What is the detection latency of your system?",
             "Telemetry samples are acquired every 33–50 ms (~20–30 Hz). Feature extraction and One-Class SVM inference take less than 1.2 ms on the host CPU. Thus, detection and two-way feedback trigger in under 50 ms, which is well within the window required to interrupt or mask cryptographic key extraction."),
            ("Q14: Does power masking increase total power consumption?",
             "Yes, active power masking draws additional current (an extra 20–40 mA). However, in our architecture, masking is dynamic and event-triggered, NOT continuously on. It remains idle during normal operation and only activates when an attack disturbance is detected, preserving IoT battery life."),
            ("Q15: What prevents an attacker from filtering out the masking noise?",
             "Simple low-pass filters only remove high-frequency thermal noise. Our masking noise is non-linear, algorithmic, and generated using mathematical operations (sin, cos, sqrt) operating in the exact same frequency band as cryptographic operations, making frequency-domain separation infeasible."),
            ("Q16: Can this system run entirely on an edge microcontroller without a PC?",
             "Yes. While we implemented the UI and Python model on a PC host for live presentation and visualization, the One-Class SVM model can be serialized and deployed directly onto the ESP32 using TensorFlow Lite for Microcontrollers or EloquentTinyML, enabling fully autonomous, standalone edge protection.")
        ]),
        # Domain 5
        ("Domain E: UI & Architecture", [
            ("Q17: Why use WebSockets instead of standard HTTP REST polling for the web interface?",
             "HTTP polling introduces request-response header overhead and latency jitter. WebSockets establish a persistent, full-duplex TCP connection, allowing lightweight JSON telemetry packets to stream smoothly at 22 FPS with sub-millisecond latency."),
            ("Q18: Why did you eliminate shadowBlur from the HTML5 canvas oscilloscope?",
             "In 2D canvas engines, shadowBlur forces Gaussian blur calculations on every frame across multiple path segments, leading to severe GPU thread contention and browser tab freezing. Replacing it with dual-pass semi-transparent strokes delivers an authentic cyberpunk neon glow with zero frame drops."),
            ("Q19: What is the minimum current shift (MIN_CHANGE) required to trigger detection?",
             "By default, MIN_CHANGE = 10.0 mA. This threshold is user-adjustable in the UI toolbar and ensures normal voltage regulator ripple (±1–2 mA) does not cause false positives."),
            ("Q20: What are the three primary contributions of your project?",
             "1. Real-time physical power telemetry acquisition on IoT edge hardware using INA219 and ESP32.\n2. Unsupervised anomaly detection using rolling 7D feature vectors and a One-Class SVM.\n3. Active Dynamic Power Masking, proving that actively changing current upon attack detection collapses the secret key correlation coefficient from > 96% to < 3.5%.")
        ])
    ]
    
    for domain_title, q_list in qas:
        story.append(Paragraph(domain_title, styles['H2']))
        for q_text, a_text in q_list:
            q_flowables = [
                Paragraph(md_to_flowable_xml(q_text), styles['QuestionTitle']),
                Spacer(1, 2),
                Paragraph(md_to_flowable_xml(f"<b>Answer:</b> {a_text}"), styles['AnswerText'])
            ]
            # Wrap in KeepTogether so question & answer never get split across a page break
            story.append(KeepTogether(create_callout_box(q_flowables, bg_color=BG_LIGHT, border_color=TEAL_MID, border_width=2.5)))
            story.append(Spacer(1, 3))
            
    # ------------------------------------------------------------------
    # QUICK CUE CARD (DESK REFERENCE)
    # ------------------------------------------------------------------
    story.append(Spacer(1, 5))
    story.append(Paragraph("🎯 QUICK CUE CARD (KEEP BESIDE YOUR LAPTOP DURING VIVA)", styles['H1']))
    cue_card_lines = [
        "• Problem: AES is mathematically safe, but CMOS bit-flips leak the key via power draw (Hamming Weight).",
        "• Core Idea: When physical current changes, detect it and change current again so the hacker can't find a pattern!",
        "• Model: One-Class SVM, RBF Kernel (K(x, x') = exp(-γ||x-x'||^2)), 7D Sliding Window Feature Vector.",
        "• Decision Barrier: Mean shift |μ - μ_base| ≥ 10.0 mA from baseline (~24.5 mA) + Outlier decision f(x) = -1.",
        "• Hardware Pins: INA219/OLED on GPIO 21 & 22 (I2C), Attack Input on GPIO 27, ESP32-C3 Button on GPIO 4.",
        "• 2-Way Protocol: Python writes b'1' for Anomaly/Masking; b'0' for Normal/Secure.",
        "• Result: Adversary's Pearson correlation coefficient drops from 96.8% to 2.8%. Secret key remains safe!"
    ]
    cue_flowables = [
        Paragraph(md_to_flowable_xml("<br/>".join(cue_card_lines)), styles['ScriptSpoken'])
    ]
    story.append(KeepTogether(create_callout_box(cue_flowables, bg_color=BG_SCRIPT, border_color=EMERALD_GREEN, border_width=3)))
    
    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF build complete: {output_path} ({os.path.getsize(output_path)} bytes)")


if __name__ == "__main__":
    generate_pdf()
