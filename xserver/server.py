import os
import time
import SocketServer
import SimpleHTTPServer
import threading


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


# servers = []
# for port in range(20101, 20200):
    # servers.append(SocketServer.ThreadingTCPServer(
    #     ("", port), HTTPCacheRequestHandler))
    # print(servers[-1])
    # # servers[-1].allow_reuse_address = True
    # print "Serving on port", port
    # servers[-1].serve_forever()

threads = []
s = SocketServer.ThreadingTCPServer(
    ("", 20101), HTTPCacheRequestHandler)
print(s)
# s[-1].allow_reuse_address = True
print("Serving on 20101", 20101)
t1 = threading.Thread(target=s.serve_forever())
threads.append(t1)

s1 = SocketServer.ThreadingTCPServer(
    ("", 20102), HTTPCacheRequestHandler)
print(s1)
# s[-1].allow_reuse_address = True
print("Serving on 20102", 20102)
t2 = threading.Thread(target=s1.serve_forever())
threads.append(t2)

s2 = SocketServer.ThreadingTCPServer(
    ("", 20103), HTTPCacheRequestHandler)
print(s2)
# s[-1].allow_reuse_address = True
print("Serving on 20103", 20103)
t3 = threading.Thread(target=s2.serve_forever())
threads.append(t3)

print(threads)
for t in threads:
    t.start()

for t in threads:
    t.join()
