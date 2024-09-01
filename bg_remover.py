from typing import List
from pathlib import Path
from transformers import AutoModelForImageSegmentation
import torch
import torch.nn.functional as F
from torchvision.transforms.functional import normalize
import numpy as np
from PIL import Image
import io
import requests
import onnxruntime as ort

ONNX_CACHE_DIR = 'onnx_cache'

def load_onnx_model(repo_name: str, cache_dir: str = ONNX_CACHE_DIR) -> ort.InferenceSession:
    model_filename = f"{repo_name.replace('/', '_')}_quantized.onnx"
    cached_model_path = Path(cache_dir) / model_filename

    if not cached_model_path.exists():
        model_url = f'https://huggingface.co/{repo_name}/resolve/main/onnx/model_quantized.onnx'
        print(f'Downloading model from {model_url}')
        response = requests.get(model_url)
        response.raise_for_status()
        cached_model_path.write_bytes(response.content)
    
    return ort.InferenceSession(str(cached_model_path))

def preprocess_image(im: np.ndarray, model_input_size: list) -> torch.Tensor:
    im_tensor = torch.tensor(im, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0)
    im_tensor = F.interpolate(im_tensor, size=model_input_size, mode='bilinear')
    return normalize(im_tensor / 255.0, [0.5, 0.5, 0.5], [1.0, 1.0, 1.0])

def postprocess_image(result: torch.Tensor, im_size: list)-> np.ndarray:
    result = F.interpolate(result, size=im_size, mode='bilinear').squeeze(0)
    return (result.clamp(0,1) * 255).byte().permute(1,2,0).cpu().numpy().squeeze()

class BaseImageProcessor:
    def do_inference(self, image: np.ndarray, image_size: List[int], model_size: List[int]):
        pass

class ONNXImageProcessor(BaseImageProcessor):
    def __init__(self):
        print('Loading quantized onnx model')
        self.model = load_onnx_model('briaai/RMBG-1.4')

    def do_inference(self, image, image_size, model_size):
        preprocessed_image = preprocess_image(image, model_size)
        results = self.model.run(['output'], {'input': preprocessed_image.numpy()})[0]
        return postprocess_image(torch.Tensor(results), image_size)

class TorchImageProcessor(BaseImageProcessor):
    def __init__(self):
        print('Loading model, this might take a while...')
        self.model = AutoModelForImageSegmentation.from_pretrained("briaai/RMBG-1.4",trust_remote_code=True)
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        print(f'Using {self.device}')
        self.model.to(self.device)
        self.model.eval()

    def do_inference(self, image, image_size, model_size):
        preprocessed_image = preprocess_image(image, model_size).to(self.device)
        with torch.no_grad():
            results = self.model(preprocessed_image)
        return postprocess_image(results[0][0], image_size)

def run_model(image_bytes: bytes, processor: BaseImageProcessor):
    with Image.open(io.BytesIO(image_bytes)) as image:
        if image.mode == 'RGBA':
            image = image.convert('RGB')

        result_array = processor.do_inference(np.array(image), image.size[::-1], [1024,1024]) 
        result_image = Image.fromarray(result_array)
        transparent_image = Image.new('RGBA', result_image.size, (0,0,0,0))
        transparent_image.paste(image, mask=result_image)
        output_image = io.BytesIO()
        transparent_image.save(output_image, format="PNG", compress_level=1)

    return output_image.getvalue()