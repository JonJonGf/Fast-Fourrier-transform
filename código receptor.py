import cv2
import numpy as np
import struct
import serial

# ==========================================
# CONFIGURAÇÕES DO PROJETO RECEPTOR
# ==========================================
PORTA_COM = "COM4"  # Mude para a porta COM do seu ESP32 RECEPTOR (ex: COM4, COM5)
BAUD_RATE = 115200

def rodar_receptor_lifi():
    try:
        # Abre a porta serial conectada ao ESP32 Receptor
        ser = serial.Serial(PORTA_COM, BAUD_RATE, timeout=1)
        print(f"Conectado ao ESP Receptor na porta {PORTA_COM}.")
        print("Aguardando alinhamento do laser e início dos dados...")
    except Exception as e:
        print(f"Erro ao abrir a porta serial {PORTA_COM}: {e}")
        return

    # Matriz preta de 64x64 que vai receber os pixels reconstruídos
    imagem_reconstruida = np.zeros((64, 64), dtype=np.uint8)
    
    # Padrão de sincronismo que define o início de cada linha
    SYNC_PATTERN = b'\xAA\xBB\xCC\xDD'
    
    # Configura a janela de exibição do OpenCV em tamanho expandido para melhor visualização
    cv2.namedWindow("UFF Li-Fi - Sintese Inversa de Fourier", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("UFF Li-Fi - Sintese Inversa de Fourier", 450, 450)

    linha_atual = 0

    try:
        while True:
            # Varre o fluxo de bytes procurando pelo primeiro byte de sincronismo (0xAA)
            if ser.read(1) == b'\xAA':
                # Se achou, checa em sequência os próximos bytes do cabeçalho
                if ser.read(1) == b'\xBB':
                    if ser.read(1) == b'\xCC':
                        if ser.read(1) == b'\xDD':
                            
                            # Cabeçalho validado! Lê os próximos 404 bytes de dados de sinais (101 floats)
                            dados_linha = ser.read(404)
                            if len(dados_linha) < 404:
                                continue # Ignora frames corrompidos/incompletos
                            
                            # Desempacota o payload binário de ponto flutuante (Little-Endian '<')
                            payload = struct.unpack('<f50f50f', dados_linha)
                            
                            dc_component = payload[0]
                            amplitudes = np.array(payload[1:51])
                            fases = np.array(payload[51:101])
                            
                            # --------------------------------------
                            # RECONSTRUÇÃO DO ESPECTRO DISCRETO (64 PONTOS)
                            # --------------------------------------
                            fft_reconstruida = np.zeros(64, dtype=complex)
                            
                            # Aloca a componente DC
                            fft_reconstruida[0] = dc_component
                            
                            # Aloca as 50 frequências espaciais enviadas pelo laser (Forma Polar: A * e^(j*fase))
                            fft_reconstruida[1:51] = amplitudes * np.exp(1j * fases)
                            
                            # Preenche as componentes espaciais restantes (frequências negativas conjugadas)
                            # utilizando a propriedade de simetria hermitiana de sinais reais
                            fft_reconstruida[51:64] = np.conj(fft_reconstruida[13:0:-1])
                            
                            # --------------------------------------
                            # SÍNTESE INVERSA (DOMÍNIO DO ESPAÇO)
                            # --------------------------------------
                            # Executa a IFFT para transformar o espectro de volta em uma linha de pixels
                            sinal_reconstruido = np.fft.ifft(fft_reconstruida)
                            
                            # Extrai a parte real, filtra ruídos numéricos e limita entre 0 e 255
                            linha_pixels = np.real(sinal_reconstruido)
                            linha_pixels = np.clip(linha_pixels, 0, 255).astype(np.uint8)
                            
                            # Insere a linha processada na matriz da imagem final
                            imagem_reconstruida[linha_atual, :] = linha_pixels
                            
                            # Atualiza a janela gráfica com a linha recém-chegada
                            cv2.imshow("UFF Li-Fi - Sintese Inversa de Fourier", imagem_reconstruida)
                            cv2.waitKey(1) # Atualiza o frame de vídeo do OpenCV
                            
                            print(f"Linha {linha_atual:02d} processada e renderizada.")
                            
                            # Incrementa e rotaciona o contador de linhas de 0 a 63
                            linha_atual = (linha_atual + 1) % 64

            # Se o usuário fechar a janela do OpenCV clicando no 'X', finaliza o programa
            if cv2.getWindowProperty("UFF Li-Fi - Sintese Inversa de Fourier", cv2.WND_PROP_VISIBLE) < 1:
                print("Janela gráfica fechada pelo usuário.")
                break

    except KeyboardInterrupt:
        print("\nInterrupção manual detectada.")
    finally:
        ser.close()
        cv2.destroyAllWindows()
        print("Porta serial fechada e ambiente limpo.")

if __name__ == "__main__":
    rodar_receptor_lifi()