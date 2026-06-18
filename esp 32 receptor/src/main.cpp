#include <Arduino.h>
/*
 * PROJETO LI-FI PROGRESSIVO - ESP32 RECEPTOR (BANCADA UFF)
 * Descrição: Captura os dados digitais do fotorreceptor via UART2 (RX2),
 * e repassa instantaneamente via USB (UART0) para o PC rodar a síntese.
 */

#define RX_LASER_PIN 16  // Conectado na saída digital (DO) do fotorreceptor óptico
#define TX_DUMMY_PIN 17  // Pino obrigatório para iniciar a Serial2 (não será usado)
#define LED_STATUS 2     // LED azul interno do ESP32 para feedback visual

void setup() {
  // 1. Inicializa a Serial0 (Comunicação USB com o PC / Python Receptor)
  Serial.begin(115200);

  // 2. Inicializa a Serial2 (Mapeada para ler o sensor óptico)
  // Usamos o pino padrão RX2 (GPIO16) rodando nos mesmos 115200 bps
  Serial2.begin(115200, SERIAL_8N1, RX_LASER_PIN, TX_DUMMY_PIN);

  // 3. Configura o LED de Status
  pinMode(LED_STATUS, OUTPUT);
  digitalWrite(LED_STATUS, LOW);
}

void loop() {
  // Escuta ativa do canal óptico de baixa latência
  if (Serial2.available() > 0) {
    
    // Acende o LED interno indicando que a luz do laser está trazendo dados
    digitalWrite(LED_STATUS, HIGH);
    
    // Lê o byte que o sensor óptico decodificou do laser
    uint8_t byteRecebido = Serial2.read();
    
    // Cospe o byte imediatamente para o cabo USB em direção ao Python
    Serial.write(byteRecebido);
    
  } else {
    // Apaga o LED se o canal óptico estiver ocioso (laser desligado ou desalinhado)
    digitalWrite(LED_STATUS, LOW);
  }
}