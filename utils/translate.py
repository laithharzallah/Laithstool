"""
Translation utility for Korean text to English using OpenAI GPT
"""

import os
from openai import OpenAI

_client = None

def tr(s: str) -> str:
    """Translate Korean text to concise English"""
    global _client
    if not s: return s
    if _client is None:
        key = os.getenv("OPENAI_API_KEY")
        if not key: return s
        _client = OpenAI(api_key=key)
    try:
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"Translate to concise English. Return text only."},
                {"role":"user","content": s}
            ],
            temperature=0,
            max_tokens=100
        )
        return (resp.choices[0].message.content or s).strip()
    except Exception as e:
        print(f"Translation error: {e}")
        return s

def translate_company_data(info: dict) -> dict:
    """Translate Korean fields in company data to English"""
    if not info or "error" in info:
        return info

    translated_info = info.copy()

    # Translate basic info fields
    basic = translated_info.get("basic_info", {})
    if basic.get("corp_name"):
        basic["corp_name_eng"] = tr(basic["corp_name"])
    if basic.get("ceo_nm"):
        basic["ceo_nm_eng"] = tr(basic["ceo_nm"])
    if basic.get("adr"):
        basic["adr_eng"] = tr(basic["adr"])

    # Translate shareholders
    shareholders = translated_info.get("shareholders", [])
    for sh in shareholders:
        if sh.get("holder"):
            sh["holder_eng"] = tr(sh["holder"])

    # Translate executives
    executives = translated_info.get("executives", [])
    for exec in executives:
        if exec.get("name"):
            exec["name_eng"] = tr(exec["name"])
        if exec.get("relation"):
            exec["relation_eng"] = tr(exec["relation"])

    return translated_info
