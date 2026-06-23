#include <Arduino.h>
#define TX_LASER_PIN 17 
#define RX_DUMMY_PIN 16  
void setup() {
  Serial.begin(9600);
  Serial.setRxBufferSize(4096); 
  pinMode(TX_LASER_PIN, OUTPUT);
  digitalWrite(TX_LASER_PIN, HIGH); 
  delay(5000); 
  digitalWrite(TX_LASER_PIN, LOW); 
  Serial2.begin(9600, SERIAL_8N1, RX_DUMMY_PIN, TX_LASER_PIN, true);
  Serial2.setTxBufferSize(4096); 
}
void loop() {
  while (Serial.available() > 0) {
    Serial2.write(Serial.read());
  }
}