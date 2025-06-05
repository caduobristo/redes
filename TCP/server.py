import socket
import threading

clients_socks = []
clients_threads = []
clients_lock = threading.Lock()
running = True

def broadcast(message, sender_sock=None):
    with clients_lock:
        for client_sock in clients_socks:
            if client_sock != sender_sock:
                try:
                    client_sock.sendall(message.encode('utf-8'))
                except Exception as e:
                    print(f"[Broadcast] Erro ao enviar para um cliente: {e}")

def handle_client(client_sock, addr_client):
    client_name = f"{addr_client[0]}:{addr_client[1]}"
    print(f"[Servidor] Conexão aceita de {client_name}")

    with clients_lock:
        clients_socks.append(client_sock)

    try:
        while True:
            received_data = client_sock.recv(1024)
            if not received_data:
                print(f"[Servidor] Cliente {client_name} desconectou.")
                break
            
            message = received_data.decode('utf-8')            
            if message.upper() == 'SAIR':
                break

            if message.startswith("CHAT:"):
                chat_message = message[5:].strip()
                print(f"[Chat] {client_name} diz: {chat_message}")
            else:
                print(f"[Servidor] Comando desconhecido de {client_name}: {message}")
            
    except ConnectionResetError:
        print(f"[Servidor] Conexão com {client_name} foi resetada pelo cliente.")
    except Exception as e:
        if running:
            print(f"[Servidor] Erro durante a comunicação com o cliente {client_name}: {e}")
    finally:
        with clients_lock:
            if client_sock in clients_socks:
                clients_socks.remove(client_sock)
        client_sock.close()
        print(f"[Servidor] Fechando conexão com o cliente {client_name}.")

def server_input(port):
    global running
    while running:
        message_to_broadcast = input()
        if message_to_broadcast == 'SHUTDOWN':
            print("[SERVIDOR] Encerrando...")
            running = False
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(('127.0.0.1', port))
            except Exception as e:
                print(f"[Servidor] Erro no auto-conectar para desligamento: {e}")
            break
        else:
            broadcast(f"[Servidor Admin] {message_to_broadcast}")

def main():
    HOST = '0.0.0.0' 
    PORT = 2002      

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        server_sock.bind((HOST, PORT))
        server_sock.listen(5)
        print(f"[Servidor] Escutando em {HOST}:{PORT}")

        server_input_thread = threading.Thread(target=server_input, args=(PORT,), daemon=True)
        server_input_thread.start()

        while True:
            try:
                client_sock, addr_client = server_sock.accept()
                if not running:
                    client_sock.close()
                    break
                
                thread = threading.Thread(target=handle_client, args=(client_sock, addr_client))
                thread.start()
                clients_threads.append(thread)
                
                print(f"[Servidor] Clientes ativos: {threading.active_count() - 1}")
            except OSError:
                break

    except Exception as e:
        print(f"[Servidor] Ocorreu um erro no servidor: {e}")
    finally:
        print("[Servidor] Fechando o servidor!")
        with clients_lock:
            for cs in clients_socks:
                cs.close()
            clients_socks.clear()

        for t in clients_threads:
            t.join()
    
        server_input_thread.join()

        server_sock.close()

if __name__ == "__main__":
    main()