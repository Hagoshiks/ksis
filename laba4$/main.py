import socket
from threading import Thread
import requests
import http.client
import httpx

serverSocket = socket.socket()
localHostIp = "0.0.0.0"
port = 10000
proxie_dick = {"http": "http://localhost:10000"}
blocked_list = {"rutor.info"}

serverSocket.bind((localHostIp, port))
serverSocket.listen(10)
allThreads = set()
buffer = 4096

from collections import defaultdict

request_counts = defaultdict(int)
MAX_REQUESTS_PER_HOST = 10  # Максимальное количество запросов от одного клиента к одному хосту

def handle_client_connection(m_client_socket, _m_client_address):
    client_header = ""
    while True:
        data = m_client_socket.recv(buffer)
        try:
            client_header += data.decode("utf-8")
        except UnicodeDecodeError:
            break
        if len(data) < buffer:
            break
    list_header = list(map(str, client_header.strip().split("\r\n")))  # разделение заголовков
    if len(list_header) > 1 and "Host:" in list_header[1]:
        host = list(map(str, list_header[1].split(" ")))[1].strip()
    else:
        return
    if host in blocked_list:
        response = "404 NOT FOUND\r\n\r\nBlocked page"
        print(f"Хост: {host} Ответ: {response}")
        m_client_socket.send(response.encode("utf-8"))
        return
    if list(map(str, list_header[0].split(" ")))[0].strip() == "GET" or list(map(str, list_header[0].split(" ")))[0].strip() == "CONNECT" :
        handle_http_request(m_client_socket, list_header, host)


def handle_http_request(m_client_socket, list_header, host):
    try:
        try:
        # Получаем URL из заголовков запроса
            http_request = list(map(str, list_header[0].split(" ")))[1]
            if "https://" in http_request:
                response = "404 NOT FOUND\r\n\r\nhttps is not supported"
                print(f"Хост: {host} Ответ: {response}")
                m_client_socket.send(response.encode("utf-8"))
                return
            if "http://" not in http_request:
                http_request = "http://" + http_request
            print(f"Запрашиваемый URL: {http_request}")  # Отладочная информация
        # Выполняем HTTP-запрос
            with httpx.Client(timeout=httpx.Timeout(120), trust_env=False, limits=httpx.Limits(max_connections=5)) as client:
                # web_request = client.get(http_request)
                try:
                    web_request = client.get(http_request)
                    web_request.raise_for_status()  # Это выбросит исключение, если код ответа != 2xx
                except httpx.RequestError as e:
                    print(f"Ошибка при запросе: {e}")
                except httpx.HTTPStatusError as e:
                    print(f"Ошибка HTTP: {e.response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при выполнении запроса: {e}")
            return

        if web_request.status_code == 200:
            print(f"Хост: {host} Ответ: 200 OK")
            m_client_socket.sendall(web_request.content)
        else:
            response = "HTTP/1.1 404 Not Found\r\n\r\nPage not found"
            print(f"Хост: {host} Ответ: {response}")
            m_client_socket.send(response.encode("utf-8"))

    except Exception as e:
        response = "HTTP/1.1 500 Internal Server Error\r\n\r\n"
        print(f"Ошибка: {str(e)}")
        m_client_socket.send(response.encode("utf-8"))


def client_to_server_transfer(m_client_socket, web_server_socket):
    while True:
        client_data = m_client_socket.recv(buffer)
        web_server_socket.send(client_data)
        if len(client_data) < 1:
            break
while True:
    client_socket, client_address = serverSocket.accept()  # установка соединения с клиентом
    print(f"Соединение получено с Ip: {client_address[0]}, Port: {client_address[1]}")
    thread = Thread(target=handle_client_connection, args=(client_socket, client_address))
    allThreads.add(thread)
    thread.start()
