# ============================================================
# IMPORTS & INITIALIZATION
# ============================================================
# Load environment variables from .env file early to ensure all
# configuration is available before the app starts
from dotenv import load_dotenv
load_dotenv()

# Core FastAPI imports for web framework, request/response handling
from fastapi import FastAPI, UploadFile, File, Form, Depends, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# SQLAlchemy for database ORM and session management
from sqlalchemy.orm import Session

# Password hashing and cryptography
import bcrypt

# Database models and utilities
from src.database import SessionLocal, init_db, User, ImageRegistry
from src.utils import load_image, save_image, binary_to_text, compute_dhash, calculate_hamming_distance
from src.core import embed_watermark, extract_watermark

# Standard library utilities
import shutil, os, uuid, numpy as np, secrets

# Image processing (PIL/Pillow)
from PIL import Image, ImageFilter

# Secure token signing and validation
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

# Initialize FastAPI application
app = FastAPI()

# ============================================================
# SECURITY HEADERS MIDDLEWARE
# ============================================================
# Middleware to add security headers to every HTTP response
# Prevents clickjacking, MIME-type sniffing, XSS, and enforces HTTPS
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    # Prevent embedding in iframes (clickjacking protection)
    response.headers["X-Frame-Options"] = "DENY"
    # Prevent browsers from sniffing MIME type (e.g., executing JS in CSS)
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Control referrer information sent to external sites
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Disable dangerous browser features (camera, mic, geolocation)
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    # Force HTTPS for one year (including subdomains)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Content Security Policy: restrict resource loading to same-origin + CDNs
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://code.jquery.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self';"
    )
    return response

# ============================================================
# 1. SECURITY SETUP
# ============================================================
# Configuration for authentication, authorization, and encryption

# Cookie signing secret: prevents cookie tampering
# Loaded from env var or randomly generated for development
APP_SECRET = os.environ.get("NEUROSTAMP_APP_SECRET", secrets.token_hex(32))
COOKIE_SIGNER = URLSafeTimedSerializer(APP_SECRET)

# Admin users list: comma-separated usernames with admin access
# If empty, no admin restrictions applied (for development)
ADMIN_USERS = [u.strip() for u in os.environ.get("NEUROSTAMP_ADMIN_USERS", "").split(",") if u.strip()]

# Secure cookie flag: set to "true" only in production with HTTPS
# When false, cookies sent over HTTP; when true, only sent over HTTPS
SECURE_COOKIES = os.environ.get("NEUROSTAMP_SECURE_COOKIES", "false").lower() == "true"

# Watermark embedding strength (SVD coefficients scaling factor)
# Decision rule: bit is "1" when (S[0]_current - S[0]_original) > WATERMARK_ALPHA/2
# Typical range: 50–80. Higher = more robust but lower PSNR; lower = smaller changes but less robust
# Must match during both embedding and extraction for correct threshold detection
WATERMARK_ALPHA = 70

# Upload size and format restrictions
MAX_UPLOAD_BYTES = int(os.environ.get("NEUROSTAMP_MAX_UPLOAD_MB", "20")) * 1024 * 1024
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
# Prevent decompression bomb attacks (e.g., tiny PNG that expands to huge size)
Image.MAX_IMAGE_PIXELS = 89_000_000  # ~9400x9400 pixels

# ============================================================
# PASSWORD HASHING & VERIFICATION UTILITIES
# ============================================================
# Using bcrypt for secure password storage and verification
# (never store plain-text passwords)

def get_password_hash(password: str) -> str:
    """Hash a plain-text password using bcrypt with salt.
    
    Args:
        password: Plain-text password from user input
    
    Returns:
        bcrypt-hashed password string (safe to store in database)
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash.
    
    Args:
        plain: Plain-text password from login attempt
        hashed: bcrypt hash from database
    
    Returns:
        True if password matches hash; False otherwise
    """
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))


# ============================================================
# 2. SIGNED SESSION HELPERS
# ============================================================
# Session management using cryptographically signed tokens
# Prevents session tampering and forgery attacks

