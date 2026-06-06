"""
OCR Engine - Tesseract OCR wrapper for rasterized PDF pages.
"""
import subprocess
import tempfile
import os
import re
from typing import List, Dict, Optional

# Common Tesseract install paths to try
_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe",
    r"tesseract",  # fallback: hope it's on PATH
]


def _find_tesseract() -> Optional[str]:
    """Find the tesseract executable, checking common paths first."""
    for path_candidate in _TESSERACT_PATHS:
        # Expand user dir in path
        try:
            resolved = path_candidate
            if "{}" in resolved:
                resolved = resolved.replace("{}", os.environ.get("USERNAME", ""))
            
            # If it's a full path, check existence
            if os.pathsep not in resolved and os.sep in resolved:
                if os.path.exists(resolved):
                    return resolved
            else:
                # Just a name, check if it's on PATH
                result = subprocess.run(
                    [resolved, "--version"],
                    capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    return resolved
        except (subprocess.TimeoutExpired, OSError):
            continue
    
    # Final try: check with 'where' on Windows
    try:
        result = subprocess.run(
            ["where", "tesseract"], capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split("\n")[0]
    except Exception:
        pass
    
    return None


_TESSERACT_BIN = None  # cached result


def _get_tesseract_bin() -> str:
    """Get tesseract path, raising if not found."""
    global _TESSERACT_BIN
    if _TESSERACT_BIN is None:
        _TESSERACT_BIN = _find_tesseract()
    if _TESSERACT_BIN is None:
        raise RuntimeError(
            "Tesseract not found. Please install from https://github.com/UB-Mannheim/tesseract/wiki"
        )
    return _TESSERACT_BIN


def ocr_page(image_path: str, languages: str = "chi_sim+eng+vie") -> List[Dict]:
    """Run Tesseract OCR on an image, return text items with bboxes.
    
    Args:
        image_path: Path to PNG image
        languages: Tesseract language codes
        
    Returns:
        List of {text, bbox, confidence} dicts
    """
    try:
        cmd = [_get_tesseract_bin(), image_path, "stdout", "-l", languages,
               "--psm", "6", "tsv"]
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=120,
            encoding="utf-8", errors="replace"
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Tesseract error: {result.stderr}")
        
        return parse_tsv(result.stdout)
    except FileNotFoundError:
        raise RuntimeError(
            "Tesseract not found. Please install from https://github.com/UB-Mannheim/tesseract/wiki"
        )


def parse_tsv(tsv_text: str) -> List[Dict]:
    """Parse Tesseract TSV output into text items with bboxes."""
    lines = tsv_text.strip().split("\n")
    if len(lines) < 2:
        return []
    
    headers = lines[0].split("\t")
    items = []
    
    for line in lines[1:]:
        cols = line.split("\t")
        if len(cols) < len(headers):
            continue
        
        row = dict(zip(headers, cols))
        level = row.get("level", "")
        if level != "5":  # word level
            continue
        
        text = row.get("text", "").strip()
        if not text:
            continue
        
        try:
            conf = int(row.get("conf", "-1"))
            bbox = [
                int(row["left"]),
                int(row["top"]),
                int(row["left"]) + int(row["width"]),
                int(row["top"]) + int(row["height"]),
            ]
            items.append({
                "text": text,
                "bbox": bbox,
                "confidence": conf,
            })
        except (KeyError, ValueError):
            continue
    
    return items


def is_tesseract_available() -> bool:
    """Check if Tesseract is installed (searches common paths)."""
    try:
        return _find_tesseract() is not None
    except Exception:
        return False


def get_available_languages() -> List[str]:
    """List available Tesseract language packs."""
    try:
        bin_path = _find_tesseract()
        if not bin_path:
            return []
        result = subprocess.run(
            [bin_path, "--list-langs"],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split("\n")
        # Skip header line
        return [l.strip() for l in lines[1:] if l.strip()]
    except Exception:
        return []
