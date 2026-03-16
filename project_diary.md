# NeuroStamp Project Diary

## Project Title: NeuroStamp - Secure Copyright Protection Using DWT-SVD Watermarking

---

## Week 1: Team Formation & Problem Identification
**Date: 01-12-2025 to 05-12-2025**

| Date | Work Done | Remarks |
|------|-----------|---------|
| 01-12-2025 to 05-12-2025 | • Team formation and problem identification | |
| | • Brainstormed domains for project scope | |
| | • Selected "Digital Asset Integrity" as the core problem | Identified the growing need for intellectual property protection in the digital age |
| | • Conducted initial literature survey on digital watermarking | |

---

## Week 2: Topic Finalization & Roadmap Planning
**Date: 06-12-2025 to 12-12-2025**

| Date | Work Done | Remarks |
|------|-----------|---------|
| 06-12-2025 to 12-12-2025 | • Finalized topic and defined functions that we wanted to implement in our project | |
| | • Discussed what we wanted to implement and what we know about it till then | |
| | • Set a roadmap for project execution | Established milestones and deliverables |
| | • Defined project objectives: Embed, Extract, Verify, and Attack Simulation | |

---

## Week 3: Research & Methodology Study
**Date: 27-12-2025 to 03-01-2026**

| Date | Work Done | Remarks |
|------|-----------|---------|
| 27-12-2025 to 03-01-2026 | • Researched existing watermarking methods (LSB, DCT) | Studied spatial and frequency domain techniques |
| | • Identified watermark paradox (Robustness vs Invisibility tradeoffs) | Key design consideration for algorithm selection |
| | • Evaluated DWT-SVD hybrid approach for optimal balance | DWT provides multi-resolution analysis; SVD offers mathematical robustness |
| | • Studied research papers on block-based watermarking techniques | |

---

## Week 4: Zeroth Review & Environment Setup
**Date: 04-01-2026 to 10-01-2026**

| Date | Work Done | Remarks |
|------|-----------|---------|
| 04-01-2026 to 10-01-2026 | • Zeroth Review: Presented the idea and obtained permission to proceed with the project | Approval received from faculty |
| | • Successfully setup Python development environment | |
| | • Installed and configured essential libraries: | |
| | - **OpenCV** (cv2) for image processing | |
| | - **PyWavelets** for Discrete Wavelet Transform | |
| | - **NumPy** for numerical computations | |
| | - **SciPy** for scientific computing | |
| | - **Matplotlib** for visualization | |

---

## Week 5: Core Algorithm Development - DWT Implementation
**Date: 11-01-2026 to 17-01-2026**

| Date | Work Done | Remarks |
|------|-----------|---------|
| 11-01-2026 to 17-01-2026 | • Wrote initial script for Discrete Wavelet Transform (DWT) | Using Haar wavelet at Level 1 |
| | • Successfully validated decomposition of sample test images into four quadrants of frequency subbands: | |
| | - **LL** (Low-Low): Approximation coefficients | Contains most image energy |
| | - **LH** (Low-High): Horizontal details | |
| | - **HL** (High-Low): Vertical details | |
| | - **HH** (High-High): Diagonal details | |
| | • Implemented YCbCr color space conversion for embedding in luminance channel | Preserves visual quality |
| | • Created `load_image()` and `save_image()` utility functions in `utils.py` | Handles image I/O and dimension normalization |

---

## Week 6: SVD Implementation & Block-Based Embedding
**Date: 18-01-2026 to 24-01-2026**

| Date | Work Done | Remarks |
|------|-----------|---------|
| 18-01-2026 to 24-01-2026 | • Developed function to perform Singular Value Decomposition (SVD) on the LL subband | |
| | • Verified that we successfully extract and isolate the Singular Value Matrix (S[0]), which is critical for the embedding strategy | S[0] represents the dominant energy component |
| | • Implemented block-based approach with 4×4 block size | Enables fine-grained watermark embedding |
| | • Created `embed_watermark()` function in `core.py`: | |
| | - Divides LL subband into 4×4 blocks | |
| | - Applies SVD to each block | |
| | - Modifies S[0] value based on watermark bit | |
| | - Reconstructs block using inverse SVD | |
| | • Developed `text_to_binary()` and `binary_to_text()` conversion functions | Converts user ID to bitstream for embedding |
| | • Implemented inverse DWT (IDWT) for image reconstruction | |

---

## Week 7: Backend Development & Security Features
**Date: 25-01-2026 to 31-01-2026**

| Date | Work Done | Remarks |
|------|-----------|---------|
| 25-01-2026 to 31-01-2026 | • Developed FastAPI backend (`main.py`) with following endpoints: | |
| | - `/stamp` - Embed watermark into image | |
| | - `/verify` - Extract and verify watermark | |
| | - `/attack` - Simulate robustness attacks | |
| | • Implemented `extract_watermark()` function in `core.py` | Uses original S[0] values as key for extraction |
| | • Created SQLite database with SQLAlchemy ORM (`database.py`): | |
| | - **User** table: Stores user credentials and encrypted keys | |
| | - **ImageRegistry** table: Tracks image ownership | |
| | • Implemented AES-256 encryption using Fernet for secure watermark key storage | Keys encrypted before database storage |
| | • Integrated bcrypt for secure password hashing | Industry-standard security |
| | • Developed perceptual hashing (dHash) in `utils.py` for double-spending protection | Prevents re-registration of already watermarked images |
| | • Created Hamming distance calculation for image similarity detection | Threshold < 10 bits indicates duplicate |

