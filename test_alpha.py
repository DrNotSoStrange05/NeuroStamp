from src.core import embed_watermark, extract_watermark
from src.utils import load_image
from PIL import Image

original = load_image("assets/zenitsu.jpg")
msg = "ID:aa6c2659-a94"
wm, key = embed_watermark(original, msg, 40)
Image.fromarray(wm).save("static/uploads/test_alpha.jpg", quality=75)
ext = extract_watermark(load_image("static/uploads/test_alpha.jpg"), key, 40, len(msg)*8)
print("Alpha=40:", ext)

wm, key = embed_watermark(original, msg, 100)
Image.fromarray(wm).save("static/uploads/test_alpha100.jpg", quality=75)
ext = extract_watermark(load_image("static/uploads/test_alpha100.jpg"), key, 100, len(msg)*8)
print("Alpha=100:", ext)
