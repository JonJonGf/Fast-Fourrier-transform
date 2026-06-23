#include <Arduino.h>

#define TX_LASER_PIN 17 
#define RX_DUMMY_PIN 16  

void setup() {
  Serial.begin(115200);
  
  pinMode(TX_LASER_PIN, OUTPUT);
  
  // 1. Acende o laser por 2 segundos para vocês alinharem a mira
  digitalWrite(TX_LASER_PIN, HIGH); 
  delay(2000); 
  
  // 2. Apaga o laser
  digitalWrite(TX_LASER_PIN, LOW); 
  
  // 3. O SEGREDO: O 5º parâmetro (true) ativa a inversão de hardware da UART.
  // Agora, o estado de repouso (Idle) passa a ser LOW (Laser desligado!)
  Serial2.begin(115200, SERIAL_8N1, RX_DUMMY_PIN, TX_LASER_PIN,true);
}

void loop() {
  if (Serial.available() > 0) {
    while (Serial.available() > 0) {
      Serial2.write(Serial.read());
    }
  } 
}