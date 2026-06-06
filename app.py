"""
CAD Translator - Flask Backend
Hybrid Architecture: Vector extraction | AI Vision OCR | Template matching | Manual calibration
"""
import os
import sys
import uuid
import json
from pathlib import Path

from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.pdf_processor import (
    get_pdf_info, is_raster_pdf, extract_text_spans,
    merge_adjacent_items, filter_translatable_items,
    render_page_preview, apply_translations,
    apply_translations_with_draft,
)
from backend.ocr_engine import ocr_page, is_tesseract_available, get_available_languages
from backend.surya_ocr import run_raster_ocr, is_surya_available
from backend.ai_vision_engine import ai_vision_extract, scale_bboxes_to_pdf, is_gemini_available
from backend.translator import translate, test_api_key
from backend.frame_detector import detect_frame, is_in_frame
from backend.template_manager import (
    init_template_tables, save_template, get_template, list_templates,
    find_matching_template, delete_template, apply_template_to_page,
)
from backend.storage import (
    init_db, create_project, get_project, update_project_status,
    save_page_data, get_page_data, get_all_page_statuses,
    save_translation_items, get_translation_items, get_pages_with_text,
    save_engine_config, get_engine_config,
)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
PREVIEW_DIR = os.path.join(BASE_DIR, "data", "previews")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")
DB_PATH = os.path.join(BASE_DIR, "data", "cad_translator.db")
FONT_PATH = os.path.join(BASE_DIR, "fonts", "NotoSansCJK-VF.ttf")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Initialize database
init_db(DB_PATH)
init_template_tables(DB_PATH)

# Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB


# ============================================================
# Static Pages
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


# ============================================================
# PDF Upload & Info
# ============================================================

@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Upload a PDF file and create a new project."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400
    
    file_id = uuid.uuid4().hex[:12]
    save_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")
    file.save(save_path)
    
    try:
        info = get_pdf_info(save_path)
    except Exception as e:
        os.remove(save_path)
        return jsonify({"error": f"Failed to read PDF: {str(e)}"}), 400
    
    project = create_project(file_id, file.filename, save_path, info["page_count"])
    
    return jsonify({
        "file_id": file_id,
        "filename": file.filename,
        "page_count": info["page_count"],
        "pages": info["pages"],
    })


