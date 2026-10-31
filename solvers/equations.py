"""Equation and system solver."""

import logging
from typing import Optional

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr

from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction

from constants import ICON_PATH, RE_EQUATION_SPLIT, SYMPY_TRANSFORMATIONS
from utils.parser import preprocess, find_variables
from utils import formatter

logger = logging.getLogger(__name__)


def handle_equations(query: str) -> Optional[RenderResultListAction]:
    """Handle equation solving and linear systems.
    
    Args:
        query: Equation query string
        
    Returns:
        Result list with solutions or None if no variables
    """
    try:
        var_names = find_variables(query)
        if not var_names:
            return None
        
        syms = {v: sp.Symbol(v) for v in var_names}
        local_scope = {**syms, "pi": sp.pi, "e": sp.E, "sqrt": sp.sqrt, "sin": sp.sin, "cos": sp.cos, "tan": sp.tan}
        
        raw_eqs = RE_EQUATION_SPLIT.split(query)
        equations = []
        
        for part in raw_eqs:
            part = part.strip()
            if "=" not in part:
                continue
            l, r = part.split("=", 1)
            lhs = parse_expr(preprocess(l.strip()), transformations=SYMPY_TRANSFORMATIONS, local_dict=local_scope)
            rhs = parse_expr(preprocess(r.strip()), transformations=SYMPY_TRANSFORMATIONS, local_dict=local_scope)
            equations.append(sp.Eq(lhs, rhs))
        
        if equations:
            sym_list = [syms[v] for v in var_names]
            sols = sp.solve(equations, sym_list)
            formatted = formatter.format_solutions(sols, var_names)
            
            return RenderResultListAction([
                ExtensionResultItem(
                    icon=ICON_PATH,
                    name=str(formatted),
                    description=f"Solved system for {', '.join(var_names)}",
                    on_enter=CopyToClipboardAction(str(sols))
                )
            ])
    except Exception as e:
        logger.debug(f"Equation solving failed: {e}")
    
    return None
