import socket
import threading
import sys
import hashlib

def receive_file(sock, file_info, initial_chunk):
    try:
        original_filename = file_info['FILENAME']   
        save_as_filename = f"received_{original_filename}"
        filesize = int(file_info['SIZE'])
        expected_hash = file_info['SHA256']
        
        print(f"\n[Cliente] Recebendo '{original_filename}' ({filesize} bytes)")
        
        with open(save_as_filename, 'wb') as f:
            f.write(initial_chunk)
            received_bytes = len(initial_chunk)
            
            # Loop para receber o restante dos dados do arquivo
            while received_bytes < filesize:
                chunk = sock.recv(4096)
                if not chunk: break
                f.write(chunk)
                received_bytes += len(chunk)

        # Após receber tudo, calcula o hash do arquivo salvo localmente
        sha256_hash = hashlib.sha256()
        with open(save_as_filename, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        calculated_hash = sha256_hash.hexdigest()

        if calculated_hash == expected_hash:
            print("[Cliente] Arquivo recebido com sucesso!")
        else:
            print(f"[Cliente] ERRO: Verificação de integridade falhou.")

    except Exception as e:
        print(f"[Cliente] Erro ao receber o arquivo: {e}")

# Thread dedicada a receber mensagens do servidor
def receive_thread(sock):
    # Buffer de bytes para lidar com dados binários e de texto misturados
    byte_buffer = bytearray()
    while True:
        try:
            data = sock.recv(1024)
            if not data: break
            
            byte_buffer.extend(data)

            # Procura pelo fim do cabeçalho (duas novas linhas)
            if b'\n\n' in byte_buffer:
                header_part, _, rest = byte_buffer.partition(b'\n\n')
                byte_buffer = rest
                
                header_str = header_part.decode('utf-8')
                header_lines = header_str.split('\n')
                command = header_lines[0].strip()

                if command == "FILE_TRANSFER_START":
                    file_info = {line.split(':', 1)[0]: line.split(':', 1)[1] for line in header_lines[1:] if ':' in line}
                    # Passa o início dos dados binários para a função de recebimento
                    receive_file(sock, file_info, byte_buffer)
                    byte_buffer.clear() # Limpa o buffer pois foi consumido
                    continue
            
            # Lógica para mensagens de texto: procura por uma nova linha
            if b'\n' in byte_buffer:
                text_part, _, rest = byte_buffer.partition(b'\n')
                byte_buffer = rest
                message = text_part.decode('utf-8').strip()
                if message:
                    # Lógica para imprimir a mensagem sem bagunçar o input do usuário
                    sys.stdout.write('\r' + ' ' * 60 + '\r')
                    if message == "FILE_NOT_FOUND":
                        print("[Servidor] ERRO: O arquivo solicitado não foi encontrado.")
                    else:
                        print(message)
                    sys.stdout.write('[Você] ')
                    sys.stdout.flush()

        except (ConnectionResetError, ConnectionAbortedError):
            print("\n[AVISO] Conexão com o servidor encerrada. Pressione Enter para sair.")
            break
        except Exception:
            break

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_input = input("[Cliente] Digite o IP e porta do servidor: ").strip()
    
        SERVER_IP, SERVER_PORT = server_input.split(':')
        SERVER_PORT = int(SERVER_PORT)
        sock.connect((SERVER_IP, SERVER_PORT))
        
        print(f"[Cliente] Conexão com o servidor {SERVER_IP}:{SERVER_PORT} estabelecida com sucesso!")
    except Exception as e:
        print(f"[Cliente] Não foi possível conectar: {e}")
        return
    
    # Inicia a thread de recebimento para uma UI não-bloqueante
    receiver = threading.Thread(target=receive_thread, args=(sock,), daemon=True)
    receiver.start()

    try:
        # Loop principal para ler o input do usuário e enviar ao servidor
        while receiver.is_alive():
            user_input = input('[Você] ')

            if not user_input: continue

            # Anexa \n para que o servidor saiba onde o comando termina
            message = f"{user_input}\n"
            sock.sendall(message.encode('utf-8'))

            if user_input.strip().upper() == 'SAIR':
                break
            
    except (BrokenPipeError, ConnectionResetError):
        print("[Cliente] A conexão com o servidor foi encerrada.")
    except (EOFError, KeyboardInterrupt):
        print("[Cliente] Desconectando...")
        try:
            sock.sendall(b'SAIR')
        except:
            pass
        
    finally:
        print("[Cliente] Desconectando...")
        sock.close()

if __name__ == "__main__":
    main()