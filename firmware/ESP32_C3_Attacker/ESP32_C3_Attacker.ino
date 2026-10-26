#include <Arduino.h>
#include <math.h>

// =====================================================
// PINS
// =====================================================

#define BUTTON_PIN 4
#define LED_PIN 8
#define ATTACK_SIGNAL_PIN 5

// =====================================================
// VARIABLES
// =====================================================

bool attackActive = false;

int lastReading = HIGH;
int stableButtonState = HIGH;

unsigned long lastDebounceTime = 0;

const unsigned long debounceDelay = 50;

float dummyValue = 0;


// =====================================================
// SETUP
// =====================================================

void setup()
{
  Serial.begin(115200);

  delay(1000);

  // ---------------------------------------------------
  // BUTTON
  // ---------------------------------------------------

  pinMode(
    BUTTON_PIN,
    INPUT_PULLUP
  );

  // ---------------------------------------------------
  // LED
  // ---------------------------------------------------

  pinMode(
    LED_PIN,
    OUTPUT
  );

  digitalWrite(
    LED_PIN,
    LOW
  );

  // ---------------------------------------------------
  // ATTACK SIGNAL
  // ---------------------------------------------------

  pinMode(
    ATTACK_SIGNAL_PIN,
    OUTPUT
  );

  digitalWrite(
    ATTACK_SIGNAL_PIN,
    LOW
  );

  // ---------------------------------------------------
  // START MESSAGE
  // ---------------------------------------------------

  Serial.println();
  Serial.println(
    "=============================="
  );

  Serial.println(
    "ESP32-C3 ATTACKER READY"
  );

  Serial.println(
    "NO WIFI"
  );

  Serial.println(
    "Press button to toggle attack"
  );

  Serial.println(
    "=============================="
  );
}


// =====================================================
// LOOP
// =====================================================

void loop()
{
  // ===================================================
  // READ BUTTON
  // ===================================================

  int reading =
    digitalRead(BUTTON_PIN);

  // ---------------------------------------------------
  // Button changed
  // ---------------------------------------------------

  if (reading != lastReading)
  {
    lastDebounceTime =
      millis();
  }

  // ---------------------------------------------------
  // Wait for stable button
  // ---------------------------------------------------

  if (
    (millis() - lastDebounceTime)
    > debounceDelay
  )
  {
    if (reading != stableButtonState)
    {
      stableButtonState =
        reading;

      // ===============================================
      // BUTTON PRESSED
      // ===============================================

      if (stableButtonState == LOW)
      {
        attackActive =
          !attackActive;

        // =============================================
        // ATTACK ON
        // =============================================

        if (attackActive)
        {
          digitalWrite(
            LED_PIN,
            HIGH
          );

          digitalWrite(
            ATTACK_SIGNAL_PIN,
            HIGH
          );

          Serial.println();
          Serial.println(
            "ATTACK_ON"
          );

          Serial.println(
            "Attack signal HIGH"
          );
        }

        // =============================================
        // ATTACK OFF
        // =============================================

        else
        {
          digitalWrite(
            LED_PIN,
            LOW
          );

          digitalWrite(
            ATTACK_SIGNAL_PIN,
            LOW
          );

          Serial.println();
          Serial.println(
            "ATTACK_OFF"
          );

          Serial.println(
            "Attack signal LOW"
          );
        }
      }
    }
  }

  lastReading =
    reading;

  // ===================================================
  // ATTACKER ACTIVITY
  // ===================================================

  if (attackActive)
  {
    // Generate CPU activity during attack
    for (
      int i = 0;
      i < 3000;
      i++
    )
    {
      dummyValue =
        sin(i * 0.05) *
        cos(i * 0.02) +
        sqrt(i + 5.0);
    }
  }
  else
  {
    delay(10);
  }
}
