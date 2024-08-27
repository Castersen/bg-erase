from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
import socketserver
import argparse
from functools import lru_cache
from pathlib import Path
import io
from PIL import Image
import json
import base64

from transformers import AutoModelForImageSegmentation
import torch
import torch.nn.functional as F
from torchvision.transforms.functional import normalize
import numpy as np

MODEL = AutoModelForImageSegmentation.from_pretrained("briaai/RMBG-1.4",trust_remote_code=True)
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
MODEL.to(DEVICE)

def preprocess_image(im: np.ndarray, model_input_size: list) -> torch.Tensor:
    im_tensor = torch.tensor(im, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0)
    im_tensor = F.interpolate(im_tensor, size=model_input_size, mode='bilinear')
    return normalize(im_tensor / 255.0, [0.5] * 3, [1.0] * 3)

def postprocess_image(result: torch.Tensor, im_size: list)-> np.ndarray:
    result = F.interpolate(result, size=im_size, mode='bilinear').squeeze(0)
    result = (result - result.min()) / (result.max()-result.min())
    im_array = (result * 255).byte().permute(1,2,0).cpu().numpy().squeeze()
    return im_array

START_PAGE = 'index.html'

class ManPageHandler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def __send_200_headers(self, length: int, type='text/html; charset=UTF-8'):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', type)
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

    def do_GET(self):
        if self.path == '/favicon.ico':
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
        elif self.path.endswith('.css') or self.path.endswith('.js'):
            self.__send_page(Path(self.path).name)
        else:
            self.__send_page(START_PAGE)

    def do_POST(self):
        try:
            post_data = self.rfile.read(int(self.headers['Content-Length']))
            data = json.loads(post_data)

            image = Image.open(io.BytesIO(base64.b64decode(data['file'])))
            size = image.size[::-1]

            pd = preprocess_image(np.array(image), [1024, 1024]).to(DEVICE)
            with torch.no_grad():
                inf = MODEL(pd)
            result_image = postprocess_image(inf[0][0], size)

            pi = Image.fromarray(result_image)
            no_bg_image = Image.new('RGBA', pi.size, (0,0,0,0))
            no_bg_image.paste(image, mask=pi)

            client_image = io.BytesIO()
            no_bg_image.save(client_image, format="PNG", compress_level=1)
            image_bytes = client_image.getvalue()

            self.__send_200_headers(len(image_bytes), type='image/png')
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