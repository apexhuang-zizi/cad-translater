"""
DXF Processor - Native CAD text extraction & annotation overlay
===============================================================
Process DXF (Drawing Exchange Format) files natively:
- Extract TEXT/MTEXT entities with exact coordinates, height, rotation
- NO OCR needed — 100% text recognition accuracy
- Full access to drawing geometry for perfect collision avoidance
- Place Vietnamese annotations on a separate layer (can be toggled)

ezdxf reference: https://ezdxf.readthedocs.io/
"""
import os
import re
import math
import copy
from typing import List, Dict, Optional, Tuple

import ezdxf
from ezdxf.math import Vec2


# ============================================================
# View label & frame patterns (same as pdf_processor for consistency)
# ============================================================

VIEW_LABELS = re.compile(
    r'(正视图|前视图|后视图|左视图|右视图|仰视图|俯视图|剖视图|'
    r'展开图|装配图|大样图|详图|剖面图|断面图|示意图|背视图|'
    r'等轴测图|三视图|底视图|顶视图|侧视图|局部详图|安装图|'
    r'平面图|立面图|节点详图|节点图|大样|定位图|开料图|'
    r'排钻图|孔位图|结构图|分件图|部件图|组装图|包装图|'
    r'FRONT\s*VIEW|BACK\s*VIEW|LEFT\s*VIEW|RIGHT\s*VIEW|'
    r'TOP\s*VIEW|BOTTOM\s*VIEW|SECTION\s*VIEW|DETAIL\s*VIEW|'
    r'SIDE\s*VIEW|ISOMETRIC\s*VIEW|EXPLODED\s*VIEW|'
    r'SECTION|DETAIL|ELEVATION|PLAN|'
    r'VIEW\s*[A-Z]|[A-Z]\s*VIEW|'
    r'A-A|B-B|C-C|D-D|E-E|'
    r'Drawing\s*Title|Drawing Title|图纸名称)',
    re.IGNORECASE
)

FRAME_KEYWORDS = re.compile(
    r'(PROJECT|DWG|TITLE|SCALE|DATE|DRAWN|CHECKED|APPROVED|'
    r'REV|SHEET|MATERIAL|FINISH|QTY|DIMENSION|UNIT|'
    r'TOLERANCE|WEIGHT|SURFACE|NOTES|SPECIFICATION|'
    r'图纸编号|图号|比例|日期|设计|审核|批准|'
    r'版本|页数|材料|表面处理|数量|单位|'
    r'页码|共.*页|第.*页|比例尺|绘图|校对|'
    r'客户|项目名称|项目编号|图纸名称|图名)',
    re.IGNORECASE
)

# Non-translatable content
SKIP_PHRASES = [
    # English
    "FRONT VIEW", "SECTION", "REAR VIEW", "TOP VIEW", "BOTTOM VIEW",
    "RIGHT VIEW", "LEFT VIEW", "DETAIL", "DETAIL VIEW", "ELEVATION",
    "SIDE VIEW", "ISOMETRIC", "ISOMETRIC VIEW", "EXPLODED VIEW",
    "PLAN VIEW", "PLAN", "SECTION VIEW", "SECTION A-A", "SECTION B-B",
    "SCALE", "DRAWN BY", "CHECKED BY", "DRAWN", "CHECKED",
    "APPROVED BY", "APPROVED", "DATE", "JOB NO", "DWG NO", "DWG",
    "KINGWOOD", "KINGWOOD NO", "PROJECT", "TITLE", "DRAWING TITLE",
    "REV", "REV:", "REVISION", "SHEET", "PAGE",
    "Tel:", "FAX:", "http", "www", "copyright", "proprietary",
    "DESCRIPTION", "Description", "Date /", "Scale /", "Dwg No",
    "QTY", "MATERIAL", "FINISH", "SURFACE", "WEIGHT",
    "TOLERANCE", "UNIT", "DIMENSION", "SPECIFICATION",
    # Chinese
    "所有尺寸为公制", "为依据", "公司之版权所有", "如无特别说明",
    "京木(中国)创意展示", "香港九龙", "正视图", "剖视图",
    "为依据,不可用比例尺", "图纸名称", "图号", "比例", "日期",
    "设计", "审核", "批准", "绘图", "校对", "版本", "页数",
    "项目名称", "项目编号", "客户", "图名", "页码",
]


