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
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex(self.server_addr)
        print(f"Conexão bem-sucedida")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = types.SimpleNamespace(connid=connid, outb=b"", recv_total=0, messages=[])
        self.sel.register(sock, events, data=data)

    def event_read(self):
        while True:
            events = self.sel.select(timeout=None)
            for key, mask in events:
                if mask & selectors.EVENT_READ:
                    sock = key.fileobj
                    data = key.data
                    recv_data = sock.recv(1024)
                    if recv_data:
                        recv_data = recv_data.decode()
                        print(f">> {recv_data[:-1]}")
                        data.recv_total += len(recv_data)
                    else:
                        print("Desconectado da sala!")
                        self.alive = False
                        return

    def event_write(self):
        while True and self.alive:
            events = self.sel.select(timeout=None)
            for key, mask in events:
                if mask & selectors.EVENT_WRITE:
                    sock = key.fileobj
                    data = key.data
                    data.messages.append(sys.stdin.readline().encode())
                    if not data.outb and data.messages:
                        data.outb = data.messages.pop(0)
                    if data.outb:
                        sent = sock.send(data.outb)
                        data.outb = data.outb[sent:]


    def catch_except(self, args, /):
        print('catch_except: ', args)
        self.alive = False


    def run(self):
        try:
            print('Digite o que desejar, sendo que "listar" retorna todos os clientes na sala')
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
        print ("Correct usage: script, IP address, port number, connid") 
        exit()
    try:
        client = Client()
        client.run()
    except:
        print("Falha na criação do cliente")
    finally:
        exit()


