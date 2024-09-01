from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
import socketserver
import argparse
from functools import lru_cache
from pathlib import Path
import json
import base64
from bg_remover import BaseImageProcessor, ONNXImageProcessor, TorchImageProcessor, run_model

START_PAGE = 'index.html'

class BGRemoverHandler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def __init__(self, *args, processor: BaseImageProcessor=None, **kwargs) -> None:
        self.processor = processor
        super().__init__(*args, **kwargs)

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
        else:
            file_path = Path(self.path).name or Path(START_PAGE)
            self.__send_page(file_path)

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        image_bytes = run_model(base64.b64decode(data['file']), self.processor)
        self.__send_200_headers(len(image_bytes), type='image/png')
        self.wfile.write(image_bytes)

def main():
    parser = argparse.ArgumentParser(description='Remove BG Options')
    parser.add_argument('-p', '--port', type=int, default=8001, help='Set port')
    parser.add_argument('-i', '--host', type=str, default='localhost', help='Set host')
    parser.add_argument('-a', '--allow-reuse', action='store_true', help='Allow reuse of address')
    parser.add_argument('-o', '--onnx', action='store_true', help='Run model using on cpu using onnx runtime')

    args = parser.parse_args()
    processor = ONNXImageProcessor() if args.onnx else TorchImageProcessor()

    class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        daemon_threads = True
        allow_reuse_address = args.allow_reuse

    print(f'Starting server at {args.host} port {args.port}')
    with ThreadingTCPServer((args.host, args.port), 
                            lambda *a, **kw: BGRemoverHandler(*a, processor=processor, **kw)) as server:
        server.serve_forever()

if __name__ == '__main__':
    main()