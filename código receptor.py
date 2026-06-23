import cv2
import numpy as np
import struct
import serial

# ==========================================
# CONFIGURAÇÕES DO PROJETO RECEPTOR (9600 BAUD)
# ==========================================
PORTA_COM = "COM21"  
BAUD_RATE = 9600     

def rodar_receptor_lifi_streaming():
    try:
        ser = serial.Serial(PORTA_COM, BAUD_RATE, timeout=2.0)
        print("==================================================")
        print("   UFF Li-Fi RECEPTOR - VIDEO STREAMING EM TEMPO REAL")
        print("==================================================")
        print(f"[OK] Conectado na porta {PORTA_COM} a {BAUD_RATE} baud.")
        
        # Limpa o lixo eletrônico gerado durante os 5 segundos de mira fixa
        ser.reset_input_buffer()
        print("[INFO] Buffer limpo. Pronto para desenhar na tela...\n")
    except Exception as e:
        print(f"[ERRO] Não foi possível abrir a porta {PORTA_COM}: {e}")
        return

    # Inicializa a matriz preta 64x64. Linhas perdidas ficarão pretas (em branco)
    imagem_reconstruida = np.zeros((64, 64), dtype=np.uint8)
    
    # Configura a janela do OpenCV em modo contínuo
    cv2.namedWindow("UFF Li-Fi - Streaming de Fourier", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("UFF Li-Fi - Streaming de Fourier", 450, 450)
    cv2.imshow("UFF Li-Fi - Streaming de Fourier", imagem_reconstruida)
    cv2.waitKey(1)

    print("[STREAM] Monitorando feixe óptico. Atividade abaixo:")

    try:
        while True:
            # Busca o byte inicial do cabeçalho
            b1 = ser.read(1)
            if not b1:
                continue

            if b1 == b'\xAA':
                b2 = ser.read(1)
                if b2 == b'\xBB':
                    b3 = ser.read(1)
                    if b3 == b'\xCC':
                        b4 = ser.read(1)
                        if b4 == b'\xDD':
                            
                            # 1. NOVIDADE: Captura o byte do ID da linha enviado pelo laser
                            id_byte = ser.read(1)
                            if len(id_byte) < 1:
                                continue
                            line_id = id_byte[0]
                            
                            # Filtro de sanidade para ignorar IDs fora do escopo 0-63
                            if line_id < 0 or line_id >= 64:
                                continue
                            
                            # 2. Captura os 404 bytes matemáticos da FFT
                            dados_linha = ser.read(404)
                            if len(dados_linha) < 404:
                                print(f"  └─► [DROP] Timeout na leitura da linha {line_id}. Linha perdida.")
                                continue
                            
                            # Desempacota e reconstrói via IFFT
                            payload = struct.unpack('<f50f50f', dados_linha)
                            dc_component = payload[0]
                            amplitudes = np.array(payload[1:51])
                            fases = np.array(payload[51:101])
                            
                            fft_reconstruida = np.zeros(64, dtype=complex)
                            fft_reconstruida[0] = dc_component
                            fft_reconstruida[1:51] = amplitudes * np.exp(1j * fases)
                            fft_reconstruida[51:64] = np.conj(fft_reconstruida[13:0:-1])
                            
                            sinal_reconstruido = np.fft.ifft(fft_reconstruida)
                            linha_pixels = np.real(sinal_reconstruido)
                            linha_pixels = np.clip(linha_pixels, 0, 255).astype(np.uint8)
                            
                            # 3. Alocação direta no índice lido do laser (Garante alinhamento perfeito!)
                            imagem_reconstruida[line_id, :] = linha_pixels
                            print(f" -> Atualizado: Linha ID [{line_id:02d}/63]")
                            
                            # 4. MODIFICAÇÃO: Atualiza a tela imediatamente linha por linha
                            cv2.imshow("UFF Li-Fi - Streaming de Fourier", imagem_reconstruida)
                            cv2.waitKey(1) # Refresh gráfico de 1ms do OpenCV

            # Se fechar a tela no 'X', encerra o script Python
            if cv2.getWindowProperty("UFF Li-Fi - Streaming de Fourier", cv2.WND_PROP_VISIBLE) < 1:
                print("\n[INFO] Janela fechada pelo usuário.")
                break

    except KeyboardInterrupt:
        print("\n[INFO] Interrupção manual detectada.")
    finally:
        ser.close()
        cv2.destroyAllWindows()
        print("[INFO] Conexão encerrada e recursos liberados.")

if __name__ == "__main__":
    rodar_receptor_lifi_streaming()