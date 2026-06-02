import numpy as np
import struct

# Configurações baseadas exatamente no seu script gerador
RESOLUCAO = 64
ELEMENTOS_POR_LINHA = 102  # 1 Sync + 1 DC + 50 Amplitudes + 50 Fases

print("--- LEITOR DE DADOS BRUTOS DO ARQUIVO BINÁRIO ---")

try:
    # 1. Lê o arquivo completo como floats de 32 bits (IEEE 754)
    dados_brutos = np.fromfile("dados_fourier.bin", dtype=np.float32)
    
    # 2. Reorganiza a fita de dados na matriz de 64 linhas
    matriz_linhas = dados_brutos.reshape((RESOLUCAO, ELEMENTOS_POR_LINHA))
    
    # 3. Varre as linhas e exibe os dados numéricos decodificados
    # (Para não inundar o terminal, você pode limitar o range, ex: range(5) para ver as 5 primeiras)
    for i in range(RESOLUCAO):
        linha_dados = matriz_linhas[i, :]
        
        # Converte o primeiro float de volta para 4 bytes para ler o formato Hex original
        sync_float = linha_dados[0]
        sync_bytes = struct.pack('<f', sync_float)
        sync_hex = sync_bytes.hex().upper()
        
        # Extrai os componentes matemáticos reais da FFT
        dc = linha_dados[1]
        amplitudes = linha_dados[2:52]
        fases = linha_dados[52:102]
        
        print(f"\n====================== LINHA {i:02d} ======================")
        print(f"Cabeçalho de Sincronismo (Hex) : 0x{sync_hex}")
        print(f"Componente DC (Brilho Médio)   : {dc:.4f}")
        
        # Exibe uma amostra dos primeiros 5 coeficientes de amplitude e fase
        print(f"Amplitudes (Primeiros 5 termos): {[round(float(a), 4) for a in amplitudes[:5]]} ...")
        print(f"Fases em Radianos (Primeiros 5): {[round(float(f), 4) for f in fases[:5]]} ...")
        print(f"Total de dados na linha        : {len(amplitudes)} amplitudes e {len(fases)} fases guardadas.")

except FileNotFoundError:
    print("Erro: O arquivo 'dados_fourier.bin' não foi encontrado na pasta.")
except ValueError as e:
    print(f"Erro de tamanho de arquivo: {e}")
    print("O tamanho do arquivo binário não condiz com uma matriz de 64x102 floats.")