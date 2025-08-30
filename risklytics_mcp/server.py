import os
import json
from typing import Optional, List, Dict, Any

import httpx
from pydantic import BaseModel, Field

try:
    # pip install mcp
    from mcp import MCP, Tool, ToolError
except Exception as e:
    raise RuntimeError("mcp package not installed. Run: pip install mcp")


app = MCP(name="risklytics-mcp", version="0.1.0")


# --------------------- Models ---------------------

class SanctionResult(BaseModel):
    query: str
    matched_name: Optional[str] = None
    pep: bool = False
    sanctioned: bool = False
    sources: List[str] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)


class OwnershipResult(BaseModel):
    query: str
    company_legal_name: Optional[str] = None
    jurisdiction: Optional[str] = None
    shareholders: List[Dict[str, Any]] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)


class DartResult(BaseModel):
    query: str
    company_legal_name_ko: Optional[str] = None
    corp_code: Optional[str] = None
    filings: List[Dict[str, Any]] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)


# --------------------- Helpers ---------------------

HTTP_TIMEOUT = httpx.Timeout(20.0, connect=5.0)


async def call_dilisense(name: str) -> SanctionResult:
    api_key = os.getenv("DILISENSE_API_KEY")
    base = os.getenv("DILISENSE_BASE_URL", "https://api.dilisense.com/v1")
    if not api_key:
        raise ToolError("DILISENSE_API_KEY is not set")

    url = f"{base}/screening"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"name": name, "type": "auto"}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()

    return SanctionResult(
        query=name,
        matched_name=(data.get("matched") or {}).get("name"),
        pep=(data.get("risk") or {}).get("pep", False),
        sanctioned=(data.get("risk") or {}).get("sanctioned", False),
        sources=[(s or {}).get("source") for s in (data.get("hits") or []) if (s or {}).get("source")],
        raw=data,
    )


async def call_orbis(query: str, country: Optional[str]) -> OwnershipResult:
    api_key = os.getenv("ORBIS_API_KEY")
    if not api_key:
        raise ToolError("ORBIS_API_KEY is not set")

    # Placeholder stub; replace with your actual Orbis integration.
    data = {
        "company_legal_name": None,
        "jurisdiction": country,
        "shareholders": []
    }
    return OwnershipResult(query=query, **data, raw=data)


async def call_korean_dart(query: str) -> DartResult:
    api_key = os.getenv("DART_API_KEY")
    if not api_key:
        raise ToolError("DART_API_KEY is not set")

    # Minimal search using list.json (3‑month window required without corp_code)
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        params = {
            "crtfc_key": api_key,
            "corp_name": query,
            "bgn_de": "20240601",
            "end_de": "20240830",
            "page_no": 1,
            "page_count": 5
        }
        r = await client.get("https://opendart.fss.or.kr/api/list.json", params=params)
        r.raise_for_status()
        data = r.json()

    first = (data.get("list") or [{}])[0] if data.get("status") == "000" else {}
    out = {
        "company_legal_name_ko": first.get("corp_name"),
        "corp_code": first.get("corp_code"),
        "filings": data.get("list") or []
    }
    return DartResult(query=query, **out, raw=data)


# --------------------- Tools ---------------------

@app.tool(name="risklytics.sanctions_check", description="Screen an individual/company via Dilisense.")
async def sanctions_check(name: str) -> dict:
    result = await call_dilisense(name)
    return json.loads(result.model_dump_json())


@app.tool(name="risklytics.ownership_lookup", description="Lookup company ownership/shareholders (Orbis/registries).")
async def ownership_lookup(query: str, country: Optional[str] = None) -> dict:
    result = await call_orbis(query, country)
    return json.loads(result.model_dump_json())


@app.tool(name="risklytics.korean_filings", description="Retrieve basic info/filings for Korean companies via DART.")
async def korean_filings(query: str) -> dict:
    result = await call_korean_dart(query)
    return json.loads(result.model_dump_json())


@app.tool(name="risklytics.health", description="Health check for the Risklytics MCP server and env.")
async def health() -> dict:
    env = {
        "DILISENSE_API_KEY": bool(os.getenv("DILISENSE_API_KEY")),
        "ORBIS_API_KEY": bool(os.getenv("ORBIS_API_KEY")),
        "DART_API_KEY": bool(os.getenv("DART_API_KEY")),
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
    }
    return {"ok": True, "env_present": env}


def main():
    app.run()


if __name__ == "__main__":
    main()


