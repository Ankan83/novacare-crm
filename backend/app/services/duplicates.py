"""Public duplicate-detection helpers."""

from app.services.crm_insights import duplicate_score, normalize_identity

__all__ = ["duplicate_score", "normalize_identity"]
