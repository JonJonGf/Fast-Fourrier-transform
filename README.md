# Li-Fi Progressivo: Transmissão Óptica de Imagens via Coeficientes de Fourier 🚀

Este repositório contém o código-fonte e as especificações técnicas do projeto de comunicação óptica em espaço livre (Li-Fi) desenvolvido para a cadeira de Sinais e Sistemas / Processamento Digital de Sinais (PDS) na **Universidade Federal Fluminense (UFF)**.

O núcleo do projeto consiste em decompor matrizes de imagens no domínio da frequência espacial e transmiti-las serialmente através de um feixe laser modulado, permitindo uma reconstrução progressiva em tempo real no receptor à medida que as componentes convergem.

---

## 🧠 Como Funciona a Mágica? (Fluxo do Sinal)

Em vez de enviar a imagem pixel por pixel (o que seria pesado e ineficiente), nós usamos o processamento digital de sinais para otimizar o canal:

1. **Codificação (Python Emissor):** Uma imagem original é convertida para escala de cinza e redimensionada para uma matriz estática de 64 x 64 pixels. Cada linha é processada pela Transformada Rápida de Fourier (FFT).
2. **Truncamento Espectral:** Filtramos o sinal para enviar apenas a componente DC e os primeiros 50 **Coeficientes de Fourier** (Magnitude e Fase) de cada linha. Isso elimina as altas frequências espaciais (detalhes abruptos/quinas), mas mantém toda a estrutura principal da imagem, reduzindo drasticamente o tamanho do payload.
3. **Ponte de Transmissão (ESP32 Emissor):** Recebe o payload binário (.bin) estruturado via USB a 115.200 bit/s e chaveia a porta serial de hardware secundária no pino GPIO14.
4. **Canal Óptico:** Um diodo laser vermelho (KY-008) pisca na frequência fundamental de 57,6 kHz, propagando os dados binários pelo ar em espaço livre.
5. **Ponte de Recepção (ESP32 Receptor):** Um fotorreceptor óptico lê os pulsos de luz no pino RX2 (GPIO16) e repassa os bytes brutos instantaneamente para a porta USB do PC receptor.
6. **Síntese Inversa (Python Receptor):** O script varre o fluxo de dados caçando os bytes de sincronismo (0xAA 0xBB 0xCC 0xDD), remonta o espectro discreto aplicando simetria hermitiana, executa a Transformada Inversa (IFFT) e renderiza a imagem progressivamente na tela através do OpenCV.

---

## ⚡ Engenharia de Hardware (O Driver de Potência)

Como o microcontrolador ESP32 opera em 3,3V com limitação de corrente por GPIO (máximo 20 mA) e o laser KY-008 exige 30 mA alimentado por uma bateria externa de 8,4V, projetamos um circuito de isolamento e chaveamento **High-Side Switch**:

* **BC547 (BJT NPN):** Atua como o tradutor de nível lógico rápido. Quando a GPIO vai para nível ALTO (3,3V), o NPN satura e puxa a base do PNP para o GND.
* **BC558 (BJT PNP):** Com o emissor conectado ao positivo de 8,4V da bateria, ele satura quando sua base vai a zero, fechando a malha de potência para a carga.
* **Resistor de Pull-Up (10 kOhm):** Garante o corte total do PNP (laser completamente apagado) se a GPIO do ESP32 flutuar ou resetar.
* **Resistor de Queda em Série (150 Ohm):** Dimensionado para absorver a diferença de potencial entre a bateria e a tensão nominal do diodo laser, limitando a corrente em estáveis 32 mA para evitar degradação térmica do componente.

---