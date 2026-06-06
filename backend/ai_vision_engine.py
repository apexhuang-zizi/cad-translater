"""
AI Vision OCR Engine - Uses Gemini/GPT-4o to extract text from raster CAD drawings.
Falls back gracefully when API is unavailable.
"""
import base64
import json
import os
import re
from typing import List, Dict, Optional
import requests


GEMINI_VISION_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# Prompt engineered for CAD drawing text extraction
CAD_VISION_PROMPT = """You are analyzing a CAD engineering drawing image.
Your task: Extract ALL Chinese and English text annotations visible in the image.

For each text annotation, provide:
1. The exact text content (preserve Chinese/English as-is)
2. Approximate bounding box coordinates [x1, y1, x2, y2] in pixel coordinates (0-1000 scale)
3. Confidence score (0.0-1.0)

Rules:
- Focus on annotation text near drawing elements, NOT title block/frame text
- Ignore view labels like "FRONT VIEW", "A-A", "SECTION"
- Ignore dimension numbers like "100", "50.5" unless they have accompanying text
- Include mixed Chinese-English text like "MTLF-01 = MT-103 不锈钢镜电镀"
- If text is very small/blurry, mark confidence < 0.5

Output format (strict JSON):
{
  "annotations": [
    {"text": "...", "bbox": [x1, y1, x2, y2], "confidence": 0.95},
    ...
  ]
}

If no readable text found, return {"annotations": []}."""


def encode_image(image_path: str) -> str:
    """Encode image to base64 string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def ai_vision_extract(image_path: str, api_key: str,
                      engine: str = "gemini") -> List[Dict]:
    """Extract text annotations from image using AI vision model.
    
    Args:
        image_path: Path to PNG/JPEG image
        api_key: API key for the vision service
        engine: "gemini" or "openai"
        
    Returns:
        List of {text, bbox, confidence} dicts
    """
    if engine == "gemini":
        return _gemini_vision_extract(image_path, api_key)
    else:
        raise ValueError(f"Unsupported vision engine: {engine}")


def _gemini_vision_extract(image_path: str, api_key: str) -> List[Dict]:
    """Use Gemini Flash vision to extract text from CAD drawing."""
    image_data = encode_image(image_path)
    
    # Detect mime type
    ext = os.path.splitext(image_path)[1].lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    
    url = f"{GEMINI_VISION_URL}?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": CAD_VISION_PROMPT},
                {
                    "inline_data": {
                        "mime_type": mime,
                        "data": image_data
                    }
                }
            ]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 4000,
            "responseMimeType": "application/json",
        }
    }
    
    try:
        resp = requests.post(url, headers={"Content-Type": "application/json"},
                            json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        
        # Extract JSON from response
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        
        # Parse JSON response
        result = json.loads(text)
        annotations = result.get("annotations", [])
        
        # Convert to standard format
        items = []
        for ann in annotations:
            bbox = ann.get("bbox", [0, 0, 100, 20])
            # Scale bbox from 0-1000 to actual image dimensions if needed
            items.append({
                "text": ann.get("text", ""),
                "bbox": bbox,
                "confidence": ann.get("confidence", 0.5),
            })
        
        return items
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            raise RuntimeError("Gemini API rate limited. Please wait a moment.")
        raise RuntimeError(f"Gemini API error: {e}")
    except (KeyError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Failed to parse Gemini response: {e}")
    except Exception as e:
        raise RuntimeError(f"Gemini vision extraction failed: {e}")


def scale_bboxes_to_pdf(items: List[Dict], img_width: int, img_height: int,
                        pdf_width: float, pdf_height: float) -> List[Dict]:
    """Scale AI vision bboxes from image pixels to PDF points.
    
    AI vision returns bboxes in 0-1000 scale or image pixel scale.
    We need to convert to PDF points for overlay placement.
    """
    result = []
    for item in items:
        bbox = item["bbox"]
        # Check if bbox is in 0-1000 scale
        if max(bbox) <= 1000 and min(bbox) >= 0:
            # Scale to image pixels first, then to PDF points
            x1 = bbox[0] / 1000 * img_width * (72 / 200)  # Assuming 200 DPI render
            y1 = bbox[1] / 1000 * img_height * (72 / 200)
            x2 = bbox[2] / 1000 * img_width * (72 / 200)
            y2 = bbox[3] / 1000 * img_height * (72 / 200)
        else:
            # Already in pixel coordinates, convert to PDF points
            x1 = bbox[0] * (72 / 200)
            y1 = bbox[1] * (72 / 200)
            x2 = bbox[2] * (72 / 200)
            y2 = bbox[3] * (72 / 200)
        
        result.append({
            **item,
            "bbox": [x1, y1, x2, y2],
        })
    return result


def is_gemini_available(api_key: str) -> bool:
    """Test if Gemini API key is valid."""
    try:
        url = f"{GEMINI_VISION_URL}?key={api_key}"
        resp = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": "Say OK"}]}],
                "generationConfig": {"maxOutputTokens": 10}
            },
            timeout=10
        )
        return resp.status_code == 200
    except Exception:
        return False
