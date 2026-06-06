"""
PDF Processor - PyMuPDF text extraction and translation overlay.
Reuses the proven V11 placement logic from EB-P250 pipeline.
"""
import fitz  # PyMuPDF
import json
import os
import re
from typing import List, Dict, Optional, Tuple


def extract_text_spans(pdf_path: str, page_num: int = 0) -> List[Dict]:
    """Extract text spans with bounding boxes from a vector PDF page."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    text_dict = page.get_text("dict")
    doc.close()

    spans = []
    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:  # text block only
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue
                spans.append({
                    "text": text,
                    "bbox": list(span["bbox"]),
                    "font": span.get("font", ""),
                    "size": span.get("size", 0),
                    "color": span.get("color", 0),
                })
    return spans


def is_raster_pdf(pdf_path: str) -> bool:
    """Check if PDF is rasterized (no extractable text)."""
    doc = fitz.open(pdf_path)
    page = doc[0]
    text = page.get_text().strip()
    doc.close()
    return len(text) == 0


def get_pdf_info(pdf_path: str) -> Dict:
    """Get PDF metadata: page count, dimensions, and per-page type."""
    doc = fitz.open(pdf_path)
    pages_info = []
    for i in range(len(doc)):
        page = doc[i]
        has_text = len(page.get_text().strip()) > 0
        pages_info.append({
            "page": i,
            "width": page.rect.width,
            "height": page.rect.height,
            "is_vector": has_text,
        })
    doc.close()
    return {
        "path": pdf_path,
        "page_count": len(pages_info),
        "pages": pages_info,
    }


def render_page_preview(pdf_path: str, page_num: int, output_path: str,
                        dpi: int = 200) -> str:
    """Render a PDF page as PNG image for frontend display."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    pix.save(output_path)
    doc.close()
    return output_path


def merge_adjacent_items(items: List[Dict], gap_threshold: float = 20.0,
                         size_ratio_max: float = 2.0) -> List[Dict]:
    """Merge adjacent text items that belong to the same annotation line."""
    if not items:
        return []
    sorted_items = sorted(items, key=lambda x: (x["bbox"][1], x["bbox"][0]))
    merged = []
    current = dict(sorted_items[0])
    current["original_texts"] = [current["text"]]

    for item in sorted_items[1:]:
        cb = current["bbox"]
        ib = item["bbox"]
        y_mid_c = (cb[1] + cb[3]) / 2
        y_mid_i = (ib[1] + ib[3]) / 2
        y_diff = abs(y_mid_c - y_mid_i)
        avg_size = (abs(cb[3] - cb[1]) + abs(ib[3] - ib[1])) / 2
        x_gap = ib[0] - cb[2]

        size_c = abs(cb[3] - cb[1])
        size_i = abs(ib[3] - ib[1])
        ratio = max(size_c, size_i) / max(min(size_c, size_i), 1)

        if y_diff < avg_size * 0.6 and 0 <= x_gap < gap_threshold * 3 and ratio < size_ratio_max:
            current["text"] += " " + item["text"]
            current["original_texts"].append(item["text"])
            current["bbox"] = [
                min(cb[0], ib[0]),
                min(cb[1], ib[1]),
                max(cb[2], ib[2]),
                max(cb[3], ib[3]),
            ]
            current.setdefault("sizes", [current.get("size", 0)])
            current["sizes"].append(item.get("size", 0))
        else:
            current.setdefault("original_texts", [current["text"]])
            merged.append(current)
            current = dict(item)
            current["original_texts"] = [current["text"]]

    current.setdefault("original_texts", [current["text"]])
    merged.append(current)
    return merged


# View label patterns to exclude from translation
VIEW_LABELS = re.compile(
    r'(正视图|前视图|后视图|左视图|右视图|仰视图|俯视图|剖视图|'
    r'展开图|装配图|大样图|详图|剖面图|断面图|示意图|'
    r'FRONT\s*VIEW|BACK\s*VIEW|LEFT\s*VIEW|RIGHT\s*VIEW|'
    r'TOP\s*VIEW|BOTTOM\s*VIEW|SECTION\s*VIEW|DETAIL\s*VIEW|'
    r'SECTION|DETAIL|ELEVATION|PLAN|'
    r'VIEW\s*[A-Z]|[A-Z]\s*VIEW|'
    r'A-A|B-B|C-C|D-D|E-E)',
    re.IGNORECASE
)

