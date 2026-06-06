"""
Translation Engine - Supports DeepSeek, Gemini, and Google Translate.
API keys are passed per-request (never stored server-side).
"""
import json
import re
import requests
from typing import List, Dict, Optional


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

TRANSLATION_SYSTEM_PROMPT = """You are a professional CAD engineering translator.
Translate the following Chinese or English annotations to Vietnamese.
Rules:
1. Output ONLY the Vietnamese translation, nothing else.
2. Preserve any numbers, units, and symbols unchanged.
3. Use technical engineering Vietnamese terms.
4. Keep the translation concise - CAD drawings have limited space.
5. For multi-line input, preserve the line structure."""


def translate_deepseek(texts: List[str], api_key: str,
                       source: str = "auto", target: str = "vi") -> List[Dict]:
    """Translate texts using DeepSeek API."""
    results = []
    
    # Batch translate up to 10 items at once
    for i in range(0, len(texts), 10):
        batch = texts[i:i+10]
        items_text = "\n---\n".join(batch)
        
        user_prompt = f"Translate these CAD annotations to Vietnamese. Return each translation separated by '---':\n\n{items_text}"
        
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
                        {"role": "system", "content": TRANSLATION_SYSTEM_PROMPT},
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
            
            translations = [t.strip() for t in reply.split("---")]
            # Pad if fewer translations returned
            while len(translations) < len(batch):
                translations.append(batch[len(translations)])
            
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
    """Translate texts using Gemini API."""
    results = []
    
    for i in range(0, len(texts), 10):
        batch = texts[i:i+10]
        items_text = "\n---\n".join(batch)
        
        prompt = f"{TRANSLATION_SYSTEM_PROMPT}\n\nTranslate these CAD annotations to Vietnamese. Return each translation separated by '---':\n\n{items_text}"
        
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
            
            translations = [t.strip() for t in reply.split("---")]
            while len(translations) < len(batch):
                translations.append(batch[len(translations)])
            
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


def translate(texts: List[str], engine: str = "google",
              api_key: Optional[str] = None,
              source: str = "auto", target: str = "vi") -> List[Dict]:
    """Unified translation interface.
    
    Args:
        texts: List of text strings to translate
        engine: "google", "deepseek", or "gemini"
        api_key: API key for deepseek/gemini (not needed for google)
        source: Source language (auto for auto-detect)
        target: Target language (default: vi)
    
    Returns:
        List of {original, translated, engine, success, [error]} dicts
    """
    if engine == "deepseek":
        if not api_key:
            raise ValueError("DeepSeek requires an API key")
        return translate_deepseek(texts, api_key, source, target)
    elif engine == "gemini":
        if not api_key:
            raise ValueError("Gemini requires an API key")
        return translate_gemini(texts, api_key, source, target)
    else:
        return translate_google(texts, source, target)


def test_api_key(engine: str, api_key: str) -> Dict:
    """Test if an API key is valid for the given engine."""
    test_text = "不锈钢镜电镀"
    
    if engine == "deepseek":
        try:
            resp = requests.post(
                DEEPSEEK_URL,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "Say 'OK' in Vietnamese."}],
                    "max_tokens": 10,
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
