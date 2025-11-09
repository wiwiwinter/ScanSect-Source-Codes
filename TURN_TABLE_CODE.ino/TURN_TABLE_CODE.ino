#include <AccelStepper.h>
#include <EEPROM.h>
#include <LiquidCrystal.h>

// Stepper pins
#define X_DIR_PIN 9
#define X_STEP_PIN 10
#define X_ENABLE_PIN 11

// Button pins
#define RESET_BUTTON_PIN 4  // Reset position button
#define PAUSE_BUTTON_PIN 3  // Pause button
#define RESUME_BUTTON_PIN 2 // Resume button

// LCD pins
#define LCD_RS 13
#define LCD_EN 12
#define LCD_D4 8
#define LCD_D5 7
#define LCD_D6 6
#define LCD_D7 5

// Initialize LCD object
LiquidCrystal lcd(LCD_RS, LCD_EN, LCD_D4, LCD_D5, LCD_D6, LCD_D7);

AccelStepper stepperX(AccelStepper::DRIVER, X_STEP_PIN, X_DIR_PIN);

const int stepsPerMoveX = round(200 / 1.8 * (5.0 / 20.0)); // Steps per 5-degree move
const unsigned long pauseMs = 3000; // Wait time at each step

unsigned long pauseStartTime = 0;
bool isMovingX = true;
bool isPaused = false;
int xMoveCount = 0;

bool waitingForCapture = false; // flag to wait for Python "DONE"

void setup() {
  Serial.begin(115200);

  // Initialize LCD
  lcd.begin(16, 2);
  lcd.clear();
  lcd.print("Initializing...");

  pinMode(X_ENABLE_PIN, OUTPUT);
  digitalWrite(X_ENABLE_PIN, LOW); // Enable stepper driver

  pinMode(RESET_BUTTON_PIN, INPUT_PULLUP);
  pinMode(PAUSE_BUTTON_PIN, INPUT_PULLUP);
  pinMode(RESUME_BUTTON_PIN, INPUT_PULLUP);

  stepperX.setMaxSpeed(200.0);
  stepperX.setAcceleration(100.0);

  // Restore previous X position
  int savedXPos;
  EEPROM.get(0, savedXPos);
  stepperX.setCurrentPosition(savedXPos);

  // Move to home
  stepperX.moveTo(0);
  while (stepperX.distanceToGo() != 0) {
    stepperX.run();
  }

  lcd.clear();
  lcd.print("Ready to start");
  stepperX.move(stepsPerMoveX);
}

void updateLCD(int angle) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Angle: ");
  lcd.print(angle);
  lcd.print(" deg");
  lcd.setCursor(0, 1);
  if (isPaused) {
    lcd.print("Status: PAUSED");
  } else if (waitingForCapture) {
    lcd.print("Status: CAPTURE");
  } else {
    lcd.print("Status: RUNNING");
  }
}

void loop() {
  // Handle reset
  if (digitalRead(RESET_BUTTON_PIN) == LOW) {
    resetToHome();
    return;
  }

  // Handle pause/resume
  if (digitalRead(PAUSE_BUTTON_PIN) == LOW) {
    isPaused = true;
    lcd.clear();
    lcd.print("Status: PAUSED");
    return;
  }
  if (digitalRead(RESUME_BUTTON_PIN) == LOW) {
    if (isPaused) {
      // If we were paused after complete rotation, reset to home and start again
      if (xMoveCount >= 72) {
        resetToHome();
      } else {
        // Normal resume
        isPaused = false;
        lcd.clear();
        lcd.print("Status: RUNNING");
      }
    }
  }
  if (isPaused) return;

  // If waiting for Python confirmation, check serial
  if (waitingForCapture) {
    if (Serial.available()) {
      String msg = Serial.readStringUntil('\n');
      msg.trim();
      if (msg == "DONE") {
        waitingForCapture = false;
        pauseStartTime = millis(); // Start delay timer for next move
        updateLCD(xMoveCount * 5); // Update LCD status
      }
    }
    return; // Stop movement until Python replies
  }

  if (isMovingX) {
    if (stepperX.distanceToGo() == 0) {
      // Movement complete, prepare for capture
      isMovingX = false;
      xMoveCount++;

      Serial.print("X-axis Rotation: ");
      Serial.println(xMoveCount * 5);

      // Tell Python we are ready for capture
      Serial.println("READY");
      waitingForCapture = true;

      updateLCD(xMoveCount * 5);

      // Check if we've completed full rotation (72 steps of 5 degrees = 360 degrees)
      if (xMoveCount >= 72) {
        resetToHome();
        return;
      }
    } else {
      stepperX.run();
    }
  } else if (!waitingForCapture) {
    // Only continue with pause timing if not waiting for capture
    if (millis() - pauseStartTime >= pauseMs) {
      stepperX.move(stepsPerMoveX);
      isMovingX = true;
    }
  }

  // Save position periodically
  static unsigned long lastSaveTime = 0;
  if (millis() - lastSaveTime > 5000) {
    savePosition();
    lastSaveTime = millis();
  }
}

void savePosition() {
  int currentXPos = stepperX.currentPosition();
  EEPROM.put(0, currentXPos);
}

void resetToHome() {
  lcd.clear();
  lcd.print("Reset to home");
  stepperX.moveTo(0);
  while (stepperX.distanceToGo() != 0) {
    stepperX.run();
  }
  lcd.clear();
  lcd.print("Reset complete.");
  xMoveCount = 0;
  waitingForCapture = false; // Reset capture flag
  isMovingX = true; // Ready to start moving again
  savePosition();
  Serial.println("RESET_COMPLETE");
  
  // Start the sequence again
  stepperX.move(stepsPerMoveX);
}