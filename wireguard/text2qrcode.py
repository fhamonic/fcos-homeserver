import os
import qrcode
import sys

if len(sys.argv) < 2:
    raise Exception("Usage: text2qrcode <input> [<output>]")

input_path = sys.argv[1]

if not os.path.exists(input_path):
    raise Exception(f"{input_path}: Input file not found.")

output_path = sys.argv[2] if len(sys.argv) > 2 else f"{input_path}.png"

with open(input_path, "r") as f:
    img = qrcode.make(f.read())
    img.save(output_path)
