import os
import SimpleHTTPServer
import SocketServer
import threading
import time

threads = []

class HTTPCacheRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def send_head(self):
        if self.command != "POST" and self.headers.get('If-Modified-Since', None):
            filename = self.path.strip("/")
            if os.path.isfile(os.path.join('./', filename)):
                a = time.strptime(time.ctime(
                    os.path.getmtime(filename)), "%a %b %d %H:%M:%S %Y")
                b = time.strptime(self.headers.get(
                    'If-Modified-Since', None), "%a %b  %d %H:%M:%S %Y")
                if a < b:
                    self.send_response(304)
                    self.end_headers()
                    f = open(os.path.join('./', filename), 'r')
                    line = str(f.read(4096))
                    while len(line) > 0:
                        self.wfile.write(line.encode('utf-8'))
                        line = str(f.read(4096))
                    return None
        return SimpleHTTPServer.SimpleHTTPRequestHandler.send_head(self)

    def end_headers(self):
        filename = self.path.strip('/')
        if filename == '2.binary':
            self.send_header('Cache-control', 'no-cache')
        else:
            self.send_header('Cache-control', 'must-revalidate')
        SimpleHTTPServer.SimpleHTTPRequestHandler.end_headers(self)


# Handler = SimpleHTTPServer.SimpleHTTPRequestHandler

http1 = SocketServer.TCPServer(("", 20101), HTTPCacheRequestHandler)
http2 = SocketServer.TCPServer(("", 20102), HTTPCacheRequestHandler)
http3 = SocketServer.TCPServer(("", 20103), HTTPCacheRequestHandler)

threads.append(threading.Thread(target=http1.serve_forever))
threads.append(threading.Thread(target=http2.serve_forever))
threads.append(threading.Thread(target=http3.serve_forever))

for t in threads:
    t.start()

for t in threads:
    t.join()
