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

*Project Diary prepared for academic documentation purposes.*
*Current Status: Week 9 - Ready for further enhancements and testing.*
