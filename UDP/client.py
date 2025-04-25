import socket
import os

SERVER_IP = '127.0.0.1' 
SERVER_PORT = 5005

file = input("Digite o caminho do arquivo: ").strip()

if not os.path.exists(file):
    print("Arquivo não encontrado.")
    exit()

file_name = os.path.basename(file)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(file_name.encode(), (SERVER_IP, SERVER_PORT))

with open(file, 'rb') as f:
    while True:
        dados = f.read(4096)
        if not dados:
            break
        sock.sendto(dados, (SERVER_IP, SERVER_PORT))

# Envia mensagem para finalizar o server
sock.sendto(b'EOF', (SERVER_IP, SERVER_PORT))
print("Arquivo enviado com sucesso.")
