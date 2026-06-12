"""
EasyOCR + Tesseract OCR Engine - Production-grade raster CAD drawing OCR.
Proven pipeline: EasyOCR text detection + Tesseract per-region OCR.

EasyOCR handles detection reliably on Windows (no datalab cache issues).
Tesseract does per-region recognition with chi_sim+eng for CAD text.

Requires: easyocr, pytesseract, tesseract-ocr with chi_sim+eng lang packs
"""
import os
import re
from typing import List, Dict, Optional

from PIL import Image


# --- Detection (EasyOCR) ---

_reader = None

def _get_reader():
    """Lazy-load EasyOCR Reader (detection model, no GPU needed)."""
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    return _reader


def detect_text_regions(image_path: str) -> List[List[int]]:
    """Run EasyOCR detection on an image, return list of [x1,y1,x2,y2] bboxes.
    Returns bboxes sorted top-to-bottom, left-to-right.
    """
    reader = _get_reader()
    horizontal_list, free_list = reader.detect(image_path)

    boxes = []
    
    def _safe_int(val):
        """Convert numpy int or list to int."""
        if isinstance(val, (list, tuple)):
            return int(val[0]) if val else 0
        return int(val)
    
    # Process horizontal text regions
    for group in horizontal_list:
        if not group:
            continue
        for box in group:
            if isinstance(box, (list, tuple)) and len(box) >= 4:
                x1 = _safe_int(box[0])
                y1 = _safe_int(box[2])
                x2 = _safe_int(box[1])
                y2 = _safe_int(box[3])
                if x2 > x1 and y2 > y1:
                    boxes.append([x1, y1, x2, y2])
    
    # Process free-form text regions
    for group in free_list:
        if not group:
            continue
        for box in group:
            if isinstance(box, (list, tuple)) and len(box) >= 4:
                x1 = _safe_int(box[0])
                y1 = _safe_int(box[2])
                x2 = _safe_int(box[1])
                y2 = _safe_int(box[3])
                if x2 > x1 and y2 > y1:
                    boxes.append([x1, y1, x2, y2])

    # Sort by y, then x (top-to-bottom, left-to-right)
    boxes.sort(key=lambda b: (b[1], b[0]))

    # Pre-filter: remove implausible bboxes before OCR
    boxes = _prefilter_bboxes(boxes)
    return boxes


# --- OCR (Tesseract, unchanged) ---

_tesseract_path = None


