"""
Translation Engine v2 - Furniture CAD Translation Platform
=========================================================
Phase 1 Upgrades:
  1. JSON format return (replaces --- separator)
  2. Synonym normalization (活动层板→层板→统一术语)
  3. Enterprise glossary + placeholder system ([[TERM_001]])
  4. Translation Memory (dict+JSON, exact match caching)

Pipeline: text → normalize → glossary_placeholder → TM lookup → AI → restore → cache

Engines: DeepSeek > Gemini > Google (priority order)
"""
import json
import re
import os
import requests
from typing import List, Dict, Optional, Tuple

# ============================================================
# Configuration
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

GLOSSARY_PATH = os.path.join(DATA_DIR, "glossary.json")
SYNONYM_PATH = os.path.join(DATA_DIR, "synonym_map.json")
TM_PATH = os.path.join(DATA_DIR, "translation_memory.json")

FURNITURE_SYSTEM_PROMPT = """You are a professional furniture manufacturing translator.

Domain:
- Furniture manufacturing (cabinet, KD furniture, panel furniture)
- Cabinet production and assembly
- Hardware installation (hinges, slides, connectors)
- Engineering drawings and technical annotations

Priority:
1. Use approved glossary terms whenever available (marked with [[TERM_NNN]]).
2. Keep terminology consistent across the whole drawing.
3. Translate customer requirements accurately.
4. Translate installation notes accurately.
5. Preserve dimensions, symbols, and units unchanged.
6. Preserve source casing for codes (e.g., KD, CNC, EB).
7. Keep translations concise - CAD drawings have limited space.

Output format: Return a JSON array of translations."""


# ============================================================
# Glossary & Synonym Management
# ============================================================

def load_json(path: str, default=None) -> dict:
    """Load a JSON file, return default if not found."""
    if default is None:
        default = {}
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return default


