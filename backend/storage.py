"""
Storage - SQLite-based persistent storage for translation review data.
Stores per-page review state so users can resume interrupted work.
"""
import sqlite3
import json
import os
from typing import List, Dict, Optional
from datetime import datetime


DB_PATH = None  # Set on init


def init_db(db_path: str):
    """Initialize SQLite database with required tables."""
    global DB_PATH
    DB_PATH = db_path
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            original_path TEXT NOT NULL,
            page_count INTEGER NOT NULL,
            current_page INTEGER DEFAULT 0,
            status TEXT DEFAULT 'scanning',
            engine TEXT DEFAULT 'google',
            api_key_encrypted TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        
        CREATE TABLE IF NOT EXISTS page_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL,
            page_num INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            frame_zone TEXT,
            items_json TEXT,
            preview_path TEXT,
            overlay_path TEXT,
            confirmed_at TEXT,
            UNIQUE(project_id, page_num),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS translation_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL,
            page_num INTEGER NOT NULL,
            item_index INTEGER NOT NULL,
            original_text TEXT NOT NULL,
            translated_text TEXT,
            confirmed_translation TEXT,
            bbox TEXT NOT NULL,
            placed_bbox TEXT,
            font_size REAL DEFAULT 14,
            status TEXT DEFAULT 'pending',
            UNIQUE(project_id, page_num, item_index),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS engine_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            current_engine TEXT DEFAULT 'google',
            deepseek_key TEXT,
            gemini_key TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        );
        
        INSERT OR IGNORE INTO engine_config (id, current_engine) VALUES (1, 'google');
    """)
    
    conn.commit()
    conn.close()


def get_conn() -> sqlite3.Connection:
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_project(file_id: str, filename: str, original_path: str,
                   page_count: int) -> Dict:
    """Create a new translation project."""
    conn = get_conn()
    conn.execute(
        "INSERT INTO projects (id, filename, original_path, page_count) VALUES (?, ?, ?, ?)",
        (file_id, filename, original_path, page_count)
    )
    conn.commit()
    conn.close()
    return {"id": file_id, "filename": filename, "page_count": page_count}


def get_project(file_id: str) -> Optional[Dict]:
    """Get project by ID."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (file_id,)).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def update_project_status(file_id: str, status: str, current_page: int = None):
    """Update project status and current page."""
    conn = get_conn()
    fields = ["status = ?", "updated_at = datetime('now')"]
    params = [status]
    if current_page is not None:
        fields.append("current_page = ?")
        params.append(current_page)
    params.append(file_id)
    conn.execute(
        f"UPDATE projects SET {', '.join(fields)} WHERE id = ?",
        params
    )
    conn.commit()
    conn.close()


def save_engine_config(engine: str, deepseek_key: str = None,
                       gemini_key: str = None):
    """Save translation engine configuration."""
    conn = get_conn()
    fields = ["current_engine = ?", "updated_at = datetime('now')"]
    params = [engine]
    if deepseek_key is not None:
        fields.append("deepseek_key = ?")
        params.append(deepseek_key)
    if gemini_key is not None:
        fields.append("gemini_key = ?")
        params.append(gemini_key)
    params.append(1)
    conn.execute(
        f"UPDATE engine_config SET {', '.join(fields)} WHERE id = ?",
        params
    )
    conn.commit()
    conn.close()


def get_engine_config() -> Dict:
    """Get current translation engine configuration."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM engine_config WHERE id = 1").fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"current_engine": "google", "deepseek_key": None, "gemini_key": None}


def save_page_data(project_id: str, page_num: int, status: str,
                   frame_zone: Dict = None, items: List[Dict] = None):
    """Save page scan/extraction results."""
    conn = get_conn()
    conn.execute("""
        INSERT INTO page_data (project_id, page_num, status, frame_zone, items_json)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(project_id, page_num) DO UPDATE SET
            status = excluded.status,
            frame_zone = excluded.frame_zone,
            items_json = excluded.items_json
    """, (
        project_id, page_num, status,
        json.dumps(frame_zone) if frame_zone else None,
        json.dumps(items) if items else None,
    ))
    conn.commit()
    conn.close()


def get_page_data(project_id: str, page_num: int) -> Optional[Dict]:
    """Get saved page data."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM page_data WHERE project_id = ? AND page_num = ?",
        (project_id, page_num)
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        if d.get("frame_zone"):
            d["frame_zone"] = json.loads(d["frame_zone"])
        if d.get("items_json"):
            d["items"] = json.loads(d["items_json"])
        return d
    return None


def get_all_page_statuses(project_id: str) -> List[Dict]:
    """Get status of all pages for a project."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT page_num, status FROM page_data WHERE project_id = ? ORDER BY page_num",
        (project_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_translation_items(project_id: str, page_num: int,
                           items: List[Dict]):
    """Save translation items for a page."""
    conn = get_conn()
    for i, item in enumerate(items):
        conn.execute("""
            INSERT INTO translation_items 
            (project_id, page_num, item_index, original_text, translated_text, 
             confirmed_translation, bbox, placed_bbox, font_size, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, page_num, item_index) DO UPDATE SET
                translated_text = excluded.translated_text,
                confirmed_translation = excluded.confirmed_translation,
                placed_bbox = excluded.placed_bbox,
                font_size = excluded.font_size,
                status = excluded.status
        """, (
            project_id, page_num, i,
            item.get("original", ""),
            item.get("translated", ""),
            item.get("confirmed_translation", ""),
            json.dumps(item.get("bbox", [])),
            json.dumps(item.get("placed_bbox")) if item.get("placed_bbox") else None,
            item.get("font_size", 14),
            item.get("status", "pending"),
        ))
    conn.commit()
    conn.close()


def get_translation_items(project_id: str, page_num: int) -> List[Dict]:
    """Get translation items for a page."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT * FROM translation_items 
           WHERE project_id = ? AND page_num = ? 
           ORDER BY item_index""",
        (project_id, page_num)
    ).fetchall()
    conn.close()
    items = []
    for row in rows:
        d = dict(row)
        d["bbox"] = json.loads(d["bbox"])
        if d.get("placed_bbox"):
            d["placed_bbox"] = json.loads(d["placed_bbox"])
        d["original"] = d.pop("original_text")
        d["translated"] = d.pop("translated_text")
        items.append(d)
    return items


def get_pages_with_text(project_id: str) -> List[int]:
    """Get list of page numbers that have translatable text."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT page_num FROM page_data WHERE project_id = ? AND status IN ('extracted', 'confirmed', 'overlayed')",
        (project_id,)
    ).fetchall()
    conn.close()
    return [r["page_num"] for r in rows]
