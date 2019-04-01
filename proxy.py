import os
import socket
import sys
import threading
import time

BUFFER_SIZE = 1024
MAX_CONNECTION = 25

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

        # if os.path.isdir('./.cache'):
        #     os.makedirs('./.cache')
        #     print('[log] Cache created')

    def serverService(self):
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((HOST, PORT))
        self.server.listen(MAX_CONNECTION)

        while True:
            try:
                conn, addr = self.server.accept()
                print('Connection received from host address: {}'.format(addr))
                # print(self.services)
                thread = threading.Thread(target=self.clientService, args=(conn, addr))
                thread.start()

                for service in self.services:
                    if not service['thread'].isAlive():
                        service['connection'].close()
                self.services = [service for service in self.services if service['thread'].isAlive()]
                service = {
                    'thread': thread,
                    'connection': conn,
                    'address': addr
                }
                self.services.append(service)
            except Exception as e:
                print('[log] Error: {}'.format(e))
                print('[log] Shutting down')
                for service in self.services:
                    service['connection'].close()
                self.server.close()
                sys.exit(1)
        self.server.close()

    def clientService(self, conn, addr):
        try:
            # HTTP request
            request = str(conn.recv(BUFFER_SIZE))
            print(request)
            # Send request to server
            # Get response from server
            # Cache it
            
            # Send response
            conn.send('Acknowledgement\n'.encode('utf-8'))
        except Exception as e:
            print('[log] Error: {}'.format(e))
        conn.close()
            

proxy = Proxy(PORT, HOST)
if proxy.server:
    proxy.serverService()
