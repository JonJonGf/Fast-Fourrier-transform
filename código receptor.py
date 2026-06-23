import cv2
import numpy as np
import struct
import serial

# ==========================================
# CONFIGURAÇÕES DO PROJETO RECEPTOR
# ==========================================
PORTA_COM = "COM21"  # Mude para a porta COM do seu ESP32 RECEPTOR
BAUD_RATE = 9600     # CALIBRADO PARA 9600 BAUD

def rodar_receptor_lifi_silencioso():
    try:
        # TIMEOUT EM 2.0 SEGUNDOS: Essencial para a velocidade de 9600 baud
        ser = serial.Serial(PORTA_COM, BAUD_RATE, timeout=2.0)
        print(f"Conectado ao ESP Receptor na porta {PORTA_COM} a 9600 baud.")
        print("Aguardando pacotes... O terminal só responderá ao sinal do laser.\n")
    except Exception as e:
        print(f"Erro ao abrir a porta serial {PORTA_COM}: {e}")
        return

    # Buffer de imagem na RAM
    imagem_reconstruida = np.zeros((64, 64), dtype=np.uint8)
    linha_atual = 0

    try:
        while linha_atual < 64:
            # Escuta o primeiro byte
            b1 = ser.read(1)
            if not b1:
                continue # Fica em standby silencioso

            # Se detectar o início do cabeçalho mágico
            if b1 == b'\xAA':
                # Só acusa atividade no terminal quando o sincronismo começar
                print(f"[SINAL] Captado início da linha [{linha_atual + 1}/64]. Sincronizando...", end="")
                
                b2 = ser.read(1)
                if b2 == b'\xBB':
                    b3 = ser.read(1)
                    if b3 == b'\xCC':
                        b4 = ser.read(1)
                        if b4 == b'\xDD':
                            print(" [OK]")
                            
                            # Força a leitura dos 404 bytes lentos da FFT
                            dados_linha = ser.read(404)
                            if len(dados_linha) < 404:
                                print(f"  └─► [ERRO] Timeout! Vieram apenas {len(dados_linha)} bytes. Linha descartada.")
                                continue
                            
                            # Desempacota o payload binário
                            payload = struct.unpack('<f50f50f', dados_linha)
                            dc_component = payload[0]
                            amplitudes = np.array(payload[1:51])
                            fases = np.array(payload[51:101])
                            
                            # Reconstrução com simetria hermitiana
                            fft_reconstruida = np.zeros(64, dtype=complex)
                            fft_reconstruida[0] = dc_component
                            fft_reconstruida[1:51] = amplitudes * np.exp(1j * fases)
                            fft_reconstruida[51:64] = np.conj(fft_reconstruida[13:0:-1])
                            
                            # Processa a IFFT para voltar ao domínio do espaço (pixels)
                            sinal_reconstruido = np.fft.ifft(fft_reconstruida)
                            linha_pixels = np.real(sinal_reconstruido)
                            linha_pixels = np.clip(linha_pixels, 0, 255).astype(np.uint8)
                            
                            # Guarda temporariamente na matriz da imagem
                            imagem_reconstruida[linha_atual, :] = linha_pixels
                            linha_atual += 1
                        else:
                            print(f" [FALHOU] Byte 4 incorreto: {b4.hex()}")
                    else:
                        print(f" [FALHOU] Byte 3 incorreto: {b3.hex()}")
                else:
                    print(f" [FALHOU] Byte 2 incorreto: {b2.hex()}")

        # ==================================================
        # EXIBIÇÃO EM BLOCO DA IMAGEM FINAL
        # ==================================================
        print("\n==================================================")
        print("   [FINALIZADO] Todas as 64 linhas na memória!    ")
        print("==================================================")
        print("Abrindo janela gráfica do Vaspinho...")
        
        cv2.namedWindow("UFF Li-Fi - Imagem Final Reconstruida", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("UFF Li-Fi - Imagem Final Reconstruida", 450, 450)
        cv2.imshow("UFF Li-Fi - Imagem Final Reconstruida", imagem_reconstruida)
        
        print("[DICA] Clique na janela da imagem e aperte qualquer tecla para encerrar.")
        cv2.waitKey(0) # Congela a imagem na tela até uma tecla ser pressionada

    except KeyboardInterrupt:
        print("\nInterrupção manual.")
    finally:
        ser.close()
        cv2.destroyAllWindows()
        print("Porta serial fechada com segurança.")

if __name__ == "__main__":
    rodar_receptor_lifi_silencioso()