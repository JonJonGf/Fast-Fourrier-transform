import cv2
import numpy as np
import struct
import time
import serial
import os

# ==========================================
# CONFIGURAÇÕES DA BANCADA TRANSMISSORA
# ==========================================
PORTA_COM = "COM21"  # Mude para a porta COM do seu ESP32 EMISSOR
BAUD_RATE = 9600     # CALIBRADO PARA 9600 BAUD
BIN_PATH = "dados_fourier.bin"

def rodar_emissor_lifi():
    # Proteção de caminho de pasta do VS Code
    diretorio_do_script = os.path.dirname(os.path.abspath(__file__))
    caminho_da_imagem = os.path.join(diretorio_do_script, "imagens", "vaspinho.png")

    print(f"[INFO] Carregando imagem de: {caminho_da_imagem}")
    img = cv2.imread(caminho_da_imagem, cv2.IMREAD_GRAYSCALE)

    if img is None:
        print(f"Erro Crítico: Não encontrei a imagem em '{caminho_da_imagem}'")
        return

    # Força os 64x64 pixels do projeto
    img_resized = cv2.resize(img, (64, 64))
    buffer_total = bytearray()
    sync_bytes = bytes([0xAA, 0xBB, 0xCC, 0xDD])

    print("Processando linhas da imagem via FFT...")
    for i in range(64):
        linha = img_resized[i, :]
        fft_linha = np.fft.fft(linha)
        
        # Componente DC (k=0) - Parte real pura
        dc_component = float(np.real(fft_linha[0]))
        
        # Coleta as 50 frequências positivas
        amplitudes = np.abs(fft_linha[1:51]).astype(np.float32)
        fases = np.angle(fft_linha[1:51]).astype(np.float32)
        
        # Empacota em binário (404 bytes)
        dados_sinal = struct.pack('<f50f50f', dc_component, *amplitudes, *fases)
        
        # Frame completo da linha (408 bytes)
        frame_linha = sync_bytes + dados_sinal
        buffer_total.extend(frame_linha)

    # Salva o arquivo binário local
    caminho_bin = os.path.join(diretorio_do_script, BIN_PATH)
    with open(caminho_bin, "wb") as f:
        f.write(buffer_total)
    print(f"[OK] Arquivo binário gerado: '{caminho_bin}' ({len(buffer_total)} bytes)")

    # Inicia a transmissão serial
    try:
        print(f"[USB] Abrindo conexão com o ESP32 na porta {PORTA_COM}...")
        ser = serial.Serial(PORTA_COM, BAUD_RATE, timeout=2)
        time.sleep(2) # Aguarda o reset de boot da placa
        
        print("\n==================================================")
        print("      INICIANDO TRANSMISSÃO ÓPTICA (9600 BAUD)    ")
        print("==================================================")
        start_time = time.time()
        
        tamanho_linha = 408
        for i in range(64):
            inicio = i * tamanho_linha
            fim = inicio + tamanho_linha
            fatia_linha = buffer_total[inicio:fim]
            
            # Gospe a linha no laser
            ser.write(fatia_linha)
            ser.flush() # Força o barramento do Windows a esvaziar
            
            # Cadência de segurança para o buffer lento respirar
            time.sleep(0.04)
            
            if (i + 1) % 10 == 0 or i == 63:
                print(f" -> Progresso: Linha [{i + 1}/64] transmitida pelo laser.")

        end_time = time.time()
        print("==================================================")
        print(f"[SUCESSO] Varredura completa em {end_time - start_time:.2f} segundos!")
        ser.close()
        
    except Exception as e:
        print(f"\nErro na transmissão: {e}")

if __name__ == "__main__":
    rodar_emissor_lifi()