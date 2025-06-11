import socket
import threading
import os
import hashlib

# Listas globais para gerenciar clientes e threads
clients_socks = []
clients_threads = []
clients_lock = threading.Lock()
running = True

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# Envia mensagem para todos os clientes
def broadcast(message, sender_sock=None):
    with clients_lock:
        for client_sock in clients_socks:
            if client_sock != sender_sock:
                try:
                    client_sock.sendall(message.encode('utf-8'))
                except Exception as e:
                    pass

# Lida com uma solicitação de arquivo
def handle_file_request(client_sock, filename):
    try:
        filename.strip()
        if os.path.exists(filename) and os.path.isfile(filename):
            file_size = os.path.getsize(filename)
            
            sha256_hash = hashlib.sha256()
            with open(filename, 'rb') as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            file_hash = sha256_hash.hexdigest()
            
            # Protocolo de cabeçalho: envia metadados antes dos dados do arquivo. \n\n sinaliza o fim.
            header = f"FILE_TRANSFER_START\nFILENAME:{os.path.basename(filename)}\nSIZE:{file_size}\nSHA256:{file_hash}\n\n"
            client_sock.sendall(header.encode('utf-8'))
            
            print(f"[Servidor] Enviando {filename} ({file_size} bytes) para o cliente...")
            # Envia o arquivo em pedaços (chunks) para suportar arquivos grandes
            with open(filename, 'rb') as f:
                while chunk := f.read(4096):
                    client_sock.sendall(chunk)
            print(f"[Servidor] Envio de {filename} concluído.")
        else:
            print(f"[Servidor] Arquivo solicitado '{filename}' não encontrado.")
            # Envia mensagem de erro padronizada, terminada em \n
            client_sock.sendall(b'FILE_NOT_FOUND\n')
    except Exception as e:
        print(f"[Servidor] Erro ao manusear requisição de arquivo: {e}")

# Função executada por cada thread para lidar com um cliente individualmente
def handle_client(client_sock, addr_client):
    global running
    client_name = f"{addr_client[0]}:{addr_client[1]}"
    print(f"[Servidor] Conexão aceita de {client_name}")

    with clients_lock:
        clients_socks.append(client_sock)

    buffer = ""
    try:
        while running:
            data = client_sock.recv(1024).decode('utf-8', errors='ignore')
            if not data: break
            
            buffer += data
            
            # Processa o buffer, tratando múltiplos comandos se chegarem juntos
            while '\n' in buffer:
                message, _, buffer = buffer.partition('\n')
                message = message.strip()
                if not message: continue

                parts = message.split(" ", 1)
                command = parts[0].upper()

                if command == 'SAIR':
                    break
                elif command == 'FILE':
                    if len(parts) > 1:
                        filename = parts[1].strip()
                        handle_file_request(client_sock, filename)
                    else:
                        client_sock.sendall(b"[Servidor] ERRO: Uso correto: FILE <nome_do_arquivo>\n")
                else:
                    print(f"[Chat] {client_name} diz: {message}")
            
    except Exception as e:
        print(f"Erro com cliente {client_name}: {e}")
    finally:
        with clients_lock:
            if client_sock in clients_socks:
                clients_socks.remove(client_sock)
        client_sock.close()
        print(f"[Servidor] Fechando conexão com o cliente {client_name}.")

# Thread para permitir que o administrador do servidor envie mensagens (broadcast)
def server_input(port):
    global running
    while running:
        message_to_broadcast = input()
        if message_to_broadcast == 'SHUTDOWN':
            print("[SERVIDOR] Encerrando...")
            running = False
            try:
                # Truque do auto-conectar para desbloquear o server_sock.accept() e permitir o desligamento
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(('127.0.0.1', port))
            except Exception as e:
                print(f"[Servidor] Erro no auto-conectar para desligamento: {e}")
            break
        else:
            broadcast(f"[Servidor Admin] {message_to_broadcast}\n")

def main():
    HOST = '0.0.0.0' # Escuta em todas as interfaces de redes
    PORT = 2002      

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        server_sock.bind((HOST, PORT))
        server_sock.listen(5)
        print(f"[Servidor] Escutando em {get_local_ip()}:{PORT}")

        # Inicia a thread para comandos do admin
        server_input_thread = threading.Thread(target=server_input, args=(PORT,), daemon=True)
        server_input_thread.start()

        # Loop principal para aceitar novas conexões
        while True:
            try:
                client_sock, addr_client = server_sock.accept()
                if not running:
                    client_sock.close()
                    break
                
                # Cria e inicia uma nova thread para cada cliente
                thread = threading.Thread(target=handle_client, args=(client_sock, addr_client))
                thread.start()
                clients_threads.append(thread)

            except OSError:
                break

    except Exception as e:
        print(f"[Servidor] Ocorreu um erro no servidor: {e}")
    finally:
        # Lógica de desligamento controlado 
        print("[Servidor] Servidor fechado!")
        with clients_lock:
            for cs in clients_socks:
                cs.close()
            clients_socks.clear()

        # Espera todas as threads terminarem
        for t in clients_threads:
            t.join()
    
        server_input_thread.join()

        server_sock.close()

if __name__ == "__main__":
    main()