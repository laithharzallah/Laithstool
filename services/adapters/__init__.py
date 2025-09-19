"""Service adapters package."""

from .dart import dart_adapter  # noqa: F401
try:
    from .dilisense import DilisenseService  # noqa: F401
except Exception:
    pass

try:
    from .companies_house import CompaniesHouseAdapter  # noqa: F401
except Exception:
    # Optional until created
    pass

try:
    from .sec_edgar import SecEdgarAdapter  # noqa: F401
except Exception:
    pass
