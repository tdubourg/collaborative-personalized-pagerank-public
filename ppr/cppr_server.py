import SocketServer
from BaseHTTPServer import BaseHTTPRequestHandler
# import SimpleHTTPServer
import json
import socket

class MyHTTPServer(SocketServer.ThreadingTCPServer):
    # c/p from BaseHTTPServer 
    allow_reuse_address = 1    # Seems to make sense in testing environment

    def server_bind(self):
        """Override server_bind to store the server name."""
        SocketServer.TCPServer.server_bind(self)
        host, port = self.socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port

class MyHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        # logging.warning("======= POST STARTED =======")
        # logging.warning(self.headers)
        # form = cgi.FieldStorage(
        #     fp=self.rfile,
        #     headers=self.headers,
        #     environ={'REQUEST_METHOD':'POST',
        #              'CONTENT_TYPE':self.headers['Content-Type'],
        #              })
        # logging.warning("======= POST VALUES =======")
        # for item in form.list:
            # logging.warning(item)
        # logging.warning("\n")
        print self.rfile.read()
        print self.__dict__

    # def handle(self):
    #     try:
    #         data = json.loads(self.request.recv(1024).strip())
    #         # process the data, i.e. print it:
    #         print data
    #         # send some 'ok' back
    #         self.request.sendall(json.dumps({"status": "BLORG!!", "scores": [42, 43, 44, 24]}))
    #     except Exception, e:
    #         print "Exception wile receiving message: ", e

server = MyHTTPServer(('127.0.0.1', 4242), MyHTTPRequestHandler)
server.serve_forever()