import socket
import threading
import time

PORT = 20100
HOST = ''

class Proxy:
    def __init__(self, port, hostname):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print('[log] Socket successfully created')
        except socket.error as err:
            print('[log] Socket cration error: {}'.format(err))
        self.services = []

    def serverService(self):
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((HOST, PORT))
        self.server.listen(10)

        while True:
            conn, addr = self.server.accept()
            print('Connection received from host address: {}'.format(addr))
            print(self.services)
            thread = threading.Thread(target=self.clientService)
            thread.start()
            self.services = [service for service in self.services if service.isAlive()]
            self.services.append(thread)
            # Remaining logic
            conn.close()

    def clientService(self):
        # message = self.server.recv(1024)
        print('Client service called')
            

proxy = Proxy(PORT, HOST)
if proxy.server:
    proxy.serverService()
