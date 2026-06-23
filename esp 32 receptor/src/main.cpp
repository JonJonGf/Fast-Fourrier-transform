#include <Arduino.h>
/*
 * PROJETO LI-FI PROGRESSIVO - ESP32 RECEPTOR (BANCADA UFF)
 * Velocidade: 57600 baud (Bits mais largos = sem erro de transição)
 * Lógica: Normal + Pull-Up Interno Ativo no pino 16
 */

#define RECEPTOR_PIN 16
#define TX_DUMMY_PIN 17

void setup() {
  // Configura a USB com o PC 2 para 57600 baud
  Serial.begin(57600);
  Serial.setTxBufferSize(1024);

  // Ativa o resistor de Pull-Up interno na GPIO 16
  pinMode(RECEPTOR_PIN, INPUT_PULLUP);

  // Inicializa a linha óptica em 57600 baud em modo NORMAL
  Serial2.begin(57600, SERIAL_8N1, RECEPTOR_PIN, TX_DUMMY_PIN);
  Serial2.setRxBufferSize(1024);

  Serial.println("==================================================");
  Serial.println("  [RECEPTOR 57600] PRONTO COM PULL-UP INTERNO ATIVO");
  Serial.println("==================================================");
  Serial.println("-> Aguardando os pulsos de luz lentos do Emissor...");
}

void loop() {
  // Ponte transparente: lê o Sensor Óptico e joga para a USB do PC
  while (Serial2.available() > 0) {
    Serial.write(Serial2.read());
  }
}