def sign_session(username: str) -> str:
    """Create a cryptographically signed session token.
    
    The token is signed with APP_SECRET, so it cannot be forged
    without knowing the secret. The username is embedded in the token
    and can be recovered by verify_session().
    
    Args:
        username: The authenticated username
    
    Returns:
        URL-safe signed token string (safe to use as cookie value)
    """
    return COOKIE_SIGNER.dumps(username, salt="user-session")

def verify_session(token: str, max_age: int = 86400) -> str | None:
    """Verify and decode a signed session token.
    
    Ensures the token was signed with APP_SECRET and has not expired.
    If valid, returns the embedded username. If invalid/expired, returns None.
    
    Args:
        token: The signed token string (from cookie)
        max_age: Maximum age of token in seconds (default 24 hours)
    
    Returns:
        Username if token is valid; None if tampered or expired
    """
    try:
        return COOKIE_SIGNER.loads(token, salt="user-session", max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None

def get_session_user(request: Request) -> str | None:
    """Extract and verify the logged-in username from the request cookies.
    
    Reads the "user_session" cookie, verifies its signature, and returns
    the username if valid. Used to protect routes that require authentication.
    
    Args:
        request: FastAPI request object (contains cookies)
    
    Returns:
        Username if session is valid; None if missing or invalid
    """
    token = request.cookies.get("user_session")
    if not token:
        return None
    return verify_session(token)


# ============================================================
# 3. CSRF PROTECTION (Double-Submit Cookie)
# ============================================================
# CSRF (Cross-Site Request Forgery) prevention using double-submit tokens
# Frontend generates a token, includes it in form submissions;
# backend verifies it matches the token in cookies

def generate_csrf_token() -> str:
    """Generate a new CSRF protection token.
    
    Uses cryptographically random hex string. One token per session.
    Client-side JS reads from cookie and must include in form submissions.
    
    Returns:
        Random 64-character hex string (32 bytes)
    """
    return secrets.token_hex(32)

def validate_csrf(request: Request, csrf_token: str = Form(None)):
    """Validate CSRF token from form against cookie.
    
    Both the cookie and form field must contain matching tokens.
    Comparison uses constant-time comparison to prevent timing attacks.
    
    Args:
        request: FastAPI request (contains cookies)
        csrf_token: Token from form submission (POST parameter)
    
    Raises:
        HTTPException with status 403 if validation fails
    """
    cookie_token = request.cookies.get("csrf_token")
    # Token must exist in both places and match exactly
    if not cookie_token or not csrf_token or not secrets.compare_digest(cookie_token, csrf_token):
        raise HTTPException(status_code=403, detail="CSRF validation failed")


# ============================================================
# 4. UPLOAD VALIDATION
# ============================================================
# Multi-layer validation for file uploads to prevent attacks
# (malicious files, oversized files, file type bypass)

async def validate_upload(file: UploadFile) -> bytes:
    """Validate an uploaded file before processing.
    
    Performs three security checks:
    1. File extension must be in ALLOWED_EXTENSIONS (allowlist)
    2. File size must not exceed MAX_UPLOAD_BYTES
    3. PIL can actually open the file (detects corrupted/fake images)
    
    Args:
        file: FastAPI UploadFile object
    
    Returns:
        File contents as bytes if all checks pass
    
    Raises:
        HTTPException with status 400 or 413 if validation fails
    """
    # CHECK 1: Verify file extension is allowed
    _, ext = os.path.splitext(file.filename or "")
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    
    # CHECK 2: Read and verify file size
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(contents) // (1024*1024)}MB). Max: {MAX_UPLOAD_BYTES // (1024*1024)}MB"
        )
    
    # CHECK 3: Verify the file is a valid, uncorrupted image
    # PIL will raise exception if file is not a valid image or is corrupted
    import io
    try:
        img = Image.open(io.BytesIO(contents))
        img.verify()  # verify() scans for file corruption
    except Exception:
        raise HTTPException(status_code=400, detail="File is not a valid image or is corrupted")
    
    # Reset file pointer for downstream consumers to read from beginning
    await file.seek(0)
    return contents


