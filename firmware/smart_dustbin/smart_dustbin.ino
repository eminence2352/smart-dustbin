/*
 * =====================================================================
 * SMART DUSTBIN - IOT EDGE FIRMWARE
 * Integrates with: Smart Dustbin Express & SQLite Dashboard
 * Endpoint: POST /api/readings
 * =====================================================================
 */

#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>
#include <math.h>

// ---------- BOARD & NETWORK SELECTION ----------
#if defined(ESP8266)
  #include <ESP8266WiFi.h>
  #include <ESP8266HTTPClient.h>
  #include <WiFiClient.h>
  #include <Servo.h>

  // NodeMCU / ESP8266 Pin Map
  #define IR_PIN      D6
  #define SERVO_PIN   D7
  #define DHT_PIN     D5
  #define TRIG_PIN    D0
  #define ECHO_PIN    D8
  #define SDA_PIN     D2
  #define SCL_PIN     D1
#elif defined(ESP32)
  #include <WiFi.h>
  #include <HTTPClient.h>
  #include <ESP32Servo.h>

  // ESP32 Standard Pin Map
  #define IR_PIN      27
  #define SERVO_PIN   13
  #define DHT_PIN     4
  #define TRIG_PIN    23
  #define ECHO_PIN    18
  #define SDA_PIN     21
  #define SCL_PIN     22
#else
  #error "Please select ESP8266 or ESP32 board in your Arduino IDE Tools menu."
#endif

#define DHT_TYPE DHT11

// =====================================================================
// USER CONFIGURATION: WI-FI & SERVER ENDPOINT
// =====================================================================
// 1. Enter your Wi-Fi credentials (must be 2.4 GHz network)
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// 2. Local IP address of the PC running the Node.js backend
// (Port 3000 is default. Check 'ipconfig' on Windows or 'hostname -I' on Linux/Mac)
const char* SERVER_URL    = "http://YOUR_COMPUTER_IP:3000/api/readings";

// 3. Bin identifier matching registered bin in dashboard (e.g., bin-01)
const char* BIN_ID        = "bin-01";

// =====================================================================
// CALIBRATION & MECHANICS
// =====================================================================
const int OPEN_ANGLE   = 150;
const int CLOSED_ANGLE = 0;

const unsigned long OPEN_TIME           = 5000; // Lid stays open for 5 seconds
const unsigned long ULTRASONIC_INTERVAL = 1000; // Check fill every 1s
const unsigned long DHT_INTERVAL        = 3000; // Read DHT every 3s
const unsigned long TELEMETRY_INTERVAL  = 5000; // Send HTTP POST every 5s

// Distance from sensor face to bottom of empty bin (cm)
const float BIN_EMPTY_DISTANCE_CM = 15.0;
// Distance from sensor face when bin is considered 100% full (cm)
const float BIN_FULL_DISTANCE_CM  = 3.0;

// ---------- COMPONENTS ----------
LiquidCrystal_I2C lcd(0x27, 16, 2);
DHT dht(DHT_PIN, DHT_TYPE);
Servo lidServo;

// ---------- RUNTIME VARIABLES ----------
bool lidIsOpen = false;
unsigned long lastDetectionTime = 0;
unsigned long lastLidCloseTime  = 0;
unsigned long lastUltrasonicRead= 0;
unsigned long lastDHTRead       = 0;
unsigned long lastTelemetrySend = 0;

float temperature = NAN;
float humidity    = NAN;
float distanceCm  = NAN;
int fillPercent   = -1;

// Tracks lid openings between telemetry transmissions
int opensDeltaAccumulator = 0;

// ---------- SMOOTH GRADUAL SERVO CONTROLLER ----------
int currentServoAngle = CLOSED_ANGLE; // Current position in degrees
int targetServoAngle  = CLOSED_ANGLE; // Desired target angle
unsigned long lastServoStepTime = 0;
const unsigned long SERVO_STEP_INTERVAL = 15; // 15ms per micro-step
const int SERVO_STEP_DEGREE = 2;             // 2 degrees per step (smooth ~1.1s total rise)

// ---------- MEASURE DISTANCE (MEDIAN FILTER) ----------
float singleDistanceMeasurement() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long duration = pulseIn(ECHO_PIN, HIGH, 30000UL);
  if (duration == 0) return NAN;

  float dist = (duration * 0.0343) / 2.0;
  if (dist < 2.0 || dist > 400.0) return NAN;
  return dist;
}

// Samples 3 measurements and takes median to filter spikes
float measureDistance() {
  float readings[3];
  int validCount = 0;

  for (int i = 0; i < 3; i++) {
    float d = singleDistanceMeasurement();
    if (!isnan(d)) {
      readings[validCount++] = d;
    }
    delay(20);
  }

  if (validCount == 0) return NAN;
  if (validCount == 1) return readings[0];
  if (validCount == 2) return (readings[0] + readings[1]) / 2.0;

  // Simple sort 3 elements
  if (readings[0] > readings[1]) { float t = readings[0]; readings[0] = readings[1]; readings[1] = t; }
  if (readings[1] > readings[2]) { float t = readings[1]; readings[1] = readings[2]; readings[2] = t; }
  if (readings[0] > readings[1]) { float t = readings[0]; readings[0] = readings[1]; readings[1] = t; }

  return readings[1]; // Median
}

