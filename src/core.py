import pywt
import numpy as np
from PIL import Image
from scipy.fftpack import dct, idct

# ============================================================
# NeuroStamp — Core Watermarking Engine
#
# Algorithm: Hybrid Block-Based DWT-DCT-SVD
#
# Pipeline (Embed):
#   RGB -> YCbCr (Y-channel only)
#   -> Level-1 Haar DWT -> LL sub-band
#   -> Partition LL into 4x4 blocks  (skip BLOCK_OFFSET outer blocks for crop robustness)
#   -> 2D DCT on each block           (energy compaction: concentrates signal into top-left DC coefficient)
#   -> SVD on each DCT block          (S[0] is the most stable/dominant singular value)
#   -> Embed watermark bit into S[0]  (S[0] += alpha * bit)
#   -> Inverse SVD -> Inverse DCT -> Inverse DWT -> YCbCr -> RGB
#
# Why DCT?
#   Applying DCT before SVD is the key improvement over plain DWT-SVD. The DCT
#   transforms each spatial 4x4 block into the frequency domain, compacting most
#   energy into the top-left (DC/low-frequency) coefficient.  When SVD is then
#   applied to this frequency-domain block, S[0] represents the dominant energy of
#   the *frequency* content rather than the raw pixel intensities, making it far
#   more stable under JPEG compression (which also operates in the frequency domain)
#   and Gaussian noise (which primarily lives in high-frequency DCT components).
#
# Extraction Model ("Semi-Blind"):
#   This is a SEMI-BLIND scheme: the original image is NOT needed (image-blind),
#   but the list of original S[0] values from each block IS required as a key.
#   The key is stored encrypted in the database per user.
#   True "blind" extraction does not require the key either — this is an important
#   distinction from what some literature labels "blind".
#
# Crop Robustness (block_offset):
#   BLOCK_OFFSET outer blocks are skipped during embedding, so a moderate crop
#   (trimming ~BLOCK_OFFSET * block_size * 2 pixels per edge at LL scale,
#   i.e. ~BLOCK_OFFSET * block_size * 4 pixels at original image scale)
#   does NOT destroy any watermarked blocks.
# ============================================================

# Number of blocks to skip on each edge (top/bottom/left/right) for crop resilience.
# A value of 2 means 8 LL-pixels (16 original-image pixels) of margin per edge.
BLOCK_OFFSET = 2


# --- HELPER FUNCTIONS ---

def text_to_binary(text):
    """Convert text string to binary string."""
    return "".join(format(ord(c), '08b') for c in text)

def binary_to_text(binary):
    """Convert binary string to text."""
    chars = []
    for i in range(0, len(binary), 8):
        byte = binary[i:i+8]
        if len(byte) < 8: break
        try:
            chars.append(chr(int(byte, 2)))
        except ValueError:
            pass
    return "".join(chars)


# --- DWT-DCT-SVD ENGINE (BLOCK BASED) ---

