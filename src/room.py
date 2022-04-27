import socket
import selectors
import types

class Room:
    def __init__(self, host, port, num, id):
        # construtor da classe que cria o socket e faz o bind
        # no address e porta indicados, seta o socket como não
        # blokante e registra o socket no selector com evento de
        # leitura e escrita
        self.clients = []
        self.sel = selectors.DefaultSelector()
        self.host = host
        self.port = port
        self.max_clients = num
        self.id = id
        lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lsock.bind((host, port))
        lsock.listen(num)
        print(f"Escutando em {(host, port)}")
        lsock.setblocking(False)
        events = selectors.EVENT_READ
        # registra socket da sala para monitoramento e multiplexação de I/O
        self.sel.register(lsock, events, data=None)

    def disconnect_client(self, client, full_server=False):
        # fecha conexão com cliente
        print(f"Fechando conexão com {client.addr}")
        if full_server:
            client.conn.send("Sala cheia!".encode())
        # retira cliente do monitoramento
        self.sel.unregister(client.conn)
        client.conn.close()
        self.clients = self.clients[:-1]

    def accept_client(self, sock):
        # aceita conexao do cliente
        conn, addr = sock.accept()
        client = types.SimpleNamespace(conn=conn, addr=addr, messages=b"")
        # adiciona cliente na lista de clientes da sala
        self.clients.append(client)
        print(f"Conexão aceita do {addr} na sala {self.id} {self.host}::{self.port}")
        conn.setblocking(False)
        data = 'client'
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        # registra socket do cliente para monitoramento e multiplexação de I/O
        self.sel.register(conn, events, data=data)
        if len(self.clients) > self.max_clients:
            self.disconnect_client(self.clients[-1], True)
        else:
            client.messages += b"Bem vindo a sala " + str(self.id).encode() + b"\n"

    def analyze_resp(self, recv, client):
        # analisa mensagem se é comando
        if recv == b"listar\n":
            message = b"Clientes conectados:\nVoce\n"
            clients = [(obj.addr[0], str(obj.addr[1])) for obj in self.clients if obj.conn != client.conn]
            clients = [" ".join(a) for a in clients]
            # adiciona lista de clientes conectados ao cliente que pediu
            if len(clients) > 0:
                client.messages += message + '\n'.join(clients).encode() + b"\n"
            else:
                client.messages += message
            return False
        else:
            return True

    def event_read(self, client):
        # recebe mensagem do socket cliente
        recv_data = client.conn.recv(1024)
        if recv_data:
            # verifica se mensagem recebida é comando ou mensagem
            # para outros clientes
            normal_chat = self.analyze_resp(recv_data, client)
            if normal_chat:
                # adiciona mensagem recebida nas mensagens de cada cliente
                clients = [obj for obj in self.clients if obj.conn != client.conn]
                for clt in clients:
                    clt.messages += str(client.addr[1]).encode() + b": " + recv_data
        else:
            self.disconnect_client(client)

    def event_write(self, client):
        # encaminha mensagem para o cliente caso possua mensagens
        # registradas para ele
        if client.messages and client.messages.decode() != '':
            sent = None
            sent = client.conn.send(client.messages)
            if sent:
                client.messages = client.messages[sent:]

    def manage_chat(self, sock, mask):
        client = None
        # da match do socket cliente com a lista de clientes da sala
        for obj in self.clients:
            if sock == obj.conn:
                client = obj
        if client:
            if mask & selectors.EVENT_READ:
                self.event_read(client)
            if mask & selectors.EVENT_WRITE:
                self.event_write(client)

    def run(self, server):
        try:
            while True:
                # verifica se server ainda está online
                if server() is False:
                    break
                # verifica se objeto socket está pronto para I/O
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    # aceita novo client na sala caso socket não esteja registrado
                    if key.data is None:
                        self.accept_client(key.fileobj)
                    # controla o chat com o socket do cliente conectado
                    else:
                        sock = key.fileobj
                        self.manage_chat(sock, mask)
        except:
            print("Fechando sala!")
        finally:
            self.sel.close()