# ============================================================
# 5. APP SETUP & INITIALIZATION
# ============================================================
# Set up static files, template engine, and database

# Create uploads directory if it doesn't exist (for storing watermarked images)
os.makedirs("static/uploads", exist_ok=True)

# Mount static file directory (CSS, JS, images) at /static path
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 template engine (for HTML rendering)
templates = Jinja2Templates(directory="templates")
# Disable Jinja2's template caching to avoid TypeError on some platforms
# (some combinations of Jinja2/Starlette pass unhashable types as cache keys)
# Setting cache_size=0 forces re-parsing templates on every request (safe for development)
templates.env.cache_size = 0

# Initialize database (create tables if they don't exist)
init_db()

# Debug: print which DATABASE_URL the app is using at startup
# Helps diagnose database configuration issues in logs
from src.database import DATABASE_URL as _DB_URL
print(f"DEBUG - Using DATABASE_URL={_DB_URL}")

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def get_secure_filename(filename: str) -> str:
    """Generate a secure filename for uploaded files.
    
    Prevents directory traversal attacks (e.g., "../etc/passwd")
    by using a UUID prefix and sanitizing the original filename.
    
    Args:
        filename: Original filename from upload
    
    Returns:
        Secure filename like "a1b2c3d4_original_image.jpg"
    """
    base = os.path.basename(filename)  # Remove any path separators
    # Keep only safe characters (alphanumeric, dots, dashes, underscores)
    clean_base = "".join(c for c in base if c.isalnum() or c in "._-")
    # Prepend random UUID to make filename unique and prevent collisions
    return f"{uuid.uuid4().hex[:8]}_{clean_base}"

def get_db():
    """FastAPI dependency: Get a database session.
    
    Creates a new SQLAlchemy session for this request and ensures
    it's properly closed after the request completes (even if an error occurs).
    
    Yields:
        SQLAlchemy Session object (used by route handlers via Depends(get_db))
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================
# COOKIE MANAGEMENT HELPER
# ============================================================

def set_secure_cookie(response: Response, key: str, value: str, httponly: bool = True):
    """Set an HTTP cookie with proper security flags.
    
    Applies industry best practices for cookie security:
    - httponly: Prevents JS from reading cookie (default True)
    - samesite: Prevents CSRF attacks (always "Lax")
    - secure: Only sent over HTTPS in production (depends on SECURE_COOKIES setting)
    - max_age: Cookie expires after 24 hours
    
    Args:
        response: FastAPI Response object to modify
        key: Cookie name (e.g., "user_session")
        value: Cookie value (should be signed/encrypted)
        httponly: If True, JS cannot access cookie (default True for security)
    """
    response.set_cookie(
        key=key,
        value=value,
        httponly=httponly,
        samesite="Lax",  # Allows same-site requests with top-level navigation
        secure=SECURE_COOKIES,  # Only HTTPS in production
        max_age=86400,  # 24 hours
    )


# ============================================================
# AUTHENTICATION ROUTES
# ============================================================
# Public routes for user login, registration, and logout

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve the login/registration page.
    
    This is the public entry point. No authentication required.
    Redirects to /dashboard if user is already logged in (client-side)
    """
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the main dashboard (watermarking interface).
    
    Requires valid session cookie. Redirects to login if not authenticated.
    Generates a new CSRF token for form submissions.
    """
    username = get_session_user(request)
    if not username:
        return RedirectResponse(url="/")
    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("index.html", {
        "request": request,
        "username": username,
        "csrf_token": csrf_token,
    })
    # Set CSRF cookie (non-httponly so client-side JS can read it)
    set_secure_cookie(response, "csrf_token", csrf_token, httponly=False)
    return response

@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Register a new user account.
    
    Args:
        username: Desired username (must be unique)
        password: Plain-text password (will be hashed)
        db: Database session (injected by FastAPI)
    
    Returns:
        JSON with status and new user's unique ID (user_uid)
        or error message if user already exists or DB error occurs
    """
    # Check if username already exists
    if db.query(User).filter(User.username == username).first():
        return JSONResponse({"status": "error", "message": "User exists!"})
    
    # Create new user with hashed password and unique user_uid
    new_user = User(
        username=username,
        hashed_password=get_password_hash(password),
        user_uid=str(uuid.uuid4())[:12]  # Short unique ID for watermark embedding
    )
    db.add(new_user)
    
    # Commit to database with error handling
    try:
        db.commit()
    except Exception as e:
        db.rollback()  # Rollback on any DB error
        print(f"DB Error during register for user {username}: {e}")
        return JSONResponse(
            {"status": "error", "message": "Database error during registration."},
            status_code=500
        )
    
    return JSONResponse({"status": "success", "message": f"ID: {new_user.user_uid}"})

