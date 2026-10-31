"""Value formatting utilities."""

import logging
from typing import Any, Dict, List, Union

import sympy as sp

from constants import EPSILON

logger = logging.getLogger(__name__)


def fmt(val: Any) -> str:
    """Format a SymPy value for display.
    
    Attempts to simplify to rational numbers or integers,
    and formats with appropriate precision.
    
    Args:
        val: SymPy expression or value
        
    Returns:
        Formatted string representation
    """
    try:
        if isinstance(val, sp.Matrix):
            flat_rows = [[str(fmt(val[i, j])) for j in range(val.cols)] for i in range(val.rows)]
            return "Rows: " + " ; ".join([f"[{', '.join(r)}]" for r in flat_rows])
        
        # Attempt to simplify to rational number
        rational = sp.nsimplify(val, rational=True)
        if isinstance(rational, sp.Rational):
            return str(rational)
        
        # Format integer-like or float values
        f = float(sp.N(val, 10))
        if abs(f - round(f)) < EPSILON:
            return str(int(round(f)))
        return f"{f:.8g}"
    except Exception:
        return str(val)


def format_solutions(sols: Union[Dict, List, None], var_names: List[str]) -> str:
    """Format equation solutions for display.
    
    Handles multiple solution formats: single dict, list of solutions,
    or list of dicts for systems of equations.
    
    Args:
        sols: Solution(s) from SymPy solver
        var_names: Variable names for formatting
        
    Returns:
        Human-readable solution string
    """
    if not sols:
        return "No solution"
    if isinstance(sols, dict):
        return ",   ".join(f"{k} = {fmt(v)}" for k, v in sols.items())
    if isinstance(sols, list):
        if len(var_names) == 1:
            return ",   ".join(f"{var_names[0]} = {fmt(s)}" for s in sols)
        results = []
        for s in sols:
            if isinstance(s, dict):
                results.append(",  ".join(f"{k} = {fmt(v)}" for k, v in s.items()))
            elif isinstance(s, (list, tuple)):
                results.append(",  ".join(f"{var_names[i]} = {fmt(s[i])}" for i in range(len(s))))
            else:
                results.append(fmt(s))
        return "   |   ".join(results)
    return str(sols)
