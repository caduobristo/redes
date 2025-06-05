import socket
import threading
import sys

running = True

def receive_thread(sock):
    while True:
        try:
            message = sock.recv(1024).decode('utf-8')
            if not message:
                break
            sys.stdout.write('\r' + ' ' * 60 + '\r')
            print(message)
            sys.stdout.write('[Você] ')
            sys.stdout.flush()
        except Exception as e:
            if running:
                print("\n[AVISO] Conexão com o servidor encerrada. Pressione Enter para sair.")
            break

def main():
    global running
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_input = input("[Cliente] Digite o IP e porta do servidor: ").strip()
    
        SERVER_IP, SERVER_PORT = server_input.split(':')
        SERVER_PORT = int(SERVER_PORT)
        
        print(f"[Cliente] Tentando conectar a {SERVER_IP}:{SERVER_PORT}...")
        sock.connect((SERVER_IP, SERVER_PORT))
        
        print("[Cliente] Conexão com o servidor estabelecida com sucesso!")
    except Exception as e:
        print(f"[Cliente] Não foi possível conectar: {e}")
        return
    
    receiver = threading.Thread(target=receive_thread, args=(sock,), daemon=True)
    receiver.start()

    try:
        while receiver.is_alive():
            message = input('[Você] ')
            if message.upper() == 'SAIR':
                sock.sendall(message.encode('utf-8'))
                break

            full_message = f"CHAT:{message}"
            sock.sendall(full_message.encode('utf-8'))
            
    except (BrokenPipeError, ConnectionResetError):
        print("[Cliente] A conexão com o servidor foi encerrada.")
    except (EOFError, KeyboardInterrupt):
        print("[Cliente] Desconectando...")
        try:
            sock.sendall(b'SAIR')
        except:
            pass
        
    finally:
        running = False
        print("[Cliente] Desconectando...")
        sock.close()

if __name__ == "__main__":
    main()