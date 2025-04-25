import socket

IP = '0.0.0.0'  # Escuta em todas as interfaces
PORT = 5005    # PORT maior que 1024

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((IP, PORT))

print(f"Aguardando dados na PORT {PORT}...")

file, adress = sock.recvfrom(4096)
file = file.decode()

print(f"Recebendo arquivo: {file}")

with open(f"received_{file}" , 'wb') as f:
    while True:
        dados, _ = sock.recvfrom(4096)
        if dados == b'EOF':
            print("Recebido EOF. Fim da transmissão.")
            break
        f.write(dados)

print(f"Arquivo salvo como received_{file}")
