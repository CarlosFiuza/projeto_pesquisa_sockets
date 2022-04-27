import socket
import selectors
import types

class Room:
    def __init__(self, host, port, num, id):
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
        self.sel.register(lsock, selectors.EVENT_READ, data=None)

    def disconnect_client(self, client, full_server=False):
        print(f"Fechando conexão com {client.addr}")
        if full_server:
            client.conn.send("Sala cheia!".encode())
        self.sel.unregister(client.conn)
        client.conn.close()
        del self.clients[:-1]

    def accept_wrapper(self, sock):
        conn, addr = sock.accept()
        client = types.SimpleNamespace(conn=conn, addr=addr, messages=b"")
        self.clients.append(client)
        print(f"Conexão aceita do {addr} na sala {self.id} {self.host}::{self.port}")
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=data)
        if len(self.clients) > self.max_clients:
            self.disconnect_client(self.clients[-1], True)
        else:
            client.messages += b"Bem vindo a sala " + str(self.id).encode() + b"\n"

    def analyze_recv(self, recv, client):
        if recv == b"listar\n":
            message = b"Clientes conectados:\nVoce\n"
            clients = [(obj.addr[0], str(obj.addr[1])) for obj in self.clients if obj.conn != client.conn]
            clients = [" ".join(a) for a in clients]
            if len(clients) > 0:
                client.messages += message + b"\n" + '\n'.join(clients).encode()
            else:
                client.messages += message
            return False
        else:
            return True

    def event_read(self, client):
        recv_data = client.conn.recv(1024)
        if recv_data:
            normal_chat = self.analyze_recv(recv_data, client)
            if normal_chat:
                clients = [obj for obj in self.clients if obj.conn != client.conn]
                for clt in clients:
                    clt.messages += str(client.addr[1]).encode() + b": " + recv_data
        else:
            self.disconnect_client(client)

    def event_write(self, client):
        if client.messages and client.messages.decode() != '':
            sent = None
            sent = client.conn.send(client.messages)
            if sent:
                client.messages = client.messages[sent:]

    def service_connection(self, key, mask):
        sock = key.fileobj
        client = None
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
                if server() is False:
                    break
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        self.service_connection(key, mask)
        except:
            print("Fechando sala!")
        finally:
            self.sel.close()