from pathlib import Path
from transformers import AutoModelForImageSegmentation
from torchvision import transforms
import torch
from PIL import Image, ImageFile
import io
import requests
import onnxruntime as ort

ONNX_CACHE_DIR = 'onnx_cache'
MODEL = 'briaai/RMBG-2.0'

transform_image = transforms.Compose([
    transforms.Resize((1024, 1024)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def load_onnx_model(repo_name: str, quantized: bool, cache_dir: str = ONNX_CACHE_DIR) -> ort.InferenceSession:
    model_filename = f"{repo_name.replace('/', '_')}_{'quantized' if quantized else 'model'}.onnx"
    cached_model_path = Path(cache_dir) / model_filename

    if not cached_model_path.exists():
        model_type = 'model_quantized.onnx' if quantized else 'model.onnx'
        model_url = f'https://huggingface.co/{repo_name}/resolve/main/onnx/{model_type}'
        print(f'Downloading model from {model_url}')
        response = requests.get(model_url)
        response.raise_for_status()
        cached_model_path.write_bytes(response.content)
    
    return ort.InferenceSession(str(cached_model_path))

def preprocess_image(im: ImageFile) -> torch.Tensor:
    return transform_image(im).unsqueeze(0)

class BaseImageProcessor:
    def do_inference(self, image: ImageFile):
        pass

class ONNXImageProcessor(BaseImageProcessor):
    def __init__(self, quantized: bool):
        print(f"Loading {'quantized' if quantized else ''} onnx model")
        self.model = load_onnx_model(MODEL, quantized)

    def do_inference(self, image):
        preprocessed_image = preprocess_image(image).numpy()
        results = self.model.run(['alphas'], {'pixel_values': preprocessed_image})
        return results[0].squeeze()

class TorchImageProcessor(BaseImageProcessor):
    def __init__(self):
        print('Loading model, this might take a while...')
        self.model = AutoModelForImageSegmentation.from_pretrained(MODEL,trust_remote_code=True)
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        print(f'Using {self.device}')
        torch.set_float32_matmul_precision(['high', 'highest'][0])
        self.model.to(self.device)
        self.model.eval()

    def do_inference(self, image):
        preprocessed_image = preprocess_image(image).to(self.device)
        with torch.no_grad():
            results = self.model(preprocessed_image)[-1].sigmoid().cpu()
        return results[0].squeeze()

def run_model(image_bytes: bytes, processor: BaseImageProcessor):
    with Image.open(io.BytesIO(image_bytes)) as image:
        if image.mode == 'RGBA':
            image = image.convert('RGB')

        result_array = processor.do_inference(image)
        image.putalpha((transforms.ToPILImage()(result_array)).resize(image.size))
        output_image = io.BytesIO()
        image.save(output_image, format="PNG", compress_level=1)

    return output_image.getvalue()