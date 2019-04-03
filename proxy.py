'''Proxy Server'''
import os
import socket
import sys
import threading
import time
import ipaddress

BUFFER_SIZE = 1024
MAX_CONNECTION = 25
ALLOWED_ACTIONS = ['GET', 'POST']
CACHE_SIZE = 3
TIMEOUT = 300

PORT = 20100
HOST = ''

BLACK_LIST = []
blocked = []
blocked_ips = []
admins = []
BLACKLIST_FILE = "blacklist.txt"
USERNAME_PASSWORD_FILE = "username_password.txt"


class Proxy:
    def __init__(self, port, hostname):
        '''Constructor for Proxy Server'''
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print('[log] Socket successfully created')
        except socket.error as err:
            print('[log] Socket cration error: {}'.format(err))

        self.services = []
        self.cache = {}
        self.NEXT_CACHE = 0
        self.key = ['', '', '']
        self.cached = {}
        self.headers = {}
        self.updates = {}

    def serverService(self):
        '''Server end of the Proxy Server,
        that will handle requests from clients'''
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((HOST, PORT))
        self.server.listen(MAX_CONNECTION)

        while True:
            try:
                (conn, addr) = self.server.accept()
                print('[log] Connection received from host: {}, port: {}'.format(
                    addr[0], addr[1]))
                thread = threading.Thread(
                    target=self.clientService, args=(conn, addr))
                thread.start()

                for service in self.services:
                    if not service['thread'].isAlive():
                        service['connection'].close()
                self.services = [
                    service for service in self.services if service['thread'].isAlive()]
                service = {
                    'thread': thread,
                    'connection': conn,
                    'address': addr
                }
                self.services.append(service)
            except Exception as e:
                print('[log] Error: {}'.format(str(e)))
                print('[log] Shutting down')
                for service in self.services:
                    service['connection'].close()
                self.server.close()
                sys.exit(1)
        self.server.close()

    def clientService(self, conn, addr):
        '''Client end of the Proxy Server, that will make requests to servers,
        get data and send to the client'''
        # Constrain requests from within IIIT only
        if addr[1] < 20000 or addr[1] > 20099:
            conn.send('HTTP/1.1 401 Access denied'.encode('utf-8'))
            conn.close()
            print('[log] Connection from host: {}, port: {} denied'.format(
                addr[0], addr[1]))
            return

        try:
            # HTTP request
            request = str(conn.recv(BUFFER_SIZE))

            (req_type, server, port, filename) = self.requestInfo(request)
            # print('Request: {}, Server: {}, Port: {}, File: {}'.format(req_type, server, port, filename))

            # Reject requests that are not GET or POST
            if req_type not in ALLOWED_ACTIONS:
                conn.send('HTTP/1.1 400 Bad request'.encode('utf-8'))
                conn.close()
                print('[log] {} request from host: {}, port: {} denied'.format(
                    req_type, addr[0], addr[1]))
                return

            # Invalid port
            if port > 20200 or port < 20101:
                conn.send('HTTP/1.1 403 Forbidden'.encode('utf-8'))
                conn.close()
                print('[log] Request from host: {}, port: {} to host: {}, port: {} denied'.format(
                    addr[0], addr[1], server, port))
                return
            # Checking if blacklisted
            if self.check_blacklist(server, port):
                print('[log] Request from host: {}, port: {} to host: {}, port: {} denied, blacklisted domain'.format(
                    addr[0], addr[1], server, port))
                return

            try:
                server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_sock.connect((server, port))
            except Exception as e:
                print('[log] Error: {}'.format(str(e)))
                conn.send('HTTP/1.1 500 Internal server error'.encode('utf-8'))
                conn.close()
                return
            print('Headers:')
            print(self.headers)
            # Send request to server
            if filename + str(server) + str(port) in self.key:
                if 'must-revalidate' in self.headers[filename + str(server) + str(port)]:
                    print('MUST REVALIDATE')
                    http_request = 'GET /' + filename + ' HTTP/1.1\r\nIf-Modified-Since: ' + \
                        self.updates[filename +
                                     str(server) + str(port)] + '\r\n\r\n'
                    server_sock.send(http_request.encode('utf-8'))
                else:
                    content = self.cached[filename + str(server) + str(port)]
                    print(content)
                    print(
                        '[log] Request serviced from cache, file: {}'.format(filename))
                    conn.send(str('HTTP/1.1 200 OK\r\n\r\n' +
                                  content).encode('utf-8'))
                    conn.close()
                    server_sock.close()
                    return
            else:
                http_request = 'GET /' + filename + ' HTTP/1.1\r\n\r\n'
                server_sock.send(http_request.encode('utf-8'))

            # Get response from server
            response = server_sock.recv(BUFFER_SIZE).decode()
            print(response)

            if filename + str(server) + str(port) not in self.cache:
                self.cache[filename + str(server) + str(port)
                           ] = {'time': time.time(), 'count': 0}
            elif str(filename + str(server) + str(port)) not in self.key:
                if time.time() - self.cache[filename + str(server) + str(port)]['time'] > TIMEOUT:
                    self.cache[filename + str(server) + str(port)
                               ] = {'time': time.time(), 'count': 0}
                else:
                    self.cache[filename +
                               str(server) + str(port)]['count'] += 1

            # Use cache, or update cache
            if response.find('200') != -1:
                res = response
                if self.cache[filename + str(server) + str(port)]['count'] > 1:
                    if filename + str(server) + str(port) not in self.key and self.key[self.NEXT_CACHE] != '':
                        self.cached.pop(self.key[self.NEXT_CACHE])
                        self.headers.pop(self.key[self.NEXT_CACHE])
                        self.updates.pop(self.key[self.NEXT_CACHE])
                    self.key[self.NEXT_CACHE] = filename + \
                        str(server) + str(port)
                    self.NEXT_CACHE = (self.NEXT_CACHE + 1) % CACHE_SIZE

                # Headers
                content = ''
                while True:
                    response = server_sock.recv(BUFFER_SIZE).decode()
                    print(response)
                    if len(response) > 0:
                        content += response
                    else:
                        break
                print(content)
                print('[log] Request serviced by server, file: {}'.format(filename))
                if self.cache[filename + str(server) + str(port)]['count'] > 1:
                    self.cached[filename + str(server) + str(port)] = content
                    self.headers[filename + str(server) + str(port)] = res
                    self.updates[filename + str(server) + str(port)] = res.split('\r\n')[
                        2].split(':', 1)[1].lstrip()
                    print(self.updates[filename + str(server) + str(port)])
                conn.send(str('HTTP/1.1 200 OK\r\n\r\n' +
                              content).encode('utf-8'))

            elif response.find('304') != -1:
                content = self.cached[filename + str(server) + str(port)]
                print('[log] Request serviced from cache, file: {}'.format(filename))
                conn.send(str('HTTP/1.1 200 OK\r\n\r\n' +
                              content).encode('utf-8'))

            elif response.find('404') != -1:
                conn.send('HTTP/1.1 404 File not found\r\n\r\n'.encode('utf-8'))
                conn.close()
                print('[log] Requested file not found')
                return

            else:
                print('[log] Response from server: {}'.format(response))

            server_sock.close()
            conn.close()
        except Exception as e:
            print('[log] Error: {}'.format(str(e)))
            conn.send(
                'Error in connecting to server, try again later\n'.encode('utf-8'))
            conn.close()

    def check_blacklist(self, requested_server, requested_port):
        # if not (details["server_url"] + ":" + str(details["server_port"])) in blocked:
        #     return False
        # if not details["auth_b64"]:
        #     return True
        # if details["auth_b64"] in admins:
        #     return False
        # return True
        print("checking")
        print(requested_server+str(requested_port))
        req = requested_server+":"+str(requested_port)
        if req in blocked_ips:
            u = input("Enter username")
            p = input("Enter password")
            print(u)
            print(p)
            if u == username and p == password:
                return False
            return True
        return False

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
            port = int((host_url[(port_start + 1):])
                       [:port_end - port_start - 1])
            server = host_url[:port_start]

        try:
            filename = host_url.split('/')[1]
        except IndexError:
            filename = '/'

        return (req_type, server, port, filename)


