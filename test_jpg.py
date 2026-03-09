from src.core import embed_watermark, extract_watermark
from src.utils import load_image
from PIL import Image

original = load_image("assets/zenitsu.jpg")
msg = "ID:aa6c2659-a94"

wm, key = embed_watermark(original, msg, 40)

# Simulate the FastAPI save flow
Image.fromarray(wm).save("static/uploads/stamped_test.jpg", quality=90)

extracted = extract_watermark(load_image("static/uploads/stamped_test.jpg"), key, 40, len(msg)*8)
print(f"Extracted: '{extracted}'")
print(f"Matches? {extracted == msg}")
