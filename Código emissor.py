import cv2
import numpy as np
import struct
import time
import serial
import os

# ==========================================
# CONFIGURAÇÕES DO PROJETO
# ==========================================
PORTA_COM = "COM21"              # Mude para a porta COM do seu ESP32 Emissor
BAUD_RATE = 115200
BIN_PATH = "dados_fourier.bin"

def gerar_e_enviar_fourier():
    # Garante o caminho correto da imagem independente de onde o terminal abrir
    diretorio_do_script = os.path.dirname(os.path.abspath(__file__))
    caminho_da_imagem = os.path.join(diretorio_do_script, "imagens", "vaspinho.png")
    
    # --------------------------------------
    # 1. PROCESSAMENTO DA IMAGEM
    # --------------------------------------
    img = cv2.imread(caminho_da_imagem, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Erro: Não foi possível encontrar a imagem em '{caminho_da_imagem}'")
        return
    
    img_resized = cv2.resize(img, (64, 64))
    buffer_total = bytearray()
    sync_bytes = bytes([0xAA, 0xBB, 0xCC, 0xDD]) # Cabeçalho de sincronismo
    
    print("Processando linhas da imagem via FFT...")
    for i in range(64):
        linha = img_resized[i, :]
        fft_linha = np.fft.fft(linha)
        
        # Componente DC (k=0)
        dc_component = float(np.real(fft_linha[0]))
        
        # Extrai as primeiras 50 componentes de frequência espacial
        amplitudes = np.abs(fft_linha[1:51]).astype(np.float32)
        fases = np.angle(fft_linha[1:51]).astype(np.float32)
        
        # Empacota em binário (404 bytes)
        dados_sinal = struct.pack('<f50f50f', dc_component, *amplitudes, *fases)
        
        # Monta o frame da linha (408 bytes)
        frame_linha = sync_bytes + dados_sinal
        buffer_total.extend(frame_linha)

    # --------------------------------------
    # 2. SALVAMENTO DO ARQUIVO BINÁRIO (.BIN)
    # --------------------------------------
    caminho_bin = os.path.join(diretorio_do_script, BIN_PATH)
    with open(caminho_bin, "wb") as f:
        f.write(buffer_total)
    print(f"Arquivo binário salvo com sucesso: '{caminho_bin}' ({len(buffer_total)} bytes)")

    # --------------------------------------
    # 3. TRANSMISSÃO SERIAL CADENCIADA (UPGRADE)
    # --------------------------------------
    try:
        print(f"Abrindo conexão com o ESP32 na porta {PORTA_COM}...")
        ser = serial.Serial(PORTA_COM, BAUD_RATE, timeout=2)
        time.sleep(2) # Aguarda o reset do bootloader estabilizar
        
        print("Transmitindo payload óptico de forma cadenciada...")
        start_time = time.time()
        
        tamanho_linha = 408 # 4 bytes de sync + 404 de dados
        
        # Loop inteligente: envia uma linha por vez
        for i in range(64):
            inicio = i * tamanho_linha
            fim = inicio + tamanho_linha
            fatia_linha = buffer_total[inicio:fim]
            
            # Envia apenas os 408 bytes daquela linha específica
            ser.write(fatia_linha)
            ser.flush() 
            
            # Dá tempo para o circuito do laser e os buffers do ESP32 respirarem
            time.sleep(0.04) 
            
            if (i + 1) % 10 == 0 or i == 63:
                print(f" -> Progresso: Linha [{i + 1}/64] enviada.")
        
        end_time = time.time()
        print(f"\n[SUCESSO] Transmissão concluída em {end_time - start_time:.2f} segundos!")
        ser.close()
        
    except serial.SerialException as e:
        print(f"\nErro de hardware na Serial: {e}")
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")

if __name__ == "__main__":
    gerar_e_enviar_fourier()