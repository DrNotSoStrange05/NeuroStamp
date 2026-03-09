from src.core import embed_watermark, extract_watermark
from src.utils import load_image, text_to_binary
from PIL import Image

def test_custom_scaling():
    # Load and prepare original
    original_arr = load_image("assets/zenitsu.jpg")
    msg = "ID:aa6c2659-a94"
    
    # Embed
    wm_arr, key = embed_watermark(original_arr, msg, 40)
    img_wm = Image.fromarray(wm_arr)
    w, h = img_wm.size
    
    print(f"Original Size: {w}x{h}")
    print(f"Target Length: 120 bits (16 bit tolerance for success)\n")
    print(f"{'Aspect Ratio Shift':<30} | {'Hamming Dist':<15} | {'Result'}")
    print("-" * 65)
    
    # Test custom aspect ratios (e.g., stretching width but crushing height)
    aspect_ratios = [
        ("Squash Height 50%", w, int(h * 0.5)),
        ("Squash Width 50%", int(w * 0.5), h),
        ("Stretch Width 150%", int(w * 1.5), h),
        ("Stretch Height 150%", w, int(h * 1.5)),
        ("Extreme: W 200%, H 20%", int(w * 2.0), int(h * 0.2)),
        ("Extreme: W 20%, H 200%", int(w * 0.2), int(h * 2.0))
    ]
    
    for label, new_w, new_h in aspect_ratios:
        # Scale to custom aspect ratio
        scaled_img = img_wm.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Scale back to original dimensions for extraction
        restored_img = scaled_img.resize((w, h), Image.Resampling.LANCZOS)
        
        # Save and load to simulate exact behavior
        restored_img.save("test_aspect_tmp.png")
        attacked_arr = load_image("test_aspect_tmp.png")
        
        # Extract
        extracted_text = extract_watermark(attacked_arr, key, 40, 120)
        
        # Calculate distance
        bin_extracted = text_to_binary(extracted_text)
        bin_expected = text_to_binary(msg)
        bin_extracted = bin_extracted.ljust(len(bin_expected), '0')[:len(bin_expected)]
        
        diff_bits = sum(1 for a, b in zip(bin_extracted, bin_expected) if a != b)
        
        status = "PASS" if diff_bits <= 16 else "FAIL"
        print(f"{label:<30} | {diff_bits:<15} | {status}")

if __name__ == '__main__':
    test_custom_scaling()