def embed_watermark(image_array, watermark_text, alpha=70, username="default"):
    """
    Embeds a text watermark using Hybrid Block-Based DWT-DCT-SVD.

    Steps:
        1. RGB -> YCbCr; extract luminance (Y) channel.
        2. Level-1 Haar DWT on Y -> LL, LH, HL, HH sub-bands.
        3. Partition LL into 4x4 blocks (skip BLOCK_OFFSET outer rows/cols of blocks).
        4. For each block: 2D DCT -> SVD -> encode bit in S[0] (S[0] += alpha * bit).
        5. Reconstruct: iSVD -> iDCT -> iDWT -> merge YCbCr -> RGB.

    Args:
        image_array : numpy array, uint8 RGB image.
        watermark_text : str, the text payload to embed (e.g. "ID:abc123").
        alpha : float, embedding strength. Higher = more robust but lower PSNR.
                Recommended range: 50-80. Must match the alpha used during extraction.
        username : str, unused — reserved for per-user block routing.

    Returns:
        (watermarked_array, s0_originals)
        watermarked_array : numpy uint8 RGB array.
        s0_originals : list of floats; the original S[0] per embedded block.
                       This is the extraction KEY — store it securely.
    """
    # 1. Convert to YCbCr and extract Y
    img_pil = Image.fromarray(image_array.astype('uint8')).convert('YCbCr')
    y, cb, cr = img_pil.split()
    y_array = np.array(y).astype(float)

    # 2. DWT Level 1
    coeffs = pywt.dwt2(y_array, 'haar')
    LL, (LH, HL, HH) = coeffs

    # 3. Prepare Blocks (crop LL to exact multiple of block_size)
    h, w = LL.shape
    block_size = 4
    h = (h // block_size) * block_size
    w = (w // block_size) * block_size
    LL = LL[:h, :w]

    # 4. Prepare Watermark payload
    binary_msg = text_to_binary(watermark_text)

    # Compute usable block count (interior blocks only, skipping BLOCK_OFFSET margins)
    row_blocks = h // block_size
    col_blocks = w // block_size
    interior_row_blocks = row_blocks - 2 * BLOCK_OFFSET
    interior_col_blocks = col_blocks - 2 * BLOCK_OFFSET
    num_blocks = max(0, interior_row_blocks) * max(0, interior_col_blocks)

    if len(binary_msg) > num_blocks:
        print(f"Warning: Truncating message. Capacity: {num_blocks} bits, "
              f"message needs: {len(binary_msg)} bits.")
        binary_msg = binary_msg[:num_blocks]

    s0_originals = []
    msg_idx = 0

    # Iterate interior blocks only (skip BLOCK_OFFSET border blocks for crop safety)
    r_start = BLOCK_OFFSET * block_size
    c_start = BLOCK_OFFSET * block_size
    r_end   = h - BLOCK_OFFSET * block_size
    c_end   = w - BLOCK_OFFSET * block_size

    for r in range(r_start, r_end, block_size):
        for c in range(c_start, c_end, block_size):
            if msg_idx >= len(binary_msg):
                break

            block = LL[r:r+block_size, c:c+block_size]

            # 2D DCT (separable — apply 1D DCT along rows then columns)
            # norm='ortho' makes it energy-preserving (orthonormal transform)
            dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')

            # SVD on the DCT block; S[0] is dominant — most stable under attacks
            U, S, Vt = np.linalg.svd(dct_block, full_matrices=False)

            # Store original S[0] — this forms the extraction key
            s0_originals.append(float(S[0]))

            # Embed bit: add alpha to S[0] for bit=1, leave unchanged for bit=0
            bit = int(binary_msg[msg_idx])
            S[0] = S[0] + (alpha * bit)

            # Reconstruct DCT block (iSVD)
            dct_block_new = np.dot(U, np.dot(np.diag(S), Vt))

            # Inverse 2D DCT
            block_new = idct(idct(dct_block_new.T, norm='ortho').T, norm='ortho')

            LL[r:r+block_size, c:c+block_size] = block_new

            msg_idx += 1

    # 5. Inverse DWT (match sub-band sizes to cropped LL)
    LH = LH[:h, :w]; HL = HL[:h, :w]; HH = HH[:h, :w]

    coeffs_new = (LL, (LH, HL, HH))
    y_watermarked = pywt.idwt2(coeffs_new, 'haar')

    # 6. Merge channels and return
    y_watermarked = np.clip(y_watermarked, 0, 255).astype('uint8')
    watermarked_y = Image.fromarray(y_watermarked)

    out_h, out_w = y_watermarked.shape
    cb = cb.resize((out_w, out_h)); cr = cr.resize((out_w, out_h))

    final_img = Image.merge('YCbCr', (watermarked_y, cb, cr)).convert('RGB')

    return np.array(final_img), s0_originals


def extract_watermark(image_array, key, alpha=70, length=None, username="default"):
    """
    Extracts watermark using Hybrid Block-Based DWT-DCT-SVD (Semi-Blind).

    This is a SEMI-BLIND extraction: the original image is not needed,
    but the list of original S[0] values (key) from the embedding step IS required.

    Decision rule per block:
        diff = S[0]_current - S[0]_original
        bit = 1  if  diff > (alpha / 2)   (midpoint threshold)
        bit = 0  otherwise

    Args:
        image_array : numpy array, uint8 RGB suspect image.
        key         : list of floats, the s0_originals returned by embed_watermark.
        alpha       : float, MUST match the alpha used during embedding for correct thresholding.
        length      : int or None, number of bits to extract (then convert to text).
        username    : str, unused — reserved for future per-user routing.

    Returns:
        str: The decoded watermark text.
    """
    # 1. Convert to YCbCr; extract Y channel
    img_pil = Image.fromarray(image_array.astype('uint8')).convert('YCbCr')
    y, cb, cr = img_pil.split()
    y_array = np.array(y).astype(float)

    # 2. DWT
    coeffs = pywt.dwt2(y_array, 'haar')
    LL, (LH, HL, HH) = coeffs

    h, w = LL.shape
    block_size = 4
    h = (h // block_size) * block_size
    w = (w // block_size) * block_size

    s0_originals = key  # List of original singular values (the extraction key)
    bits = ""
    idx = 0

    # Iterate the same interior block region as embedding (BLOCK_OFFSET margin)
    r_start = BLOCK_OFFSET * block_size
    c_start = BLOCK_OFFSET * block_size
    r_end   = h - BLOCK_OFFSET * block_size
    c_end   = w - BLOCK_OFFSET * block_size

    for r in range(r_start, r_end, block_size):
        for c in range(c_start, c_end, block_size):
            if idx >= len(s0_originals):
                break

            block = LL[r:r+block_size, c:c+block_size]

            # 2D DCT (identical transform to embedding)
            dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')

            # SVD
            U, S, Vt = np.linalg.svd(dct_block, full_matrices=False)

            s_extracted = S[0]
            s_original  = s0_originals[idx]

            diff = s_extracted - s_original

            # Threshold = alpha/2 (midpoint between 0 and alpha — optimal binary decision)
            # This assumes embedding used: S[0] += alpha for bit=1, no change for bit=0
            if diff > (alpha / 2):
                bits += "1"
            else:
                bits += "0"
            idx += 1

    if length:
        bits = bits[:length]

    return binary_to_text(bits)
