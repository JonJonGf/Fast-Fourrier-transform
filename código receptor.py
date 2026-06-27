import cv2
import numpy as np
import struct
import serial
import time

# ==========================================
# CONFIGURAÇÕES DO PROJETO RECEPTOR (9600 BAUD)
# ==========================================
PORTA_COM = "COM21"  # Certifique-se de manter o Monitor Serial da IDE fechado!
BAUD_RATE = 9600     

def rodar_receptor_lifi_blindado():
    try:
        # Inicialização controlada para destravar o barramento serial no Windows
        ser = serial.Serial(
            port=PORTA_COM,
            baudrate=BAUD_RATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1,  
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )
        
        # Pulsa as linhas de controle de fluxo de hardware para acordar o chip UART
        ser.dtr = True
        ser.rts = True
        time.sleep(0.1)
        ser.dtr = False
        ser.rts = False
        time.sleep(0.2)
        
        print("==================================================")
        print("   UFF Li-Fi RECEPTOR - SÍNTESE INVERSA BLINDADA  ")
        print("==================================================")
        print(f"[OK] Conectado e DESTRAVADO na porta {PORTA_COM} a {BAUD_RATE} baud.")
        
        ser.reset_input_buffer()
        print("[INFO] Buffer zerado. Aguardando rajada de pacotes por laser...\n")
    except Exception as e:
        print(f"[ERRO CRÍTICO] Não foi possível abrir a porta {PORTA_COM}: {e}")
        return

    # Parâmetros matemáticos e estruturais fixos da imagem de 64x64
    IMAGEM_H = 64
    IMAGEM_W = 64
    COEFICIENTES = 50
    TAMANHO_FRAME = 409  # Cabeçalho(4B) + ID(1B) + Payload(404B)
    
    imagem_reconstruida = np.zeros((IMAGEM_H, IMAGEM_W), dtype=np.uint8)
    lines_captured = set()
    buffer_local = bytearray()
    
    ultimo_tempo_dados = time.time()

    try:
        while True:
            # 1. CAPTURA DOS BYTES DISPONÍVEIS NA UART
            if ser.in_waiting > 0:
                dados_vindos = ser.read(ser.in_waiting)
                buffer_local.extend(dados_vindos)
                ultimo_tempo_dados = time.time()
            
            # Print de telemetria contínua na mesma linha
            print(f" -> Bytes no buffer: {len(buffer_local)} b | Linhas salvas: {len(lines_captured)}/{IMAGEM_H} ", end="\r")
            
            # 2. CAÇADOR DINÂMICO DE CABEÇALHO (MÁQUINA DE ESTADOS DO BUFFER)
            while b'\xAA\xBB\xCC\xDD' in buffer_local:
                idx_inicio = buffer_local.find(b'\xAA\xBB\xCC\xDD')
                
                # Se achou o cabeçalho perto do final do buffer, precisa esperar o ID chegar
                if len(buffer_local) < (idx_inicio + 5): 
                    break
                
                # Extrai e valida o ID da linha diretamente no buffer antes de cortar o bloco
                line_id = buffer_local[idx_inicio + 4]
                
                # Se o ID for inválido devido a ruído elétrico mascarando o bit,
                # avança 1 byte para tirar o cabeçalho antigo do caminho e tentar o próximo
                if line_id < 0 or line_id >= IMAGEM_H:
                    buffer_local = buffer_local[idx_inicio + 1:]
                    continue
                
                # Se o restante do frame de 409 bytes ainda não chegou completo, interrompe o processamento e aguarda
                if len(buffer_local) < (idx_inicio + TAMANHO_FRAME):
                    break
                
                # Isola o frame legítimo de 409 bytes
                frame_completo = buffer_local[idx_inicio : idx_inicio + TAMANHO_FRAME]
                
                # Remove o frame processado do buffer de memória local
                buffer_local = buffer_local[idx_inicio + TAMANHO_FRAME :]
                
                # Isola a porção dos coeficientes floats (índice 5 em diante)
                dados_linha = frame_completo[5:]
                
                # 3. PROCESSAMENTO MATEMÁTICO DA SÍNTESE INVERSA (IFFT)
                try:
                    payload = struct.unpack('<f50f50f', dados_linha)
                    dc_component = payload[0]
                    amplitudes = np.array(payload[1:COEFICIENTES+1])
                    fases = np.array(payload[COEFICIENTES+1 : 2*COEFICIENTES+1])
                    
                    # Reconstrói a grade de frequências da FFT
                    fft_reconstruida = np.zeros(IMAGEM_W, dtype=complex)
                    fft_reconstruida[0] = dc_component
                    fft_reconstruida[1:COEFICIENTES+1] = amplitudes * np.exp(1j * fases)
                    
                    # Espelhamento simétrico complexo conjugado para reconstruir sinal puramente real
                    fft_reconstruida[14:64] = np.conj(fft_reconstruida[50:0:-1])
                    
                    # Executa a Transformada Inversa de Fourier
                    sinal_reconstruido = np.fft.ifft(fft_reconstruida)
                    linha_pixels = np.real(sinal_reconstruido)
                    
                    # Filtro contra estouros matemáticos (NaN/Inf) provocados por deslocamento de bit
                    if np.isnan(linha_pixels).any() or np.isinf(linha_pixels).any():
                        continue
                    
                    # Trunca os níveis de cinza entre 0 e 255 e aloca na matriz de imagem
                    linha_pixels = np.clip(linha_pixels, 0, 255).astype(np.uint8)
                    imagem_reconstruida[line_id, :] = linha_pixels
                    
                    if line_id not in lines_captured:
                        lines_captured.add(line_id)
                        print(f"\n[OK] Linha {line_id:02d} Decodificada com Sucesso! Total: {len(lines_captured)}/{IMAGEM_H}")
                        
                except Exception:
                    # Se o desempacotamento de floats falhar por dados truncados, o loop continua caçando
                    continue
            
            # 4. CRITÉRIOS DE RENDERIZAÇÃO E SAÍDA
            # Se coletou todas as 64 linhas perfeitamente, encerra o loop de escuta
            if len(lines_captured) == IMAGEM_H:
                print(f"\n\n[SUCESSO] Todas as {IMAGEM_H} linhas foram recebidas com sucesso perfeito!")
                break
                
            # Se o laser silenciar por mais de 2.0 segundos após o início dos pacotes, força a renderização parcial
            if len(lines_captured) > 0 and (time.time() - ultimo_tempo_dados > 2.0):
                print(f"\n\n[TIMEOUT] Rajada de laser cessou. Forçando exibição com {len(lines_captured)}/{IMAGEM_H} linhas.")
                break
                
            time.sleep(0.001)  # Respira 1ms para não estressar a CPU do PC

        # ==================================================
        # EXIBIÇÃO DA JANELA GRÁFICA DO OPENCV
        # ==================================================
        print("==================================================")
        print("       Mostrando a Janela do Vaspinho Reconstruído")
        print("==================================================")

        cv2.namedWindow("UFF Li-Fi - Vaspinho Indexado", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("UFF Li-Fi - Vaspinho Indexado", 450, 450)
        cv2.imshow("UFF Li-Fi - Vaspinho Indexado", imagem_reconstruida)
        
        print("[INFO] Janela aberta! Clique nela e aperte QUALQUER tecla para encerrar.")
        cv2.waitKey(0)

    except KeyboardInterrupt:
        print("\n[INFO] Interrupção manual do usuário detectada pelo teclado.")
    finally:
        ser.close()
        cv2.destroyAllWindows()
        print("[INFO] Recursos de hardware e janelas liberados.")

if __name__ == "__main__":
    rodar_receptor_lifi_blindado()