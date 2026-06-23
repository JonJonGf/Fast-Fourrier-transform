#include <Arduino.h>

void setup() {
 
  Serial.begin(115200);
  Serial.setTxBufferSize(1024); 
  Serial2.begin(115200, SERIAL_8N1, 16, 17); 
  Serial2.setRxBufferSize(1024); 
}

void loop() {
  
  while (Serial2.available() > 0) {
    Serial.write(Serial2.read());
  }
}