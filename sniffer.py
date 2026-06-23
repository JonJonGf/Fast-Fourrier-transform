import serial
import time

PORTA_COM = "COM4"  # Confirme a porta COM do seu RECEPTOR
BAUD_RATE = 19200

def rodar_sniffer_lifi():
    try:
        ser = serial.Serial(PORTA_COM, BAUD_RATE, timeout=1.0)
        print("==================================================")
        print("      UFF Li-Fi SNIFFER ÓPTICO - 19200 BAUD       ")
        print("==================================================")
        print(f"[OK] Monitorando a porta {PORTA_COM}... Pressione Ctrl+C para parar.\n")
        
        ser.reset_input_buffer()
    except Exception as e:
        print(f"[ERRO] Não foi possível abrir a porta {PORTA_COM}: {e}")
        return

    try:
        while True:
            # Espera até ter pelo menos 1 byte no buffer
            if ser.in_waiting > 0:
                # Lê tudo o que estiver disponível no momento
                dados_brutos = ser.read(ser.in_waiting)
                
                # Converte para string hexadecimal para visualizarmos os cabeçalhos
                hex_dados = dados_brutos.hex().upper()
                
                # Formata o hex espaçado de 2 em 2 caracteres para leitura humana fácil
                hex_formatado = " ".join(hex_dados[i:i+2] for i in range(0, len(hex_dados), 2))
                
                print(f"[BYTES RECEBIDOS ({len(dados_brutos)}B)]: {hex_formatado}")
            
            time.sleep(0.05)  # Pequeno respiro para o processador não fritar

    except KeyboardInterrupt:
        print("\n[INFO] Sniffer encerrado manualmente.")
    finally:
        ser.close()
        print("[INFO] Porta serial fechada.")

if __name__ == "__main__":
    rodar_sniffer_lifi()