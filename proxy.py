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
                (conn, addr) = self.server.accept()
                print('[log] Connection received from host address: {}'.format(addr))
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

            (server, port, filename) = self.requestInfo(request)
            print('Server: {}, Port: {}, File: {}'.format(server, port, filename))

            # Connect to server
            try:
                server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_sock.connect((server, port))            
            except Exception as e:
                print('[log] Error: {}'.format(e))
                conn.send('Unable to connect with server\n'.encode('utf-8'))
                conn.close()
                return
            
            if filename in os.listdir('./.cache'):
                server_sock.send('GET /' + filename + ' HTTP/1.1\r\nIf-Modified-Since: ' + time.ctime(os.path.getmtime('./.cache/' + filename)) + ' \r\n\r\n')
            else:
                server_sock.send('GET /' + filename + 'HTTP/1.1\r\n\r\n')

            server_res = str(server_sock.recv(BUFFER_SIZE))

            print(server_res)

            # Send request to server
            # Get response from server
            # Cache it
            
            # Send response
            conn.send('Acknowledgement\n'.encode('utf-8'))
        except Exception as e:
            print('[log] Error: {}'.format(e))
            conn.send('Error in connecting to server, try again later\n'.encode('utf-8'))
        conn.close()

    def requestInfo(self, request):
        url = request.split()[1]
        # line = request.split('\r\n')[0]
        # url = line.split()[1]

        no_protocol = url.find('://')
        
        if no_protocol == -1:
            host_url = url
        else:
            host_url = url[(no_protocol + 3):]

        port_start = host_url.find(':')
        port_end = host_url.find('/')

        if port_end == -1:
            port_end = len(host_url)

        server = ''
        port = -1

        if port_start == -1 or port_end < port_start:
            port = 20101
            server = host_url[:port_end]
        else:
            port = int((host_url[(port_start + 1):])[:port_end - port_start - 1])
            server = host_url[:port_start]
        
        try:
            filename = host_url.split('/')[1]
        except IndexError:
            filename = '/'

        return (server, port, filename)
            

proxy = Proxy(PORT, HOST)
if proxy.server:
    proxy.serverService()
