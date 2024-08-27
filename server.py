from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
import socketserver
import argparse
from functools import lru_cache
from pathlib import Path
import io as py_io
from PIL import Image
import json
import base64
import numpy as np
from bg_remover import MODEL, DEVICE, preprocess_image, postprocess_image

START_PAGE = 'index.html'

class ManPageHandler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def __send_200_headers(self, length: int):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', 'text/html; charset=UTF-8')
        self.send_header('Content-Length', str(length))
        self.end_headers()

    def __send_200_headers_image(self, length: int):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', 'image/png')
        self.send_header('Content-Length', str(length))
        self.end_headers()

    # @lru_cache(maxsize=32)
    def __get_page(self, page) -> bytes:
        with open(page, 'r') as fr:
            return fr.read().encode('utf-8')

    def __send_page(self, page) -> None:
        payload = self.__get_page(page)
        self.__send_200_headers(len(payload))
        self.wfile.write(payload)

    def __get_name(self) -> str:
        return Path(self.path).name

    def do_GET(self):
        if self.path == '/favicon.ico':
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
        elif self.path.endswith('.css') or self.path.endswith('.js'):
            self.__send_page(self.__get_name())
        else:
            self.__send_page(START_PAGE)
            return

    def do_POST(self):
        try:
            post_data = self.rfile.read(int(self.headers['Content-Length']))
            data = json.loads(post_data)

            image = Image.open(py_io.BytesIO(base64.b64decode(data['file'])))
            size = image.size[::-1]

            pd = preprocess_image(np.array(image), [1024, 1024]).to(DEVICE)
            result_image = postprocess_image(MODEL(pd)[0][0], size)

            pi = Image.fromarray(result_image)
            no_bg_image = Image.new('RGBA', pi.size, (0,0,0,0))
            no_bg_image.paste(image, mask=pi)

            client_image = py_io.BytesIO()
            no_bg_image.save(client_image, format="PNG")
            image_bytes = client_image.getvalue()

            self.__send_200_headers_image(len(image_bytes))
            self.wfile.write(image_bytes)
        except Exception as e:
            print(f'Error processing image: {e}')

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