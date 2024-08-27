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