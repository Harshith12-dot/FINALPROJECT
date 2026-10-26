#include <Wire.h>
#include <Adafruit_INA219.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// Display configuration
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

// Pin definitions
#define BUTTON_PIN_ATTACK 12

// Create display and sensor objects
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
Adafruit_INA219 ina219;

// Buffer and state variables
const int WINDOW_SIZE = 128;
float powerData[WINDOW_SIZE];
int dataIndex = 0;

bool isAnomaly = false;
bool isSimulatingAttack = false;
bool buttonPressed = false;
int attackDuration = 0;
const int MAX_GRAPH_MA = 150;

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  
  // Configure attack button
  pinMode(BUTTON_PIN_ATTACK, INPUT_PULLUP);

  // Initialize OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 allocation failed"));
    for (;;);
  }
  
  // Initialize INA219
  if (!ina219.begin()) {
    Serial.println(F("Failed to find INA219 chip"));
    for (;;);
  }

  // Initialize power data buffer
  for (int i = 0; i < WINDOW_SIZE; i++) {
    powerData[i] = 0;
  }

  // Display startup message
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 20);
  display.println(F("WAITING FOR PC..."));
  display.display();
  
  delay(1000);
}

void loop() {
  // Check for attack button press
  if (digitalRead(BUTTON_PIN_ATTACK) == LOW) {
    delay(50);  // Debounce
    if (digitalRead(BUTTON_PIN_ATTACK) == LOW && !buttonPressed) {
      buttonPressed = true;
      isSimulatingAttack = true;
      attackDuration = 100;
      Serial.println(F("ATTACK_ON"));
      Serial.println(F("BUTTON: Attack simulation started"));
    }
  } else {
    buttonPressed = false;
    if (isSimulatingAttack) {
      isSimulatingAttack = false;
      Serial.println(F("ATTACK_OFF"));
      Serial.println(F("BUTTON: Attack simulation ended"));
    }
  }
  
  // Read current from INA219
  float current_mA = ina219.getCurrent_mA();
  
  // Add power spike during attack simulation
  if (isSimulatingAttack && attackDuration > 0) {
    current_mA += random(50, 150);
    attackDuration--;
    if (attackDuration == 0) {
      isSimulatingAttack = false;
      Serial.println(F("ATTACK_OFF"));
      Serial.println(F("BUTTON: Attack simulation ended"));
    }
  }
  
  // Send current value to Python script
  Serial.println(current_mA);

  // Receive anomaly verdict from Python script
  if (Serial.available() > 0) {
    char ai_status = Serial.read();
    if (ai_status == '1') {
      isAnomaly = true;
    } else if (ai_status == '0') {
      isAnomaly = false;
    }
  }

  // Store power data in circular buffer
  powerData[dataIndex] = current_mA;
  dataIndex++;
  if (dataIndex >= WINDOW_SIZE) {
    dataIndex = 0;
  }

  // Update OLED display
  drawInterface(current_mA);
  
  delay(20);  // ~50Hz sampling rate
}

void drawInterface(float current_mA) {
  display.clearDisplay();

  // Display status bar
  display.setTextSize(1);
  display.setCursor(0, 0);
  
  if (isAnomaly) {
    // Alert mode
    display.fillRect(0, 0, 128, 16, SSD1306_WHITE);
    display.setTextColor(SSD1306_BLACK);
    display.println(F("! ML ALERT: HIJACK !"));
    display.setTextColor(SSD1306_WHITE);
  } else {
    // Secure mode
    display.println(F("ML STATUS: SECURE"));
  }

  // Display current value
  display.setCursor(90, 0);
  display.print((int)current_mA);
  display.println(F("mA"));

  // Draw power trace graph
  int graphHeight = 48;
  int graphYOffset = 16;
  
  for (int i = 0; i < WINDOW_SIZE - 1; i++) {
    int readIndex = (dataIndex + i) % WINDOW_SIZE;
    int nextIndex = (dataIndex + i + 1) % WINDOW_SIZE;

    int y1 = graphYOffset + graphHeight - map(powerData[readIndex], 0, MAX_GRAPH_MA, 0, graphHeight);
    int y2 = graphYOffset + graphHeight - map(powerData[nextIndex], 0, MAX_GRAPH_MA, 0, graphHeight);

    y1 = constrain(y1, graphYOffset, 63);
    y2 = constrain(y2, graphYOffset, 63);

    display.drawLine(i, y1, i + 1, y2, SSD1306_WHITE);
  }

  display.display();
}
