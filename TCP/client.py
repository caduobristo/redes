import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5) 

while True:
    try:
        server_input = input("[Cliente] Digite o IP e porta do servidor: ").strip()
    
        SERVER_IP, SERVER_PORT = server_input.split(':')
        SERVER_PORT = int(SERVER_PORT)
        
        print(f"[Cliente] Tentando conectar a {SERVER_IP}:{SERVER_PORT}...")
        sock.connect((SERVER_IP, SERVER_PORT))
        
        print("[Cliente] Conexão com o servidor estabelecida com sucesso!")
        break

    except ValueError:
        print("[Cliente] Entrada inválida. Use o formato IP:PORTA.")
    except socket.timeout:
        print("[Cliente] A tentativa de conexão demorou demais.")
    except ConnectionRefusedError:
        print("[Cliente] Conexão recusada.")
    except socket.gaierror:
        print("[Cliente] O IP ou hostname é inválido.")
    except Exception as e:
        print(f"[Cliente] Ocorreu um erro ao tentar conectar: {e}.")

try:
    sock.settimeout(None)

    message = "Olá, servidor! Tudo bem?"
    sock.sendall(message.encode('utf-8'))
    print(f"[Cliente] Mensagem enviada: {message}")

    received_data = sock.recv(1024)
    server_message = received_data.decode('utf-8')

    print(f"[Cliente] Resposta recebida: {server_message}")

except socket.error as e:
    print(f"[Cliente] Erro de socket durante a comunicação: {e}")
except Exception as e:
    print(f"[Cliente] Ocorreu um erro inesperado: {e}")
finally:
    print("[Cliente] Fechando socket.")
    sock.close()