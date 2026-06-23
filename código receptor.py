import cv2
import numpy as np
import struct
import serial

PORTA_COM = "COM4"  # Confirme a sua porta COM ativa
BAUD_RATE = 9600     

def rodar_receptor_lifi_bloco_id():
    try:
        ser = serial.Serial(PORTA_COM, BAUD_RATE, timeout=2.0)
        print("==================================================")
        print("   UFF Li-Fi RECEPTOR - SÍNTESE INVERSA EM BLOCO ")
        print("==================================================")
        print(f"[OK] Conectado na porta {PORTA_COM} a {BAUD_RATE} baud.")
        
        ser.reset_input_buffer()
        print("[INFO] Buffer zerado. Aguardando rajada de pacotes...\n")
    except Exception as e:
        print(f"[ERRO] Não foi possível abrir a porta {PORTA_COM}: {e}")
        return

    imagem_reconstruida = np.zeros((64, 64), dtype=np.uint8)
    lines_captured = set()
    total_tentativas = 0  

    try:
        while len(lines_captured) < 64:
            b1 = ser.read(1)
            
            if not b1:
                if len(lines_captured) > 0:
                    print("\n[TIMEOUT] Transmissão óptica interrompida ou encerrada.")
                    break
                continue

            if b1 == b'\xAA':
                total_tentativas += 1
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
                                print(f" -> [DROP] ID {line_id} incompleto na USB. Descartando.")
                                continue
                            
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
                            lines_captured.add(line_id)
                            
                            print(f" -> Coletando: [{len(lines_captured)}/64] | Último ID válido: {line_id:02d}", end="\r")

        print("\n\n==================================================")
        print("         ANÁLISE DE QUALIDADE DO LINK ÓPTICO      ")
        print("==================================================")
        
        if total_tentativas > 0:
            rendimento = (len(lines_captured) / total_tentativas) * 100
            print(f"[TELEMETRIA] Rendimento do Link: {rendimento:.1f}%")
            if rendimento >= 95.0 and len(lines_captured) == 64:
                print("⭐ [STATUS] SINAL EXCELENTE: O laser está PERFEITAMENTE alinhado!")
            elif rendimento >= 75.0:
                print("⚠️ [STATUS] SINAL BOM: Transmissão estável com poucas perdas.")
            else:
                print("❌ [STATUS] SINAL FRACO: Melhore o posicionamento físico dos componentes.")
        
        print("==================================================")
        print(" Renderizando o frame final do Vaspinho...")

        cv2.namedWindow("UFF Li-Fi - Vaspinho Indexado", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("UFF Li-Fi - Vaspinho Indexado", 450, 450)
        cv2.imshow("UFF Li-Fi - Vaspinho Indexado", imagem_reconstruida)
        cv2.waitKey(0)

    except KeyboardInterrupt:
        print("\n[INFO] Interrupção manual detectada.")
    finally:
        ser.close()
        cv2.destroyAllWindows()
        print("[INFO] Porta serial e janelas fechadas.")

if __name__ == "__main__":
    rodar_receptor_lifi_bloco_id()