// ---------- CONNECT TO WIFI ----------
void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.print("Connecting to Wi-Fi '");
  Serial.print(WIFI_SSID);
  Serial.print("'");

  lcd.setCursor(0, 1);
  lcd.print("WiFi: Connecting");

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long startAttempt = millis();
  // Non-blocking attempt during startup (up to 10 seconds)
  while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < 10000) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWi-Fi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());

    lcd.setCursor(0, 1);
    lcd.print("IP: ");
    lcd.print(WiFi.localIP().toString().substring(0, 12));
    delay(1500);
  } else {
    Serial.println("\nWi-Fi Connection Failed (will retry in background)");
    lcd.setCursor(0, 1);
    lcd.print("WiFi: Offline   ");
    delay(1000);
  }
}

// ---------- TELEMETRY INGESTION (HTTP POST) ----------
void sendTelemetry() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[Telemetry] Wi-Fi not connected. Skipping upload.");
    return;
  }

  // Build JSON payload
  // Ingestion schema requires: binId, distanceCm, tempC, humidity, opensDelta
  String payload = "{";
  payload += "\"binId\":\"" + String(BIN_ID) + "\",";

  // If lid is open or moving, avoid sending invalid ultrasonic echoes
  if (!isnan(distanceCm) && !lidIsOpen && (millis() - lastLidCloseTime > 1500)) {
    payload += "\"distanceCm\":" + String(distanceCm, 2) + ",";
  } else {
    payload += "\"distanceCm\":null,";
  }

  if (!isnan(temperature) && temperature >= 0.0 && temperature <= 50.0) {
    payload += "\"tempC\":" + String(temperature, 1) + ",";
  } else {
    payload += "\"tempC\":null,";
  }

  if (!isnan(humidity) && humidity >= 0.0 && humidity <= 100.0) {
    payload += "\"humidity\":" + String((int)(humidity + 0.5)) + ",";
  } else {
    payload += "\"humidity\":null,";
  }

  int opensToSend = opensDeltaAccumulator;
  payload += "\"opensDelta\":" + String(opensToSend);
  payload += "}";

  Serial.print("[HTTP POST] ");
  Serial.print(SERVER_URL);
  Serial.print(" -> ");
  Serial.println(payload);

#if defined(ESP8266)
  WiFiClient client;
  HTTPClient http;
  http.begin(client, SERVER_URL);
#else
  HTTPClient http;
  http.begin(SERVER_URL);
#endif

  http.addHeader("Content-Type", "application/json");
  http.setTimeout(2500); // 2.5s maximum timeout to keep lid operations responsive

  int httpCode = http.POST(payload);

  if (httpCode > 0) {
    Serial.print("[HTTP Result] Code: ");
    Serial.println(httpCode);
    if (httpCode == HTTP_CODE_OK) {
      String response = http.getString();
      Serial.print("[HTTP Response] ");
      Serial.println(response);

      // Decrement the counted openings that were safely delivered
      opensDeltaAccumulator -= opensToSend;
      if (opensDeltaAccumulator < 0) opensDeltaAccumulator = 0;
    }
  } else {
    Serial.print("[HTTP Error] POST failed: ");
    Serial.println(http.errorToString(httpCode).c_str());
  }

  http.end();
}