---

## Week 8: Frontend Development & Visualization Engine
**Date: 01-02-2026 to 07-02-2026**

| Date | Work Done | Remarks |
|------|-----------|---------|
| 01-02-2026 to 07-02-2026 | • Developed cyberpunk-themed web interface using: | |
| | - Bootstrap 5 for responsive layout | |
| | - JetBrains Mono & Rajdhani fonts | |
| | - Glassmorphism CSS effects | |
| | - Neon color scheme (#00ff9d, #00d2ff, #ff0055) | |
| | • Created HTML templates: | |
| | - `login.html` - User authentication page | |
| | - `index.html` - Main dashboard with stamp/verify/attack functionality | |
| | - `visualize.html` - Algorithm visualization page | |
| | • Implemented Visualization Engine (`visualizer.py`): | Helps demonstrate algorithm internals |
| | - **DWT Decomposition View**: Displays LL, LH, HL, HH subbands | |
| | - **Block Grid Overlay**: Shows 4×4 block structure on LL | |
| | - **SVD Energy Heatmap**: Visualizes S[0] values across image | |
| | - **Difference Map**: Compares original vs watermarked | |
| | • Implemented attack simulation UI (future enhancement for robustness testing) | Placeholder for future work |
| | • Created Database Viewer (`/db-viewer`) for encrypted data inspection | |
| | • Developed `test_robustness.py` for automated algorithm testing | |
| | • Created comprehensive `README.md` documentation | |

---

## Technical Stack Summary

| Category | Technologies |
|----------|-------------|
| **Backend** | Python, FastAPI, SQLAlchemy, Uvicorn |
| **Signal Processing** | NumPy, PyWavelets, OpenCV, SciPy |
| **Security** | Cryptography (Fernet/AES-256), bcrypt |
| **Frontend** | Bootstrap 5, Jinja2 Templates, Vanilla JavaScript |
| **Database** | SQLite |

---

## Project Structure

```
NeuroStamp/
├── main.py                    # FastAPI application & routes
├── requirements.txt           # Project dependencies
├── README.md                  # Documentation
├── neurostamp.db              # SQLite database
├── secret.key                 # Fernet encryption key
├── src/
│   ├── core.py               # DWT-SVD watermarking engine
│   ├── database.py           # SQLAlchemy models & encryption
│   ├── utils.py              # Image utilities & perceptual hashing
│   └── visualizer.py         # Visualization generation
├── templates/
│   ├── login.html            # Authentication page
│   ├── index.html            # Main dashboard
│   └── visualize.html        # Algorithm visualization
├── static/
│   ├── uploads/              # User uploaded/processed images
│   └── vis/                  # Visualization outputs
└── test_robustness.py        # Robustness testing script
```

---

## Key Achievements

1. ✅ Implemented robust Block-Based DWT-SVD watermarking algorithm
2. ✅ Developed secure key management with AES-256 encryption
3. ✅ Created user authentication with bcrypt password hashing
4. ✅ Built double-spending protection using perceptual hashing
5. ✅ Designed intuitive cyberpunk-themed web interface
6. ✅ Implemented visualization engine for algorithm demonstration
7. 🔄 Attack simulation UI ready (robustness testing - in progress)


---

## Week 9: Scaling Robustness & Aspect Ratio Testing
**Date: 15-02-2026 to 21-02-2026**

| Date | Work Done | Remarks |
|------|-----------|---------| 
| 15-02-2026 to 21-02-2026 | • Identified failure of watermark extraction after image scaling attacks | Watermark was lost when image was resized to smaller dimensions |
| | • Investigated root cause: DWT grid misalignment after resize | Scaled image no longer matches the original embedding grid |
| | • Implemented **dimension recovery alignment** in `/verify` route: resizes the suspect image back to its original registered dimensions before extraction | Original width/height stored in `ImageRegistry` table at stamp time |
| | • Created `test_scaling_limits.py` — tests watermark survival from 90% down to 10% scale | Found that extraction succeeds down to ~40% scale with recovery alignment |
| | • Created `test_scaling_limits_lena.py` — scaling limit tests using `lena.jpg` as reference image | Cross-validated results across different image types |
| | • Created `test_aspect_ratio_scaling.py` — tests extreme aspect ratio distortions (e.g., squash height 50%, stretch width 200%) | Simulates Instagram/social media crop/resize pipelines |
| | • Verified extraction survives standard aspect ratio shifts with recovery alignment active | Pass rate significantly improved |

---

## Week 10: Crop Attack Survival
**Date: 22-02-2026 to 28-02-2026**

| Date | Work Done | Remarks |
|------|-----------|---------| 
| 22-02-2026 to 28-02-2026 | • Identified critical vulnerability: **crop attack destroys watermark** | 5% crop removes border blocks where watermark was embedded |
| | • Root cause analysis: watermark bits were embedded starting from the first/outermost image blocks | Outermost blocks are exactly what a crop attack removes |
| | • Designed fix: add a **`block_offset`** parameter to both `embed_watermark()` and `extract_watermark()` in `core.py` | Skipping the outermost N blocks ensures the watermark survives cropping |
| | • Implemented `block_offset` in `embed_watermark()` — embedding begins from an inner safe zone | Frontend passes consistent offset value in both stamp and verify calls |
| | • Implemented matching `block_offset` in `extract_watermark()` — extraction reads from the same inner zone | Offset must match on both sides; stored implicitly via consistent API calls |
| | • Re-ran attack simulation with crop attack enabled — verified watermark survives 5% and 10% crop | Extraction integrity confirmed post-fix |
| | • Created `test_robustness.py` update — added crop attack to robustness test suite | Automated regression testing for crop, scale, noise, blur, and JPEG attacks |

---

## Week 11: Algorithm Hardening & Integration Testing
**Date: 01-03-2026 to 07-03-2026**

| Date | Work Done | Remarks |
|------|-----------|---------| 
| 01-03-2026 to 07-03-2026 | • End-to-end robustness testing of the complete pipeline after crop and scaling fixes | Stamp → Attack → Verify cycle tested for all 6 attack types |
| | • Fixed edge case: odd-dimension images causing DWT grid misalignment | `load_image()` already trimmed odd pixels — confirmed it works correctly post-offset |
| | • Tested combined attacks (e.g., crop + noise, JPEG + scale) | Combined attacks increase bit error rate but stay within 32-bit tolerance threshold |
| | • Tuned bit error tolerance in `/verify` — allows up to 32 corrupted bits out of 120 before declaring integrity failure | Balances robustness vs false-positive rate |
| | • Verified the double-spending protection (dHash check) still works after watermarking | Hamming distance < 10 threshold correctly identifies duplicate submissions |
| | • Performed manual walkthrough of the full web UI flow | Confirmed stamp → download → attack → verify works end-to-end in browser |
| | • Documented algorithm parameters (alpha strength, block size, bit count) for report | 70 alpha for stamp, 40 alpha for verify extraction, 120 bits, 4×4 blocks |

---

## Week 12: Security Hardening & Production Readiness
**Date: 08-03-2026 to 14-03-2026**

| Date | Work Done | Remarks |
|------|-----------|---------| 
| 08-03-2026 to 14-03-2026 | • Conducted comprehensive security audit of the web application | Identified 8 vulnerabilities across auth, data exposure, uploads, and session management |
| | • **Fix 1 — Broken Auth Model**: Replaced client-sent `username` in form body with server-side signed session cookies using `itsdangerous` library | Prevents account impersonation — attacker can no longer POST any username |
| | • **Fix 2 — Admin Endpoint Exposure**: Protected `/db-viewer` behind session auth; removed password hash and encrypted key previews from HTML output | `/db-viewer` was previously accessible by anyone without credentials |
| | • **Fix 3 — Secure Cookie Flags**: Added `HttpOnly`, `SameSite=Lax`, and `Max-Age=86400` to all cookies; added `Secure` flag toggle for HTTPS via env var | Reduces session theft and CSRF risk in browsers |
| | • **Fix 4 — CSRF Protection**: Implemented double-submit cookie pattern; all state-changing POST endpoints validate a `csrf_token` form field against the cookie | Applied to `/stamp`, `/attack`, `/process-vis` |
| | • **Fix 5 — Upload Hardening**: Added extension allowlist, 20MB size cap, PIL decompression bomb guard (`MAX_IMAGE_PIXELS`), and PIL `verify()` check | Rejects `.exe`, oversized files, and malformed/corrupted uploads |
| | • **Fix 6 — Key Management**: Fernet encryption key now loaded from `NEUROSTAMP_SECRET_KEY` environment variable, falling back to `secret.key` file with a startup warning | Decouples secrets from codebase for production deployments |
| | • **Fix 7 — DB Query Optimization**: Added exact-match fast path before full perceptual hash scan; bounded scan to 5000 rows | Prevents linear CPU/latency DoS as image registry grows |
| | • **Fix 8 — Dependency Pinning**: Pinned all 15 packages to exact versions in `requirements.txt`; added previously unlisted `bcrypt` and `itsdangerous` | Ensures reproducible builds and prevents accidental vulnerable upgrades |
| | • Security regression tests verified all fixes working: 401 on auth bypass, 307 on unauthenticated `/db-viewer`, 403 on missing CSRF, 400 on disallowed extension | All tests passed |

---

*Project Diary prepared for academic documentation purposes.*
*Current Status: Week 12 Complete — Security hardened and production-ready.*

