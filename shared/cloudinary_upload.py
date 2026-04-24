"""
cloudinary_upload.py — Upload files to Cloudinary via REST API.
No cloudinary SDK — uses requests + SHA1 signature (Cloudinary standard).

IMPORTANT:
  On Termux (local dev): uploads will FAIL with timeout/connection error.
  This is because Termux in this environment has no outbound internet access.
  On Render.com (production): uploads will WORK correctly — Render has full internet.

Credentials (.env):
  CLOUDINARY_CLOUD_NAME=dkuqh3lhq
  CLOUDINARY_API_KEY=761217912351
  CLOUDINARY_API_SECRET=CVpTbwlpZKGgX-zVbv63_PDhLSc
"""
import hashlib, time, requests
from shared.config import Config

CLOUD_NAME  = Config.CLOUDINARY_CLOUD_NAME   # dkuqh3lhq
API_KEY     = Config.CLOUDINARY_API_KEY       # 761217912351
API_SECRET  = Config.CLOUDINARY_API_SECRET    # CVpTbwlpZKGgX-zVbv63_PDhLSc
UPLOAD_URL  = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/auto/upload"

# Detect if running on Render.com (has RENDER env var) or locally
import os
IS_RENDER = os.getenv('RENDER') == 'true' or os.getenv('RENDER_SERVICE_ID') is not None

# ── Signature (Cloudinary requires SHA1) ─────────────────────────────────────
def _sign(params: dict) -> str:
    """
    Cloudinary signature rules:
    1. Sort params alphabetically
    2. Exclude: api_key, file, resource_type, cloud_name
    3. Join as key=value&key=value
    4. Append API_SECRET directly (no separator, no &)
    5. SHA1 hash → 40-char hex string
    """
    excluded = {'api_key', 'file', 'resource_type', 'cloud_name'}
    sorted_pairs = sorted(
        (k, str(v)) for k, v in params.items() if k not in excluded
    )
    param_str = "&".join(f"{k}={v}" for k, v in sorted_pairs)
    to_sign   = param_str + API_SECRET
    return hashlib.sha1(to_sign.encode('utf-8')).hexdigest()


def _build_transformation(t: dict) -> str:
    """Convert dict to Cloudinary transformation string."""
    parts = []
    if t.get('width'):   parts.append(f"w_{t['width']}")
    if t.get('height'):  parts.append(f"h_{t['height']}")
    if t.get('crop'):    parts.append(f"c_{t['crop']}")
    if t.get('gravity'): parts.append(f"g_{t['gravity']}")
    if t.get('quality'): parts.append(f"q_{t['quality']}")
    if t.get('format'):  parts.append(f"f_{t['format']}")
    return ",".join(parts)


# ── Core upload ───────────────────────────────────────────────────────────────
def upload_file(file_stream, filename: str, folder: str,
                transformation: dict = None) -> dict | None:
    """
    Upload a file to Cloudinary.
    Returns: {'url', 'public_id', 'format', 'width', 'height', 'bytes'} or None.

    Fails gracefully on Termux (no internet). Works on Render.com.
    """
    if not all([CLOUD_NAME, API_KEY, API_SECRET]):
        print("[Cloudinary] ❌ Missing credentials in .env")
        return None

    timestamp = str(int(time.time()))

    # Build params for signature
    params = {
        'timestamp': timestamp,
        'folder':    folder,
    }
    if transformation:
        params['transformation'] = _build_transformation(transformation)

    # Sign first, then add api_key
    params['signature'] = _sign(params)
    params['api_key']   = API_KEY

    try:
        resp = requests.post(
            UPLOAD_URL,
            data=params,
            files={'file': (filename, file_stream)},
            timeout=30
        )
        data = resp.json()

        if 'secure_url' in data:
            print(f"[Cloudinary] ✅ Uploaded: {data['secure_url'][:60]}...")
            return {
                'url':       data['secure_url'],
                'public_id': data.get('public_id', ''),
                'format':    data.get('format', ''),
                'width':     data.get('width', 0),
                'height':    data.get('height', 0),
                'bytes':     data.get('bytes', 0),
            }

        err = data.get('error', {}).get('message', str(data))
        print(f"[Cloudinary] ❌ Upload failed: {err}")
        return None

    except (requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            OSError) as e:
        # Expected on Termux (no internet) — will work on Render.com
        env_note = "Termux has no outbound internet — will work on Render.com" if not IS_RENDER else "Check internet connection"
        print(f"[Cloudinary] ⚠️  Connection failed ({env_note}): {e}")
        return None
    except Exception as e:
        print(f"[Cloudinary] ❌ Unexpected error: {e}")
        return None


# ── Avatar upload (400×400 face-crop, WebP) ──────────────────────────────────
def upload_avatar(file_stream, filename: str, user_id: str) -> str | None:
    result = upload_file(
        file_stream, filename,
        folder='etuktuk/avatars',
        transformation={
            'width': 400, 'height': 400,
            'crop': 'fill', 'gravity': 'face',
            'quality': 'auto', 'format': 'webp',
        }
    )
    return result['url'] if result else None


# ── Identity document upload (full resolution) ────────────────────────────────
def upload_id_doc(file_stream, filename: str,
                  user_id: str, role: str) -> str | None:
    result = upload_file(
        file_stream, filename,
        folder=f'etuktuk/id_docs/{role}',
        transformation={'quality': 'auto'}
    )
    return result['url'] if result else None


# ── File validators ───────────────────────────────────────────────────────────
ALLOWED_IMAGE = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'heic', 'heif'}
ALLOWED_DOC   = {'jpg', 'jpeg', 'png', 'pdf', 'webp'}
MAX_SIZE_MB   = 10

def validate_image(file) -> tuple:
    if not file or not getattr(file, 'filename', None):
        return False, "No file selected."
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_IMAGE:
        return False, "Unsupported format. Use JPG, PNG, GIF, or WEBP."
    file.seek(0, 2)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)
    if size_mb > MAX_SIZE_MB:
        return False, f"File too large ({size_mb:.1f}MB). Max {MAX_SIZE_MB}MB."
    return True, ""

def validate_doc(file) -> tuple:
    if not file or not getattr(file, 'filename', None):
        return False, "No file selected."
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_DOC:
        return False, "Unsupported format. Use JPG, PNG, or PDF."
    file.seek(0, 2)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)
    if size_mb > MAX_SIZE_MB:
        return False, f"File too large ({size_mb:.1f}MB). Max {MAX_SIZE_MB}MB."
    return True, ""