@app.post("/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Authenticate user and create session cookie.
    
    Args:
        username: Username to authenticate
        password: Plain-text password to verify
        response: FastAPI Response (will set cookie)
        db: Database session (injected by FastAPI)
    
    Returns:
        JSON with {"status": "success"} and user_session cookie set
        or error message if credentials invalid
    """
    # Look up user in database
    user = db.query(User).filter(User.username == username).first()
    
    # Verify user exists and password matches
    if not user or not verify_password(password, user.hashed_password):
        return JSONResponse(
            {"status": "error", "message": "Invalid Credentials"},
            status_code=401
        )
    
    # Create response with success message
    resp = JSONResponse({"status": "success"})
    
    # Set signed session cookie (cannot be forged without APP_SECRET)
    set_secure_cookie(resp, "user_session", sign_session(username))
    
    return resp

@app.get("/logout")
async def logout():
    """Clear session and CSRF cookies, redirect to login.
    
    Doesn't require authentication (safe endpoint).
    """
    resp = RedirectResponse(url="/")
    resp.delete_cookie("user_session")
    resp.delete_cookie("csrf_token")
    return resp


# ============================================================
# CORE ROUTES
# ============================================================
# These routes implement the core watermarking functionality

@app.post("/stamp")
async def stamp_image(
    request: Request,
    file: UploadFile = File(...),
    csrf_token: str = Form(None),
    db: Session = Depends(get_db),
):
    """Embed digital watermark into an image.
    
    Workflow:
    1. Authenticate user via session cookie
    2. Validate uploaded image (size, format, corruption)
    3. Check for copyright conflicts (double-spending attack)
    4. Embed watermark using DWT-SVD algorithm
    5. Register image hash in global registry
    6. Return watermarked image for download
    
    Args:
        file: Image file to watermark
        csrf_token: CSRF protection token
        db: Database session
    
    Returns:
        JSON with download URL for watermarked image
    """
    # Derive username from signed session (never trust client-sent username)
    username = get_session_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # CSRF validation (prevents cross-site attacks)
    validate_csrf(request, csrf_token)
    
    # Multi-layer file validation
    file_bytes = await validate_upload(file)
    
    # Look up user in database
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User error. Relogin.")

    # Save uploaded image to temporary location
    secure_name = get_secure_filename(file.filename)
    path = f"static/uploads/{secure_name}"
    with open(path, "wb") as f:
        f.write(file_bytes)
    original = load_image(path)
    
    # ============================================================
    # DOUBLE-SPENDING ATTACK PREVENTION
    # ============================================================
    # Check if this image (or a perceptually similar one) was already watermarked by someone else
    img_hash = compute_dhash(original)
    
    # Fast path: exact hash match
    exact = db.query(ImageRegistry).filter_by(image_hash=img_hash).first()
    if exact and exact.owner_uid != user.user_uid:
        owner = db.query(User).filter(User.user_uid == exact.owner_uid).first()
        return {"status": "error", "error": f"Conflict: Owned by {owner.username if owner else 'Unknown'}"}
    
    # Slow path: bounded perceptual scan (handles similar images, prevents DoS)
    if not exact:
        SCAN_LIMIT = 5000
        for r in db.query(ImageRegistry).limit(SCAN_LIMIT).all():
            if calculate_hamming_distance(img_hash, r.image_hash) < 10 and r.owner_uid != user.user_uid:
                owner = db.query(User).filter(User.user_uid == r.owner_uid).first()
                return {"status": "error", "error": f"Conflict: Owned by {owner.username if owner else 'Unknown'}"}

    # ============================================================
    # WATERMARK EMBEDDING
    # ============================================================
    # Embed user's ID into image using DWT-SVD algorithm
    watermarked, key = embed_watermark(original, f"ID:{user.user_uid}", WATERMARK_ALPHA, username)
    
    # Store the embedding key (encrypted) for later extraction
    user.set_key_data(key)
    
    # ============================================================
    # COPYRIGHT REGISTRY
    # ============================================================
    # Register this image in the global copyright registry (prevent double-stamping)
    if not db.query(ImageRegistry).filter_by(image_hash=img_hash).first():
        h, w, c = original.shape
        db.add(ImageRegistry(
            image_hash=img_hash, 
            owner_uid=user.user_uid,
            original_width=w,
            original_height=h
        ))
    db.commit()
    
    # Save watermarked image and return download URL
    out_name = f"stamped_{secure_name}"
    save_image(watermarked, f"static/uploads/{out_name}")
    return {"status": "success", "download_url": f"/static/uploads/{out_name}"}

@app.post("/verify")
async def verify(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Validate uploaded file
    file_bytes = await validate_upload(file)
    
    # 1. Save uploaded file securely
    secure_name = get_secure_filename(file.filename)
    path = f"static/uploads/verify_{secure_name}"
    with open(path, "wb") as f:
        f.write(file_bytes)
    
    # 2. Load the suspected image
    suspect_img_arr = load_image(path)
    
    # 3. Autonomous Pirate Detection (dHash Search)
    suspect_hash = compute_dhash(suspect_img_arr)
    
    matched_registry = None
    min_dist = 100
    
    # Fast path: exact match first
    exact = db.query(ImageRegistry).filter_by(image_hash=suspect_hash).first()
    if exact:
        matched_registry = exact
        min_dist = 0
    else:
        # Bounded perceptual scan
        SCAN_LIMIT = 5000
        for r in db.query(ImageRegistry).limit(SCAN_LIMIT).all():
            dist = calculate_hamming_distance(suspect_hash, r.image_hash)
            if dist < 22 and dist < min_dist: # 22 bit tolerance for dHash (handles crop/scale/screenshot attacks)
                min_dist = dist
                matched_registry = r
            
    if not matched_registry:
        return {"status": "error", "error": "No matching copyright found in the NeuroStamp Global Registry."}
        
    # 4. We found the owner! Load their profile.
    user = db.query(User).filter(User.user_uid == matched_registry.owner_uid).first()
    if not user: return {"error": "Registry Corrupted: Owner UID missing."}
    
    key = user.get_key_data()
    if not key: return {"error": "User Key not found."}
    
    # 5. RECOVERY ALIGNMENT
    # If the image was squashed by Instagram, we must resize it back to the mathematically
    # expected DWT grid dimensions before extraction!
    orig_w = matched_registry.original_width
    orig_h = matched_registry.original_height
    
    h, w, c = suspect_img_arr.shape
    if orig_w > 0 and orig_h > 0 and (w != orig_w or h != orig_h):
        print(f"   [ALIGNMENT] Restoring dimensions from {w}x{h} back to {orig_w}x{orig_h}")
        pil_img = Image.fromarray(suspect_img_arr)
        pil_img = pil_img.resize((orig_w, orig_h), Image.Resampling.LANCZOS)
        suspect_img_arr = np.array(pil_img)
    
    # 6. Extract the 120-bit Bipolar DCT Signature
    # alpha MUST match WATERMARK_ALPHA used during embedding so the threshold is correct
    text = extract_watermark(suspect_img_arr, key, WATERMARK_ALPHA, 120, user.username)
    print(f"DEBUG - Expected: 'ID:{user.user_uid}'")
    print(f"DEBUG - Extracted: '{text}'")
    
    # 7. Signature Integrity Validation
    expected = f"ID:{user.user_uid}"
    
    from src.utils import text_to_binary
    
    is_match = False
    if text == expected:
        is_match = True
    else:
        bin_extracted = text_to_binary(text)
        bin_expected = text_to_binary(expected)
        
        # Format padding
        bin_extracted = bin_extracted.ljust(len(bin_expected), '0')[:len(bin_expected)]
        
        diff_bits = sum(1 for a, b in zip(bin_extracted, bin_expected) if a != b)
        print(f"DEBUG - Bits different: {diff_bits}")
        
        # Allow up to 32 bits of damage to survive screenshot/rendering pipeline attacks
        if diff_bits <= 32:
            is_match = True
            
    return {
        "status": "complete", 
        # If match found, show the corrected ID from the database (not the garbled raw extraction)
        "extracted_text": expected if is_match else text, 
        "is_match": is_match, 
        "owner": user.username if is_match else "Unknown"
    }

@app.post("/attack")
async def attack(
    request: Request,
    filename: str = Form(...),
    attack_type: str = Form(...),
    csrf_token: str = Form(None),
):
    # Require session for attack sim
    username = get_session_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # CSRF check
    validate_csrf(request, csrf_token)
    
    # Sanitize filename (ensure just basename)
    safe_filename = os.path.basename(filename)
    path = f"static/uploads/{safe_filename}"

    if not os.path.exists(path): return {"error": "File not found"}
    img = Image.open(path).convert("RGB")
    
    if attack_type == "noise":
        arr = np.array(img).astype(np.float32) + np.random.normal(0, 10, (img.size[1], img.size[0], 3))
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    elif attack_type == "blur": img = img.filter(ImageFilter.GaussianBlur(1))
    elif attack_type == "jpeg": 
        img.save(f"{path}.jpg", "JPEG", quality=50); img = Image.open(f"{path}.jpg")
    elif attack_type == "rotate": img = img.rotate(5)
    elif attack_type == "crop": img = img.crop((img.width*0.05, img.height*0.05, img.width*0.95, img.height*0.95))
    elif attack_type == "scale":
        w, h = img.size
        # Keep the image physically smaller (50%) to demonstrate the attack visually
        img = img.resize((w // 2, h // 2), Image.Resampling.LANCZOS)
        
    out = f"attacked_{attack_type}_{safe_filename}"
    img.save(f"static/uploads/{out}")
    return {"status": "success", "attack_url": f"/static/uploads/{out}"}


# ============================================================
# ADMIN ROUTES — Requires authenticated session
# ============================================================

@app.get("/db-viewer", response_class=HTMLResponse)
async def view_database(request: Request, db: Session = Depends(get_db)):
    # Require valid session
    username = get_session_user(request)
    if not username:
        return RedirectResponse(url="/")
    
    # Admin check: block access unless ADMIN_USERS is configured AND the user is in the list
    if not ADMIN_USERS or username not in ADMIN_USERS:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = db.query(User).all()
    registry = db.query(ImageRegistry).all()
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>NeuroStamp Database Vault</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body { background-color: #050505; color: #00ff9d; font-family: 'JetBrains Mono', monospace; }
            .card { background: rgba(20, 20, 20, 0.8); border: 1px solid #333; }
            .card-header { background: #111; border-bottom: 1px solid #333; color: #fff; font-weight: bold; }
            .table { color: #ccc; }
            .table-hover tbody tr:hover { color: #fff; background-color: rgba(0, 255, 157, 0.1); }
            .uuid { color: #00d2ff; font-weight: bold; }
            h2 { text-shadow: 0 0 10px rgba(0, 255, 157, 0.5); }
        </style>
    </head>
    <body class="p-5">
        <div class="container">
            <div class="d-flex justify-content-between align-items-center mb-5">
                <h2>📂 DATABASE VAULT</h2>
                <div class="d-flex gap-2">
                     <a href="/visualize" class="btn btn-info btn-sm fw-bold">👁️ VISUALIZATION ENGINE</a>
                     <a href="/dashboard" class="btn btn-outline-light btn-sm">↻ REFRESH</a>
                </div>
            </div>

            <div class="card mb-5 shadow-lg">
                <div class="card-header">🔒 REGISTERED USERS (Table: users)</div>
                <div class="card-body p-0">
                    <table class="table table-dark table-hover mb-0">
                        <thead>
                            <tr class="text-secondary">
                                <th>ID</th>
                                <th>USERNAME</th>
                                <th>PUBLIC UUID</th>
                                <th>HAS WATERMARK KEY</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    
    for u in users:
        # SECURITY: Do NOT expose password hashes or encrypted key data
        has_key = "✅ YES" if u.encrypted_key_data else "❌ NO"
        html_content += f"""
            <tr>
                <td>{u.id}</td>
                <td class="fw-bold text-white">{u.username}</td>
                <td class="uuid">{u.user_uid}</td>
                <td>{has_key}</td>
            </tr>
        """
        
    html_content += """
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="card shadow-lg">
                <div class="card-header text-info">👁️ COPYRIGHT REGISTRY (Table: image_registry)</div>
                <div class="card-body p-0">
                    <table class="table table-dark table-hover mb-0">
                        <thead>
                            <tr class="text-secondary">
                                <th>ID</th>
                                <th>PERCEPTUAL HASH (dHash)</th>
                                <th>OWNER UUID</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    
    for r in registry:
        html_content += f"""
            <tr>
                <td>{r.id}</td>
                <td class="text-white"><code>{r.image_hash}</code></td>
                <td class="uuid">{r.owner_uid}</td>
            </tr>
        """
        
    html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="mt-4 text-center text-muted small">
                SECURE CONNECTION | AES-256 ENCRYPTION ACTIVE
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ============================================================
# VISUALIZATION ENGINE ENDPOINTS
# ============================================================

@app.get("/visualize", response_class=HTMLResponse)
async def visualize_page(request: Request):
    username = get_session_user(request)
    if not username:
        return RedirectResponse(url="/")
    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("visualize.html", {
        "request": request,
        "username": username,
        "csrf_token": csrf_token,
    })
    set_secure_cookie(response, "csrf_token", csrf_token, httponly=False)
    return response

from src.visualizer import generate_visualizations, generate_diff_map

@app.post("/process-vis", response_class=HTMLResponse)
async def process_visualization(
    request: Request,
    file: UploadFile = File(...),
    csrf_token: str = Form(None),
    db: Session = Depends(get_db),
):
    # Derive identity from session — not from form
    username = get_session_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # CSRF check
    validate_csrf(request, csrf_token)
    
    # Validate uploaded file
    file_bytes = await validate_upload(file)
    
    # 1. Save Original
    os.makedirs("static/vis", exist_ok=True)
    unique_id = uuid.uuid4().hex[:8]
    file_path = f"static/vis/demo_original_{unique_id}.jpg"
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    
    # 2. Generate Watermarked Version
    original = load_image(file_path)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found. Please re-login.")
    wm_img, key = embed_watermark(original, f"ID:{user.user_uid}", WATERMARK_ALPHA, username)
    
    wm_path = file_path.replace("original", "watermarked")
    save_image(wm_img, wm_path)
    
    # 3. Generate Visualizations (DWT, Grid, SVD)
    vis_assets = generate_visualizations(file_path, "static/vis", unique_id)
    
    # 4. Generate Diff Map
    vis_diff = generate_diff_map(file_path, wm_path, "static/vis", unique_id)
    
    new_csrf = generate_csrf_token()
    response = templates.TemplateResponse("visualize.html", {
        "request": request,
        "username": username,
        "csrf_token": new_csrf,
        "processed": True,
        "original_url": "/" + file_path,
        "watermarked_url": "/" + wm_path,
        "vis_dwt": vis_assets["dwt"],
        "vis_grid": vis_assets["grid"],
        "vis_svd": vis_assets["svd"],
        "vis_diff": vis_diff
    })
    set_secure_cookie(response, "csrf_token", new_csrf, httponly=False)
    return response