def save_json(path: str, data: dict):
    """Save data to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_glossary() -> Dict[str, str]:
    """Load enterprise glossary: {中文术语: 越南语翻译}."""
    return load_json(GLOSSARY_PATH, {})


def save_glossary(glossary: Dict[str, str]):
    """Save enterprise glossary."""
    save_json(GLOSSARY_PATH, glossary)


def add_glossary_term(chinese: str, vietnamese: str):
    """Add or update a term in the glossary."""
    g = load_glossary()
    g[chinese] = vietnamese
    save_glossary(g)


def remove_glossary_term(chinese: str) -> bool:
    """Remove a term from the glossary."""
    g = load_glossary()
    if chinese in g:
        del g[chinese]
        save_glossary(g)
        return True
    return False


def load_synonym_map() -> Dict[str, str]:
    """Load synonym map: {变体: 标准名称}."""
    return load_json(SYNONYM_PATH, {})


def save_synonym_map(syn_map: Dict[str, str]):
    """Save synonym map."""
    save_json(SYNONYM_PATH, syn_map)


def add_synonym(variant: str, standard: str):
    """Add a synonym mapping."""
    sm = load_synonym_map()
    sm[variant] = standard
    save_synonym_map(sm)


def remove_synonym(variant: str) -> bool:
    """Remove a synonym mapping."""
    sm = load_synonym_map()
    if variant in sm:
        del sm[variant]
        save_synonym_map(sm)
        return True
    return False


def load_tm() -> Dict[str, str]:
    """Load translation memory: {normalized_source: translation}."""
    return load_json(TM_PATH, {})


def save_tm(tm: Dict[str, str]):
    """Save translation memory."""
    save_json(TM_PATH, tm)


def add_tm_entry(source: str, translation: str, engine: str = "google"):
    """Add an entry to translation memory (key scoped by engine)."""
    tm = load_tm()
    key = f"{engine}:{source}"
    tm[key] = translation
    save_tm(tm)


def get_tm_stats() -> Dict:
    """Get TM statistics."""
    tm = load_tm()
    glossary = load_glossary()
    synonyms = load_synonym_map()
    return {
        "tm_entries": len(tm),
        "glossary_terms": len(glossary),
        "synonym_rules": len(synonyms),
        "tm_path": TM_PATH,
        "glossary_path": GLOSSARY_PATH,
        "synonym_path": SYNONYM_PATH,
    }


# ============================================================
# Synonym Normalization
# ============================================================

def normalize_term(text: str, synonym_map: Optional[Dict[str, str]] = None) -> str:
    """Normalize a term using synonym map.
    
    Example:
        活动层板 → 层板
        活动板 → 层板
        隔板 → 层板
    """
    if synonym_map is None:
        synonym_map = load_synonym_map()
    if not synonym_map:
        return text
    return synonym_map.get(text, text)


def normalize_terms(texts: List[str]) -> Tuple[List[str], Dict[str, str]]:
    """Normalize a list of terms. Returns (normalized, mapping).
    
    mapping: {original_term: normalized_term} for non-identity mappings.
    """
    synonym_map = load_synonym_map()
    normalized = []
    mapping = {}
    for t in texts:
        norm = normalize_term(t, synonym_map)
        normalized.append(norm)
        if norm != t:
            mapping[t] = norm
    return normalized, mapping


# ============================================================
# Glossary Placeholder System
# ============================================================

def replace_with_placeholders(texts: List[str], glossary: Optional[Dict[str, str]] = None) -> Tuple[List[str], Dict[str, str], Dict[str, str]]:
    """Replace glossary terms with placeholders.
    
    Returns:
        (processed_texts, placeholder_map, reverse_map)
        placeholder_map: {placeholder: vietnamese_translation}
        reverse_map: {placeholder: original_term}
    """
    if glossary is None:
        glossary = load_glossary()
    
    processed = []
    placeholder_map = {}   # TERM_001 → vietnamese
    reverse_map = {}       # TERM_001 → chinese
    
    term_id = 1
    for text in texts:
        processed_text = text
        for cn_term, vi_term in glossary.items():
            if cn_term in processed_text:
                placeholder = f"[[TERM_{term_id:03d}]]"
                processed_text = processed_text.replace(cn_term, placeholder)
                placeholder_map[placeholder] = vi_term
                reverse_map[placeholder] = cn_term
                term_id += 1
        processed.append(processed_text)
    
    return processed, placeholder_map, reverse_map


def restore_placeholders(translations: List[str], placeholder_map: Dict[str, str]) -> List[str]:
    """Restore placeholders to actual translations."""
    restored = []
    for trans in translations:
        for placeholder, vi_term in placeholder_map.items():
            trans = trans.replace(placeholder, vi_term)
        restored.append(trans)
    return restored


# ============================================================
# Translation Memory (TM)
# ============================================================

def tm_lookup(texts: List[str], engine: str = "google") -> Tuple[List[Optional[str]], List[int]]:
    """Look up texts in translation memory (engine-scoped keys).
    
    Returns:
        (hits, missed_indices)
        hits: [translation|None, ...] where None means cache miss
        missed_indices: indices that need API translation
    """
    tm = load_tm()
    hits = []
    missed = []
    
    for i, text in enumerate(texts):
        key = f"{engine}:{text.strip()}"
        if key in tm:
            hits.append(tm[key])
        else:
            hits.append(None)
            missed.append(i)
    
    return hits, missed


# ============================================================
# JSON Parsing (Defensive)
# ============================================================

def parse_translation_response(text: str, expected_count: int) -> List[str]:
    """Parse AI translation response into list of translations.
    
    Handles:
    - JSON arrays (standard)
    - JSON wrapped in markdown code blocks
    - Trailing/leading whitespace
    """
    text = text.strip()
    
    # Remove markdown code block wrappers
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    
    try:
        data = json.loads(text)
        translations = []
        for item in data:
            if isinstance(item, dict):
                translations.append(item.get("translation", ""))
            elif isinstance(item, str):
                translations.append(item)
            else:
                translations.append(str(item))
        
        # Pad if fewer translations returned
        while len(translations) < expected_count:
            translations.append("")
        
        return translations[:expected_count]
    except json.JSONDecodeError:
        return []


# ============================================================
# Translation Engines
# ============================================================

# Google Translate (free, no API key needed)
def translate_google(texts: List[str], source: str = "auto",
                     target: str = "vi") -> List[Dict]:
    """Translate texts using Google Translate (unofficial API)."""
    results = []
    for text in texts:
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": "auto",
                "tl": target,
                "dt": "t",
                "q": text,
            }
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            translated = ""
            for segment in data[0]:
                if segment[0]:
                    translated += segment[0]
            
            results.append({
                "original": text,
                "translated": translated.strip(),
                "engine": "google",
                "success": True,
            })
        except Exception as e:
            results.append({
                "original": text,
                "translated": text,
                "engine": "google",
                "success": False,
                "error": str(e),
            })
    
    return results


# DeepSeek API
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"


def translate_deepseek(texts: List[str], api_key: str,
                       source: str = "auto", target: str = "vi") -> List[Dict]:
    """Translate texts using DeepSeek API with JSON format."""
    results = []
    
    for i in range(0, len(texts), 15):
        batch = texts[i:i+15]
        
        batch_json = json.dumps([
            {"id": j, "text": t} for j, t in enumerate(batch)
        ], ensure_ascii=False)
        
        user_prompt = (
            f"Translate these CAD annotations to Vietnamese.\n"
            f"Return ONLY a JSON array of objects with format:\n"
            f'[{{"id": number, "translation": "Vietnamese text"}}]\n\n'
            f"Items to translate:\n{batch_json}"
        )
        
        try:
            resp = requests.post(
                DEEPSEEK_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": FURNITURE_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000,
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data["choices"][0]["message"]["content"].strip()
            
            translations = parse_translation_response(reply, len(batch))
            
            # If JSON parsing failed, fall back to Google
            if not translations:
                for orig in batch:
                    results.append({
                        "original": orig,
                        "translated": orig,
                        "engine": "deepseek",
                        "success": False,
                        "error": "Response parsing failed",
                    })
                continue
            
            for j, orig in enumerate(batch):
                results.append({
                    "original": orig,
                    "translated": translations[j] if j < len(translations) else orig,
                    "engine": "deepseek",
                    "success": True,
                })
        except Exception as e:
            for orig in batch:
                results.append({
                    "original": orig,
                    "translated": orig,
                    "engine": "deepseek",
                    "success": False,
                    "error": str(e),
                })
    
    return results


# Gemini API
GEMINI_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


def translate_gemini(texts: List[str], api_key: str,
                     source: str = "auto", target: str = "vi") -> List[Dict]:
    """Translate texts using Gemini API with JSON format."""
    results = []
    
    for i in range(0, len(texts), 15):
        batch = texts[i:i+15]
        
        batch_json = json.dumps([
            {"id": j, "text": t} for j, t in enumerate(batch)
        ], ensure_ascii=False)
        
        prompt = (
            f"{FURNITURE_SYSTEM_PROMPT}\n\n"
            f"Translate these CAD annotations to Vietnamese.\n"
            f"Return ONLY a JSON array of objects with format:\n"
            f'[{{"id": number, "translation": "Vietnamese text"}}]\n\n'
            f"Items to translate:\n{batch_json}"
        )
        
        try:
            url = f"{GEMINI_URL_TEMPLATE}?key={api_key}"
            resp = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 2000,
                    },
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            
            reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            translations = parse_translation_response(reply, len(batch))
            
            if not translations:
                for orig in batch:
                    results.append({
                        "original": orig,
                        "translated": orig,
                        "engine": "gemini",
                        "success": False,
                        "error": "Response parsing failed",
                    })
                continue
            
            for j, orig in enumerate(batch):
                results.append({
                    "original": orig,
                    "translated": translations[j] if j < len(translations) else orig,
                    "engine": "gemini",
                    "success": True,
                })
        except Exception as e:
            for orig in batch:
                results.append({
                    "original": orig,
                    "translated": orig,
                    "engine": "gemini",
                    "success": False,
                    "error": str(e),
                })
    
    return results


# ============================================================
# Unified Translation Interface (v2)
# ============================================================

def translate(texts: List[str], engine: str = "google",
              api_key: Optional[str] = None,
              source: str = "auto", target: str = "vi",
              use_tm: bool = True,
              use_glossary: bool = True,
              use_synonyms: bool = True) -> List[Dict]:
    """Unified translation interface with Phase 1 pipeline.
    
    Pipeline:
    text → normalize → glossary_placeholder → TM_lookup → AI/Google → restore → cache
    
    Args:
        texts: List of text strings to translate
        engine: "google", "deepseek", or "gemini"
        api_key: API key for deepseek/gemini
        source: Source language
        target: Target language (default: vi)
        use_tm: Enable translation memory lookup
        use_glossary: Enable glossary placeholder substitution
        use_synonyms: Enable synonym normalization
    
    Returns:
        List of {original, normalized, translated, engine, success, from_tm, [error]} dicts
    """
    if not texts:
        return []
    
    # Step 1: Synonym normalization
    normalized_texts = list(texts)
    synonym_hits = {}
    if use_synonyms:
        normalized_texts, synonym_hits = normalize_terms(texts)
    
    # Step 2: Glossary placeholder replacement
    placeholder_map = {}
    reverse_map = {}
    tm_texts = list(normalized_texts)
    if use_glossary:
        tm_texts, placeholder_map, reverse_map = replace_with_placeholders(normalized_texts)
    
    # Step 3: Translation Memory lookup
    tm_hits = {}
    to_translate = []       # texts that need API translation
    to_translate_indices = []  # original indices
    
    if use_tm:
        hits, missed = tm_lookup(tm_texts, engine)
        for i, (hit, text) in enumerate(zip(hits, tm_texts)):
            if hit is not None:
                tm_hits[i] = hit  # cached translation
            else:
                to_translate.append(text)
                to_translate_indices.append(i)
    else:
        to_translate = list(tm_texts)
        to_translate_indices = list(range(len(tm_texts)))
    
    # Step 4: API translation (only for cache misses)
    api_results = {}
    if to_translate:
        if engine == "deepseek":
            if not api_key:
                raise ValueError("DeepSeek requires an API key")
            api_batch = translate_deepseek(to_translate, api_key, source, target)
        elif engine == "gemini":
            if not api_key:
                raise ValueError("Gemini requires an API key")
            api_batch = translate_gemini(to_translate, api_key, source, target)
        else:
            api_batch = translate_google(to_translate, source, target)
        
        for j, result in enumerate(api_batch):
            orig_idx = to_translate_indices[j]
            api_results[orig_idx] = result
    
    # Step 5: Assemble final results
    results = []
    for i in range(len(texts)):
        orig = texts[i]
        norm = normalized_texts[i] if i < len(normalized_texts) else orig
        tm_text = tm_texts[i] if i < len(tm_texts) else norm
        
        if i in tm_hits:
            # TM cache hit: restore placeholders
            translation = restore_placeholders([tm_hits[i]], placeholder_map)[0]
            results.append({
                "original": orig,
                "normalized": norm,
                "translated": translation,
                "engine": engine,
                "success": True,
                "from_tm": True,
                "synonym_applied": orig != norm,
            })
        elif i in api_results:
            # API translation: restore placeholders, cache result
            api_result = api_results[i]
            raw_translation = api_result.get("translated", norm)
            translation = restore_placeholders([raw_translation], placeholder_map)[0]
            if api_result["success"] and use_tm:
                add_tm_entry(tm_text, raw_translation, engine)
            results.append({
                "original": orig,
                "normalized": norm,
                "translated": translation,
                "engine": engine,
                "success": api_result["success"],
                "from_tm": False,
                "error": api_result.get("error", ""),
                "synonym_applied": orig != norm,
            })
        else:
            results.append({
                "original": orig,
                "normalized": norm,
                "translated": orig,
                "engine": engine,
                "success": False,
                "from_tm": False,
                "error": "No translation available",
                "synonym_applied": orig != norm,
            })
    
    return results


def test_api_key(engine: str, api_key: str) -> Dict:
    """Test if an API key is valid for the given engine."""
    if engine == "deepseek":
        try:
            resp = requests.post(
                DEEPSEEK_URL,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "Say OK"}],
                    "max_tokens": 5,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                return {"valid": True, "message": "DeepSeek API key is valid"}
            else:
                return {"valid": False, "message": f"DeepSeek API error: {resp.status_code}"}
        except Exception as e:
            return {"valid": False, "message": f"DeepSeek connection error: {str(e)}"}
    
    elif engine == "gemini":
        try:
            url = f"{GEMINI_URL_TEMPLATE}?key={api_key}"
            resp = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": "Say OK"}]}],
                },
                timeout=15,
            )
            if resp.status_code == 200:
                return {"valid": True, "message": "Gemini API key is valid"}
            else:
                error_msg = resp.json().get("error", {}).get("message", f"Status {resp.status_code}")
                return {"valid": False, "message": f"Gemini API error: {error_msg}"}
        except Exception as e:
            return {"valid": False, "message": f"Gemini connection error: {str(e)}"}
    
    else:
        return {"valid": True, "message": "Google Translate is always available (no key needed)"}


# ============================================================
# Data Initialization (seed with common furniture terms)
# ============================================================

def init_default_data():
    """Initialize default glossary and synonym data for furniture manufacturing."""
    
    # Default synonym map
    default_synonyms = {
        "活动层板": "层板",
        "活动板": "层板",
        "隔板": "层板",
        "置物板": "层板",
        "底板": "底板",
        "顶板": "顶板",
        "侧板": "侧板",
        "旁板": "侧板",
        "背板": "背板",
        "后板": "背板",
        "门板": "门板",
        "柜门": "门板",
        "抽面板": "抽屉面板",
        "抽屉面板": "抽屉面板",
        "踢脚板": "踢脚板",
        "底座": "踢脚板",
        "封边": "封边",
        "封边条": "封边",
        "木榫": "木榫",
        "圆棒榫": "木榫",
        "三合一": "三合一连接件",
        "三合一连接件": "三合一连接件",
        "偏心轮": "三合一连接件",
        "层板托": "层板托",
        "层板粒": "层板托",
        "门铰": "铰链",
        "铰链": "铰链",
        "阻尼铰链": "铰链",
        "拉手": "拉手",
        "把手": "拉手",
        "导轨": "导轨",
        "滑轨": "导轨",
        "路轨": "导轨",
        "自攻螺丝": "螺丝",
        "螺丝": "螺丝",
        "木螺丝": "螺丝",
    }
    
    # Default glossary (Chinese → Vietnamese)
    default_glossary = {
        "层板": "Vách ngăn",
        "侧板": "Tấm bên",
        "背板": "Tấm sau",
        "底板": "Tấm đáy",
        "顶板": "Tấm trên",
        "门板": "Cánh cửa",
        "抽屉面板": "Mặt ngăn kéo",
        "踢脚板": "Tấm đạp chân",
        "封边": "Dán cạnh",
        "木榫": "Chốt gỗ",
        "三合一连接件": "Ke góc 3 trong 1",
        "层板托": "Đỡ vách ngăn",
        "铰链": "Bản lề",
        "拉手": "Tay nắm",
        "导轨": "Ray trượt",
        "螺丝": "Vít",
        "偏心轮": "Bánh lệch tâm",
        "连接杆": "Thanh kết nối",
        "预埋螺母": "Đai ốc chìm",
        "KD家具": "Nội thất KD",
        "不锈钢": "Inox",
        "电镀": "Mạ điện",
        "喷粉": "Sơn tĩnh điện",
        "镜面": "Gương",
        "客户要求": "Yêu cầu khách hàng",
        "安装说明": "Hướng dẫn lắp đặt",
        "注意": "Lưu ý",
        "所有尺寸为公制": "Tất cả kích thước là hệ mét",
        "以为依据": "làm cơ sở",
    }
    
    if not os.path.exists(SYNONYM_PATH):
        save_synonym_map(default_synonyms)
        print(f"Initialized {len(default_synonyms)} synonym rules at {SYNONYM_PATH}")
    
    if not os.path.exists(GLOSSARY_PATH):
        save_glossary(default_glossary)
        print(f"Initialized {len(default_glossary)} glossary terms at {GLOSSARY_PATH}")


# Auto-initialize on import
init_default_data()
