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
    """Handle equation solving, linear systems, and identity checks."""
    try:
        var_names = find_variables(query)
        if not var_names:
            return None

        syms = {v: sp.Symbol(v) for v in var_names}
        local_scope = {**syms, "pi": sp.pi, "e": sp.E, "sqrt": sp.sqrt,
                       "sin": sp.sin, "cos": sp.cos, "tan": sp.tan}

        pairs = []  # (lhs, rhs) – don't use sp.Eq here, it auto-evaluates to True/False
        for part in RE_EQUATION_SPLIT.split(query):
            part = part.strip()
            if "=" not in part:
                continue
            l, r = part.split("=", 1)
            lhs = parse_expr(preprocess(l.strip()),
                             transformations=SYMPY_TRANSFORMATIONS, local_dict=local_scope)
            rhs = parse_expr(preprocess(r.strip()),
                             transformations=SYMPY_TRANSFORMATIONS, local_dict=local_scope)
            pairs.append((lhs, rhs))

        if not pairs:
            return None

        # Classify each equation: identity (always true) / contradiction / real constraint
        constraints = []
        for lhs, rhs in pairs:
            diff = sp.simplify(lhs - rhs)
            if diff == 0:
                continue  # identity, imposes no constraint
            if diff.free_symbols == set() and diff != 0:
                return _result("✗ False", "Contradiction: never true", "False")
            constraints.append(sp.Eq(lhs, rhs))

        # Every equation was an identity
        if not constraints:
            return _result("✓ True", f"Identity: holds for all {', '.join(var_names)}", "True")

        sym_list = [syms[v] for v in var_names]
        sols = sp.solve(constraints, sym_list)
        formatted = formatter.format_solutions(sols, var_names)
        return _result(str(formatted), f"Solved system for {', '.join(var_names)}", str(sols))

    except Exception as e:
        logger.debug(f"Equation solving failed: {e}")

    return None


def _result(name: str, description: str, copy_value: str) -> RenderResultListAction:
    return RenderResultListAction([
        ExtensionResultItem(
            icon=ICON_PATH,
            name=name,
            description=description,
            on_enter=CopyToClipboardAction(copy_value),
        )
    ])
