# BG Erase (Python)

![Python Version](https://img.shields.io/badge/python-3.8-brightgreen.svg)

Uses the [briaai/BRIA_RMBG-1.4 model](https://huggingface.co/briaai/RMBG-1.4) for image background removal.

## Dependencies 

* python3.8+  
* Install required packages:

`pip install -qr requirements.txt`

## How to use

**Run server using PyTorch (recommended for CUDA-enabled devices):**

`python3 server.py`

This will load the full model using PyTorch and starts a TCP server on port 8001.

**Run server with ONNX (recommended for CPU-only devices):**

`python3 server.py --onnx`

**Change the port:**

`python3 server.py -p [port]`

**See all options:**

`python3 server.py -h`