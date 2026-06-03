import cv2
import numpy as np
import struct
import time
import serial

# ==========================================
# CONFIGURAÇÕES DO PROJETO
# ==========================================
IMG_PATH = "vaspinho.png"      # Substitua pelo nome ou caminho da sua imagem
BIN_PATH = "dados_fourier.bin"  # Nome do arquivo binário que será gerado
PORTA_COM = "COM3"              # Mude para a porta COM do seu ESP32 (ex: COM3, COM4 ou /dev/ttyUSB0 no Linux)
BAUD_RATE = 115200

def gerar_e_enviar_fourier():
    # --------------------------------------
    # 1. PROCESSAMENTO DA IMAGEM
    # --------------------------------------
    # Carrega em escala de cinza
    img = cv2.imread(IMG_PATH, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Erro: Não foi possível encontrar a imagem em '{IMG_PATH}'")
        return
    
    # Força a resolução estática de 64x64 pixels
    img_resized = cv2.resize(img, (64, 64))
    
    buffer_total = bytearray()
    
    # Cabeçalho de sincronismo de 4 bytes por linha
    sync_bytes = bytes([0xAA, 0xBB, 0xCC, 0xDD])
    
    print("Processando linhas da imagem via FFT...")
    for i in range(64):
        linha = img_resized[i, :]
        
        # Executa a Transformada Rápida de Fourier (FFT) na linha
        fft_linha = np.fft.fft(linha)
        
        # Componente DC (k=0) -> Apenas a magnitude (brilho médio da linha)
        dc_component = float(np.abs(fft_linha[0]))
        
        # Extrai as primeiras 50 componentes de frequência espacial (k=1 até 50)
        amplitudes = np.abs(fft_linha[1:51]).astype(np.float32)
        fases = np.angle(fft_linha[1:51]).astype(np.float32)
        
        # Empacota os dados em binário (padrão Little-Endian '<')
        # f: 1 float (DC) | 50f: 50 floats (Amplitudes) | 50f: 50 floats (Fases)
        # Total = 101 floats * 4 bytes = 404 bytes de dados de sinais
        dados_sinal = struct.pack('<f50f50f', dc_component, *amplitudes, *fases)
        
        # Monta o frame final da linha: Sync (4 bytes) + Dados (404 bytes) = 408 bytes
        frame_linha = sync_bytes + dados_sinal
        buffer_total.extend(frame_linha)

    # --------------------------------------
    # 2. SALVAMENTO DO ARQUIVO BINÁRIO (.BIN)
    # --------------------------------------
    with open(BIN_PATH, "wb") as f:
        f.write(buffer_total)
    print(f"Arquivo binário salvo com sucesso: '{BIN_PATH}' ({len(buffer_total)} bytes)")

    # --------------------------------------
    # 3. TRANSMISSÃO SERIAL VIA USB PARA O ESP32
    # --------------------------------------
    try:
        print(f"Abrindo conexão com o ESP32 na porta {PORTA_COM}...")
        # Abre a porta serial configurada
        ser = serial.Serial(PORTA_COM, BAUD_RATE, timeout=2)
        
        # O ESP32 costuma resetar quando a porta serial é aberta pelo PC.
        # Aguardamos 2 segundos para o bootloader estabilizar antes de enviar dados.
        time.sleep(2) 
        
        print(f"Transmitindo payload óptico para a bancada ({len(buffer_total)} bytes)...")
        start_time = time.time()
        
        # Envia o buffer completo de uma vez só pela Serial
        ser.write(buffer_total)
        
        # Garante o escoamento total do buffer de hardware do PC
        ser.flush() 
        
        end_time = time.time()
        print(f"Transmissão concluída em {end_time - start_time:.2f} segundos!")
        
        ser.close()
        print("Porta serial fechada com segurança.")
        
    except serial.SerialException as e:
        print(f"\nErro de hardware na Serial: {e}")
        print("Verifique se o ESP32 está conectado corretamente e se fechou o Monitor Serial da IDE do Arduino.")
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")

if __name__ == "__main__":
    gerar_e_enviar_fourier()