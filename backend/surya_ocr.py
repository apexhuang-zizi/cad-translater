"""
Surya OCR Engine - Production-grade raster CAD drawing OCR.
Proven pipeline: Surya text detection + Tesseract per-region OCR.

This is the recommended approach for rasterized CAD PDFs where plain
Tesseract alone fails on Chinese text. The detection model locates
text regions precisely, then Tesseract runs on each cropped region
with chi_sim+eng PSM 6, achieving much higher accuracy.

Requires: surya, pytesseract, tesseract-ocr with chi_sim+eng lang packs
"""
import os
import re
from typing import List, Dict, Optional

from PIL import Image


# --- Detection ---

_detector = None


def _get_detector():
    """Lazy-load Surya DetectionPredictor (heavy model, ~200MB)."""
    global _detector
    if _detector is None:
        from surya.detection import DetectionPredictor
        _detector = DetectionPredictor()
    return _detector


def detect_text_regions(image_path: str) -> List[List[int]]:
    """Run Surya detection on an image, return list of [x1,y1,x2,y2] bboxes.
    Returns bboxes sorted top-to-bottom, left-to-right.
    """
    detector = _get_detector()
    img = Image.open(image_path)
    result = detector([img])

    boxes = []
    if result and result[0].bboxes:
        for box in result[0].bboxes:
            x1 = int(box.bbox[0])
            y1 = int(box.bbox[1])
            x2 = int(box.bbox[2])
            y2 = int(box.bbox[3])
            boxes.append([x1, y1, x2, y2])

    boxes.sort(key=lambda b: (b[1], b[0]))
    return boxes


# --- OCR ---

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


def ocr_region(img: Image.Image, bbox: List[int], pad: int = 2) -> str:
    """Run Tesseract OCR on a single image region."""
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
    try:
        return pytesseract.image_to_string(
            crop, lang="chi_sim+eng", config="--psm 6"
        ).strip()
    except Exception:
        return ""


# --- Filtering ---

SKIP_PHRASES = [
    "FRONT VIEW", "SECTION", "REAR VIEW", "TOP VIEW", "BOTTOM VIEW",
    "RIGHT VIEW", "LEFT VIEW", "DETAIL", "SCALE", "DRAWN BY", "CHECKED BY",
    "APPROVED BY", "DATE", "JOB NO", "DWG NO", "KINGWOOD", "KINGWOOD NO",
    "REV:", "Tel:", "FAX:", "http", "copyright", "proprietary",
    "DESCRIPTION", "Description", "Date /", "Scale /", "Dwg No",
    "If no specification", "All measurements", "have to be verified",
    "scale drawing", "All design drawings", "copyright and proprietary",
    "International Enterprises", "limited",
    "所有尺寸为公制", "为依据", "公司之版权所有", "如无特别说明",
    "京木(中国)创意展示", "香港九龙", "正视图", "剖视图",
    "为依据,不可用比例尺",
]

NOISE_PATTERNS = [
    re.compile(r"^[ |\-]+$"),
    re.compile(r"^[A-Z]{1,3}$"),
    re.compile(r"^\d{1,4}$"),
    re.compile(r"^[~\-_=.]{2,}$"),
]


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

        if has_chinese(text) or has_significant_en(text):
            translatable.append(item)

    return translatable


# --- Main Pipeline ---

def run_raster_ocr(image_path: str) -> Dict:
    """Full Surya+Tesseract pipeline for a raster CAD image.

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
        text = ocr_region(img, bbox)
        if text:
            raw_items.append({"idx": i, "text": text, "bbox": bbox})

    translatable = filter_translatable(raw_items)

    return {
        "total_detected": len(all_bboxes),
        "ocr_results": len(raw_items),
        "translatable": len(translatable),
        "items": translatable,
        "raw_items": raw_items,
    }


def is_surya_available() -> bool:
    """Check if Surya detection model can be loaded."""
    try:
        import surya.detection
        return True
    except ImportError:
        return False