# ============================================================
# Text Entity Extraction
# ============================================================

def extract_text_entities(dxf_path: str) -> List[Dict]:
    """Extract all TEXT/MTEXT entities from a DXF file's modelspace.

    Returns list of dicts with:
        text, layer, insert(x,y), height, rotation, style, type,
        bbox(estimated), width_factor
    """
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    entities = []

    for e in msp:
        etype = e.dxftype()
        if etype not in ('TEXT', 'MTEXT'):
            continue

        try:
            if etype == 'TEXT':
                txt = e.dxf.text
            else:
                txt = e.plain_text()  # MTEXT: strip formatting codes

            if not txt or not txt.strip():
                continue

            insert = (e.dxf.insert.x, e.dxf.insert.y, e.dxf.insert.z
                      if e.dxf.hasattr('insert') and hasattr(e.dxf.insert, 'z') else 0)
            height = e.dxf.height
            rotation = e.dxf.rotation if e.dxf.hasattr('rotation') else 0.0
            width_factor = e.dxf.width if e.dxf.hasattr('width') else 1.0
            layer = e.dxf.layer
            style = e.dxf.style if e.dxf.hasattr('style') else 'STANDARD'

            # Estimate text bounding box
            # Width: approximate — CJK chars ~height wide, ASCII ~0.55*height
            cjk_count = len(re.findall(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]', txt))
            ascii_count = len(txt) - cjk_count
            est_w = (cjk_count * height + ascii_count * height * 0.55) * width_factor

            # Apply rotation to bbox
            if abs(rotation) < 0.01:
                bbox = [insert[0], insert[1] - height * 1.2,
                        insert[0] + est_w, insert[1] + height * 0.1]
            else:
                # Rotated text: use a simpler bounding box
                rad = math.radians(rotation)
                dx = est_w * math.cos(rad) - height * math.sin(rad)
                dy = est_w * math.sin(rad) + height * math.cos(rad)
                bbox = [
                    insert[0], insert[1],
                    insert[0] + dx, insert[1] + dy,
                ]
                # Normalize bbox
                bbox = [
                    min(bbox[0], bbox[2]), min(bbox[1], bbox[3]),
                    max(bbox[0], bbox[2]), max(bbox[1], bbox[3]),
                ]

            entities.append({
                'type': etype,
                'text': txt.strip(),
                'layer': layer,
                'insert': list(insert[:2]),
                'height': height,
                'rotation': rotation,
                'width_factor': width_factor,
                'style': style,
                'bbox': bbox,
            })
        except Exception as ex:
            # Skip malformed entities
            continue

    return entities


def extract_geometry_bboxes(dxf_path: str) -> List[List[float]]:
    """Extract bounding boxes of all drawing geometry (lines, circles, etc.)
    for collision avoidance when placing annotations."""
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    bboxes = []

    for e in msp:
        etype = e.dxftype()
        try:
            if etype == 'LINE':
                x0 = e.dxf.start.x
                y0 = e.dxf.start.y
                x1 = e.dxf.end.x
                y1 = e.dxf.end.y
                bboxes.append([min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)])

            elif etype == 'CIRCLE':
                cx = e.dxf.center.x
                cy = e.dxf.center.y
                r = e.dxf.radius
                bboxes.append([cx - r, cy - r, cx + r, cy + r])

            elif etype == 'ARC':
                cx = e.dxf.center.x
                cy = e.dxf.center.y
                r = e.dxf.radius
                bboxes.append([cx - r, cy - r, cx + r, cy + r])

            elif etype == 'LWPOLYLINE':
                pts = list(e.get_points('xy'))
                if pts:
                    xs = [p[0] for p in pts]
                    ys = [p[1] for p in pts]
                    # Expand by bulge radius
                    margin = max(abs(e.dxf.elevation) if e.dxf.hasattr('elevation') else 0, 5)
                    bboxes.append([
                        min(xs) - margin, min(ys) - margin,
                        max(xs) + margin, max(ys) + margin,
                    ])

            elif etype in ('POLYLINE', 'SPLINE'):
                # Simplified: use entity's bounding box from ezdxf
                try:
                    bb = e.bbox()
                    if bb.corners2d():
                        corners = list(bb.corners2d())
                        xs = [c.x for c in corners]
                        ys = [c.y for c in corners]
                        bboxes.append([min(xs), min(ys), max(xs), max(ys)])
                except Exception:
                    pass

            elif etype == 'INSERT':
                # Block reference — get block bounding box
                try:
                    bb = e.bbox()
                    if bb.corners2d():
                        corners = list(bb.corners2d())
                        xs = [c.x for c in corners]
                        ys = [c.y for c in corners]
                        bboxes.append([min(xs), min(ys), max(xs), max(ys)])
                except Exception:
                    pass

        except Exception:
            continue

    return bboxes


