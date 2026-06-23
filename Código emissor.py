import cv2
import numpy as np
import struct
import time
import serial
import os

# ==========================================
# CONFIGURAÇÕES DA BANCADA TRANSMISSORA
# ==========================================
PORTA_COM = "COM3"  
BAUD_RATE = 9600     
BIN_PATH = "dados_fourier.bin"

def rodar_emissor_lifi():
    diretorio_do_script = os.path.dirname(os.path.abspath(__file__))
    caminho_da_imagem = os.path.join(diretorio_do_script, "imagens", "vaspinho.png")

    print(f"[INFO] Carregando imagem de: {caminho_da_imagem}")
    img = cv2.imread(caminho_da_imagem, cv2.IMREAD_GRAYSCALE)

    if img is None:
        print(f"[ERRO CRÍTICO] Não encontrei a imagem em '{caminho_da_imagem}'")
        return

    img_resized = cv2.resize(img, (64, 64))
    buffer_total = bytearray()
    sync_bytes = bytes([0xAA, 0xBB, 0xCC, 0xDD])

    print("[MATEMÁTICA] Calculando a FFT de cada linha...")
    for i in range(64):
        linha = img_resized[i, :]
        fft_linha = np.fft.fft(linha)
        
        dc_component = float(np.real(fft_linha[0]))
        amplitudes = np.abs(fft_linha[1:51]).astype(np.float32)
        fases = np.angle(fft_linha[1:51]).astype(np.float32)
        
        # Payload matemático (404 bytes)
        dados_sinal = struct.pack('<f50f50f', dc_component, *amplitudes, *fases)
        
        # NOVO PROTOCOLO: Sync (4 bytes) + ID da Linha (1 byte) + Dados (404 bytes) = 409 bytes
        line_id_byte = bytes([i])
        frame_linha = sync_bytes + line_id_byte + dados_sinal
        buffer_total.extend(frame_linha)

    try:
        print(f"[USB] Abrindo conexão com o ESP32 Emissor na porta {PORTA_COM}...")
        ser = serial.Serial(PORTA_COM, BAUD_RATE, timeout=2)
        time.sleep(2) 
        
        print("\n==================================================")
        print("   TRANSMISSÃO COM INDEXAÇÃO DE LINHA ATIVADA     ")
        print("==================================================")
        start_time = time.time()
        
        # O tamanho do passo agora mudou para 409 bytes por linha
        tamanho_linha = 409
        for i in range(64):
            inicio = i * tamanho_linha
            fim = inicio + tamanho_linha
            fatia_linha = buffer_total[inicio:fim]
            
            ser.write(fatia_linha)
            ser.flush() 
            
            # Ajustado para 0.45s para bater com o tempo de transmissão física dos 409 bytes
            time.sleep(0.45)
            
            if (i + 1) % 10 == 0 or i == 63:
                print(f" -> Progresso: Linha [{i + 1:02d}/64] enviada com ID {i:02d}.")

        end_time = time.time()
        print("==================================================")
        print(f"[SUCESSO] Varredura Li-Fi concluída em {end_time - start_time:.2f} segundos!")
        ser.close()
        
    except Exception as e:
        print(f"\n[ERRO] Falha durante a transmissão serial: {e}")

if __name__ == "__main__":
    rodar_emissor_lifi()