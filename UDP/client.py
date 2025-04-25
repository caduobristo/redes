import socket
import os
import struct

SERVER_IP = '127.0.0.1' 
SERVER_PORT = 5005

file = input("[Cliente]Digite o caminho do arquivo: ").strip()

if not os.path.exists(file):
    print("[Cliente]Arquivo não encontrado.")
    exit()

file_name = os.path.basename(file)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(file_name.encode(), (SERVER_IP, SERVER_PORT))

seq_num = 0
with open(file, 'rb') as f:
    while True:
        data = f.read(4092)
        if not data:
            break
        sock.sendto(data, (SERVER_IP, SERVER_PORT))

        header = struct.pack('!I', seq_num)
        package = header + data
        sock.sendto(package, (SERVER_IP, SERVER_PORT))
        print(f"[Cliente] Pacote {seq_num} enviado ({len(data)} bytes)")
        seq_num += 1

# Envia mensagem para finalizar o server
sock.sendto(b'EOF', (SERVER_IP, SERVER_PORT))
print("[Cliente]Arquivo enviado com sucesso.")
