#include <Arduino.h>
/*
 * PROJETO LI-FI PROGRESSIVO - ESP32 EMISSOR (BANCADA UFF)
 * Velocidade: 9600 baud (Imunidade a tempo de subida RC)
 * Lógica: Invertida (Repouso = Laser Apagado)
 */

#define TX_LASER_PIN 17 
#define RX_DUMMY_PIN 16  

void setup() {
  // Configura a USB com o PC 1 para 57600 baud
  Serial.begin(57600);
  
  pinMode(TX_LASER_PIN, OUTPUT);
  
  // MODO ALINHAMENTO: Laser aceso por 5 segundos para mirar
  digitalWrite(TX_LASER_PIN, HIGH); 
  Serial.println("==================================================");
  Serial.println("  [EMISSOR 57600] MODO ALINHAMENTO: LASER ACESO (5s)");
  Serial.println("==================================================");
  delay(5000); 
  
  // Apaga o laser e passa o controle para o hardware da Serial2
  digitalWrite(TX_LASER_PIN, LOW); 
  
  // Inicializa a linha óptica em 57600 baud com lógica invertida (true)
  Serial2.begin(57600, SERIAL_8N1, RX_DUMMY_PIN, TX_LASER_PIN, true);
  Serial.println("[OK] Transmissão ativa a 57600 baud. Laser em espera...");
  Serial.println("==================================================");
}

void loop() {
  // Ponte transparente: lê o Python (USB) e joga no Laser
  while (Serial.available() > 0) {
    Serial2.write(Serial.read());
  }
}