// ---------- SETUP ----------
void setup() {
  Serial.begin(9600);
  delay(200);

  pinMode(IR_PIN, INPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  digitalWrite(TRIG_PIN, LOW);

  // Initialize LCD
#if defined(ESP8266)
  Wire.begin(SDA_PIN, SCL_PIN);
#else
  Wire.begin(SDA_PIN, SCL_PIN);
#endif

  lcd.init();
  lcd.backlight();
  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("Smart Waste Bin");
  lcd.setCursor(0, 1);
  lcd.print("Starting...");

  dht.begin();

  lidServo.attach(SERVO_PIN);
  currentServoAngle = CLOSED_ANGLE;
  targetServoAngle  = CLOSED_ANGLE;
  lidServo.write(CLOSED_ANGLE);

  delay(1200);

  // Connect to Wi-Fi
  connectWiFi();

  lcd.clear();
  Serial.println("\n--- Smart Waste Bin System Ready ---");
}

// ---------- MAIN LOOP ----------
void loop() {
  unsigned long now = millis();

  // =======================================================
  // 1. FAST LOCAL LOOP: IR SENSOR & SERVO TARGET LOGIC
  // =======================================================
  // Active LOW: LOW indicates hand / object presence
  bool objectDetected = (digitalRead(IR_PIN) == LOW);

  if (objectDetected) {
    lastDetectionTime = now;

    if (!lidIsOpen) {
      targetServoAngle = OPEN_ANGLE; // Command smooth gradual rise
      lidIsOpen = true;
      opensDeltaAccumulator++; // Record new opening event

      Serial.println(">> Object detected: Lid smoothly RISING...");
    }
  }

  // Automatic lid closure after clear delay
  if (lidIsOpen && !objectDetected && (now - lastDetectionTime >= OPEN_TIME)) {
    targetServoAngle = CLOSED_ANGLE; // Command smooth gradual lowering
    lidIsOpen = false;
    lastLidCloseTime = now;

    Serial.println(">> Object cleared: Lid smoothly CLOSING...");
  }

  // =======================================================
  // 1b. NON-BLOCKING SMOOTH SERVO MOTION CONTROLLER
  // Steps servo gradually so it rises and closes steadily without sudden jerks
  // =======================================================
  if (now - lastServoStepTime >= SERVO_STEP_INTERVAL) {
    lastServoStepTime = now;

    if (currentServoAngle < targetServoAngle) {
      currentServoAngle += SERVO_STEP_DEGREE;
      if (currentServoAngle > targetServoAngle) currentServoAngle = targetServoAngle;
      lidServo.write(currentServoAngle);
    } else if (currentServoAngle > targetServoAngle) {
      currentServoAngle -= SERVO_STEP_DEGREE;
      if (currentServoAngle < targetServoAngle) currentServoAngle = targetServoAngle;
      lidServo.write(currentServoAngle);
    }
  }

  // =======================================================
  // 2. ULTRASONIC FILL MEASUREMENT
  // (Inhibited while lid is moving or open to avoid false reflections)
  // =======================================================
  bool servoMoving = (currentServoAngle != targetServoAngle);

  if (now - lastUltrasonicRead >= ULTRASONIC_INTERVAL) {
    lastUltrasonicRead = now;

    if (!lidIsOpen && !servoMoving && (currentServoAngle == CLOSED_ANGLE) && (now - lastLidCloseTime >= 1000)) {
      float measured = measureDistance();

      if (!isnan(measured)) {
        distanceCm = measured;

        // Accurate fill percentage based on physical bin dimensions
        float fill = ((BIN_EMPTY_DISTANCE_CM - distanceCm) /
                      (BIN_EMPTY_DISTANCE_CM - BIN_FULL_DISTANCE_CM)) * 100.0;

        fill = constrain(fill, 0.0, 100.0);
        fillPercent = (int)(fill + 0.5);

        Serial.print("[Ultrasonic] Dist: ");
        Serial.print(distanceCm, 1);
        Serial.print(" cm | Fill: ");
        Serial.print(fillPercent);
        Serial.println("%");
      }
    }
  }

  // =======================================================
  // 3. DHT11 CLIMATE SENSING
  // =======================================================
  if (now - lastDHTRead >= DHT_INTERVAL) {
    lastDHTRead = now;

    float newHumidity = dht.readHumidity();
    float newTemperature = dht.readTemperature();

    if (!isnan(newHumidity) && !isnan(newTemperature)) {
      humidity = newHumidity;
      temperature = newTemperature;

      Serial.print("[DHT11] Temp: ");
      Serial.print(temperature, 1);
      Serial.print(" C | Hum: ");
      Serial.print(humidity, 1);
      Serial.println("%");
    }
  }

  // =======================================================
  // 4. TELEMETRY TRANSMISSION (HTTP POST TO DASHBOARD)
  // =======================================================
  if (now - lastTelemetrySend >= TELEMETRY_INTERVAL) {
    lastTelemetrySend = now;
    sendTelemetry();
  }

  // =======================================================
  // 5. UPDATE 16x2 LCD DISPLAY
  // =======================================================
  static unsigned long lastLcdUpdate = 0;
  if (now - lastLcdUpdate >= 500) {
    lastLcdUpdate = now;

    // Row 0: Temperature & Humidity
    lcd.setCursor(0, 0);
    if (isnan(temperature) || isnan(humidity)) {
      lcd.print("T:--.-C H:--%   ");
    } else {
      lcd.print("T:");
      lcd.print(temperature, 1);
      lcd.print("C H:");
      lcd.print((int)(humidity + 0.5));
      lcd.print("%   ");
    }

    // Row 1: Fill percentage & Wi-Fi indicator
    lcd.setCursor(0, 1);
    if (fillPercent < 0) {
      lcd.print("Fill: Measuring ");
    } else {
      lcd.print("Fill: ");
      lcd.print(fillPercent);
      lcd.print("% ");
      if (WiFi.status() == WL_CONNECTED) {
        lcd.print("[ON] ");
      } else {
        lcd.print("[OFF]");
      }
    }
  }

  delay(5);
}
