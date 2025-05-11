import socket
import struct
import os
import hashlib
import random

# Função para calcular o checksum SHA-256 truncado (4 bytes)
def calculate_checksum(data):
    return hashlib.sha256(data).digest()[:4]

IP = '0.0.0.0' 
PORT = 5005 
WINDOW_SIZE = 4
TIMEOUT = 2

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((IP, PORT))
sock.settimeout(TIMEOUT)

print(f"[Servidor] Aguardando requisição na porta {PORT}...")

# Loop principal para escutar requisições
while True:
    try:
        request, client_addr = sock.recvfrom(4096)
    except socket.timeout:
        continue
    
    request = request.decode()

    # Mensagem de confirmação de conexão
    if request == 'PING':
        sock.sendto(b'PONG', client_addr)
        print("[Servidor] Conexão com cliente estabelecida com sucesso.")
        continue

    if request.strip() == 'EOF':
        print("[Servidor] Comando EOF recebido. Encerrando servidor.")
        break

    if not request.startswith("GET /"):
        print(f"[Servidor] Requisição inválida de {client_addr}: {request}")
        continue

    file = request[5:]  # Remove o "GET /"
    print(f"[Servidor] Enviando arquivo: {file} para {client_addr}")

    if not os.path.exists(file):
        print("[Servidor] Arquivo não encontrado.")
        sock.sendto(b'FILE_NOT_FOUND', client_addr)
        continue

    # Organização dos pacotes que serão enviados
    with open(file, 'rb') as f:
        packages = []
        seq_num = 0
        while True:
            data = f.read(4084) # 4084 = 4096 - 4 (seq) - 8 (checksum)
            if not data:
                break

            header = struct.pack('!I', seq_num)
            checksum = calculate_checksum(data)
            package = header + checksum + data
            packages.append(package)
            seq_num += 1

    base = 0
    next_seq = 0
    total_packages = len(packages)

    # Loop de envio com janela deslizante Go-Back-N
    while base < total_packages:
        while next_seq < base + WINDOW_SIZE and next_seq < total_packages:
            sock.sendto(packages[next_seq], client_addr)
            print(f"[Servidor] Pacote {next_seq} enviado")
            next_seq += 1
        
        # 5% de chance de simular uma perda
        if random.random() < 0.05:
            print(f"[Servidor] Simulando perda do pacote {next_seq}")
            next_seq += 1
            continue

        try:
            # Espera ACK do cliente
            ack_data, _ = sock.recvfrom(1024)
            if ack_data.startswith(b'ACK') and len(ack_data) >= 7:
                ack_num = struct.unpack('!I', ack_data[3:7])[0]
                print(f"[Servidor] ACK {ack_num} recebido")
                base = ack_num + 1 # Avança a base da janela
            else:
                continue
        except socket.timeout:
            print(f"[Servidor] Timeout - reenviando a partir de {base}")
            next_seq = base

    sock.sendto(b'EOF', client_addr)
    print("[Servidor] Envio finalizado.\n")
