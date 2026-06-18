#include <Arduino.h>
/*
 * PROJETO LI-FI PROGRESSIVO - ESP32 EMISSOR (BANCADA UFF)
 * ---------------------------------------------------------------------
 * Mapeado para a GPIO 17 (Nativo TX2) - Direto na base do BC547
 * ---------------------------------------------------------------------
 */

#define TX_LASER_PIN 17  // ATUALIZADO: Agora soldado no TX2 padrão
#define RX_DUMMY_PIN 16  // Pino RX2 padrão (pode deixar mapeado aqui)
#define LED_STATUS 2     // LED azul interno para feedback

void setup() {
  // 1. Inicializa a Serial0 (Comunicação USB com o PC)
  Serial.begin(115200);

  // 2. Configura os pinos de IO digitais
  pinMode(LED_STATUS, OUTPUT);
  pinMode(TX_LASER_PIN, OUTPUT);
  
  digitalWrite(LED_STATUS, LOW);

  // 3. MODO ALINHAMENTO: Força a GPIO 17 em HIGH para o laser ficar aceso estático
  digitalWrite(TX_LASER_PIN, HIGH); 
  
  Serial.println("==================================================");
  Serial.println("  [MODO ALINHAMENTO] LASER ACESO NA GPIO 17        ");
  Serial.println("==================================================");
  Serial.println("-> Mire o feixe exatamente no fototransistor (10s)...");
  
  // 10 segundos para ajustar a mira mecânica
  delay(10000); 
  
  Serial.println("-> Tempo esgotado! Ativando Serial2 (Modulação)...");
  Serial.println("==================================================");

  // 4. PASSA O BASTÃO: Inicializa a Serial2 forçando os pinos 16 e 17
  Serial2.begin(115200, SERIAL_8N1, RX_DUMMY_PIN, TX_LASER_PIN);
}

void loop() {
  // Escuta ativa de alta velocidade (Stream Bridge)
  if (Serial.available() > 0) {
    
    // Acende o LED interno indicando que dados estão passando
    digitalWrite(LED_STATUS, HIGH); 
    
    // Esvazia o buffer da USB direto para o Laser via GPIO 17
    while (Serial.available() > 0) {
      Serial2.write(Serial.read());
    }
    
  } else {
    // Apaga o LED se o canal óptico estiver ocioso
    digitalWrite(LED_STATUS, LOW);
  }
}