@app.route("/api/pdf/<file_id>/info", methods=["GET"])
def api_pdf_info(file_id):
    """Get detailed PDF information."""
    project = get_project(file_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    info = get_pdf_info(project["original_path"])
    return jsonify(info)


# ============================================================
# PDF Scanning - Hybrid: Vector | AI Vision | Template | Manual
# ============================================================

@app.route("/api/pdf/<file_id>/scan", methods=["POST"])
def api_scan(file_id):
    """Scan all pages with hybrid detection."""
    project = get_project(file_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    pdf_path = project["original_path"]
    engine_config = get_engine_config()
    
    pages_with_text = []
    total_pages = project["page_count"]
    scan_results = []
    
    for page_num in range(total_pages):
        is_vector = not is_raster_for_page(pdf_path, page_num)
        
        if is_vector:
            spans = extract_text_spans(pdf_path, page_num)
            merged = merge_adjacent_items(spans)
            frame_zone = detect_frame(pdf_path, page_num)
            translatable = filter_translatable_items(merged, frame_zone)
            
            scan_results.append({
                "page": page_num,
                "type": "vector",
                "total_items": len(merged),
                "translatable_count": len(translatable),
                "frame_zone": frame_zone,
            })
            
            if len(translatable) > 0:
                pages_with_text.append(page_num)
                save_page_data(file_id, page_num, "extracted",
                              frame_zone=frame_zone, items=translatable)
            else:
                save_page_data(file_id, page_num, "no_text")
        else:
            # Raster page - check for matching template first
            import fitz
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            pw, ph = page.rect.width, page.rect.height
            doc.close()
            
            template = find_matching_template(DB_PATH, pw, ph)
            
            scan_results.append({
                "page": page_num,
                "type": "raster",
                "total_items": 0,
                "translatable_count": 0,
                "frame_zone": None,
                "needs_ocr": True,
                "has_template": template is not None,
                "template_name": template["name"] if template else None,
            })
            pages_with_text.append(page_num)
            save_page_data(file_id, page_num, "needs_ocr")
    
    update_project_status(file_id, "scanned")
    
    return jsonify({
        "total_pages": total_pages,
        "pages_with_text": len(pages_with_text),
        "page_list": pages_with_text,
        "scan_results": scan_results,
        "engine_config": {
            "current": engine_config["current_engine"],
            "tesseract_available": is_tesseract_available(),
            "surya_available": is_surya_available(),
            "gemini_available": is_gemini_available(engine_config.get("gemini_key", "")),
        },
    })


def is_raster_for_page(pdf_path: str, page_num: int) -> bool:
    """Check if a specific page is rasterized."""
    import fitz
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    text = page.get_text().strip()
    doc.close()
    return len(text) == 0


# ============================================================
# Page Preview
# ============================================================

@app.route("/api/pdf/<file_id>/page/<int:page_num>/preview", methods=["GET"])
def api_page_preview(file_id, page_num):
    """Render a PDF page as PNG image."""
    project = get_project(file_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    preview_path = os.path.join(PREVIEW_DIR, f"{file_id}_p{page_num}.png")
    render_page_preview(project["original_path"], page_num, preview_path)
    
    return send_file(preview_path, mimetype="image/png")


# ============================================================
# Text Extraction per Page
# ============================================================

@app.route("/api/pdf/<file_id>/page/<int:page_num>/extract", methods=["GET"])
def api_extract_page(file_id, page_num):
    """Extract text items from a specific page."""
    project = get_project(file_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    pdf_path = project["original_path"]
    
    if is_raster_for_page(pdf_path, page_num):
        return jsonify({
            "type": "raster",
            "needs_ocr": True,
            "tesseract_available": is_tesseract_available(),
            "surya_available": is_surya_available(),
            "languages": get_available_languages(),
        })
    
    spans = extract_text_spans(pdf_path, page_num)
    merged = merge_adjacent_items(spans)
    frame_zone = detect_frame(pdf_path, page_num)
    translatable = filter_translatable_items(merged, frame_zone)
    
    return jsonify({
        "type": "vector",
        "page": page_num,
        "total_items": len(merged),
        "translatable_count": len(translatable),
        "frame_zone": frame_zone,
        "items": translatable,
    })


# ============================================================
# Hybrid OCR: AI Vision → Tesseract → Template → Manual
# ============================================================

@app.route("/api/pdf/<file_id>/page/<int:page_num>/ocr", methods=["POST"])
def api_ocr_page(file_id, page_num):
    """Run hybrid OCR on a raster PDF page.
    
    Priority:
    1. Surya detection + Tesseract per-region (best for CAD raster)
    2. AI Vision (Gemini) if API key available
    3. Tesseract stand-alone fallback
    4. Template matching fallback
    5. Raw fallback for manual calibration
    """
    project = get_project(file_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    data = request.get_json() or {}
    use_ai = data.get("use_ai", True)
    
    # Render page to high-res image
    preview_path = os.path.join(PREVIEW_DIR, f"{file_id}_p{page_num}_ocr.png")
    render_page_preview(project["original_path"], page_num, preview_path, dpi=300)
    
    # Get image dimensions for bbox scaling
    from PIL import Image
    with Image.open(preview_path) as img:
        img_w, img_h = img.size
    
    # Get PDF dimensions
    import fitz
    doc = fitz.open(project["original_path"])
    page = doc[page_num]
    pdf_w, pdf_h = page.rect.width, page.rect.height
    doc.close()
    
    engine_config = get_engine_config()
    gemini_key = engine_config.get("gemini_key", "")
    
    items = []
    extraction_method = "none"
    warning = ""
    
    # Tier 1: Surya detection + Tesseract per-region (proven for CAD raster)
    if is_surya_available() and is_tesseract_available():
        try:
            surya_result = run_raster_ocr(preview_path)
            if surya_result["translatable"] > 0:
                # Scale image bboxes to PDF coordinates
                scale_x = pdf_w / img_w
                scale_y = pdf_h / img_h
                for it in surya_result["items"]:
                    bx = it["bbox"]
                    items.append({
                        "text": it["text"],
                        "bbox": [
                            bx[0] * scale_x, bx[1] * scale_y,
                            bx[2] * scale_x, bx[3] * scale_y,
                        ],
                        "size": (bx[3] - bx[1]) * scale_y * 0.8,
                        "surya_idx": it["idx"],
                    })
                extraction_method = "surya_tesseract"
                warning = f"Surya+Tesseract: {surya_result['total_detected']} regions detected, {surya_result['translatable']} translatable items extracted."
            else:
                # Surya ran but nothing translatable - save raw for manual
                if surya_result.get("raw_items"):
                    scale_x = pdf_w / img_w
                    scale_y = pdf_h / img_h
                    for it in surya_result["raw_items"]:
                        bx = it["bbox"]
                        items.append({
                            "text": it["text"],
                            "bbox": [
                                bx[0] * scale_x, bx[1] * scale_y,
                                bx[2] * scale_x, bx[3] * scale_y,
                            ],
                            "size": (bx[3] - bx[1]) * scale_y * 0.8,
                            "status": "raw_ocr",
                            "needs_review": True,
                        })
                    extraction_method = "surya_tesseract"
                    warning = f"Surya+Tesseract: {surya_result['ocr_results']} OCR results, but none passed translatable filter. Showing raw for manual review."
        except Exception as e:
            app.logger.warning(f"Surya+Tesseract failed: {e}")
            warning = f"Surya+Tesseract failed: {e}. Trying fallbacks."
    
    # Tier 2: AI Vision (Gemini)
    if not items and use_ai and gemini_key and is_gemini_available(gemini_key):
        try:
            ai_items = ai_vision_extract(preview_path, gemini_key, engine="gemini")
            if ai_items:
                items = scale_bboxes_to_pdf(ai_items, img_w, img_h, pdf_w, pdf_h)
                extraction_method = "ai_vision"
                warning = "AI Vision extraction completed. Please review each item."
        except Exception as e:
            app.logger.warning(f"AI Vision failed: {e}")
            if not warning:
                warning = f"AI Vision failed: {e}."
    
    # Tier 3: Tesseract stand-alone
    if not items and is_tesseract_available():
        try:
            tess_items = ocr_page(preview_path)
            if tess_items:
                items = tess_items
                extraction_method = "tesseract"
                if not warning:
                    warning = "Tesseract OCR completed. CAD raster accuracy may be low - review carefully."
        except Exception as e:
            app.logger.warning(f"Tesseract failed: {e}")
            if not warning:
                warning = f"Tesseract failed: {e}."
    
    # Tier 3: Template matching
    if not items:
        template = find_matching_template(DB_PATH, pdf_w, pdf_h)
        if template:
            items = apply_template_to_page(template, pdf_w, pdf_h)
            extraction_method = "template"
            warning = f"Applied template '{template['name']}'. Please verify all positions."
    
    # Process items
    merged = merge_adjacent_items(items, gap_threshold=30) if items else []
    frame_zone = detect_frame(project["original_path"], page_num)
    translatable = filter_translatable_items(merged, frame_zone)
    
    # Fallback: if nothing translatable but we have raw items, show them
    if not translatable and merged:
        raw_fallback = []
        for item in merged:
            raw_fallback.append({**item, "status": "raw_ocr", "needs_review": True})
        translatable = raw_fallback
    
    # If still nothing, return empty for manual calibration
    if not translatable:
        return jsonify({
            "type": "raster_ocr",
            "page": page_num,
            "total_items": 0,
            "translatable_count": 0,
            "frame_zone": frame_zone,
            "items": [],
            "extraction_method": extraction_method,
            "warning": warning or "No text detected. Please use manual calibration mode.",
            "needs_manual": True,
        })
    
    save_page_data(file_id, page_num, "extracted",
                  frame_zone=frame_zone, items=translatable)
    
    return jsonify({
        "type": "raster_ocr",
        "page": page_num,
        "total_items": len(merged),
        "translatable_count": len(translatable),
        "frame_zone": frame_zone,
        "items": translatable,
        "extraction_method": extraction_method,
        "warning": warning,
        "needs_manual": False,
    })


# ============================================================
# Manual Calibration - Add items by clicking on canvas
# ============================================================

@app.route("/api/pdf/<file_id>/page/<int:page_num>/manual", methods=["POST"])
def api_manual_add(file_id, page_num):
    """Add a manually calibrated text item."""
    project = get_project(file_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    bbox = data.get("bbox", [0, 0, 100, 20])
    
    if not text:
        return jsonify({"error": "Text is required"}), 400
    
    # Get existing items
    page_data = get_page_data(file_id, page_num)
    items = page_data.get("items", []) if page_data else []
    
    new_item = {
        "text": text,
        "bbox": bbox,
        "status": "manual",
        "needs_review": True,
        "confidence": 1.0,
    }
    items.append(new_item)
    
    save_page_data(file_id, page_num, "extracted", items=items)
    
    return jsonify({
        "page": page_num,
        "item_index": len(items) - 1,
        "item": new_item,
        "total_items": len(items),
    })


@app.route("/api/pdf/<file_id>/page/<int:page_num>/manual", methods=["DELETE"])
def api_manual_clear(file_id, page_num):
    """Clear all manual items for a page."""
    project = get_project(file_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    save_page_data(file_id, page_num, "needs_ocr", items=[])
    
    return jsonify({"status": "cleared", "page": page_num})


# ============================================================
# Template Management
# ============================================================

@app.route("/api/templates", methods=["GET"])
def api_list_templates():
    """List all calibration templates."""
    drawing_type = request.args.get("type", None)
    templates = list_templates(DB_PATH, drawing_type)
    return jsonify({"templates": templates})


@app.route("/api/templates", methods=["POST"])
def api_save_template():
    """Save current page items as a template."""
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    items = data.get("items", [])
    description = data.get("description", "")
    drawing_type = data.get("drawing_type", "")
    page_width = data.get("page_width", 0)
    page_height = data.get("page_height", 0)
    
    if not name or not items:
        return jsonify({"error": "Name and items are required"}), 400
    
    template_id = save_template(
        DB_PATH, name, items,
        description=description,
        drawing_type=drawing_type,
        page_width=page_width,
        page_height=page_height,
    )
    
    return jsonify({"template_id": template_id, "name": name})


@app.route("/api/templates/<int:template_id>", methods=["GET"])
def api_get_template(template_id):
    """Get a specific template."""
    template = get_template(DB_PATH, template_id)
    if not template:
        return jsonify({"error": "Template not found"}), 404
    return jsonify(template)


@app.route("/api/templates/<int:template_id>", methods=["DELETE"])
def api_delete_template(template_id):
    """Delete a template."""
    if delete_template(DB_PATH, template_id):
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Template not found"}), 404


@app.route("/api/templates/<int:template_id>/apply", methods=["POST"])
def api_apply_template(template_id):
    """Apply a template to current page."""
    data = request.get_json() or {}
    page_width = data.get("page_width", 0)
    page_height = data.get("page_height", 0)
    
    template = get_template(DB_PATH, template_id)
    if not template:
        return jsonify({"error": "Template not found"}), 404
    
    items = apply_template_to_page(template, page_width, page_height)
    
    return jsonify({
        "template_name": template["name"],
        "items": items,
        "item_count": len(items),
    })


# ============================================================
# Translation
# ============================================================

@app.route("/api/pdf/<file_id>/page/<int:page_num>/translate", methods=["POST"])
def api_translate_page(file_id, page_num):
    """Translate extracted text items."""
    project = get_project(file_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    data = request.get_json() or {}
    engine = data.get("engine", "google")
    api_key = data.get("api_key", "")
    items = data.get("items", [])
    
    if not items:
        page_data = get_page_data(file_id, page_num)
        if page_data and page_data.get("items"):
            items = page_data["items"]
        else:
            return jsonify({"error": "No items to translate"}), 400
    
    texts = [item.get("text", "") for item in items]
    
    try:
        results = translate(texts, engine=engine, api_key=api_key or None)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Translation failed: {str(e)}"}), 500
    
    response_items = []
    for i, item in enumerate(items):
        r = dict(item)
        r["original"] = item.get("text", "")
        r["translated"] = results[i]["translated"] if i < len(results) else ""
        r["engine"] = engine
        r["success"] = results[i]["success"] if i < len(results) else False
        if not r["success"] and i < len(results):
            r["error"] = results[i].get("error", "")
        response_items.append(r)
    
    save_translation_items(file_id, page_num, response_items)
    
    return jsonify({
        "engine": engine,
        "items": response_items,
    })


# ============================================================
# Overlay / Apply Translations
# ============================================================

@app.route("/api/pdf/<file_id>/page/<int:page_num>/overlay", methods=["POST"])
def api_overlay_page(file_id, page_num):
    """Apply translations to a PDF page (generate preview with translations)."""
    project = get_project(file_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    data = request.get_json() or {}
    items = data.get("items", [])
    
    if not items:
        items = get_translation_items(file_id, page_num)
    
    if not items:
        return jsonify({"error": "No translation items"}), 400
    
    translations = []
    for item in items:
        text = item.get("confirmed_translation") or item.get("translated", "")
        if not text:
            continue
        translations.append({
            "id": item.get("item_index", 0),
            "bbox": item.get("bbox", [0, 0, 100, 20]),
            "translated_text": text,
            "size": item.get("font_size", 10),
            "confirmed": item.get("status") == "confirmed",
        })
    
    if not translations:
        return jsonify({"error": "No confirmed translations to overlay"}), 400
    
    output_path = os.path.join(PREVIEW_DIR, f"{file_id}_p{page_num}_overlay.pdf")
    
    try:
        apply_translations_with_draft(
            project["original_path"], page_num, translations, output_path,
            font_path=FONT_PATH if os.path.exists(FONT_PATH) else None,
        )
    except Exception as e:
        return jsonify({"error": f"Overlay failed: {str(e)}"}), 500
    
    import fitz
    doc = fitz.open(output_path)
    page = doc[page_num if page_num < len(doc) else 0]
    mat = fitz.Matrix(200/72, 200/72)
    pix = page.get_pixmap(matrix=mat)
    preview_img = os.path.join(PREVIEW_DIR, f"{file_id}_p{page_num}_preview.png")
    pix.save(preview_img)
    doc.close()
    
    for item in translations:
        if "placed_bbox" not in item:
            item["placed_bbox"] = None
    
    for t in translations:
        for item in items:
            if item.get("item_index") == t["id"]:
                item["placed_bbox"] = t.get("placed_bbox")
    
    save_translation_items(file_id, page_num, items)
    save_page_data(file_id, page_num, "overlayed")
    
    return jsonify({
        "preview_url": f"/api/pdf/{file_id}/page/{page_num}/preview/overlay",
        "items": items,
    })


@app.route("/api/pdf/<file_id>/page/<int:page_num>/preview/overlay", methods=["GET"])
def api_overlay_preview(file_id, page_num):
    """Serve the overlay preview image."""
    preview_img = os.path.join(PREVIEW_DIR, f"{file_id}_p{page_num}_preview.png")
    if not os.path.exists(preview_img):
        return jsonify({"error": "Preview not generated yet"}), 404
    return send_file(preview_img, mimetype="image/png")


# ============================================================
# Page Confirmation
# ============================================================

@app.route("/api/pdf/<file_id>/page/<int:page_num>/confirm", methods=["POST"])
def api_confirm_page(file_id, page_num):
    """Confirm translations for a page, apply overlay to PDF, and save to storage."""
    project = get_project(file_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    data = request.get_json() or {}
    items = data.get("items", [])
    
    if items:
        save_translation_items(file_id, page_num, items)
    else:
        items = get_translation_items(file_id, page_num) or []
    
    translations = []
    for item in items:
        text = item.get("confirmed_translation") or item.get("translated", "")
        if not text:
            continue
        translations.append({
            "id": item.get("item_index", 0),
            "bbox": item.get("bbox", [0, 0, 100, 20]),
            "translated_text": text,
            "size": item.get("font_size", 10),
            "confirmed": item.get("status") == "confirmed",
            "placed_bbox": item.get("placed_bbox"),
        })
    
    overlay_applied = False
    if translations:
        try:
            output_path = os.path.join(PREVIEW_DIR, f"{file_id}_p{page_num}_overlay.pdf")
            apply_translations_with_draft(
                project["original_path"], page_num, translations, output_path,
                font_path=FONT_PATH if os.path.exists(FONT_PATH) else None,
            )
            
            import fitz
            doc = fitz.open(output_path)
            page = doc[page_num if page_num < len(doc) else 0]
            mat = fitz.Matrix(200 / 72, 200 / 72)
            pix = page.get_pixmap(matrix=mat)
            preview_img = os.path.join(PREVIEW_DIR, f"{file_id}_p{page_num}_preview.png")
            pix.save(preview_img)
            doc.close()
            
            overlay_applied = True
        except Exception as e:
            app.logger.warning(f"Overlay generation failed for page {page_num}: {e}")
    
    save_page_data(file_id, page_num, "confirmed")
    
    return jsonify({
        "page": page_num,
        "status": "confirmed",
        "items_saved": len(items),
        "overlay_applied": overlay_applied,
        "preview_url": f"/api/pdf/{file_id}/page/{page_num}/preview/overlay" if overlay_applied else None,
    })


# ============================================================
# Finalize / Build Final PDF
# ============================================================

@app.route("/api/pdf/<file_id>/finalize", methods=["POST"])
def api_finalize(file_id):
    """Build the final PDF with all translations applied."""
    project = get_project(file_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    pages_with_text = get_pages_with_text(file_id)
    
    if not pages_with_text:
        return jsonify({"error": "No pages have been processed"}), 400
    
    import fitz
    from backend.pdf_processor import apply_translations
    
    output_filename = project["filename"].replace(".pdf", "_越南文版.pdf")
    output_path = os.path.join(OUTPUT_DIR, f"{file_id}_final.pdf")
    
    doc = fitz.open(project["original_path"])
    
    for page_num in pages_with_text:
        items = get_translation_items(file_id, page_num)
        if not items:
            continue
        
        translations = []
        for item in items:
            text = item.get("confirmed_translation") or item.get("translated", "")
            if not text:
                continue
            translations.append({
                "bbox": item["bbox"],
                "translated_text": text,
                "size": item.get("font_size", 10),
            })
        
        if translations:
            apply_translations(
                project["original_path"], page_num, translations,
                output_path,
                font_path=FONT_PATH if os.path.exists(FONT_PATH) else None,
                font_ratio=0.72,
            )
    
    doc.close()
    
    import shutil
    final_dest = os.path.join(OUTPUT_DIR, output_filename)
    shutil.copy(output_path, final_dest)
    
    update_project_status(file_id, "completed")
    
    return jsonify({
        "output_path": final_dest,
        "output_filename": output_filename,
        "pages_processed": len(pages_with_text),
    })


@app.route("/api/pdf/<file_id>/download", methods=["GET"])
def api_download(file_id):
    """Download the final translated PDF."""
    project = get_project(file_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    output_filename = project["filename"].replace(".pdf", "_越南文版.pdf")
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    if not os.path.exists(output_path):
        output_path = os.path.join(OUTPUT_DIR, f"{file_id}_final.pdf")
    
    if not os.path.exists(output_path):
        return jsonify({"error": "Final PDF not generated yet"}), 404
    
    return send_file(
        output_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=output_filename,
    )


# ============================================================
# Engine Configuration
# ============================================================

@app.route("/api/engine/config", methods=["GET"])
def api_get_engine_config():
    """Get current engine configuration (without API keys)."""
    config = get_engine_config()
    gemini_key = config.get("gemini_key", "")
    return jsonify({
        "current_engine": config["current_engine"],
        "has_deepseek_key": bool(config.get("deepseek_key")),
        "has_gemini_key": bool(gemini_key),
        "gemini_available": is_gemini_available(gemini_key) if gemini_key else False,
    })


@app.route("/api/engine/config", methods=["POST"])
def api_set_engine_config():
    """Update engine configuration."""
    data = request.get_json() or {}
    engine = data.get("engine", "google")
    deepseek_key = data.get("deepseek_key", "")
    gemini_key = data.get("gemini_key", "")
    
    save_engine_config(
        engine=engine,
        deepseek_key=deepseek_key or None,
        gemini_key=gemini_key or None,
    )
    
    return jsonify({"status": "ok", "engine": engine})


@app.route("/api/engine/test", methods=["POST"])
def api_test_engine():
    """Test a translation API key."""
    data = request.get_json() or {}
    engine = data.get("engine", "google")
    api_key = data.get("api_key", "")
    
    if engine == "google":
        return jsonify({"valid": True, "message": "Google Translate is always available"})
    
    result = test_api_key(engine, api_key)
    return jsonify(result)


# ============================================================
# Project Status / Resume
# ============================================================

@app.route("/api/project/<file_id>/status", methods=["GET"])
def api_project_status(file_id):
    """Get full project status for resume."""
    project = get_project(file_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    page_statuses = get_all_page_statuses(file_id)
    pages_with_text = get_pages_with_text(file_id)
    
    return jsonify({
        "file_id": file_id,
        "filename": project["filename"],
        "page_count": project["page_count"],
        "current_page": project["current_page"],
        "status": project["status"],
        "page_statuses": page_statuses,
        "pages_with_text": pages_with_text,
        "engine_config": get_engine_config(),
    })


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  CAD Translator Server - Hybrid Architecture")
    print("  Vector | AI Vision | Template | Manual")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
