"""Simple expression evaluation solver."""

import logging

from sympy.parsing.sympy_parser import parse_expr

from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction

from constants import ICON_PATH, SYMPY_TRANSFORMATIONS
from utils.parser import preprocess
from utils import formatter

logger = logging.getLogger(__name__)


def handle_simple_expression(query: str) -> RenderResultListAction:
    """Handle simple expression evaluation.
    
    Args:
        query: Expression query string
        
    Returns:
        Result list with computed value
    """
    try:
        parsed_expr = parse_expr(preprocess(query), transformations=SYMPY_TRANSFORMATIONS)
        res_str = formatter.fmt(parsed_expr)
        return RenderResultListAction([
            ExtensionResultItem(
                icon=ICON_PATH,
                name=str(res_str),
                description=f"{query} = {res_str}",
                on_enter=CopyToClipboardAction(str(parsed_expr))
            )
        ])
    except Exception as e:
        logger.error(f"Expression evaluation failed: {e}", exc_info=True)
        return RenderResultListAction([
            ExtensionResultItem(
                icon=ICON_PATH,
                name="Error: Could not parse expression",
                description="Check your mathematical syntax.",
                on_enter=HideWindowAction()
            )
        ])
