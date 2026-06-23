#include <Arduino.h>
#define RECEPTOR_PIN 16
#define TX_DUMMY_PIN 17
void setup() {
  Serial.begin(9600);
  Serial.setTxBufferSize(4096);
  pinMode(RECEPTOR_PIN, INPUT_PULLUP);
  Serial2.begin(9600, SERIAL_8N1, RECEPTOR_PIN, TX_DUMMY_PIN);
  Serial2.setRxBufferSize(4096);
}
void loop() {
  while (Serial2.available() > 0) {
    Serial.write(Serial2.read());
  }
}