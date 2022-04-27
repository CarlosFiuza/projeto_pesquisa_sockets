import sys
import socket
import selectors
import types
import threading

class Client:
    def __init__(self):
        host = str(sys.argv[1])  
        port = int(sys.argv[2])
        connid = int(sys.argv[3])
        self.server_addr = (host, port)
        self.sel = selectors.DefaultSelector()
        self.alive = True
        # Cria socket 
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        # Conecta com a sala com por meio de conexao não blocante
        sock.connect_ex(self.server_addr)
        print(f"Conexão bem-sucedida")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = types.SimpleNamespace(connid=connid, messages=b"")
        # registra socket para monitoramento e multiplexação de I/O
        self.sel.register(sock, events, data=data)

    def event_read(self):
        while True:
            # verifica se objeto socket está pronto para I/O
            events = self.sel.select(timeout=None)
            for key, mask in events:
                # se for evento para leitura
                if mask & selectors.EVENT_READ:
                    sock = key.fileobj
                    # recebe mensagem do socket
                    recv_data = sock.recv(1024)
                    if recv_data:
                        recv_data = recv_data.decode()
                        print(f">> {recv_data[:-1]}")
                    else:
                        print("Desconectado da sala!")
                        self.alive = False
                        return

    def event_write(self):
        while True and self.alive:
            # verifica se objeto socket está pronto para I/O
            events = self.sel.select(timeout=None)
            for key, mask in events:
                # se for evento para escrita
                if mask & selectors.EVENT_WRITE:
                    sock = key.fileobj
                    data = key.data
                    # captura entrada do cliente
                    data.messages += sys.stdin.readline().encode()
                    if data.messages.decode():
                        # envia mensagem
                        sent = sock.send(data.messages)
                        # atualiza mensagens a serem enviadas de acordo com quantos bytes
                        # foram enviados bem sucedidos
                        data.messages = data.messages[sent:]


    def catch_except(self, args, /):
        print('catch_except: ', args)
        self.alive = False


    def run(self):
        try:
            print('Digite o que desejar, sendo que "listar" retorna todos os clientes na sala')
            # cria thread para evento de leitura
            thread = threading.Thread(target = self.event_read)
            thread.start()
            # threading.excepthook = self.catch_except(self)
            self.event_write()
            thread.join()
        except:
            self.sel.close()
            raise Exception()


if __name__ == '__main__':
    if len(sys.argv) != 4:  
        print ("Necessita dos argumentos: endereço IP, porta, connid") 
        exit()
    try:
        client = Client()
        client.run()
    except:
        print("Falha na criação do cliente")
    finally:
        exit()


