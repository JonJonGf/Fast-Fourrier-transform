import cv2
import numpy as np
import struct
import serial

# ==========================================
# CONFIGURAÇÕES DO PROJETO RECEPTOR (19200 BAUD)
# ==========================================
PORTA_COM = "COM4"  # Confirme a sua porta COM ativa
BAUD_RATE = 19200     

def rodar_receptor_lifi_bloco_id():
    try:
        # Timeout em 2.0 segundos monitora o fim da rajada do laser
        ser = serial.Serial(PORTA_COM, BAUD_RATE, timeout=2.0)
        print("==================================================")
        print("   UFF Li-Fi RECEPTOR - SÍNTESE INVERSA EM BLOCO ")
        print("==================================================")
        print(f"[OK] Conectado na porta {PORTA_COM} a {BAUD_RATE} baud.")
        
        # Garante buffer zerado após o tempo de alinhamento
        ser.reset_input_buffer()
        print("[INFO] Buffer zerado. Aguardando rajada de pacotes...\n")
    except Exception as e:
        print(f"[ERRO] Não foi possível abrir a porta {PORTA_COM}: {e}")
        return

    # Cria a matriz preta 64x64. Linhas não recebidas permanecerão pretas
    imagem_reconstruida = np.zeros((64, 64), dtype=np.uint8)
    lines_captured = set()

    try:
        # Coleta silenciosa até juntar as 64 linhas únicas na memória
        while len(lines_captured) < 64:
            b1 = ser.read(1)
            
            # Se der timeout (laser terminou de enviar ou o feixe caiu)
            if not b1:
                if len(lines_captured) > 0:
                    print("\n[TIMEOUT] Transmissão óptica interrompida ou encerrada.")
                    print(f"[INFO] Rendimento final do link: {len(lines_captured)}/64 linhas salvas.")
                    break
                continue

            # Caçador de cabeçalho mágico de sincronismo
            if b1 == b'\xAA':
                b2 = ser.read(1)
                if b2 == b'\xBB':
                    b3 = ser.read(1)
                    if b3 == b'\xCC':
                        b4 = ser.read(1)
                        if b4 == b'\xDD':
                            
                            # 1. Extrai o ID da linha direto do protocolo óptico
                            id_byte = ser.read(1)
                            if len(id_byte) < 1:
                                continue
                            line_id = id_byte[0]
                            
                            # Filtro contra estouro de índice por ruído
                            if line_id < 0 or line_id >= 64:
                                continue
                            
                            # 2. Coleta os 404 bytes matemáticos da linha
                            dados_linha = ser.read(404)
                            
                            # Validação do tamanho do payload
                            if len(dados_linha) < 404:
                                print(f" -> [DROP] ID {line_id} incompleto na USB. Descartando.")
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
                            
                            # Filtro protetor contra desalinhamento de bytes (efeito NaNs)
                            if np.isnan(linha_pixels).any() or np.isinf(linha_pixels).any():
                                continue
                            
                            linha_pixels = np.clip(linha_pixels, 0, 255).astype(np.uint8)
                            
                            # 4. Grava na posição exata do ID
                            imagem_reconstruida[line_id, :] = pointer = linha_pixels
                            lines_captured.add(line_id)
                            
                            # Atualização leve de texto em linha única (sem pesar o processador)
                            print(f" -> Coletando: [{len(lines_captured)}/64] | Último ID válido: {line_id:02d}", end="\r")

        # ==================================================
        # RENDERIZAÇÃO EM BLOCO DA IMAGEM COMPLETA
        # ==================================================
        print("\n\n==================================================")
        print("   [PROCESSO CONCLUÍDO] Abrindo Janela do Vaspinho")
        print("==================================================")

        cv2.namedWindow("UFF Li-Fi - Vaspinho Indexado", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("UFF Li-Fi - Vaspinho Indexado", 450, 450)
        cv2.imshow("UFF Li-Fi - Vaspinho Indexado", imagem_reconstruida)
        
        print("[INFO] Janela aberta com sucesso! Foque nela e aperte qualquer tecla para fechar.")
        cv2.waitKey(0)

    except KeyboardInterrupt:
        print("\n[INFO] Interrupção manual detectada.")
    finally:
        ser.close()
        cv2.destroyAllWindows()
        print("[INFO] Porta serial e janelas fechadas.")

if __name__ == "__main__":
    rodar_receptor_lifi_bloco_id()