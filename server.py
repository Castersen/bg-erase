from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
import socketserver
import argparse
from functools import lru_cache
from pathlib import Path
import json
import base64
from bg_remover import ImageProcessor

PROCESSOR = ImageProcessor()
START_PAGE = 'index.html'

class ManPageHandler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def __send_200_headers(self, length: int, type='text/html; charset=UTF-8'):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', type)
        self.send_header('Content-Length', str(length))
        self.end_headers()

    @lru_cache(maxsize=32)
    def __get_page(self, page) -> bytes:
        with open(page, 'r') as fr:
            return fr.read().encode('utf-8')

    def __send_page(self, page) -> None:
        payload = self.__get_page(page)
        self.__send_200_headers(len(payload))
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == '/favicon.ico':
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
        elif self.path.endswith('.css') or self.path.endswith('.js'):
            self.__send_page(Path(self.path).name)
        else:
            self.__send_page(START_PAGE)

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        image_bytes = PROCESSOR.get_image_bytes(base64.b64decode(data['file']))
        self.__send_200_headers(len(image_bytes), type='image/png')
        self.wfile.write(image_bytes)

def main():
    port = 8001
    host = 'localhost'
    allow_reuse = False

    parser = argparse.ArgumentParser(description='Remove BG Options')
    parser.add_argument('-p', '--port', type=int, help='Set port')
    parser.add_argument('-i', '--host', type=str, help='Set host')
    parser.add_argument('-a', '--allow', action='store_true', help='Allow reuse of address')

    args = parser.parse_args()
    if (args.port):
        port = args.port
    if (args.host):
        host = args.host
    if (args.allow):
        allow_reuse = args.allow

    class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        daemon_threads = True
        allow_reuse_address = allow_reuse

    print(f'Starting server at {host} port {port}')
    with ThreadingTCPServer((host, port), ManPageHandler) as server:
        server.serve_forever()

if __name__ == '__main__':
    main()