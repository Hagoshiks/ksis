import time
import sys
import socket
from threading import Thread

class Server(Thread):
    BUFFER_SIZE = 512

    def __init__(self):
        super().__init__()

        # 1) Привязываемся к loopback
        self.IP = '127.0.0.1'
        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            self.port_ser = int(input("Введите порт для сервера: "))
            self.udpSocket.bind((self.IP, self.port_ser))
            print(f"Сервер запущен. IP сервера: {self.IP}:{self.port_ser}")
        except (ValueError, socket.error) as e:
            print(f"Не удалось запустить сервер: {e}")
            sys.exit(1)

        # 2) Храним кортежи (ip, port) вместо одних IP
        self.users = []  # список адресов активных клиентов

    def run(self):
        print(f"{self.getCurrentTime()}: Ждём сообщений на {self.IP}:{self.port_ser}")
        while True:
            try:
                data, addr = self.udpSocket.recvfrom(Server.BUFFER_SIZE)
            except socket.error as e:
                print(f"Сокет упал: {e}")
                break

            msg = data.decode()
            # Новый клиент
            if addr not in self.users:
                if msg == 'init':
                    self.users.append(addr)
                    # Отправляем только новому клиенту
                    self.sendRequest(f"Количество пользователей в сети: {len(self.users)}", addr)
                    print(f"Новый пользователь: {addr}")
                    # Уведомляем всех остальных
                    self.broadcast(f"К сети присоединился новый пользователь {addr[0]}", exclude=addr)
                # Иначе игнорируем всё, что не init
                continue

            # Выход клиента
            if msg == 'exit':
                self.users.remove(addr)
                print(f"Пользователь вышел: {addr}")
                self.broadcast(f"Из сети вышел пользователь {addr[0]}", exclude=addr)
                continue

            # Обычное сообщение
            text = f"{addr[0]}:{addr[1]} >> {msg}"
            print(f"{self.getCurrentTime()} {text}")
            self.broadcast(text, exclude=addr)

    def broadcast(self, message: str, exclude=None):
        """ Разослать всем в self.users, кроме exclude """
        for client in self.users:
            if client == exclude:
                continue
            self.sendRequest(message, client)

    def sendRequest(self, message: str, client):
        try:
            self.udpSocket.sendto(message.encode(), client)
        except ConnectionResetError:
            # Windows шлёт ICMP-port-unreachable, ловим и игнорируем
            pass
        except socket.error as e:
            print(f"Ошибка при отправке {client}: {e}")

    @staticmethod
    def getCurrentTime():
        return time.strftime("%H:%M:%S", time.localtime())


if __name__ == "__main__":
    server = Server()
    server.start()
