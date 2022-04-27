import types
import threading
from room import Room
class Server:
    server_up = True

    def __init__(self):
        self.room_threads = []

    def get_all_rooms(self):
        rooms = [room.id + " " + room.addr for room in self.room_threads]
        if len(rooms) == 0:
            print("Nenhuma sala existente")
        else:
            print("Salas:")
            print("\n".join(rooms))

    def run(self):
        try:
            print("-- Escreva 'listar' para receber todas as salas ativas")
            print("-- Digite o IP, porta, num_max pessoas e identificador a qualquer momento para criar uma sala")
            while True:
                try:
                    text = input("-> ")
                    if text == "listar":
                        self.get_all_rooms()
                    else:
                        host, port, num, id = text.split()
                        room = Room(host, int(port), int(num), id)
                        thread = threading.Thread(target = room.run, args = (lambda : self.server_up, ))
                        thread.start()
                        room_map = types.SimpleNamespace(id=id, thread=thread, addr=host + " " + port)
                        self.room_threads.append(room_map)
                except KeyboardInterrupt:
                    break
                except:
                    print('Falha na criação da sala')
                    continue
        except KeyboardInterrupt:
            print("Fechando...")
            self.server_up = False
            for room_map in self.room_threads:
                room_map.thread.join()
        finally:
            exit()

if __name__ == '__main__':
    server = Server()
    server.run()
