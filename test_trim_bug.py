from src.core import embed_watermark, extract_watermark
from src.utils import load_image
from PIL import Image
import numpy as np

# Let's create a small dummy image of ODD size
arr = np.random.randint(0, 255, (225, 225, 3), dtype=np.uint8)
Image.fromarray(arr).save("test_odd.png")

original = load_image("test_odd.png")
msg = "ID:aa6c2659-a94"
wm, key = embed_watermark(original, msg, 40)
print("Len of key:", len(key)) # Should be len of msg * 8

extracted = extract_watermark(wm, key, 40, len(msg)*8)
print(f"Direct Extracted: '{extracted}'")
