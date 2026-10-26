#include <Wire.h>
#include <Adafruit_INA219.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// =====================================================
// I2C PINS
// =====================================================

#define SDA_PIN 21
#define SCL_PIN 22

// =====================================================
// OLED
// =====================================================

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define OLED_ADDRESS 0x3C

Adafruit_SSD1306 display(
  SCREEN_WIDTH,
  SCREEN_HEIGHT,
  &Wire,
  OLED_RESET
);

// =====================================================
// INA219
// =====================================================

Adafruit_INA219 ina219;

// =====================================================
// ATTACK SIGNAL
//
// C3 GPIO5  ---> Main GPIO27
// C3 GND    ---> Main GND
// =====================================================

#define ATTACK_SIGNAL_PIN 27

// =====================================================
// ATTACK SIMULATION
// =====================================================

// Large enough to clearly see on graph
#define ATTACK_INCREASE_MA 50.0

// =====================================================
// GRAPH
// =====================================================

#define GRAPH_SIZE 128

float currentData[GRAPH_SIZE];

int dataIndex = 0;

// =====================================================
// STATUS
// =====================================================

bool attackerActive = false;
bool aiAnomaly = false;

unsigned long lastSample = 0;


// =====================================================
// SETUP
// =====================================================

void setup()
{
  Serial.begin(115200);

  delay(1000);

  // ---------------------------------------------------
  // I2C
  // ---------------------------------------------------

  Wire.begin(SDA_PIN, SCL_PIN);

  // ---------------------------------------------------
  // ATTACK INPUT
  // ---------------------------------------------------

  pinMode(
    ATTACK_SIGNAL_PIN,
    INPUT_PULLDOWN
  );

  // ---------------------------------------------------
  // OLED
  // ---------------------------------------------------

  if (!display.begin(
        SSD1306_SWITCHCAPVCC,
        OLED_ADDRESS))
  {
    Serial.println("OLED_ERROR");

    while (true)
    {
      delay(1000);
    }
  }

  // ---------------------------------------------------
  // INA219
  // ---------------------------------------------------

  if (!ina219.begin())
  {
    Serial.println("INA219_ERROR");

    display.clearDisplay();

    display.setTextColor(
      SSD1306_WHITE
    );

    display.setTextSize(1);

    display.setCursor(15, 25);
    display.println("INA219 ERROR");

    display.display();

    while (true)
    {
      delay(1000);
    }
  }

  ina219.setCalibration_32V_2A();

  // ---------------------------------------------------
  // CLEAR GRAPH
  // ---------------------------------------------------

  for (int i = 0; i < GRAPH_SIZE; i++)
  {
    currentData[i] = 0;
  }

  // ---------------------------------------------------
  // START SCREEN
  // ---------------------------------------------------

  display.clearDisplay();

  display.setTextColor(
    SSD1306_WHITE
  );

  display.setTextSize(2);

  display.setCursor(5, 5);
  display.println("SCA");

  display.setTextSize(1);

  display.setCursor(5, 30);
  display.println("SIDE-CHANNEL");

  display.setCursor(5, 43);
  display.println("DETECTOR");

  display.display();

  Serial.println("SYSTEM_READY");

  delay(2000);
}


// =====================================================
// MAIN LOOP
// =====================================================

void loop()
{
  // Sample every 50 ms
  if (millis() - lastSample < 50)
  {
    return;
  }

  lastSample = millis();

  // ===================================================
  // READ ATTACK SIGNAL
  // ===================================================

  bool signalState =
    digitalRead(ATTACK_SIGNAL_PIN);

  // ---------------------------------------------------
  // Detect change
  // ---------------------------------------------------

  if (signalState != attackerActive)
  {
    attackerActive = signalState;

    if (attackerActive)
    {
      Serial.println("ATTACK_ON");
    }
    else
    {
      Serial.println("ATTACK_OFF");

      // Immediately reset anomaly display
      aiAnomaly = false;
    }
  }

  // ===================================================
  // READ REAL INA219 CURRENT
  // ===================================================

  float realCurrent =
    ina219.getCurrent_mA();

  // ===================================================
  // CREATE DEMONSTRATION ATTACK
  // ===================================================

  float displayedCurrent =
    realCurrent;

  if (attackerActive)
  {
    displayedCurrent =
      realCurrent +
      ATTACK_INCREASE_MA;
  }

  // ===================================================
  // STORE GRAPH DATA
  // ===================================================

  currentData[dataIndex] =
    displayedCurrent;

  dataIndex++;

  if (dataIndex >= GRAPH_SIZE)
  {
    dataIndex = 0;
  }

  // ===================================================
  // SEND CURRENT TO PYTHON
  // ===================================================

  Serial.println(
    displayedCurrent,
    2
  );

  // ===================================================
  // RECEIVE AI RESULT
  // ===================================================

  while (Serial.available() > 0)
  {
    char c = Serial.read();

    if (c == '1')
    {
      aiAnomaly = true;
    }

    if (c == '0')
    {
      aiAnomaly = false;
    }
  }

  // ===================================================
  // DRAW OLED
  // ===================================================

  drawOLED(
    realCurrent,
    displayedCurrent
  );
}


// =====================================================
// OLED DISPLAY
// =====================================================

void drawOLED(
  float realCurrent,
  float displayedCurrent
)
{
  display.clearDisplay();

  // ===================================================
  // STATUS
  // ===================================================

  if (aiAnomaly)
  {
    display.fillRect(
      0,
      0,
      128,
      14,
      SSD1306_WHITE
    );

    display.setTextColor(
      SSD1306_BLACK,
      SSD1306_WHITE
    );

    display.setTextSize(1);

    display.setCursor(4, 3);

    display.print(
      "!! ANOMALY DETECTED !!"
    );
  }
  else
  {
    display.setTextColor(
      SSD1306_WHITE
    );

    display.setTextSize(1);

    display.setCursor(4, 3);

    display.print(
      "STATUS: SECURE"
    );
  }

  // ===================================================
  // CURRENT
  // ===================================================

  display.setTextColor(
    SSD1306_WHITE
  );

  display.setCursor(80, 16);

  display.print(
    (int)displayedCurrent
  );

  display.print(
    "mA"
  );

  // ===================================================
  // ATTACK STATUS
  // ===================================================

  display.setCursor(3, 27);

  if (attackerActive)
  {
    display.print(
      "ATTACK: ON"
    );
  }
  else
  {
    display.print(
      "ATTACK: OFF"
    );
  }

  // ===================================================
  // GRAPH
  // ===================================================

  int graphTop = 38;
  int graphBottom = 63;

  for (int i = 0;
       i < GRAPH_SIZE - 1;
       i++)
  {
    int index1 =
      (dataIndex + i) %
      GRAPH_SIZE;

    int index2 =
      (dataIndex + i + 1) %
      GRAPH_SIZE;

    float v1 =
      currentData[index1];

    float v2 =
      currentData[index2];

    // -------------------------------------------------
    // Graph scale
    // -------------------------------------------------

    v1 = constrain(
      v1,
      0,
      300
    );

    v2 = constrain(
      v2,
      0,
      300
    );

    int y1 =
      map(
        (int)v1,
        0,
        300,
        graphBottom,
        graphTop
      );

    int y2 =
      map(
        (int)v2,
        0,
        300,
        graphBottom,
        graphTop
      );

    display.drawLine(
      i,
      y1,
      i + 1,
      y2,
      SSD1306_WHITE
    );
  }

  display.display();
}
