"""
Frame Detector - Identifies standard drawing frame zones in CAD PDFs.

The frame (title block zone) is typically on the right side of the drawing,
bounded by the rightmost vertical line and a parallel inner vertical line.
Text inside this zone (title, scale, date, drawing number) should not be translated.
"""
import fitz
from typing import List, Dict, Optional, Tuple


def detect_frame_zone(pdf_path: str, page_num: int = 0) -> Optional[Dict]:
    """Detect the right-side title block zone using vertical line analysis.
    
    Strategy:
    1. Extract all vertical line segments from the page drawings
    2. Cluster them by x-coordinate
    3. Find the rightmost cluster (x > 65% of page width)
    4. The zone starts at the left edge of this cluster
    
    Returns:
        Dict with {left, right, top, bottom, description} or None
    """
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    pw = page.rect.width
    ph = page.rect.height
    
    # Extract all line segments from drawings
    drawings = page.get_drawings()
    vertical_lines = []
    
    for drawing in drawings:
        for item in drawing.get("items", []):
            if len(item) < 5:
                continue
            if item[0] == "l":  # line
                x1, y1, x2, y2 = item[1], item[2], item[3], item[4]
                dx = abs(x1 - x2)
                dy = abs(y1 - y2)
                # Vertical or near-vertical line (>10pt tall, <2pt horizontal deviation)
                if dy > 10 and dx < 2:
                    vertical_lines.append((min(x1, x2), min(y1, y2), max(y1, y2)))
    
    doc.close()
    
    if not vertical_lines:
        return None
    
    # Cluster vertical lines by x-coordinate
    clusters = cluster_lines(vertical_lines, x_threshold=20)
    
    # Find rightmost cluster that is significant
    rightmost = None
    for cx, lines in clusters.items():
        if cx > pw * 0.6 and len(lines) >= 2:  # At least 2 vertical lines for a frame
            if rightmost is None or cx > rightmost:
                rightmost = cx
    
    if rightmost is None:
        return None
    
    cluster_lines_list = clusters[rightmost]
    # Frame zone: from the leftmost line of the cluster to the right edge
    frame_left = min(l[0] for l in cluster_lines_list)
    frame_left = max(frame_left - 20, pw * 0.5)  # safety margin
    
    return {
        "left": round(frame_left, 1),
        "right": round(pw, 1),
        "top": 0.0,
        "bottom": round(ph, 1),
        "description": f"Frame zone x=[{frame_left:.0f}, {pw:.0f}]pt (right {100*(pw-frame_left)/pw:.0f}% of page)"
    }


def cluster_lines(lines: List[Tuple[float, float, float]],
                  x_threshold: float = 20.0) -> Dict[float, List[Tuple[float, float, float]]]:
    """Cluster vertical lines by their x-coordinate."""
    if not lines:
        return {}
    
    sorted_by_x = sorted(lines, key=lambda l: l[0])
    clusters = {}
    
    for line in sorted_by_x:
        x = line[0]
        placed = False
        for cx in list(clusters.keys()):
            if abs(x - cx) < x_threshold:
                clusters[cx].append(line)
                placed = True
                break
        if not placed:
            clusters[x] = [line]
    
    return clusters


def is_in_frame(bbox: List[float], frame_zone: Optional[Dict]) -> bool:
    """Check if a text bbox is inside the detected frame zone."""
    if frame_zone is None:
        return False
    x_center = (bbox[0] + bbox[2]) / 2
    return x_center > frame_zone["left"]


def detect_frame_by_text_density(pdf_path: str, page_num: int = 0) -> Optional[Dict]:
    """Alternative detection: use text density on the right side.
    
    If vector PDF text extraction shows a dense cluster of small text
    on the right 25% of the page, that's likely the title block.
    """
    import fitz as fitz_mod
    doc = fitz_mod.open(pdf_path)
    page = doc[page_num]
    pw = page.rect.width
    
    text_dict = page.get_text("dict")
    doc.close()
    
    right_quarter_x = pw * 0.75
    right_text_items = []
    
    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                bbox = span["bbox"]
                if bbox[0] > right_quarter_x:
                    right_text_items.append(span)
    
    if len(right_text_items) >= 3:
        min_x = min(s["bbox"][0] for s in right_text_items)
        return {
            "left": round(min_x - 10, 1),
            "right": round(pw, 1),
            "top": 0.0,
            "bottom": round(page.rect.height, 1),
            "description": f"Frame zone x=[{min_x-10:.0f}, {pw:.0f}]pt (text-density detection)"
        }
    
    return None


def detect_frame(pdf_path: str, page_num: int = 0) -> Optional[Dict]:
    """Combined frame detection: try line analysis first, then text density."""
    # Priority 1: Line-based detection (most accurate for CAD)
    result = detect_frame_zone(pdf_path, page_num)
    if result:
        return result
    
    # Priority 2: Text density (fallback for rasterized drawings)
    return detect_frame_by_text_density(pdf_path, page_num)
