from transformers import AutoModelForImageSegmentation
import torch
import torch.nn.functional as F
from torchvision.transforms.functional import normalize
import numpy as np
from PIL import Image
import io

class ImageProcessor:
    def __init__(self):
        print('Loading model this might take a while...')
        self.model = AutoModelForImageSegmentation.from_pretrained("briaai/RMBG-1.4",trust_remote_code=True)
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

    def preprocess_image(self, im: np.ndarray, model_input_size: list) -> torch.Tensor:
        im_tensor = torch.tensor(im, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0)
        im_tensor = F.interpolate(im_tensor, size=model_input_size, mode='bilinear')
        return normalize(im_tensor / 255.0, [0.5] * 3, [1.0] * 3)

    def postprocess_image(self, result: torch.Tensor, im_size: list)-> np.ndarray:
        result = F.interpolate(result, size=im_size, mode='bilinear').squeeze(0)
        result = (result - result.min()) / (result.max()-result.min())
        im_array = (result * 255).byte().permute(1,2,0).cpu().numpy().squeeze()
        return im_array

    def get_image_bytes(self, image_bytes: bytes) -> bytes:
        with Image.open(io.BytesIO(image_bytes)) as image:
            processed_image = self.preprocess_image(np.array(image), [1024,1024]).to(self.device)

            with torch.no_grad():
                results = self.model(processed_image)

            result_array = self.postprocess_image(results[0][0], image.size[::-1])
            result_image = Image.fromarray(result_array)

            transparent_image = Image.new('RGBA', result_image.size, (0,0,0,0))
            transparent_image.paste(image, mask=result_image)
            output_image = io.BytesIO()
            transparent_image.save(output_image, format="PNG", compress_level=1)

        return output_image.getvalue()