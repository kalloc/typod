import SimpleHTTPServer
import SocketServer
import sys
import os
import logging

from typo import TypoDefault

CWD = os.path.dirname(os.path.realpath(__file__))
correcter = TypoDefault(CWD + '/test.index')


class Handler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.getheader('content-length'))
            data = self.rfile.read(length).decode('utf-8')
            corrected, is_converted = correcter.suggestion(data.strip())
            self.send_response(200, "OK")
            self.send_header('Content-Type', 'text/plain; charset=UTF-8')
            self.end_headers()
            self.wfile.write(corrected.encode('utf-8'))
            self.finish()
        except Exception as exc:
            logging.error(
                "{0}/{1}({2})".format(
                    type(self).__name__, type(exc).__name__, str(exc)))


if len(sys.argv) > 1:
    PORT = int(sys.argv[1])
else:
    PORT = 8000

print "serving at port", PORT
httpd = SocketServer.TCPServer(("", PORT), Handler)
httpd.serve_forever()