# ============================================================
# Text Classification
# ============================================================

def is_view_label(text: str) -> bool:
    """Check if text is a view label (not to be translated)."""
    # Exact line match for English labels
    upper = text.strip().upper()
    for skip in SKIP_PHRASES:
        if skip.upper() == upper:
            return True

    # Regex pattern match
    if VIEW_LABELS.search(text):
        return True

    if FRAME_KEYWORDS.search(text):
        return True

    return False


def has_chinese(text: str) -> bool:
    """Check if text contains Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def has_significant_en(text: str) -> bool:
    """Check if text contains significant English content (>3 chars)."""
    en_chars = re.findall(r'[a-zA-Z]{3,}', text)
    return len(en_chars) > 0 and sum(len(c) for c in en_chars) > 3


def classify_entities(entities: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Classify extracted entities into translatable and skip.

    Returns (translatable, skipped).
    """
    translatable = []
    skipped = []

    for ent in entities:
        text = ent['text'].strip()

        # Skip view labels and frame text
        if is_view_label(text):
            skipped.append({**ent, 'reason': 'view_label'})
            continue

        # Skip pure ASCII words that are clearly codes/identifiers
        if re.match(r'^[A-Z0-9_\-\.]+$', text) and len(text) < 8:
            skipped.append({**ent, 'reason': 'code/label'})
            continue

        # Skip dimension-only text (e.g. "350", "1200", "R5")
        if re.match(r'^[\d.,xX×\+\-\sRrØøMm]+$', text):
            skipped.append({**ent, 'reason': 'dimension'})
            continue

        translatable.append(ent)

    return translatable, skipped


def get_dxf_bounds(dxf_path: str) -> Dict:
    """Get the overall bounding box of the DXF drawing."""
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    try:
        # Try ezdxf's built-in bbox calculation
        bb = msp.bbox()
        corners = list(bb.corners2d())
        xs = [c.x for c in corners]
        ys = [c.y for c in corners]
        bounds = {
            'x_min': min(xs), 'y_min': min(ys),
            'x_max': max(xs), 'y_max': max(ys),
            'width': max(xs) - min(xs),
            'height': max(ys) - min(ys),
        }
    except Exception:
        # Fallback: scan all entities
        x_vals, y_vals = [], []
        for e in msp:
            if e.dxftype() in ('TEXT', 'MTEXT'):
                x_vals.append(e.dxf.insert.x)
                y_vals.append(e.dxf.insert.y)
            elif e.dxftype() == 'LINE':
                x_vals.extend([e.dxf.start.x, e.dxf.end.x])
                y_vals.extend([e.dxf.start.y, e.dxf.end.y])
        bounds = {
            'x_min': min(x_vals) if x_vals else 0,
            'y_min': min(y_vals) if y_vals else 0,
            'x_max': max(x_vals) if x_vals else 1000,
            'y_max': max(y_vals) if y_vals else 1000,
            'width': (max(x_vals) - min(x_vals)) if x_vals else 1000,
            'height': (max(y_vals) - min(y_vals)) if y_vals else 1000,
        }

    return bounds


