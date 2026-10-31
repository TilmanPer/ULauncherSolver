"""Constants, regex patterns, and aliases for the Solver extension."""

import ast
import math
import re
from typing import Dict, List, Tuple

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

# Numeric constants
EPSILON: float = 1e-9
ICON_PATH: str = "images/icon.svg"

# Pre-compiled regex patterns for better performance
RE_FUNC_CALL = re.compile(r"^([a-zA-Z0-9_]+)\s*\(\s*(.+)\s*\)$")
RE_TABLE_CALL = re.compile(
    r"^table\s*\(\s*(.+?)\s*,\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*,\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*,\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*\)$",
    re.IGNORECASE
)
RE_INCOMPLETE_FUNC = re.compile(r"^([a-zA-Z0-9_]+)\s*\([^)]*$")
RE_IMPLICIT_MULT = re.compile(r"(\d)([a-zA-Z])")
RE_CLOSE_PAREN = re.compile(r"\)\(")
RE_EXTRACT_LETTERS = re.compile(r"[a-zA-Z]")
RE_FUNC_NAMES = re.compile(r"\b(?:sqrt|sin|cos|tan|log|exp|abs|asin|acos|atan|sind|cosd|tand)\b")
RE_EQUATION_SPLIT = re.compile(r"[,;]")

# Pre-computed transformations for SymPy parser
SYMPY_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)

# Function aliases (German & English)
SYMPY_ALIASES: Dict[str, str] = {
    "ew": "eigenvals", "eigenvalues": "eigenvals",
    "ev": "eigenvects", "eigenvectors": "eigenvects",
    "det": "det", "determinante": "det",
    "inv": "inv", "inverse": "inv",
    "spur": "trace", "rang": "rank",
    "ableitung": "diff", "ableiten": "diff",
    "integral": "integrate", "integrieren": "integrate",
    "grenzwert": "limit", "lim": "limit",
}

# Function signatures for input hints
FUNCTION_HINTS: Dict[str, str] = {
    "table": "table(Func1 | Func2, Start, End, Step)",
    "det": "determinante(Matrix)",
    "determinante": "determinante(Matrix)",
    "inv": "inverse(Matrix)",
    "inverse": "inverse(Matrix)",
    "rank": "rank(Matrix)",
    "rang": "rang(Matrix)",
    "trace": "trace(Matrix)",
    "spur": "spur(Matrix)",
    "eigenvalues": "eigenvalues(Matrix)",
    "eigenvals": "eigenvals(Matrix)",
    "ew": "ew(Matrix)",
    "eigenvectors": "eigenvectors(Matrix)",
    "eigenvects": "eigenvects(Matrix)",
    "ev": "ev(Matrix)",
    "diff": "diff(Expression, Variable)",
    "ableitung": "ableitung(Expression, Variable)",
    "ableiten": "ableiten(Expression, Variable)",
    "integrate": "integrate(Expression, Variable)",
    "integral": "integral(Expression, Variable)",
    "integrieren": "integrieren(Expression, Variable)",
    "limit": "limit(Expression, Variable, Point)",
    "lim": "lim(Expression, Variable, Point)",
    "grenzwert": "grenzwert(Expression, Variable, Point)",
}

# Safe math functions for eval()
SAFE_MATH: Dict[str, any] = {
    "__builtins__": {},
    "pi": math.pi, "e": math.e, "tau": math.tau, "inf": math.inf,
    "abs": abs, "round": round, "min": min, "max": max, "sum": sum, "pow": pow,
    "sqrt": math.sqrt, "exp": math.exp, "log": math.log,
    "log2": math.log2, "log10": math.log10,
    "ceil": math.ceil, "floor": math.floor, "factorial": math.factorial,
    "gcd": math.gcd, "comb": math.comb, "perm": math.perm,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
    "sind": lambda x: math.sin(math.radians(x)),
    "cosd": lambda x: math.cos(math.radians(x)),
    "tand": lambda x: math.tan(math.radians(x)),
    "deg": math.degrees, "rad": math.radians, "hypot": math.hypot,
}

# Unicode character replacements
REPLACEMENTS: List[Tuple[str, str]] = [
    ("²", "**2"), ("³", "**3"), ("⁴", "**4"), ("⁵", "**5"),
    ("⁶", "**6"), ("⁷", "**7"), ("⁸", "**8"), ("⁹", "**9"),
    ("×", "*"), ("÷", "/"), ("−", "-"),
]
