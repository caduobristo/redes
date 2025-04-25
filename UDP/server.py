import socket
import struct

IP = '0.0.0.0'  # Escuta em todas as interfaces
PORT = 5005    # PORT maior que 1024

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((IP, PORT))

print(f"[Servidor]Aguardando dados na PORT {PORT}...")

file, adress = sock.recvfrom(4096)
file = file.decode()

print(f"[Servidor]Recebendo arquivo: {file}")

received_data = {}

while True:
    package, _ = sock.recvfrom(4096)
    if package == b'EOF':
        print("[Servidor]Recebido EOF. Fim da transmissão.")
        break

    if len(package) < 4:
        print(f"[Servidor]Pacote inválido recebido {len(package)}")
        continue

    try:
        seq_num = struct.unpack('!I', package[:4])[0]
        data = package[4:]

        received_data[seq_num] = data
        print(f"[Servidor] Pacote {seq_num} recebido ({len(data)} bytes)")
    except struct.error:
        print("[Servidor] Erro ao desempacotar número de sequência. Pacote ignorado.")


with open(f"received_{file}" , 'wb') as f:
    for data in sorted(received_data.keys()):
        f.write(received_data[data])
        print(f"[Servidor]Gravando pacote {data}")


print(f"[Servidor]Arquivo salvo como received_{file}")
