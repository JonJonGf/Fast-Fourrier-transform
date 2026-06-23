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
BAUD_RATE = 9600     # CALIBRADO EM 9600 BAUD PARA IMUNIDADE A RUÍDO
BIN_PATH = "dados_fourier.bin"

def rodar_emissor_lifi():
    # Ajusta o caminho dinâmico para carregar a imagem na pasta correta
    diretorio_do_script = os.path.dirname(os.path.abspath(__file__))
    caminho_da_imagem = os.path.join(diretorio_do_script, "imagens", "vaspinho.png")

    print(f"[INFO] Carregando imagem de: {caminho_da_imagem}")
    img = cv2.imread(caminho_da_imagem, cv2.IMREAD_GRAYSCALE)

    if img is None:
        print(f"[ERRO CRÍTICO] Não encontrei a imagem em '{caminho_da_imagem}'")
        return

    # Força a imagem a ter exatamente os 64x64 pixels do projeto
    img_resized = cv2.resize(img, (64, 64))
    buffer_total = bytearray()
    sync_bytes = bytes([0xAA, 0xBB, 0xCC, 0xDD])

    print("[MATEMÁTICA] Calculando a FFT de cada linha da imagem...")
    for i in range(64):
        linha = img_resized[i, :]
        fft_linha = np.fft.fft(linha)
        
        # Componente DC (k=0) - Parte real pura (1 float)
        dc_component = float(np.real(fft_linha[0]))
        
        # Coleta as 50 frequências espaciais positivas (50 amplitudes + 50 fases)
        amplitudes = np.abs(fft_linha[1:51]).astype(np.float32)
        fases = np.angle(fft_linha[1:51]).astype(np.float32)
        
        # Empacota o payload em binário puro (1 + 50 + 50 = 101 floats = 404 bytes)
        dados_sinal = struct.pack('<f50f50f', dc_component, *amplitudes, *fases)
        
        # Frame final da linha (4 bytes de Sync + 404 bytes de dados = 408 bytes)
        frame_linha = sync_bytes + dados_sinal
        buffer_total.extend(frame_linha)

    # Salva uma cópia em arquivo binário local para auditoria se necessário
    caminho_bin = os.path.join(diretorio_do_script, BIN_PATH)
    with open(caminho_bin, "wb") as f:
        f.write(buffer_total)
    print(f"[OK] Arquivo binário gerado com sucesso: '{caminho_bin}' ({len(buffer_total)} bytes)")

    # Inicia o processo de transmissão via Laser
    try:
        print(f"[USB] Abrindo conexão com o ESP32 Emissor na porta {PORTA_COM}...")
        ser = serial.Serial(PORTA_COM, BAUD_RATE, timeout=2)
        time.sleep(2) # Aguarda 2 segundos pelo reset de boot automático da placa
        
        print("\n==================================================")
        print("      INICIANDO TRANSMISSÃO ÓPTICA (9600 BAUD)    ")
        print("==================================================")
        print("-> O laser vai modular os dados de forma cadenciada.")
        start_time = time.time()
        
        tamanho_linha = 408
        for i in range(64):
            inicio = i * tamanho_linha
            fim = inicio + tamanho_linha
            fatia_linha = buffer_total[inicio:fim]
            
            # Injeta a linha de 408 bytes na porta serial
            ser.write(fatia_linha)
            ser.flush() # Força o Windows a esvaziar o barramento USB imediatamente
            
            # ----------------------------------------------------------------
            # CORREÇÃO DO TIMING (PULO DO GATO):
            # A 9600 baud, 408 bytes demoram ~425 milissegundos para cruzar o ar.
            # O sleep de 0.45s (450ms) garante sincronia perfeita com o silício!
            # ----------------------------------------------------------------
            time.sleep(0.45)
            
            # Printa o progresso no terminal do transmissor a cada 10 linhas
            if (i + 1) % 10 == 0 or i == 63:
                print(f" -> Progresso: Linha [{i + 1:02d}/64] transmitida fisicamente pelo laser.")

        end_time = time.time()
        print("==================================================")
        print(f"[SUCESSO] Varredura Li-Fi concluída em {end_time - start_time:.2f} segundos!")
        ser.close()
        
    except Exception as e:
        print(f"\n[ERRO] Falha durante a transmissão serial: {e}")

if __name__ == "__main__":
    rodar_emissor_lifi()