# # Generating the blacklist
# f = open('./blacklist.txt', 'r')
# blacklist = f.read()
# entries = blacklist.split('\n')
# while len(blacklist) > 0:
#     for entry in entries:
#         if len(entry) > 0:
#             info = entry.split()
#             BLACK_LIST.append((info[0], info[1]))
#     blacklist = f.read()
#     entries = blacklist.split('\n')
# f.close()

f = open(BLACKLIST_FILE, "rb")
data = ""
while True:
    chunk = f.read()
    if not len(chunk):
        break
    data += str(chunk)
f.close()
blocked = data.split("\\n")
blocked[0] = blocked[0][2:]
blocked = blocked[:-1]

for b in blocked:
    net4 = ipaddress.ip_network(b.split(":")[0])
    port = b.split(":")[1]
    for x in net4.hosts():
        blocked_ips.append(str(x)+":"+port)


f = open(USERNAME_PASSWORD_FILE, "rb")
data = ""
while True:
    chunk = f.read()
    if not len(chunk):
        break
    data += str(chunk)
f.close()
data = data.splitlines()
for d in data:
    # admins.append(base64.b64encode(d))
    admins.append(d[2:-1].split("\\n")[:-1])
username = admins[0][0]
password = admins[0][1]

# print(blocked)
# print()
# print(admins)
# print()
# # print(blocked_ips)
# print(username)
# print(password)

proxy = Proxy(PORT, HOST)
if proxy.server:
    proxy.serverService()
