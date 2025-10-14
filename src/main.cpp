/*
 * DMX Output - CQRobot Shield using D4 for TX (IO mode) and D2 for direction
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
  Serial.println("DMX_READY");
  Serial.println("Channels:512");
  Serial.println("Mode:Pin4_TX");
  Serial.println("USB:Serial@250000");

  digitalWrite(STATUS_LED, HIGH);
  delay(200);
  digitalWrite(STATUS_LED, LOW);
}

void loop() {
  // Robust non-blocking parser:
  // Frame = 0xFF, len_lo, len_hi, payload[len]
  enum ParserState { WAIT_START, WAIT_LEN_LO, WAIT_LEN_HI, WAIT_PAYLOAD };
  static ParserState state = WAIT_START;
  static uint16_t expectedLen = 0;
  static uint16_t bytesRead = 0;

  while (Serial.available() > 0) {
    int byteIn = Serial.read();

    switch (state) {
      case WAIT_START:
        if (byteIn == 0xFF) {
          expectedLen = 0;
          bytesRead = 0;
          state = WAIT_LEN_LO;
        }
        break;

      case WAIT_LEN_LO:
        expectedLen = (uint8_t)byteIn;
        state = WAIT_LEN_HI;
        break;

      case WAIT_LEN_HI:
        expectedLen |= ((uint16_t)(uint8_t)byteIn) << 8;
        if (expectedLen == 0 || expectedLen > DMX_CHANNELS) {
          // Malformed; resync
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
        DmxSimple.write((int)channel, (uint8_t)byteIn);
        bytesRead++;
        if (bytesRead >= expectedLen) {
          // Frame complete
          digitalWrite(STATUS_LED, LOW);
          state = WAIT_START;
        }
        break;
      }
    }
  }
}
