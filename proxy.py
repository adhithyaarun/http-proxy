'''Proxy Server'''
import os
import queue
import socket
import sys
import threading
import time

BUFFER_SIZE = 4096
MAX_CONNECTION = 25
ALLOWED_ACTIONS = ['GET', 'POST']
CACHE_SIZE = 3

PORT = 20100
HOST = ''

class Proxy:
    def __init__(self, port, hostname):
        '''Constructor for Proxy Server'''
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print('[log] Socket successfully created')
        except socket.error as err:
            print('[log] Socket cration error: {}'.format(err))
        
        self.services = []
        self.cache = queue.Queue(maxsize=CACHE_SIZE)

        # if os.path.isdir('./.cache'):
        #     os.makedirs('./.cache')
        #     print('[log] Cache created')

    def serverService(self):
        '''Server end of the Proxy Server, 
        that will handle requests from clients'''
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((HOST, PORT))
        self.server.listen(MAX_CONNECTION)

        while True:
            try:
                (conn, addr) = self.server.accept()
                print('[log] Connection received from host: {}, port: {}'.format(addr[0], addr[1]))
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
        '''Client end of the Proxy Server, that will make requests to servers, 
        get data and send to the client'''
        if addr[1] < 20000 or addr[1] > 20099:
            conn.send('Access denied.\n'.encode('utf-8'))
            conn.close()
            print('[log] Connection from host: {}, port: {} denied'.format(addr[0], addr[1]))
            return

        try:
            # HTTP request
            request = str(conn.recv(BUFFER_SIZE))

            (req_type, server, port, filename) = self.requestInfo(request)
            # print('Request: {}, Server: {}, Port: {}, File: {}'.format(req_type, server, port, filename))

            # Reject requests that are not GET or POST
            if req_type not in ALLOWED_ACTIONS:
                conn.send('Invalid action\n'.encode('utf-8'))
                conn.close()
                print('[log] {} request from host: {}, port: {} denied'.format(req_type, addr[0], addr[1]))
                return
            
            if port > 20200 or port < 20101:
                conn.send('Invalid action\n'.encode('utf-8'))
                conn.close()
                print('[log] Request from host: {}, port: {} to host: {}, port: {} denied'.format(addr[0], addr[1], server, port))
                return

            # Connect to server
            try:
                server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_sock.connect((server, port))            
            except Exception as e:
                print('[log] Error: {}'.format(e))
                conn.send('Unable to connect with server\n'.encode('utf-8'))
                conn.close()
                return
            
            # Send request to server
            if str(filename + server + port) in os.listdir('./.cache'):
                server_sock.send('GET /' + filename + ' HTTP/1.1\r\nIf-Modified-Since: ' + time.ctime(os.path.getmtime('./.cache/' + str(filename + server + port))) + ' \r\n\r\n')
            else:
                server_sock.send('GET /' + filename + 'HTTP/1.1\r\n\r\n')

            # Get response from server
            response = str(server_sock.recv(BUFFER_SIZE))

            print(response)
            
            # Use cache, or update cache
            if response.find('200') != -1:
                f = open(os.path.join('./.cache/', str(filename + server + port)), 'wb')
                while True:
                    if len(response) > 0:
                        f.write(response.encode('utf-8'))
                        conn.send(response.encode('utf-8'))
                        # res_size = float(len(response)) / 1024
                        # print('[log] Request serviced by server \n\tfile: {}\n\tsize: {}'.format(filename, res_size))
                        response = str(server_sock.recv(BUFFER_SIZE))
                    else:
                        break
                f.close()
            elif response.find('304') != -1:
                f = open(os.path.join('./.cache/', str(filename + server + port)), 'rb')
                line = f.read(BUFFER_SIZE)
                while line:
                    conn.send(line)
                    # res_size = float(len(line) / 1024)
                    # print('[log] Request serviced from cache \n\tfile: {}\n\tsize: {}'.format(filename, res_size))
                    line = f.read(BUFFER_SIZE)
                f.close()
            else:
                print('[log] Response from server: {}'.format(response))

            server_sock.close()
            # conn.send('Acknowledgement\n'.encode('utf-8'))
        except Exception as e:
            print('[log] Error: {}'.format(e))
            conn.send('Error in connecting to server, try again later\n'.encode('utf-8'))
        conn.close()

    def requestInfo(self, request):
        '''Function to extract server, port and filename requested from HTTP request'''
        req_type = request.split()[0][2:]
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

        return (req_type, server, port, filename)
            

proxy = Proxy(PORT, HOST)
if proxy.server:
    proxy.serverService()
