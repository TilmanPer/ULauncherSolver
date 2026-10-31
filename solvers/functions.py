"""Explicit function call solver."""

import logging
import re
from typing import Optional

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr

from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction

from constants import ICON_PATH, SYMPY_ALIASES, SYMPY_TRANSFORMATIONS
from utils.parser import preprocess, parse_matrix_string
from utils import formatter

logger = logging.getLogger(__name__)


def handle_function_call(func_match: re.Match, query: str) -> Optional[RenderResultListAction]:
    """Handle explicit function calls (e.g., det([...]) or ableitung(x^2)).
    
    Args:
        func_match: Regex match for function pattern
        query: Original query string
        
    Returns:
        Result list or None if function not found
    """
    user_func = func_match.group(1).lower()
    arg_str = func_match.group(2).strip()
    resolved_func = SYMPY_ALIASES.get(user_func, user_func)
    
    try:
        if arg_str.startswith("[") and arg_str.endswith("]"):
            M = parse_matrix_string(arg_str)
            if hasattr(M, resolved_func):
                method = getattr(M, resolved_func)
                res = method() if callable(method) else method
                return RenderResultListAction([ExtensionResultItem(
                    icon=ICON_PATH,
                    name=f"{user_func.title()}: {formatter.fmt(res)}",
                    description="Click to copy",
                    on_enter=CopyToClipboardAction(str(res))
                )])
        
        if hasattr(sp, resolved_func):
            parsed_arg = parse_expr(preprocess(arg_str), transformations=SYMPY_TRANSFORMATIONS)
            sympy_func = getattr(sp, resolved_func)
            res = sympy_func(parsed_arg)
            return RenderResultListAction([ExtensionResultItem(
                icon=ICON_PATH,
                name=str(formatter.fmt(res)),
                description=f"Result of {user_func}",
                on_enter=CopyToClipboardAction(str(res))
            )])
    except Exception as e:
        logger.debug(f"Function call failed: {user_func}: {e}")
        return RenderResultListAction([ExtensionResultItem(
            icon=ICON_PATH,
            name=f"Error in {user_func}: {e}",
            description="Check syntax",
            on_enter=HideWindowAction()
        )])
    
    return None
