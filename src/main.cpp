/*
 * DMX Output - Optimized for high-performance reception from Python
 * 
 * This Arduino code is simplified to just receive and display DMX data.
 * All computation is handled by the Python application running at 2x DMX rate.
 *
 * Jumper settings (per CQRobot wiki):
 * - TX jumper: TX-IO position → Digital pin 4
 * - RX jumper: RX-IO position → Digital pin 3 (ignored for TX-only)
 * - Slave/Master: Middle pin to DE → controlled by D2 (HIGH = TX)
 * - Enable: Connected (remove before upload, reconnect after)
 *
 * PC communication: Hardware USB Serial @ 250000 baud
 * DMX output: D4 via DmxSimple (bit-banged, TX-only)
 */

#include <Arduino.h>
#include <DmxSimple.h>

static const uint16_t DMX_CHANNELS = 512;
static const uint8_t STATUS_LED = 13;
static const uint8_t DMX_DIR_PIN = 2;  // RE/DE: HIGH = driver enabled (TX)
static const uint8_t DMX_TX_PIN = 4;   // Shield TX jumper set to D4

// Performance monitoring
static uint32_t frames_received = 0;
static uint32_t last_stats_time = 0;

void setup() {
  pinMode(STATUS_LED, OUTPUT);

  // Set D2 HIGH to enable transceiver driver (TX/master mode)
  pinMode(DMX_DIR_PIN, OUTPUT);
  digitalWrite(DMX_DIR_PIN, HIGH);

  // Start PC communication on the USB CDC serial
  Serial.begin(250000);

  // Initialize DmxSimple on D4
  DmxSimple.usePin(DMX_TX_PIN);
  DmxSimple.maxChannel(DMX_CHANNELS);

  // Clear all channels
  for (int channel = 1; channel <= (int)DMX_CHANNELS; channel++) {
    DmxSimple.write(channel, 0);
  }

  // Boot test pattern: channels 1-100 at full
  for (int channel = 1; channel <= 100; channel++) {
    DmxSimple.write(channel, 255);
  }
  // Hold briefly then turn off
  delay(500);
  for (int channel = 1; channel <= 100; channel++) {
    DmxSimple.write(channel, 0);
  }

  // Ready banner
  Serial.println("DMX_READY_OPTIMIZED");
  Serial.println("Channels:512");
  Serial.println("Mode:Pin4_TX");
  Serial.println("USB:Serial@250000");
  Serial.println("Processing:Python");

  digitalWrite(STATUS_LED, HIGH);
  delay(200);
  digitalWrite(STATUS_LED, LOW);
  
  // Initialize performance monitoring
  frames_received = 0;
  last_stats_time = millis();
}

void loop() {
  // Optimized high-performance parser for Python-generated frames
  // Frame format: [0xFF, len_lo, len_hi, payload[len]]
  enum ParserState { WAIT_START, WAIT_LEN_LO, WAIT_LEN_HI, WAIT_PAYLOAD };
  static ParserState state = WAIT_START;
  static uint16_t expectedLen = 0;
  static uint16_t bytesRead = 0;

  // Process all available bytes in one go for maximum performance
  while (Serial.available() > 0) {
    uint8_t byteIn = Serial.read();

    switch (state) {
      case WAIT_START:
        if (byteIn == 0xFF) {
          expectedLen = 0;
          bytesRead = 0;
          state = WAIT_LEN_LO;
        }
        break;

      case WAIT_LEN_LO:
        expectedLen = byteIn;
        state = WAIT_LEN_HI;
        break;

      case WAIT_LEN_HI:
        expectedLen |= ((uint16_t)byteIn) << 8;
        if (expectedLen == 0 || expectedLen > DMX_CHANNELS) {
          // Malformed frame; resync
          state = WAIT_START;
        } else {
          bytesRead = 0;
          digitalWrite(STATUS_LED, HIGH);
          state = WAIT_PAYLOAD;
        }
        break;

      case WAIT_PAYLOAD: {
        // Write channel (DMX is 1-indexed)
        uint16_t channel = bytesRead + 1;
        DmxSimple.write((int)channel, byteIn);
        bytesRead++;
        
        if (bytesRead >= expectedLen) {
          // Frame complete - update stats
          frames_received++;
          digitalWrite(STATUS_LED, LOW);
          state = WAIT_START;
        }
        break;
      }
    }
  }
  
  // Print performance stats every 5 seconds
  uint32_t current_time = millis();
  if (current_time - last_stats_time >= 5000) {
    Serial.print("Frames: ");
    Serial.println(frames_received);
    last_stats_time = current_time;
  }
}
