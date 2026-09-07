"""Public compliance helper for callers that do not need HTTP."""

from app.services.crm_insights import run_compliance_checks

__all__ = ["run_compliance_checks"]
