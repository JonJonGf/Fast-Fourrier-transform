import cv2
import numpy as np
import struct
import serial

# ==========================================
# CONFIGURAÇÕES DO PROJETO RECEPTOR (9600 BAUD)
# ==========================================
PORTA_COM = "COM4"  # Certifique-se de usar a sua porta COM correta
BAUD_RATE = 9600     

def rodar_receptor_lifi_live():
    try:
        # Timeout longo para monitorar o fluxo cadenciado
        ser = serial.Serial(PORTA_COM, BAUD_RATE, timeout=3.0)
        print("==================================================")
        print("   UFF Li-Fi - STREAMING DE FOURIER AO VIVO       ")
        print("==================================================")
        print(f"[OK] Conectado na porta {PORTA_COM} a {BAUD_RATE} baud.")
        
        # Limpa o lixo elétrico gerado durante o alinhamento
        ser.reset_input_buffer()
        print("[INFO] Pronto para o show. Dispare o Transmissor!")
    except Exception as e:
        print(f"[ERRO] Não foi possível abrir a porta {PORTA_COM}: {e}")
        return

    # Inicializa a matriz preta 64x64
    imagem_reconstruida = np.zeros((64, 64), dtype=np.uint8)
    lines_captured = set()

    # Configura e abre a janela do OpenCV ANTES de começar a receber
    cv2.namedWindow("UFF Li-Fi - Vaspinho ao Vivo", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("UFF Li-Fi - Vaspinho ao Vivo", 450, 450)
    
    # Plota a tela preta inicial
    cv2.imshow("UFF Li-Fi - Vaspinho ao Vivo", imagem_reconstruida)
    cv2.waitKey(1)

    try:
        while len(lines_captured) < 64:
            b1 = ser.read(1)
            
            # Se der timeout geral (rajada acabou)
            if not b1:
                if len(lines_captured) > 0:
                    print("\n\n[INFO] Fim da rajada do laser detectada.")
                    break
                continue

            # Caçador de cabeçalho
            if b1 == b'\xAA':
                b2 = ser.read(1)
                if b2 == b'\xBB':
                    b3 = ser.read(1)
                    if b3 == b'\xCC':
                        b4 = ser.read(1)
                        if b4 == b'\xDD':
                            
                            # 1. Captura o ID da linha
                            id_byte = ser.read(1)
                            if len(id_byte) < 1:
                                continue
                            line_id = id_byte[0]
                            
                            if line_id < 0 or line_id >= 64:
                                continue
                            
                            # 2. Captura os 404 bytes matemáticos
                            dados_linha = ser.read(404)
                            if len(dados_linha) < 404:
                                continue
                            
                            # 3. Processamento matemático da IFFT
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
                            
                            # 4. Injeta a linha na matriz
                            imagem_reconstruida[line_id, :] = linha_pixels
                            lines_captured.add(line_id)
                            
                            # 5. ATUALIZAÇÃO EM TEMPO REAL EXTRA LEVE
                            # Exibe a matriz atualizada na janela ja aberta
                            cv2.imshow("UFF Li-Fi - Vaspinho ao Vivo", imagem_reconstruida)
                            
                            # O waitKey(10) dá 10 milissegundos para o Windows processar os pixels na tela
                            # Isso impede o congelamento da interface gráfica!
                            cv2.waitKey(10)
                            
                            # Log no terminal para acompanhamento
                            print(f" -> Atualizando ao vivo: [{len(lines_captured)}/64] | Linha ID: {line_id:02d}", end="\r")

        print("\n\n==================================================")
        print("   [FINALIZADO] Streaming concluído com sucesso!  ")
        print("==================================================")
        print("[INFO] Imagem congelada na tela. Pressione qualquer tecla na janela para fechar.")
        cv2.waitKey(0)

    except KeyboardInterrupt:
        print("\n[INFO] Streaming interrompido manualmente.")
    finally:
        ser.close()
        cv2.destroyAllWindows()
        print("[INFO] Recursos liberados.")

if __name__ == "__main__":
    rodar_receptor_lifi_live()