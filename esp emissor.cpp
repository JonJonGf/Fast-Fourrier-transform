/*
 * PROJECTO LI-FI PROGRESSIVO - ESP32 EMISSOR (BANCADA UFF)
 * * Descrição: Atua como um "Media Converter" de alta velocidade.
 * Recebe o payload binário de Fourier via USB (UART0) e retransmite
 * via luz laser modulada através da UART2 no GPIO14.
 */

#define TX_LASER_PIN 14  // Conectado no resistor de 1kΩ do transistor BC547
#define RX_DUMMY_PIN 12  // Pino obrigatório para iniciar a Serial2 (não será usado)
#define LED_STATUS 2     // LED azul interno do ESP32 DevKit para feedback visual

void setup() {
  // 1. Inicializa a Serial0 (Comunicação USB com o PC / Python Emissor)
  // Configuração padrão: 115200 bps, 8 bits de dados, sem paridade, 1 stop bit (8N1)
  Serial.begin(115200);

  // 2. Inicializa a Serial2 (Mapeada diretamente para o Driver do Laser)
  // Remapeamos o pino TX2 padrão para o GPIO14 conforme o diagrama do nosso circuito
  Serial2.begin(115200, SERIAL_8N1, RX_DUMMY_PIN, TX_LASER_PIN);

  // 3. Configura o LED de Status da placa
  pinMode(LED_STATUS, OUTPUT);
  digitalWrite(LED_STATUS, LOW);
}

void loop() {
  // Escuta ativa de baixíssima latência (Stream Bridge)
  if (Serial.available() > 0) {
    
    // Sinaliza visualmente na placa que os blocos de Fourier estão trafegando
    digitalWrite(LED_STATUS, HIGH); 
    
    // Lê o byte vindo do USB do PC
    uint8_t byteTransmissao = Serial.read();
    
    // Injeta o byte imediatamente na base do BC547 via GPIO14
    // Isso vai modular o feixe do laser KY-008 na frequência de 57.6 kHz
    Serial2.write(byteTransmissao);
    
  } else {
    // Apaga o LED se o canal óptico estiver ocioso
    digitalWrite(LED_STATUS, LOW);
  }
}