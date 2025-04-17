import socket
import sys
import argparse
from threading import Thread

class User(Thread):
    BUFFER_SIZE = 512

    def __init__(self, local_ip, local_port, server_ip, server_port):
        super().__init__()
        self.local_ip    = local_ip
        self.port_user   = local_port
        self.IP_udp      = server_ip
        self.port_server = server_port

        try:
            self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udpSocket.bind((self.local_ip, self.port_user))
        except socket.error as e:
            print(f"Ошибка создания сокета: {e}")
            sys.exit(1)

        self.daemon = True

    def run(self):
        # Отправляем init для регистрации
        self.sendRequest('init', (self.IP_udp, self.port_server))
        while True:
            try:
                data, _ = self.udpSocket.recvfrom(self.BUFFER_SIZE)
                print(data.decode())
            except socket.error as e:
                print(f"Ошибка при приёме данных: {e}")
                break

    def sendRequest(self, data, client):
        try:
            self.udpSocket.sendto(data.encode(), client)
        except socket.error as e:
            print(f"Ошибка при отправке запроса: {e}")
            sys.exit(1)


def find_free_loopback(local_port):
    """
    Находит первый доступный loopback IP 127.0.0.X, начиная с .2, для указанного порта
    """
    for i in range(2, 255):
        ip = f"127.0.0.{i}"
        try:
            temp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp.bind((ip, local_port))
            temp.close()
            return ip
        except OSError:
            continue
    print(f"Нет свободного loopback IP для порта {local_port}")
    sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UDP Client for chat with unique loopback IP per instance")
    parser.add_argument(
        "--local-port", type=int, required=True,
        help="Ваш локальный порт (1024–65535)"
    )
    parser.add_argument(
        "--server-port", type=int, required=True,
        help="Порт сервера"
    )
    args = parser.parse_args()

    # Валидация портов
    if not (1024 <= args.local_port <= 65535):
        print("Локальный порт должен быть 1024–65535.")
        sys.exit(1)
    if not (1024 <= args.server_port <= 65535):
        print("Порт сервера должен быть 1024–65535.")
        sys.exit(1)

    # Определяем уникальный loopback IP
    local_ip = find_free_loopback(args.local_port)
    server_ip = '127.0.0.1'

    client = User(
        local_ip=local_ip,
        local_port=args.local_port,
        server_ip=server_ip,
        server_port=args.server_port
    )
    client.start()

    print(f"Клиент запущен на {local_ip}:{args.local_port}, соединяюсь с сервером {server_ip}:{args.server_port}")

    while True:
        msg = input()
        client.sendRequest(msg, (server_ip, args.server_port))
        if msg.strip().lower() == 'exit':
            break