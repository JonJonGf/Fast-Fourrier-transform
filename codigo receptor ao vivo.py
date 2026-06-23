import cv2
import numpy as np
import struct
import serial

# ==========================================
# CONFIGURAÇÕES DO PROJETO RECEPTOR (9600 BAUD)
# ==========================================
PORTA_COM = "COM4"  # Confirme a sua porta COM ativa
BAUD_RATE = 9600     

def rodar_receptor_lifi_live_blocos():
    try:
        # Timeout em 2.0s monitora com folga o fluxo de 9600 baud
        ser = serial.Serial(PORTA_COM, BAUD_RATE, timeout=2.0)
        print("==================================================")
        print("   UFF Li-Fi RECEPTOR - LIVE STREAMING OTIMIZADO  ")
        print("==================================================")
        print(f"[OK] Conectado na porta {PORTA_COM} a {BAUD_RATE} baud.")
        
        ser.reset_input_buffer()
        print("[INFO] Buffer pronto. Aguardando rajada de pacotes...\n")
    except Exception as e:
        print(f"[ERRO] Não foi possível abrir a porta {PORTA_COM}: {e}")
        return

    # Inicializa a matriz preta 64x64
    imagem_reconstruida = np.zeros((64, 64), dtype=np.uint8)
    lines_captured = set()
    
    # Criamos uma janela estável ANTES do loop começar
    cv2.namedWindow("UFF Li-Fi - Vaspinho em Blocos", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("UFF Li-Fi - Vaspinho em Blocos", 450, 450)
    cv2.imshow("UFF Li-Fi - Vaspinho em Blocos", imagem_reconstruida)
    cv2.waitKey(1)

    print("[STREAM] Monitorando link óptico. Atualizações gráficas a cada 10 linhas:")

    try:
        while len(lines_captured) < 64:
            b1 = ser.read(1)
            
            if not b1:
                if len(lines_captured) > 0:
                    print("\n\n[TIMEOUT] O laser terminou de enviar ou o sinal caiu.")
                    break
                continue

            if b1 == b'\xAA':
                b2 = ser.read(1)
                if b2 == b'\xBB':
                    b3 = ser.read(1)
                    if b3 == b'\xCC':
                        b4 = ser.read(1)
                        if b4 == b'\xDD':
                            
                            id_byte = ser.read(1)
                            if len(id_byte) < 1:
                                continue
                            line_id = id_byte[0]
                            
                            if line_id < 0 or line_id >= 64:
                                continue
                            
                            dados_linha = ser.read(404)
                            if len(dados_linha) < 404:
                                continue
                            
                            # Processamento matemático da IFFT
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
                            
                            if np.isnan(linha_pixels).any() or np.isinf(linha_pixels).any():
                                continue
                            
                            linha_pixels = np.clip(linha_pixels, 0, 255).astype(np.uint8)
                            imagem_reconstruida[line_id, :] = linha_pixels
                            tamanho_antes = len(lines_captured)
                            lines_captured.add(line_id)
                            tamanho_depois = len(lines_captured)
                            print(f" -> Coletando: [{tamanho_depois}/64] | Último ID válido: {line_id:02d}", end="\r")
                            if tamanho_depois > tamanho_antes and (tamanho_depois % 10 == 0):
                                print(f"\n[DISPLAY] Bloco de {tamanho_depois} linhas atingido. Atualizando tela...")
                                cv2.imshow("UFF Li-Fi - Vaspinho em Blocos", imagem_reconstruida)
                                cv2.waitKey(10) # Dá 10ms estáveis para a GUI do Windows desenhar

        # Força a última renderização das linhas finais (ex: de 60 a 64)
        print("\n\n==================================================")
        print("   [SUCESSO] Transmissão Finalizada com Segurança! ")
        print("==================================================")
        cv2.imshow("UFF Li-Fi - Vaspinho em Blocos", imagem_reconstruida)
        print("[INFO] Renderização final completa na tela.")
        print("[INFO] Clique na janela e pressione qualquer tecla para fechar.")
        cv2.waitKey(0)

    except KeyboardInterrupt:
        print("\n[INFO] Execução interrompida manualmente pelo usuário.")
    finally:
        ser.close()
        cv2.destroyAllWindows()
        print("[INFO] Porta serial fechada com segurança.")

if __name__ == "__main__":
    rodar_receptor_lifi_live_blocos()