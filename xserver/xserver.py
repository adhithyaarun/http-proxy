import os
from http.server import SimpleHTTPRequestHandler
import socketserver
import threading
import time

threads = []

class HTTPCacheRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        filename = self.path.strip('/')
        try:
            f = open(os.path.join('./', filename), 'r')
        except Exception:
            self.send_response(404)
            self.end_headers()
            self.wfile.write('File not found\r\n\r\n'.encode())
            return

        if self.headers.get('If-Modified-Since', None):
            if os.path.isfile(os.path.join('./', filename)):
                a = time.gmtime(time.mktime(time.strptime(time.ctime(
                    os.path.getmtime(filename)), "%a %b %d %H:%M:%S %Y")))
                b = time.strptime(self.headers.get(
                    'If-Modified-Since', None), "%a, %d %b %Y %H:%M:%S GMT")
                if a < b:
                    self.send_response(304)
                    self.end_headers()
                else:
                    print(a > b)
                    self.send_response(200)
                    self.send_header('Cache-control', 'must-revalidate')
                    self.end_headers()
                    data = f.read()
                    self.wfile.write(data)
        else:
            self.send_response(200)
            self.send_header('Cache-control', 'must-revalidate')
            self.end_headers()
            f = open(os.path.join('./', filename), 'r')
            data = f.read()
            self.wfile.write(data.encode())

        return
    def do_POST(self):
        filename = self.path.strip('/')
        try:
            f = open(os.path.join('./', filename), 'r')
            data = f.read()
            self.wfile.write(data.encode())
        except Exception:
            self.send_response(404)
            self.end_headers()
            self.wfile.write('File not found\r\n\r\n'.encode())




http1 = socketserver.TCPServer(('', 20103), HTTPCacheRequestHandler)
# http2 = socketserver.TCPServer(('', 20105), HTTPCacheRequestHandler)
# http3 = socketserver.TCPServer(('', 20106), HTTPCacheRequestHandler)

# threads.append(threading.Thread(target=http1.serve_forever))
# threads.append(threading.Thread(target=http2.serve_forever))
# threads.append(threading.Thread(target=http3.serve_forever))

# for t in threads:
#     t.start()

# for t in threads:
#     t.join()
http1.serve_forever()
