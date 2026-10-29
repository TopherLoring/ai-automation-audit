"""All static checks return a list of Finding objects."""

from .base import Finding, Severity
from .error_handling import check_error_handling
from .retries import check_retries
from .duplicates import check_duplicate_risk
from .validation import check_missing_validation
from .webhooks import check_webhooks
from .settings import check_workflow_settings

ALL_CHECKS = [
    check_error_handling,
    check_retries,
    check_duplicate_risk,
    check_missing_validation,
    check_webhooks,
    check_workflow_settings,
]

__all__ = ["Finding", "Severity", "ALL_CHECKS"]