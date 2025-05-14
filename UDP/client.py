import socket
import struct
import hashlib
import random

# Função para calcular o checksum SHA-256 truncado (4 bytes)
def calculate_checksum(data):
    return hashlib.sha256(data).digest()[:4]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2)

# Verifica a conexão com o servidor
while True:
    server_input = input("[Cliente] Digite o IP e porta do servidor: ").strip()

    try:
        SERVER_IP, SERVER_PORT = server_input.split(':')
        SERVER_PORT = int(SERVER_PORT) 
        sock.sendto(b'PING', (SERVER_IP, SERVER_PORT))
        try:
            response, _ = sock.recvfrom(1024)
            if response == b'PONG':
                print("[Cliente] Conexão com servidor estabelecida com sucesso.")
                break
            else:
                print("[Cliente] Servidor respondeu, mas com mensagem inesperada.")
        except e:
            print("[Cliente] Sem resposta do servidor. Verifique o IP/porta e tente novamente.")
            
    except ValueError:
        print("[Cliente] Entrada inválida, use o formato IP:PORTA")
        continue

    except Exception as e:
        print("[Cliente] Sem resposta do servidor. Verifique o IP/porta e tente novamente.")

# Loop principal para enviar requisições
while True:
    user_input = input("[Cliente] Digite a requisição: ").strip()

    if user_input == 'EOF':
        sock.sendto(b'EOF', (SERVER_IP, SERVER_PORT))
        print("[Cliente] Comando EOF enviado. Encerrando cliente.")
        break

    if not user_input.startswith("GET /"):
        print("[Cliente] Comando inválido. Use o formato GET /nome_do_arquivo.ext")
        continue

    try:
        _, endpoint = user_input.split(" ", 1)
        sock.sendto(user_input.encode(), (SERVER_IP, SERVER_PORT))
        print("[Cliente] Requisição enviada ao servidor.")

        expected_seq = 0
        received_data = {}
        ack_lost_counter = 0

        # Loop de recepção e verificação dos pacotes
        while True:
            try:
                package, _ = sock.recvfrom(1024)
            except socket.timeout:
                ack_lost_counter += 1
                if ack_lost_counter > 3:
                    print("[Cliente] Timeout contínuo. Encerrando tentativa de recepção.")
                    break
                continue

            if package == b'EOF':
                print("[Cliente] EOF recebido. Fim da transmissão.")
                break
            if package == b'FILE_NOT_FOUND':
                print("[Cliente] Arquivo não encontrado no servidor.")
                break

            try:
                # Extrai o número de sequência e o checksum
                seq_num = struct.unpack('!I', package[:4])[0]                
                recv_checksum = package[4:8]

                # 5% de chance de simular uma perda
                if random.random() < 0.05:
                    print(f"[Cliente] Simulando perda do pacote {seq_num}")
                    continue

                data = package[8:]
                local_checksum = calculate_checksum(data)

                if recv_checksum != local_checksum:
                    print(f"[Cliente] Pacote {seq_num} com checksum inválido! Ignorado.")
                    continue

                if seq_num == expected_seq:
                    # Pacote correto - armazena e envia ACK
                    received_data[seq_num] = data
                    print(f"[Cliente] Pacote {seq_num} recebido corretamente ({len(data)} bytes)")
                    ack_msg = struct.pack('!I', seq_num)
                    sock.sendto(b'ACK' + ack_msg, (SERVER_IP, SERVER_PORT))
                    expected_seq += 1
                else:
                    # Pacote fora de ordem - reenvia último ACK correto
                    last_ack = expected_seq - 1 if expected_seq > 0 else 0
                    ack_msg = struct.pack('!I', last_ack)
                    sock.sendto(b'ACK' + ack_msg, (SERVER_IP, SERVER_PORT))
                    print(f"[Cliente] Pacote fora de ordem. Esperado: {expected_seq}, Recebido: {seq_num}")

            except Exception as e:
                print(f"[Cliente] Erro ao processar pacote: {e}")

        if received_data:
            file = endpoint.strip("/")
            with open(f"received_{file}", 'wb') as f:
                for seq in sorted(received_data.keys()):
                    f.write(received_data[seq])
                print(f"[Cliente] Arquivo salvo como received_{file}")

    except Exception as e:
        print(f"[Cliente] Erro: {e}")
