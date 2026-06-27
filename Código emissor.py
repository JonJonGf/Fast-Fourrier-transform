import cv2
import numpy as np
import struct
import time
import serial
import os

PORTA_COM = "COM21"  # Confirme a sua porta COM ativa
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

    print("[MATEMÁTICA] Calculando a FFT de cada linha da imagem...")
    for i in range(64):
        linha = img_resized[i, :]
        fft_linha = np.fft.fft(linha)
        
        dc_component = float(np.real(fft_linha[0]))
        amplitudes = np.abs(fft_linha[1:51]).astype(np.float32)
        fases = np.angle(fft_linha[1:51]).astype(np.float32)
        
        dados_sinal = struct.pack('<f50f50f', dc_component, *amplitudes, *fases)
        
        line_id_byte = bytes([i])
        frame_linha = sync_bytes + line_id_byte + dados_sinal
        buffer_total.extend(frame_linha)

    try:
        print(f"[USB] Abrindo conexão com o ESP32 Emissor na porta {PORTA_COM}...")
        ser = serial.Serial(PORTA_COM, BAUD_RATE, timeout=2)
        
        print("[BOOT] Aguardando 10 segundos para estabilização do hardware...")
        time.sleep(10) 
        
        print("\n==================================================")
        print("      INICIANDO TRANSMISSÃO ÓPTICA (9600 BAUD)    ")
        print("==================================================")
        start_time = time.time()
        
        tamanho_linha = 409  
        for i in range(64):
            inicio = i * tamanho_linha
            fim = inicio + tamanho_linha
            fatia_linha = buffer_total[inicio:fim]
            
            ser.write(fatia_linha)
            ser.flush() 
            
            # Cadência calibrada para 9600 baud
            time.sleep(0.45)
            
            if (i + 1) % 10 == 0 or i == 63:
                print(f" -> Progresso: Linha [{i + 1:02d}/64] transmititada (ID {i:02d}).")

        end_time = time.time()
        print("==================================================")
        print(f"[SUCESSO] Varredura Li-Fi concluída em {end_time - start_time:.2f} segundos!")
        ser.close()
        
    except Exception as e:
        print(f"\n[ERRO] Falha durante a transmissão serial: {e}")

if __name__ == "__main__":
    rodar_emissor_lifi()