"""Expression parsing and preprocessing utilities."""

import ast
import logging
from typing import List

import sympy as sp

from constants import RE_IMPLICIT_MULT, RE_CLOSE_PAREN, RE_FUNC_NAMES, RE_EXTRACT_LETTERS, REPLACEMENTS

logger = logging.getLogger(__name__)


def normalise(expr: str) -> str:
    """Replace Unicode mathematical symbols with ASCII equivalents.
    
    Args:
        expr: Expression string with Unicode symbols
        
    Returns:
        Normalized expression with standard operators
    """
    for src, dst in REPLACEMENTS:
        expr = expr.replace(src, dst)
    return expr


def preprocess(expr: str) -> str:
    """Preprocess mathematical expression for evaluation.
    
    Converts common notation to Python syntax:
    - ^ to ** (exponentiation)
    - 2x to 2*x (implicit multiplication)
    - )( to )*(  (parentheses multiplication)
    
    Args:
        expr: Raw mathematical expression
        
    Returns:
        Preprocessed expression ready for evaluation
    """
    expr = normalise(expr)
    expr = expr.replace("^", "**")
    expr = RE_IMPLICIT_MULT.sub(r"\1*\2", expr)
    expr = RE_CLOSE_PAREN.sub(r")*(", expr)
    return expr


def find_variables(query: str) -> List[str]:
    """Extract variable names from a mathematical expression.
    
    Removes function names and returns sorted unique letters,
    excluding 'e' (Euler's number) and 'I' (imaginary unit).
    
    Args:
        query: Mathematical expression
        
    Returns:
        Sorted list of variable names
    """
    cleaned = RE_FUNC_NAMES.sub("", query)
    letters = sorted(set(RE_EXTRACT_LETTERS.findall(cleaned)))
    return [c for c in letters if c not in ("e", "I")]


def parse_matrix_string(matrix_str: str) -> sp.Matrix:
    """Parse matrix notation to SymPy Matrix.
    
    Supports both semicolon notation [1,2;3,4] and Python list notation.
    
    Args:
        matrix_str: Matrix string representation
        
    Returns:
        SymPy Matrix object
        
    Raises:
        ValueError: If matrix notation is invalid
    """
    matrix_str = matrix_str.strip()
    try:
        if ";" in matrix_str:
            inner = matrix_str[1:-1].strip()
            rows = inner.split(";")
            matrix_data = []
            for r in rows:
                matrix_data.append([sp.sympify(preprocess(item.strip())) for item in r.split(",") if item.strip()])
        else:
            matrix_data = ast.literal_eval(matrix_str)
        return sp.Matrix(matrix_data)
    except (ValueError, SyntaxError) as e:
        logger.error(f"Failed to parse matrix: {matrix_str}", exc_info=True)
        raise
