import serial
import time
import sys

# ==========================================
# CONFIGURAÇÕES DO SNIFFER (9600 BAUD)
# ==========================================
PORTA_COM = "COM4"  # Confirme a porta COM do seu RECEPTOR
BAUD_RATE = 9600

def rodar_sniffer_lifi_inteligente():
    try:
        # Timeout curto para detectar rapidamente as pausas entre as linhas do laser
        ser = serial.Serial(PORTA_COM, BAUD_RATE, timeout=0.5)
        print("==================================================")
        print("    UFF Li-Fi SNIFFER INTELIGENTE - 9600 BAUD     ")
        print("==================================================")
        print(f"[OK] Monitorando a porta {PORTA_COM}... Pressione Ctrl+C para parar.\n")
        
        ser.reset_input_buffer()
    except Exception as e:
        print(f"[ERRO] Não foi possível abrir a porta {PORTA_COM}: {e}")
        return

    buffer_acumulado = bytearray()
    ultimo_tempo_dados = time.time()

    try:
        while True:
            if ser.in_waiting > 0:
                # Lê os bytes disponíveis no momento
                dados_novos = ser.read(ser.in_waiting)
                buffer_acumulado.extend(dados_novos)
                ultimo_tempo_dados = time.time()
                
                # Print dinâmico na MESMA linha (Sem spammar o terminal)
                sys.stdout.write(f"\r -> Capturando fluxo óptico... Total acumulado: {len(buffer_acumulado)} bytes")
                sys.stdout.flush()
            
            # Se já temos dados guardados e o laser silenciou por mais de 0.4 segundos
            # significa que uma linha inteira terminou de passar ou a rajada acabou
            if len(buffer_acumulado) > 0 and (time.time() - ultimo_tempo_dados > 0.4):
                print(f"\n[BLOCO DETECTADO ({len(buffer_acumulado)}B)]")
                
                # Transforma em Hexadecimal espaçado para análise visual humana
                hex_dados = buffer_acumulado.hex().upper()
                hex_formatado = " ".join(hex_dados[i:i+2] for i in range(0, len(hex_dados), 2))
                
                # Exibe apenas os primeiros 30 bytes e os últimos 10 bytes para não poluir
                if len(buffer_acumulado) > 40:
                    inicio_hex = " ".join(hex_dados[i:i+2] for i in range(0, 60, 2))
                    fim_hex = " ".join(hex_dados[i:i+2] for i in range(len(hex_dados)-20, len(hex_dados), 2))
                    print(f" ├─► HEX: {inicio_hex} ... {fim_hex}")
                else:
                    print(f" ├─► HEX: {hex_formatado}")
                
                # Procura se o cabeçalho indexado está correto
                if b'\xAA\xBB\xCC\xDD' in buffer_acumulado:
                    idx = buffer_acumulado.find(b'\xAA\xBB\xCC\xDD')
                    # Pega o byte seguinte ao cabeçalho (que é o ID da linha)
                    if idx + 4 < len(buffer_acumulado):
                        print(f" └─► [OK] Sincronismo encontrado! ID da Linha: {buffer_acumulado[idx+4]:02d}")
                else:
                    print(" └─► [AVISO] Cabeçalho AA BB CC DD não encontrado neste bloco.")
                
                print("-" * 50)
                buffer_acumulado.clear() # Limpa para esperar a próxima rajada
                
            time.sleep(0.02) # Evita uso excessivo de CPU

    except KeyboardInterrupt:
        print("\n\n[INFO] Sniffer encerrado manualmente.")
    finally:
        ser.close()
        print("[INFO] Porta serial fechada.")

if __name__ == "__main__":
    rodar_sniffer_lifi_inteligente()