FRAME_KEYWORDS = re.compile(
    r'(PROJECT|DWG|TITLE|SCALE|DATE|DRAWN|CHECKED|APPROVED|'
    r'REV|SHEET|MATERIAL|FINISH|QTY|DIMENSION|UNIT|'
    r'TOLERANCE|WEIGHT|SURFACE|NOTES|'
    r'图纸编号|图号|比例|日期|设计|审核|批准|'
    r'版本|页数|材料|表面处理|数量|单位)',
    re.IGNORECASE
)

# Noise patterns: single chars, pure numbers, pure symbols
NOISE_PATTERNS = re.compile(
    r'^[\d\.\,\-\+\×\±\°\%\#\@\*\(\)\[\]\{\}\/\\\|]+$'
)


def is_view_label(text: str) -> bool:
    """Check if text is a standard view label (should not translate)."""
    return bool(VIEW_LABELS.search(text.strip()))


def is_frame_text(text: str) -> bool:
    """Check if text looks like it belongs to the title block/frame area."""
    return bool(FRAME_KEYWORDS.search(text.strip()))


def is_noise(text: str) -> bool:
    """Check if text is noise (single chars, pure numbers, symbols)."""
    text = text.strip()
    if len(text) <= 1:
        return True
    if NOISE_PATTERNS.match(text):
        return True
    return False


def is_translatable(text: str) -> bool:
    """Determine if text content should be translated.
    Excludes: view labels, frame/title block text, noise."""
    text = text.strip()
    if not text:
        return False
    if is_noise(text):
        return False
    if is_view_label(text):
        return False
    if is_frame_text(text):
        return False
    # Must contain at least some Chinese or English letters
    has_cjk = bool(re.search(r'[\u4e00-\u9fff\u3400-\u4dbf]', text))
    has_alpha = bool(re.search(r'[a-zA-Z]{2,}', text))
    return has_cjk or has_alpha