def _find_tesseract() -> Optional[str]:
    """Locate Tesseract binary on Windows."""
    global _tesseract_path
    if _tesseract_path:
        return _tesseract_path

    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for p in candidates:
        if os.path.exists(p):
            _tesseract_path = p
            return p

    import subprocess
    try:
        result = subprocess.run(
            ["where", "tesseract"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            _tesseract_path = result.stdout.strip().split("\n")[0]
            return _tesseract_path
    except Exception:
        pass

    return None


def ocr_region(img: Image.Image, bbox: List[int], pad: int = 3) -> str:
    """Run Tesseract OCR on a single image region with improved preprocessing."""
    import pytesseract

    tesseract_bin = _find_tesseract()
    if not tesseract_bin:
        raise RuntimeError(
            "Tesseract not found. Install from https://github.com/UB-Mannheim/tesseract/wiki"
        )
    pytesseract.pytesseract.tesseract_cmd = tesseract_bin

    x1, y1, x2, y2 = bbox
    cx1 = max(0, x1 - pad)
    cy1 = max(0, y1 - pad)
    cx2 = min(img.width, x2 + pad)
    cy2 = min(img.height, y2 + pad)

    if cx2 <= cx1 or cy2 <= cy1:
        return ""

    crop = img.crop((cx1, cy1, cx2, cy2))

    # Convert to grayscale and enhance contrast for better OCR
    crop_gray = crop.convert('L')
    # Auto-contrast (stretch histogram)
    import numpy as np
    arr = np.array(crop_gray)
    p2, p98 = np.percentile(arr, (2, 98))
    if p98 > p2:
        arr = np.clip((arr - p2) * 255.0 / (p98 - p2), 0, 255).astype(np.uint8)
    enhanced = Image.fromarray(arr)

    try:
        # Try chi_sim+eng first, fall back to eng only
        text = pytesseract.image_to_string(
            enhanced, lang="chi_sim+eng", config="--psm 6"
        ).strip()
        if not text:
            text = pytesseract.image_to_string(
                enhanced, lang="eng", config="--psm 7"
            ).strip()
        return text
    except Exception:
        try:
            return pytesseract.image_to_string(
                crop, lang="eng", config="--psm 7"
            ).strip()
        except Exception:
            return ""


# --- Filtering ---

SKIP_PHRASES = [
    # English view labels
    "FRONT VIEW", "SECTION", "REAR VIEW", "TOP VIEW", "BOTTOM VIEW",
    "RIGHT VIEW", "LEFT VIEW", "DETAIL", "DETAIL VIEW", "ELEVATION",
    "SIDE VIEW", "ISOMETRIC", "ISOMETRIC VIEW", "EXPLODED VIEW",
    "PLAN VIEW", "PLAN", "SECTION VIEW", "SECTION A-A", "SECTION B-B",
    # Drawing info keywords
    "SCALE", "DRAWN BY", "CHECKED BY", "DRAWN", "CHECKED",
    "APPROVED BY", "APPROVED", "DATE", "JOB NO", "DWG NO", "DWG",
    "KINGWOOD", "KINGWOOD NO", "PROJECT", "TITLE", "DRAWING TITLE",
    "REV", "REV:", "REVISION", "SHEET", "PAGE",
    "Tel:", "FAX:", "http", "www", "copyright", "proprietary",
    "DESCRIPTION", "Description", "Date /", "Scale /", "Dwg No",
    "QTY", "MATERIAL", "FINISH", "SURFACE", "WEIGHT",
    "TOLERANCE", "UNIT", "DIMENSION", "SPECIFICATION",
    # Boilerplate legal
    "If no specification", "All measurements", "have to be verified",
    "scale drawing", "All design drawings", "copyright and proprietary",
    "International Enterprises", "limited",
    "Unless otherwise specified", "without written",
    # Chinese view labels & frame text
    "\u6240\u6709\u5c3a\u5bf8\u4e3a\u516c\u5236", "\u4e3a\u4f9d\u636e",
    "\u516c\u53f8\u4e4b\u7248\u6743\u6240\u6709", "\u5982\u65e0\u7279\u522b\u8bf4\u660e",
    "\u4eac\u6728(\u4e2d\u56fd)\u521b\u610f\u5c55\u793a", "\u9999\u6e2f\u4e5d\u9f99",
    "\u6b63\u89c6\u56fe", "\u524d\u89c6\u56fe", "\u4fef\u89c6\u56fe", "\u4ef0\u89c6\u56fe",
    "\u5de6\u89c6\u56fe", "\u53f3\u89c6\u56fe", "\u540e\u89c6\u56fe", "\u80cc\u89c6\u56fe",
    "\u5256\u89c6\u56fe", "\u5c55\u5f00\u56fe", "\u88c5\u914d\u56fe", "\u5927\u6837\u56fe",
    "\u8be6\u56fe", "\u5256\u9762\u56fe", "\u65ad\u9762\u56fe", "\u793a\u610f\u56fe",
    "\u7b49\u8f74\u6d4b\u56fe", "\u4e09\u89c6\u56fe", "\u5e73\u9762\u56fe", "\u7acb\u9762\u56fe",
    "\u90e8\u4ef6\u56fe", "\u7ec4\u88c5\u56fe", "\u7ed3\u6784\u56fe", "\u5b89\u88c5\u56fe",
    "\u5f00\u6599\u56fe", "\u6392\u94bb\u56fe", "\u5b54\u4f4d\u56fe", "\u5206\u4ef6\u56fe",
    "\u56fe\u7eb8\u540d\u79f0", "\u56fe\u53f7", "\u6bd4\u4f8b", "\u65e5\u671f",
    "\u8bbe\u8ba1", "\u5ba1\u6838", "\u6279\u51c6", "\u7ed8\u56fe", "\u6821\u5bf9",
    "\u7248\u672c", "\u9875\u6570", "\u5408\u8ba1", "\u5171", "\u9875",
    "\u9879\u76ee\u540d\u79f0", "\u9879\u76ee\u7f16\u53f7",
    "\u4e3a\u4f9d\u636e,\u4e0d\u53ef\u7528\u6bd4\u4f8b\u5c3a",
    "\u5ba2\u6237", "\u56fe\u540d", "\u9875\u7801",
]

NOISE_PATTERNS = [
    re.compile(r"^[ |\-]+$"),
    re.compile(r"^[A-Z]{1,3}$"),
    re.compile(r"^\d{1,4}$"),
    re.compile(r"^[~\-_=.]{2,}$"),
    # CAD-specific garbled text: random symbol salad
    re.compile(r"^[\\|/\-\|\\/\\\|\-_=~.+*]{4,}$"),  # line fragments
    re.compile(r"^[lI1i|]{3,}$"),                           # vertical bar soup
    re.compile(r"^[Il1|.!'`,:;]{2,}$"),                     # punctuation noise
    re.compile(r"^[oO0Q]{3,}$"),                             # circle-like noise
    re.compile(r"^[xX\*+\-\d]{1,2}[xX\*+\-]\d{1,3}$"),     # dimension fragments: 8x30, 10-20
    re.compile(r"^[Rr]\d{1,4}$"),                           # isolated radius: R50
    re.compile(r"^\d{1,2}\.\d{1,2}$"),                       # floating point fragment
]

# Garbled text: high ratio of non-alphanumeric chars
GARBLE_THRESHOLD = 0.6


def _is_garbled(text: str) -> bool:
    """Detect OCR output that is likely noise, not real text."""
    if not text or len(text) < 2:
        return True
    # Count alphanumeric chars (include Chinese as 'meaningful')
    meaningful = sum(1 for c in text if c.isalnum() or '\u4e00' <= c <= '\u9fff' or c in ' ./-')
    ratio = meaningful / len(text) if text else 0
    if ratio < GARBLE_THRESHOLD:
        return True
    # Single repeated char
    if len(set(text)) <= 2 and len(text) >= 4:
        return True
    return False


def _prefilter_bboxes(boxes: List[List[int]]) -> List[List[int]]:
    """Remove bboxes that are likely non-text (CAD line artifacts, noise)."""
    filtered = []
    for box in boxes:
        x1, y1, x2, y2 = box
        w = x2 - x1
        h = y2 - y1
        # Too small to be real text
        if w < 8 or h < 6:
            continue
        # Suspiciously narrow aspect ratio (vertical lines, 1D artifacts)
        if h > 0 and w / h < 0.05:
            continue
        # Aspect ratio too extreme for text (no text is 20:1 wide)
        if h > 0 and w / h > 25:
            continue
        filtered.append(box)
    return filtered


def has_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def has_significant_en(text: str) -> bool:
    words = re.findall(r"[a-zA-Z]{2,}", text)
    return len(words) >= 3


def filter_translatable(raw_items: List[Dict]) -> List[Dict]:
    """Filter raw OCR results to keep only translatable annotations."""
    translatable = []

    for item in raw_items:
        text = item["text"].strip()
        if not text or len(text) < 3:
            continue
        # Keep items with Chinese chars OR mixed content
        if len(text) >= 4 and all(not c.isalnum() for c in text):
            continue

        skip = False
        for phrase in SKIP_PHRASES:
            if phrase.lower() in text.lower():
                skip = True
                break
        if skip:
            continue

        skip = False
        for pat in NOISE_PATTERNS:
            if pat.match(text):
                skip = True
                break
        if skip:
            continue

        # Check for garbled OCR output (non-text noise)
        if _is_garbled(text):
            continue

        if has_chinese(text) or has_significant_en(text):
            translatable.append(item)

    return translatable


# --- Main Pipeline ---

def run_raster_ocr(image_path: str) -> Dict:
    """Full EasyOCR+Tesseract pipeline for a raster CAD image.

    Returns:
        {
            "total_detected": int,
            "ocr_results": int,
            "translatable": int,
            "items": [{"idx": int, "text": str, "bbox": [x1,y1,x2,y2]}],
            "raw_items": [...]
        }
    """
    all_bboxes = detect_text_regions(image_path)

    if not all_bboxes:
        return {
            "total_detected": 0,
            "ocr_results": 0,
            "translatable": 0,
            "items": [],
            "raw_items": [],
        }

    img = Image.open(image_path)
    raw_items = []
    for i, bbox in enumerate(all_bboxes):
        try:
            text = ocr_region(img, bbox)
            if text:
                raw_items.append({"idx": i, "text": text, "bbox": bbox})
        except Exception:
            continue

    translatable = filter_translatable(raw_items)

    return {
        "total_detected": len(all_bboxes),
        "ocr_results": len(raw_items),
        "translatable": len(translatable),
        "items": translatable,
        "raw_items": raw_items,
    }


def is_surya_available() -> bool:
    """Check if EasyOCR detection is available.

    Note: Function renamed for backward compatibility with app.py imports.
    """
    try:
        import easyocr
        return True
    except ImportError:
        return False


# Alias for backward compatibility
is_easyocr_available = is_surya_available