# ============================================================
# Annotation Placement (DXF)
# ============================================================

def boxes_overlap(a: List[float], b: List[float]) -> bool:
    """Check if two bounding boxes overlap."""
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def find_annotation_position(
    text_bbox: List[float],
    ann_width: float,
    ann_height: float,
    drawing_bounds: Dict,
    geometry_bboxes: List[List[float]],
    placed_boxes: List[List[float]],
    margin: float = 5.0,
) -> Optional[List[float]]:
    """Find the best position for a Vietnamese annotation near the original text.
    Checks collision with: drawing geometry, other text entities, and already-placed annotations.

    Priority: right → below → above → left
    """
    x0, y0, x1, y1 = text_bbox
    dx_min, dy_min = drawing_bounds['x_min'], drawing_bounds['y_min']
    dx_max, dy_max = drawing_bounds['x_max'], drawing_bounds['y_max']

    candidates = [
        {
            'dir': 'right',
            'bbox': [x1 + margin, y0, x1 + margin + ann_width, y0 + ann_height],
        },
        {
            'dir': 'below',
            'bbox': [x0, y1 + margin, x0 + ann_width, y1 + margin + ann_height],
        },
        {
            'dir': 'above',
            'bbox': [x0, y0 - ann_height - margin, x0 + ann_width, y0 - margin],
        },
        {
            'dir': 'left',
            'bbox': [x0 - ann_width - margin, y0, x0 - margin, y0 + ann_height],
        },
    ]

    # Shift below candidates right if the text is wide
    if (x1 - x0) > ann_width * 0.8:
        # Narrow annotations can go under the right side
        candidates.insert(3, {
            'dir': 'below-right',
            'bbox': [x1 - ann_width, y1 + margin, x1, y1 + margin + ann_height],
        })

    all_obstacles = geometry_bboxes + placed_boxes

    for cand in candidates:
        cb = cand['bbox']

        # Check bounds
        if cb[0] < dx_min or cb[1] < dy_min or cb[2] > dx_max or cb[3] > dy_max:
            continue

        # Check collision with all obstacles
        collision = False
        for obs in all_obstacles:
            if boxes_overlap(cb, obs):
                collision = True
                break

        if not collision:
            return cb

    # Fallback: bottom-right offset
    fallback = [x1 + margin * 2, y1 + margin * 3,
                x1 + margin * 2 + ann_width, y1 + margin * 3 + ann_height]
    return fallback


# ============================================================
# DXF Output — Create annotated copy
# ============================================================

