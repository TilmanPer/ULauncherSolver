"""Arithmetic verification solver."""

import logging
from typing import Optional

from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction

from constants import EPSILON, ICON_PATH, SAFE_MATH
from utils.parser import preprocess
from utils import formatter

logger = logging.getLogger(__name__)


def handle_arithmetic_check(normalised: str) -> Optional[RenderResultListAction]:
    """Check if arithmetic equation is true or false.
    
    Args:
        normalised: Normalized query string
        
    Returns:
        Result item or None if parsing fails
    """
    if normalised.count("=") != 1:
        return None
        
    lhs_raw, rhs_raw = normalised.split("=", 1)
    try:
        lval = eval(preprocess(lhs_raw), SAFE_MATH)
        rval = eval(preprocess(rhs_raw), SAFE_MATH)
        equal = abs(lval - rval) < EPSILON
        verdict = "✓ True" if equal else f"✗ False  ({lhs_raw.strip()}={formatter.fmt(lval)}, {rhs_raw.strip()}={formatter.fmt(rval)})"
        return RenderResultListAction([
            ExtensionResultItem(
                icon=ICON_PATH,
                name=verdict,
                description="Arithmetic Verification",
                on_enter=CopyToClipboardAction(verdict)
            )
        ])
    except Exception as e:
        logger.debug(f"Arithmetic check failed: {e}")
        return None
