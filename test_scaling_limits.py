from src.core import embed_watermark, extract_watermark
from src.utils import load_image, text_to_binary
from PIL import Image
import numpy as np

def test_scaling():
    # Load and prepare original
    original_arr = load_image("assets/zenitsu.jpg")
    msg = "ID:aa6c2659-a94"
    
    # Embed
    wm_arr, key = embed_watermark(original_arr, msg, 40)
    img_wm = Image.fromarray(wm_arr)
    w, h = img_wm.size
    
    print(f"Original Size: {w}x{h}")
    print(f"Target Length: 120 bits (16 bit tolerance for success)\n")
    print(f"{'Scale %':<10} | {'Hamming Dist':<15} | {'Result'}")
    print("-" * 45)
    
    # Test scales
    for scale_pct in [90, 80, 70, 60, 50, 45, 40, 35, 30, 25, 20, 15, 10]:
        # Scale down and up
        new_w = int(w * (scale_pct / 100))
        new_h = int(h * (scale_pct / 100))
        
        scaled_down = img_wm.resize((new_w, new_h), Image.Resampling.LANCZOS)
        scaled_up = scaled_down.resize((w, h), Image.Resampling.LANCZOS)
        
        # We must save and load to simulate exact behavior
        scaled_up.save("test_scale_tmp.png")
        attacked_arr = load_image("test_scale_tmp.png")
        
        # Extract
        extracted_text = extract_watermark(attacked_arr, key, 40, 120)
        
        # Calculate distance
        bin_extracted = text_to_binary(extracted_text)
        bin_expected = text_to_binary(msg)
        bin_extracted = bin_extracted.ljust(len(bin_expected), '0')[:len(bin_expected)]
        
        diff_bits = sum(1 for a, b in zip(bin_extracted, bin_expected) if a != b)
        
        status = "PASS" if diff_bits <= 16 else "FAIL"
        print(f"{scale_pct:<10}% | {diff_bits:<15} | {status}")

if __name__ == '__main__':
    test_scaling()
