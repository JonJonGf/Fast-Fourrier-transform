import cv2
import numpy as np
import struct
import serial

# ==========================================
# CONFIGURAÇÕES DO PROJETO RECEPTOR (9600 BAUD)
# ==========================================
PORTA_COM = "COM21"  # Confirme a porta COM do seu ESP32 Receptor
BAUD_RATE = 9600     # Casado perfeitamente com os ESPs

def rodar_receptor_lifi():
    try:
        # TIMEOUT EM 2.0 SEGUNDOS: Essencial para a velocidade de 9600 baud.
        # Uma linha de 408 bytes demora cerca de 425 milissegundos para cruzar o laser!
        ser = serial.Serial(PORTA_COM, BAUD_RATE, timeout=2.0)
        print("==================================================")
        print("   UFF Li-Fi RECEPTOR - SÍNTESE INVERSA DE FOURIER")
        print("==================================================")
        print(f"[OK] Conectado na porta {PORTA_COM} a {BAUD_RATE} baud.")
        print("[INFO] Aguardando os pulsos do laser para iniciar a captura...\n")
    except Exception as e:
        print(f"[ERRO] Não foi possível abrir a porta {PORTA_COM}: {e}")
        return

    # Matriz na memória RAM que vai acumular as 64 linhas da imagem (64x64 pixels)
    imagem_reconstruida = np.zeros((64, 64), dtype=np.uint8)
    linha_atual = 0

    try:
        while linha_atual < 64:
            # Lê o primeiro byte do fluxo buscando o início do cabeçalho
            b1 = ser.read(1)
            if not b1:
                continue  # Standby silencioso caso o laser pare de transmitir temporariamente

            # Se encontrar o primeiro marcador de sincronismo
            if b1 == b'\xAA':
                # Confere os próximos 3 bytes em sequência rápida
                b2 = ser.read(1)
                if b2 == b'\xBB':
                    b3 = ser.read(1)
                    if b3 == b'\xCC':
                        b4 = ser.read(1)
                        if b4 == b'\xDD':
                            
                            # Cabeçalho 100% validado! Lê os próximos 404 bytes de payload (101 floats)
                            dados_linha = ser.read(404)
                            
                            if len(dados_linha) < 404:
                                print(f" └─► [AVISO] Linha {linha_atual + 1} cortada por timeout. Descartando pacote.")
                                continue
                            
                            # Desempacota os dados binários float (Little-Endian '<')
                            payload = struct.unpack('<f50f50f', dados_linha)
                            
                            dc_component = payload[0]
                            amplitudes = np.array(payload[1:51])
                            fases = np.array(payload[51:101])
                            
                            # --------------------------------------
                            # RECONSTRUÇÃO DO ESPECTRO DISCRETO (64 PONTOS)
                            # --------------------------------------
                            fft_reconstruida = np.zeros(64, dtype=complex)
                            
                            # Aloca a componente DC no índice 0
                            fft_reconstruida[0] = dc_component
                            
                            # Aloca as 50 frequências espaciais (Forma Polar: A * e^(1j * fase))
                            fft_reconstruida[1:51] = amplitudes * np.exp(1j * fases)
                            
                            # Aplica a Simetria Hermitiana para preencher as frequências negativas conjugadas
                            fft_reconstruida[51:64] = np.conj(fft_reconstruida[13:0:-1])
                            
                            # --------------------------------------
                            # SÍNTESE INVERSA (DOMÍNIO DO ESPAÇO)
                            # --------------------------------------
                            # Executa a IFFT para transformar o espectro de volta em linha de pixels
                            sinal_reconstruido = np.fft.ifft(fft_reconstruida)
                            
                            # Extrai a parte real, filtra ruídos e limita matematicamente entre 0 e 255
                            linha_pixels = np.real(sinal_reconstruido)
                            linha_pixels = np.clip(linha_pixels, 0, 255).astype(np.uint8)
                            
                            # Grava a linha decodificada na matriz da imagem final
                            imagem_reconstruida[linha_atual, :] = linha_pixels
                            
                            # Feedback visual no terminal para você acompanhar a recepção
                            print(f"[CONTAGEM] -> Linha [{linha_atual + 1:02d}/64] processada e guardada.")
                            
                            # Avança o ponteiro da linha
                            linha_atual += 1

        # ==================================================
        # EXIBIÇÃO EM BLOCO DA IMAGEM COMPLETA
        # ==================================================
        print("\n==================================================")
        print("   [SUCESSO] Todas as 64 linhas foram coletadas!  ")
        print("==================================================")
        print("Renderizando o frame completo do Vaspinho...")
        
        # Configura a janela gráfica expandida do OpenCV
        cv2.namedWindow("UFF Li-Fi - Vaspinho Reconstruido", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("UFF Li-Fi - Vaspinho Reconstruido", 450, 450)
        cv2.imshow("UFF Li-Fi - Vaspinho Reconstruido", imagem_reconstruida)
        
        print("\n[INFO] Janela aberta! Clique nela e pressione QUALQUER TECLA para encerrar.")
        cv2.waitKey(0) # Congela a imagem na tela até um comando do teclado

    except KeyboardInterrupt:
        print("\n[INFO] Execução interrompida manualmente pelo usuário.")
    finally:
        ser.close()
        cv2.destroyAllWindows()
        print("[INFO] Porta serial fechada com segurança.")

if __name__ == "__main__":
    rodar_receptor_lifi()