def detect_frame_zone(pdf_path: str, page_num: int = 0) -> Optional[Dict]:
    """Detect right-side title block zone by finding vertical line clusters.
    Returns the frame zone bbox or None if not detected."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    
    # Get all vertical lines from drawings
    drawings = page.get_drawings()
    vertical_lines = []
    for d in drawings:
        for item in d.get("items", []):
            if item[0] == "l":  # line
                x1, y1 = item[1], item[2]
                x2, y2 = item[3], item[4]
                if abs(x1 - x2) < 2 and abs(y1 - y2) > 10:
                    vertical_lines.append((x1, y1, x2, y2))
    
    if not vertical_lines:
        doc.close()
        return None
    
    # Find the rightmost cluster of vertical lines
    page_w = page.rect.width
    right_lines = [l for l in vertical_lines if l[0] > page_w * 0.65]
    if not right_lines:
        doc.close()
        return None
    
    # Get the leftmost x of the right-side cluster
    frame_left = min(l[0] for l in right_lines)
    # Extended slightly to the left for safety margin
    frame_left = max(frame_left - 15, page_w * 0.5)
    
    doc.close()
    return {
        "left": frame_left,
        "right": page_w,
        "top": 0,
        "bottom": page.rect.height if hasattr(page, 'rect') else 842,
        "description": f"Title block zone: x > {frame_left:.0f}pt"
    }


def filter_translatable_items(items: List[Dict], frame_zone: Optional[Dict] = None) -> List[Dict]:
    """Filter items, keeping only translatable text outside the frame zone."""
    result = []
    for item in items:
        text = item.get("text", "").strip()
        if not is_translatable(text):
            continue
        if frame_zone:
            bbox = item["bbox"]
            x_center = (bbox[0] + bbox[2]) / 2
            if x_center > frame_zone["left"]:
                continue
        result.append(item)
    return result


# --- V11 Placement Algorithm ---

def find_position_v11(item_bbox: List[float], text_width: float, text_height: float,
                      page_rect: List[float], placed_boxes: List[List[float]],
                      margin: float = 6.0) -> Optional[Dict]:
    """V11 placement: prioritize below-left → right → above → below-offset.
    Checks collision with existing placed boxes and page boundaries."""
    x0, y0, x1, y1 = item_bbox
    pw, ph = page_rect[2], page_rect[3]

    candidates = [
        {
            "dir": "below",
            "bbox": [x0, y1 + margin, x0 + text_width, y1 + margin + text_height],
        },
        {
            "dir": "below-left",
            "bbox": [max(0, x0 - text_width), y1 + margin, x0, y1 + margin + text_height],
        },
        {
            "dir": "right",
            "bbox": [x1 + margin, y0, x1 + margin + text_width, y0 + text_height],
        },
        {
            "dir": "right-same-line",
            "bbox": [x1 + margin, (y0 + y1) / 2 - text_height / 2,
                     x1 + margin + text_width, (y0 + y1) / 2 + text_height / 2],
        },
        {
            "dir": "above",
            "bbox": [x0, y0 - margin - text_height, x0 + text_width, y0 - margin],
        },
    ]

    for candidate in candidates:
        cb = candidate["bbox"]
        if cb[2] > pw or cb[3] > ph or cb[0] < 0 or cb[1] < 0:
            continue

        collision = False
        for pb in placed_boxes:
            if boxes_overlap(cb, pb):
                collision = True
                break

        if not collision:
            return candidate

    # Fallback: place below with offset
    offset = 0
    while offset < 200:
        fb = [x0, y1 + margin + offset, x0 + text_width, y1 + margin + offset + text_height]
        if fb[2] <= pw and fb[3] <= ph:
            collision = False
            for pb in placed_boxes:
                if boxes_overlap(fb, pb):
                    collision = True
                    break
            if not collision:
                return {"dir": "below-fallback", "bbox": fb}
        offset += text_height + margin
    return None


def boxes_overlap(a: List[float], b: List[float]) -> bool:
    """Check if two bounding boxes overlap."""
    return not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3])


def wrap_text(text: str, font_size: float, max_width: float,
              font_name: str = "china-s") -> List[str]:
    """Wrap text to fit within max_width at given font size.
    Handles both space-separated (Vietnamese/English) and unspaced (Chinese) text."""
    # For text with spaces, split by word
    words = text.split()
    if not words:
        return [text]
    
    lines = []
    current_line = ""

    for word in words:
        sep = " " if current_line else ""
        test_line = current_line + sep + word
        test_width = estimate_text_width(test_line, font_size)
        if test_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            # If a single word exceeds max_width, force it onto its own line
            word_width = estimate_text_width(word, font_size)
            if word_width > max_width:
                # Break the long word at char level
                char_line = ""
                for ch in word:
                    test_char = char_line + ch
                    if estimate_text_width(test_char, font_size) > max_width and char_line:
                        lines.append(char_line)
                        char_line = ch
                    else:
                        char_line = test_char
                if char_line:
                    current_line = char_line
                else:
                    current_line = word
            else:
                current_line = word
    if current_line:
        lines.append(current_line)
    return lines if lines else [text]


def estimate_text_width(text: str, font_size: float) -> float:
    """Rough estimate of text width. CJK chars ~1x font_size, Latin ~0.55x,
    Vietnamese diacritic chars ~0.6x (slightly wider due to tone marks)."""
    # Vietnamese-specific diacritic characters (ă, â, ê, ô, ơ, ư + tone marks)
    vi_chars = set('áàảãạăắằẳẵặâấầẩẫậđéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ'
                   'ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ')
    width = 0
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff' or '\u3400' <= ch <= '\u4dbf':
            width += font_size * 0.95  # CJK
        elif ch == ' ':
            width += font_size * 0.3
        elif ch in vi_chars:
            width += font_size * 0.62  # Vietnamese diacritics
        elif ch.isascii() and ch.isalpha():
            width += font_size * 0.55  # Latin
        else:
            width += font_size * 0.55
    return width


def apply_translations(pdf_path: str, page_num: int,
                       translations: List[Dict],
                       output_path: str,
                       font_path: Optional[str] = None,
                       font_ratio: float = 0.72,
                       margin: float = 6.0) -> str:
    """Apply translations to a PDF page using V11 placement algorithm.
    
    Args:
        pdf_path: Source PDF path
        page_num: Page number (0-indexed)
        translations: List of {id, bbox, translated_text}
        output_path: Output PDF path
        font_path: Path to font file (None = use built-in)
        font_ratio: Ratio of translation font to original font size (default 0.72)
        margin: Margin between original text and translation box
    
    Returns:
        Output PDF path
    """
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    pw, ph = page.rect.width, page.rect.height

    # Determine font
    if font_path and os.path.exists(font_path):
        try:
            page.insert_font(fontname="vfont", fontfile=font_path)
            use_font = "vfont"
        except Exception:
            use_font = "china-s"
    else:
        use_font = "helv"

    placed_boxes = []
    for item in translations:
        bbox = item["bbox"]
        text = item.get("translated_text", "")
        if not text:
            continue

        orig_size = item.get("size", 14)
        font_size = max(orig_size * font_ratio, 7.0)
        orig_w = bbox[2] - bbox[0]

        # Wrap text — use generous width for Vietnamese (longer than source Chinese)
        max_w = max(orig_w * 4.0, pw * 0.35)
        lines = wrap_text(text, font_size, max_w, use_font)
        line_height = font_size * 1.35
        text_height = line_height * len(lines)
        text_width = max(estimate_text_width(l, font_size) for l in lines)

        # Find position
        position = find_position_v11(bbox, text_width, text_height,
                                     [0, 0, pw, ph], placed_boxes, margin)
        if not position:
            continue

        px, py = position["bbox"][0], position["bbox"][1]

        # Insert text in orange (#E65100) for visibility
        for i, line in enumerate(lines):
            y = py + i * line_height + font_size * 0.8
            page.insert_text(
                (px, y),
                line,
                fontname=use_font,
                fontsize=font_size,
                color=(0.9, 0.32, 0.0),  # Orange
                render_mode=0,
            )

        placed_boxes.append(position["bbox"])
        item["placed_bbox"] = position["bbox"]
        item["placed_dir"] = position.get("dir", "unknown")

    doc.save(output_path)
    doc.close()
    return output_path


def apply_translations_with_draft(pdf_path: str, page_num: int,
                                  translations: List[Dict],
                                  output_path: str,
                                  font_path: Optional[str] = None,
                                  font_ratio: float = 0.72,
                                  margin: float = 6.0,
                                  draft_color: Tuple = (0.5, 0.5, 0.5),
                                  final_color: Tuple = (0.9, 0.32, 0.0)) -> str:
    """Apply translations with draft marking for review mode.
    Unconfirmed items show in gray, confirmed in orange.
    """
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    pw, ph = page.rect.width, page.rect.height

    if font_path and os.path.exists(font_path):
        try:
            page.insert_font(fontname="vfont", fontfile=font_path)
            use_font = "vfont"
        except Exception:
            use_font = "china-s"
    else:
        use_font = "helv"

    placed_boxes = []
    for item in translations:
        bbox = item["bbox"]
        text = item.get("translated_text", "")
        if not text:
            continue

        confirmed = item.get("confirmed", False)
        color = final_color if confirmed else draft_color

        orig_size = item.get("size", 14)
        font_size = max(orig_size * font_ratio, 7.0)
        orig_w = bbox[2] - bbox[0]

        max_w = max(orig_w * 4.0, pw * 0.35)
        lines = wrap_text(text, font_size, max_w, use_font)
        line_height = font_size * 1.35
        text_height = line_height * len(lines)
        text_width = max(estimate_text_width(l, font_size) for l in lines)

        position = find_position_v11(bbox, text_width, text_height,
                                     [0, 0, pw, ph], placed_boxes, margin)
        if not position:
            continue

        px, py = position["bbox"][0], position["bbox"][1]

        for i, line in enumerate(lines):
            y = py + i * line_height + font_size * 0.8
            page.insert_text(
                (px, y), line,
                fontname=use_font,
                fontsize=font_size,
                color=color,
                render_mode=0,
            )

        placed_boxes.append(position["bbox"])
        item["placed_bbox"] = position["bbox"]

    doc.save(output_path)
    doc.close()
    return output_path
