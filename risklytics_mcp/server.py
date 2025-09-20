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

# Import in-repo adapters/services
_DILI_AVAILABLE = False
_DART_AVAILABLE = False
try:
    from services.dilisense import dilisense_service  # type: ignore
    _DILI_AVAILABLE = True
except Exception:
    pass

try:
    from services.adapters.dart import dart_adapter  # type: ignore
    _DART_AVAILABLE = True
except Exception:
    pass


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
    if not _DILI_AVAILABLE:
        raise ToolError("dilisense_service not available in this environment")
    # dilisense_service.screen_company is async in our app integration
    try:
        data = await dilisense_service.screen_company(name, "")
    except TypeError:
        # If implemented sync, fall back
        data = dilisense_service.screen_company(name, "")

    return SanctionResult(
        query=name,
        matched_name=((data or {}).get("matched") or {}).get("name") if isinstance(data, dict) else None,
        pep=((data or {}).get("risk") or {}).get("pep", False) if isinstance(data, dict) else False,
        sanctioned=((data or {}).get("risk") or {}).get("sanctioned", False) if isinstance(data, dict) else False,
        sources=[(s or {}).get("source") for s in ((data or {}).get("hits") or []) if (s or {}).get("source")] if isinstance(data, dict) else [],
        raw=data if isinstance(data, dict) else {"result": data},
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
    if not _DART_AVAILABLE:
        raise ToolError("dart_adapter not available in this environment")
    companies = dart_adapter.search_company(query)
    first = companies[0] if companies else {}
    corp_code = first.get("corp_code") if isinstance(first, dict) else None
    filings = []
    if corp_code:
        try:
            filings = dart_adapter.search_filings(corp_code, years_back=2)
        except Exception:
            filings = []
    return DartResult(
        query=query,
        company_legal_name_ko=(first.get("name") if isinstance(first, dict) else None),
        corp_code=corp_code,
        filings=filings,
        raw={"companies": companies}
    )


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