def create_annotated_dxf(
    dxf_path: str,
    translations: List[Dict],
    output_path: str,
    annotation_layer: str = "VI_ANNOTATIONS",
    annotation_color: int = 1,  # Red
    annotation_style: str = 'STANDARD',
) -> str:
    """Create an annotated copy of the DXF with Vietnamese translations
    on a separate layer.

    Args:
        dxf_path: Path to original DXF
        translations: [{text, translated_text, bbox, insert?, height?, ...}, ...]
        output_path: Where to save annotated DXF
        annotation_layer: Layer name for Vietnamese annotations
        annotation_color: ACI color (1=red)
        annotation_style: Text style to use
    """
    doc = ezdxf.readfile(dxf_path)

    # Create annotation layer
    if annotation_layer not in doc.layers:
        doc.layers.add(name=annotation_layer, color=annotation_color)

    msp = doc.modelspace()

    # Extract geometry for collision detection
    geometry_bboxes = extract_geometry_bboxes(dxf_path)
    bounds = get_dxf_bounds(dxf_path)
    placed_boxes = []

    for item in translations:
        text = item.get('translated_text', '')
        if not text:
            continue

        bbox = item.get('bbox', [0, 0, 50, 20])
        orig_height = item.get('height', 4.0)
        ann_height = orig_height * 0.85
        ann_width = len(text) * ann_height * 0.55

        # Find placement
        ann_bbox = find_annotation_position(
            bbox, ann_width, ann_height,
            bounds, geometry_bboxes, placed_boxes,
        )

        if ann_bbox:
            insert_x = ann_bbox[0]
            insert_y = ann_bbox[1] + ann_height  # ezdxf text insert is bottom-left

            # Add Vietnamese annotation text
            msp.add_text(
                text,
                dxfattribs={
                    'insert': (insert_x, insert_y),
                    'height': ann_height,
                    'layer': annotation_layer,
                    'style': annotation_style,
                }
            )

            placed_boxes.append(ann_bbox)

    doc.saveas(output_path)
    return output_path


def create_numbered_annotations_dxf(
    dxf_path: str,
    translations: List[Dict],
    output_path: str,
    annotation_layer: str = "VI_ANNOTATIONS",
    annotation_color: int = 1,
) -> str:
    """Create DXF with numbered markers at original positions and a
    translation table in a clear area."""
    doc = ezdxf.readfile(dxf_path)

    if annotation_layer not in doc.layers:
        doc.layers.add(name=annotation_layer, color=annotation_color)

    # Create table layer
    table_layer = f"{annotation_layer}_TABLE"
    if table_layer not in doc.layers:
        doc.layers.add(name=table_layer, color=7)  # White/Black

    msp = doc.modelspace()
    geometry_bboxes = extract_geometry_bboxes(dxf_path)
    bounds = get_dxf_bounds(dxf_path)

    circled = [chr(0x2460 + i) for i in range(20)]  # ①-⑳

    valid_items = []
    marker_boxes = []
    marker_height = 4.0

    for idx, item in enumerate(translations):
        text = item.get('translated_text', '')
        if not text:
            continue

        bbox = item.get('bbox', [0, 0, 50, 20])
        marker = circled[idx] if idx < len(circled) else f"({idx+1})"

        # Place marker near original text
        mx = bbox[0] - 2
        my = bbox[3] + 2  # Just above original

        msp.add_text(
            marker,
            dxfattribs={
                'insert': (mx, my),
                'height': marker_height,
                'layer': annotation_layer,
                'color': annotation_color,
            }
        )

        marker_boxes.append([mx - 5, my - 5, mx + 20, my + marker_height + 5])
        valid_items.append({
            'marker': marker,
            'original': item.get('text', ''),
            'translated': text,
        })

    if not valid_items:
        doc.saveas(output_path)
        return output_path

    # Find clear area for table (try top-right, bottom-right, then center-right)
    table_x = bounds['x_max'] * 0.55
    table_y = bounds['y_max'] - 20
    line_height = marker_height * 1.8

    # Header
    msp.add_text(
        "Dịch thuật / 翻译",
        dxfattribs={
            'insert': (table_x, table_y),
            'height': marker_height + 1,
            'layer': table_layer,
        }
    )

    table_y -= line_height * 1.5

    # Entries
    for entry in valid_items:
        if table_y < bounds['y_min'] + 50:
            break

        msp.add_text(
            f"{entry['marker']} → {entry['translated']}",
            dxfattribs={
                'insert': (table_x, table_y),
                'height': marker_height,
                'layer': table_layer,
            }
        )
        table_y -= line_height

    doc.saveas(output_path)
    return output_path
