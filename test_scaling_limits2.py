from src.core import embed_watermark, extract_watermark
from src.utils import load_image, text_to_binary
from PIL import Image

def test_scaling():
    original_arr = load_image("assets/zenitsu.jpg")
    msg = "ID:aa6c2659-a94"
    wm_arr, key = embed_watermark(original_arr, msg, 40)
    img_wm = Image.fromarray(wm_arr)
    w, h = img_wm.size
    
    # Test scales
    for scale_pct in [30, 25, 20, 15, 10, 5]:
        new_w = int(w * (scale_pct / 100))
        new_h = int(h * (scale_pct / 100))
        
        scaled_down = img_wm.resize((new_w, new_h), Image.Resampling.LANCZOS)
        scaled_up = scaled_down.resize((w, h), Image.Resampling.LANCZOS)
        
        scaled_up.save("test_scale_tmp.png")
        attacked_arr = load_image("test_scale_tmp.png")
        
        extracted_text = extract_watermark(attacked_arr, key, 40, 120)
        
        bin_extracted = text_to_binary(extracted_text)
        bin_expected = text_to_binary(msg)
        bin_extracted = bin_extracted.ljust(len(bin_expected), '0')[:len(bin_expected)]
        
        diff_bits = sum(1 for a, b in zip(bin_extracted, bin_expected) if a != b)
        status = "PASS" if diff_bits <= 16 else "FAIL"
        print(f"{scale_pct:<10}% | {diff_bits:<15} | {status}")

if __name__ == '__main__':
    test_scaling()
