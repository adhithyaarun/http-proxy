import SimpleHTTPServer
import SocketServer
import threading

threads = []


class HTTPCacheRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def send_head(self):
        if self.command != "POST" and self.headers.get('If-Modified-Since', None):
            filename = self.path.strip("/")
            if os.path.isfile(filename):
                a = time.strptime(time.ctime(
                    os.path.getmtime(filename)), "%a %b %d %H:%M:%S %Y")
                b = time.strptime(self.headers.get(
                    'If-Modified-Since', None), "%a %b  %d %H:%M:%S %Y")
                if a < b:
                    self.send_response(304)
                    self.end_headers()
                    return None
        return SimpleHTTPServer.SimpleHTTPRequestHandler.send_head(self)

    def end_headers(self):
        filename = self.path.strip("/")
        if filename == "2.binary":
            self.send_header('Cache-control', 'no-cache')
        else:
            self.send_header('Cache-control', 'must-revalidate')
        SimpleHTTPServer.SimpleHTTPRequestHandler.end_headers(self)


# Handler = SimpleHTTPServer.SimpleHTTPRequestHandler

http1 = SocketServer.TCPServer(("", 20101), HTTPCacheRequestHandler)
http2 = SocketServer.TCPServer(("", 20102), HTTPCacheRequestHandler)
http3 = SocketServer.TCPServer(("", 20103), HTTPCacheRequestHandler)
print "serving at port"

threads.append(threading.Thread(target=http1.serve_forever))
threads.append(threading.Thread(target=http2.serve_forever))
threads.append(threading.Thread(target=http3.serve_forever))

print(threads)
for t in threads:
    t.start()

for t in threads:
    t.join()
