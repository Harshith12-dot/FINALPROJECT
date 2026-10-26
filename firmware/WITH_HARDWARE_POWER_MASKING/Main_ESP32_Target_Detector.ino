#include <Wire.h>
#include <Adafruit_INA219.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <math.h>

// =====================================================
// OPTIONAL HARDWARE POWER MASKING VERSION
// (If you want the ESP32 itself to run dynamic math loops
//  and current jitter when attack is detected)
// =====================================================

#define SDA_PIN 21
#define SCL_PIN 22
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define OLED_ADDRESS 0x3C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
Adafruit_INA219 ina219;

#define ATTACK_SIGNAL_PIN 27
#define ATTACK_INCREASE_MA 50.0

#define GRAPH_SIZE 128
float currentData[GRAPH_SIZE];
int dataIndex = 0;

bool attackerActive = false;
bool aiAnomaly = false;
float dummyMask = 0.0;
unsigned long lastSample = 0;

void drawOLED(float realCurrent, float displayedCurrent);

void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin(SDA_PIN, SCL_PIN);
  pinMode(ATTACK_SIGNAL_PIN, INPUT_PULLDOWN);

  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDRESS)) {
    Serial.println("OLED_ERROR");
    while (true) delay(1000);
  }

  if (!ina219.begin()) {
    Serial.println("INA219_ERROR");
    while (true) delay(1000);
  }

  ina219.setCalibration_32V_2A();

  for (int i = 0; i < GRAPH_SIZE; i++) currentData[i] = 0;

  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(10, 25);
  display.println("AI-SCA READY");
  display.display();

  Serial.println("SYSTEM_READY");
  delay(1500);
}

void loop() {
  if (millis() - lastSample < 50) return;
  lastSample = millis();

  bool signalState = digitalRead(ATTACK_SIGNAL_PIN);
  if (signalState != attackerActive) {
    attackerActive = signalState;
    if (attackerActive) {
      Serial.println("ATTACK_ON");
    } else {
      Serial.println("ATTACK_OFF");
      aiAnomaly = false;
    }
  }

  float realCurrent = ina219.getCurrent_mA();
  float displayedCurrent = realCurrent;

  if (attackerActive) {
    displayedCurrent += ATTACK_INCREASE_MA;
  }

  // Active Power Masking: Change current again when anomaly occurs
  if (aiAnomaly) {
    for (int j = 0; j < random(500, 1500); j++) {
      dummyMask += sin(j * 0.05) * cos(j * 0.02) + sqrt(j + 1.0);
    }
    displayedCurrent += random(15, 35);
  }

  currentData[dataIndex] = displayedCurrent;
  dataIndex = (dataIndex + 1) % GRAPH_SIZE;

  Serial.println(displayedCurrent, 2);

  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '1') aiAnomaly = true;
    if (c == '0') aiAnomaly = false;
  }

  drawOLED(realCurrent, displayedCurrent);
}

void drawOLED(float realCurrent, float displayedCurrent) {
  display.clearDisplay();
  if (aiAnomaly) {
    display.fillRect(0, 0, 128, 14, SSD1306_WHITE);
    display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(2, 3);
    display.print("! DEFENSE: MASKING !");
  } else {
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(4, 3);
    display.print("STATUS: SECURE");
  }

  display.setTextColor(SSD1306_WHITE);
  display.setCursor(80, 16);
  display.print((int)displayedCurrent);
  display.print("mA");

  display.setCursor(3, 27);
  display.print(attackerActive ? "ATTACK: ON" : "ATTACK: OFF");

  int graphTop = 38;
  int graphBottom = 63;
  for (int i = 0; i < GRAPH_SIZE - 1; i++) {
    int idx1 = (dataIndex + i) % GRAPH_SIZE;
    int idx2 = (dataIndex + i + 1) % GRAPH_SIZE;
    float v1 = constrain(currentData[idx1], 0, 300);
    float v2 = constrain(currentData[idx2], 0, 300);
    int y1 = map((int)v1, 0, 300, graphBottom, graphTop);
    int y2 = map((int)v2, 0, 300, graphBottom, graphTop);
    display.drawLine(i, y1, i + 1, y2, SSD1306_WHITE);
  }
  display.display();
}
