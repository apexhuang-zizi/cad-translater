"""
Template Manager - Save and reuse manual calibration templates for similar drawings.
When OCR fails completely, users can manually mark text positions.
Templates can be saved and auto-matched for similar drawings.
"""
import sqlite3
import json
import os
from typing import List, Dict, Optional
from datetime import datetime


def init_template_tables(db_path: str):
    """Add template tables to existing database."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS calibration_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            drawing_type TEXT,  -- e.g., 'furniture_first_piece', 'purchase_order'
            page_width REAL,
            page_height REAL,
            thumbnail_path TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS template_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            item_index INTEGER NOT NULL,
            original_text TEXT,
            bbox TEXT NOT NULL,  -- JSON [x1, y1, x2, y2]
            font_size REAL DEFAULT 14,
            placed_bbox TEXT,  -- JSON [x1, y1, x2, y2] for translation placement
            FOREIGN KEY (template_id) REFERENCES calibration_templates(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()


def save_template(db_path: str, name: str, items: List[Dict],
                  description: str = "", drawing_type: str = "",
                  page_width: float = 0, page_height: float = 0,
                  thumbnail_path: str = "") -> int:
    """Save a calibration template.
    
    Args:
        db_path: SQLite database path
        name: Template name
        items: List of {original_text, bbox, font_size, placed_bbox}
        description: Optional description
        drawing_type: Category for auto-matching
        page_width, page_height: Page dimensions for matching
        thumbnail_path: Path to thumbnail image
        
    Returns:
        Template ID
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        """INSERT INTO calibration_templates 
           (name, description, drawing_type, page_width, page_height, thumbnail_path)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (name, description, drawing_type, page_width, page_height, thumbnail_path)
    )
    template_id = cursor.lastrowid
    
    for i, item in enumerate(items):
        conn.execute(
            """INSERT INTO template_items 
               (template_id, item_index, original_text, bbox, font_size, placed_bbox)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                template_id, i,
                item.get("original", ""),
                json.dumps(item.get("bbox", [])),
                item.get("font_size", 14),
                json.dumps(item.get("placed_bbox")) if item.get("placed_bbox") else None,
            )
        )
    
    conn.commit()
    conn.close()
    return template_id


def get_template(db_path: str, template_id: int) -> Optional[Dict]:
    """Get a template by ID."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    row = conn.execute(
        "SELECT * FROM calibration_templates WHERE id = ?",
        (template_id,)
    ).fetchone()
    
    if not row:
        conn.close()
        return None
    
    template = dict(row)
    
    item_rows = conn.execute(
        "SELECT * FROM template_items WHERE template_id = ? ORDER BY item_index",
        (template_id,)
    ).fetchall()
    
    template["items"] = []
    for r in item_rows:
        item = dict(r)
        item["bbox"] = json.loads(item["bbox"])
        if item.get("placed_bbox"):
            item["placed_bbox"] = json.loads(item["placed_bbox"])
        template["items"].append(item)
    
    conn.close()
    return template


def list_templates(db_path: str, drawing_type: str = None) -> List[Dict]:
    """List all templates, optionally filtered by drawing type."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    if drawing_type:
        rows = conn.execute(
            "SELECT id, name, description, drawing_type, created_at FROM calibration_templates WHERE drawing_type = ? ORDER BY updated_at DESC",
            (drawing_type,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, name, description, drawing_type, created_at FROM calibration_templates ORDER BY updated_at DESC"
        ).fetchall()
    
    conn.close()
    return [dict(r) for r in rows]


def find_matching_template(db_path: str, page_width: float, page_height: float,
                           drawing_type: str = None,
                           tolerance: float = 0.05) -> Optional[Dict]:
    """Find a template matching the given page dimensions.
    
    Args:
        db_path: Database path
        page_width, page_height: Page dimensions to match
        drawing_type: Optional type filter
        tolerance: Size tolerance ratio (e.g., 0.05 = 5%)
        
    Returns:
        Best matching template or None
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    sql = """SELECT id, name, page_width, page_height, drawing_type 
             FROM calibration_templates 
             WHERE ABS(page_width - ?) / MAX(page_width, ?) < ?
               AND ABS(page_height - ?) / MAX(page_height, ?) < ?"""
    params = [page_width, page_width, tolerance, page_height, page_height, tolerance]
    
    if drawing_type:
        sql += " AND drawing_type = ?"
        params.append(drawing_type)
    
    sql += " ORDER BY updated_at DESC LIMIT 1"
    
    row = conn.execute(sql, params).fetchone()
    conn.close()
    
    if row:
        return get_template(db_path, row["id"])
    return None


def delete_template(db_path: str, template_id: int) -> bool:
    """Delete a template."""
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("DELETE FROM calibration_templates WHERE id = ?", (template_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def apply_template_to_page(template: Dict, page_width: float,
                           page_height: float) -> List[Dict]:
    """Apply a template to a new page, scaling coordinates if dimensions differ.
    
    Args:
        template: Template dict with items
        page_width, page_height: Target page dimensions
        
    Returns:
        List of items scaled to target page
    """
    if not template or not template.get("items"):
        return []
    
    tw, th = template.get("page_width", page_width), template.get("page_height", page_height)
    scale_x = page_width / tw if tw > 0 else 1
    scale_y = page_height / th if th > 0 else 1
    
    result = []
    for item in template["items"]:
        bbox = item["bbox"]
        placed = item.get("placed_bbox")
        
        scaled = {
            **item,
            "bbox": [
                bbox[0] * scale_x, bbox[1] * scale_y,
                bbox[2] * scale_x, bbox[3] * scale_y,
            ],
            "status": "template_applied",
            "needs_review": True,  # Always review template-applied items
        }
        
        if placed:
            scaled["placed_bbox"] = [
                placed[0] * scale_x, placed[1] * scale_y,
                placed[2] * scale_x, placed[3] * scale_y,
            ]
        
        result.append(scaled)
    
    return result
