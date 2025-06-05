import socket

HOST = '0.0.0.0' 
PORTA = 2002      

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    sock.bind((HOST, PORTA))
    print(f"[Servidor] Vinculado a {HOST}:{PORTA}")

    sock.listen(1)
    print("[Servidor] escutando por conexões...")

    client_sock, addr_client = sock.accept()
    client_name = f"{addr_client[0]}:{addr_client[1]}"
    print(f"[Servidor] Conexão aceita de {client_name}")

    try:
        received_data = client_sock.recv(1024)
        if received_data:
            client_message = received_data.decode('utf-8')            
            print(f"[Servidor] Cliente {client_name} diz: {client_message}")

            response = "Olá, cliente! Mensagem recebida."
                
            client_sock.sendall(response.encode('utf-8'))
            print(f"[Servidor] Resposta enviada para o cliente: {response}")
        else:
            print(f"[Servidor] Cliente {client_name} desconectou prematuramente.")

    except socket.error as e:
        print(f"[Servidor] Erro durante a comunicação com o cliente {client_name}: {e}")
    finally:
        print(f"[Servidor] Fechando conexão com o cliente {client_name}.")
        client_sock.close()

except socket.error as e:
    print(f"[Servidor] Erro no socket: {e}")
except Exception as e:
    print(f"[Servidor] Ocorreu um erro inesperado: {e}")
finally:
    print("[Servidor] Fechando servidor!")
    sock.close()