"""Ulauncher Solver Extension - Mathematical expression and equation solver."""

import ast
import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

logger = logging.getLogger(__name__)

# Constants
EPSILON: float = 1e-9
ICON_PATH: str = "images/icon.svg"

# Pre-compiled regex patterns for better performance
RE_FUNC_CALL = re.compile(r"^([a-zA-Z0-9_]+)\s*\(\s*(.+)\s*\)$")
RE_TABLE_CALL = re.compile(r"^table\s*\(\s*(.+?)\s*,\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*,\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*,\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*\)$", re.IGNORECASE)
RE_INCOMPLETE_FUNC = re.compile(r"^([a-zA-Z0-9_]+)\s*\([^)]*$")
RE_IMPLICIT_MULT = re.compile(r"(\d)([a-zA-Z])")
RE_CLOSE_PAREN = re.compile(r"\)\(")
RE_EXTRACT_LETTERS = re.compile(r"[a-zA-Z]")
RE_FUNC_NAMES = re.compile(r"\b(?:sqrt|sin|cos|tan|log|exp|abs|asin|acos|atan|sind|cosd|tand)\b")
RE_EQUATION_SPLIT = re.compile(r"[,;]")

# Pre-computed transformations for SymPy parser
SYMPY_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)

# Aliase für explizite Funktionsaufrufe
SYMPY_ALIASES = {
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

SAFE_MATH = {
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

REPLACEMENTS = [
    ("²", "**2"), ("³", "**3"), ("⁴", "**4"), ("⁵", "**5"),
    ("⁶", "**6"), ("⁷", "**7"), ("⁸", "**8"), ("⁹", "**9"),
    ("×", "*"), ("÷", "/"), ("−", "-"),
]


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


def _fmt(val: Any) -> str:
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
            flat_rows = [[str(_fmt(val[i, j])) for j in range(val.cols)] for i in range(val.rows)]
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


def parse_matrix_string(matrix_str: str) -> sp.Matrix:
    """Parse matrix notation to SymPy Matrix.
    
    Supports both semicolon notation [1,2;3,4] and Python list notation.
    
    Args:
        matrix_str: Matrix string representation
        
    Returns:
        SymPy Matrix object
        
    Raises:
        SyntaxError: If matrix notation is invalid
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
        return ",   ".join(f"{k} = {_fmt(v)}" for k, v in sols.items())
    if isinstance(sols, list):
        if len(var_names) == 1:
            return ",   ".join(f"{var_names[0]} = {_fmt(s)}" for s in sols)
        results = []
        for s in sols:
            if isinstance(s, dict):
                results.append(",  ".join(f"{k} = {_fmt(v)}" for k, v in s.items()))
            elif isinstance(s, (list, tuple)):
                results.append(",  ".join(f"{var_names[i]} = {_fmt(s[i])}" for i in range(len(s))))
            else:
                results.append(_fmt(s))
        return "   |   ".join(results)
    return str(sols)


class SolverExtension(Extension):
    """Ulauncher extension for mathematical expression solving."""

    def __init__(self) -> None:
        """Initialize the Solver extension."""
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):
    """Handles keyword query events and routes to appropriate solver mode."""

    def on_event(self, event: KeywordQueryEvent, extension: Extension) -> RenderResultListAction:
        """Handle a keyword query event."""
        query = (event.get_argument() or "").strip()

        if not query:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon=ICON_PATH,
                    name="Type anything...",
                    description="Equations (3x+5=4)  |  LGS (x+y=2, 3x+y=5)  |  Matrices ([1,2;3,4])",
                    on_enter=HideWindowAction(),
                )
            ])

        normalised = normalise(query)
        has_equals = "=" in normalised

        # Check for incomplete function calls (show hints)
        hint_result = self._check_function_hints(query)
        if hint_result:
            return hint_result

        # MODE 1: Arithmetic verification (no variables)
        if has_equals and not find_variables(normalised):
            result = self._handle_arithmetic_check(normalised)
            if result:
                return result

        # MODE 2: Matrix operations
        if query.startswith("[") and query.endswith("]"):
            return self._handle_matrix_query(query)

        # MODE 3: Value table generation
        table_match = RE_TABLE_CALL.match(query)
        if table_match:
            result = self._handle_table_query(table_match)
            if result:
                return result

        # MODE 4: Explicit function calls
        func_match = RE_FUNC_CALL.match(query)
        if func_match:
            result = self._handle_function_call(func_match, query)
            if result:
                return result

        # MODE 5: Equations & systems
        if has_equals:
            result = self._handle_equations(query)
            if result:
                return result

        # MODE 6: Simple expression evaluation
        return self._handle_simple_expression(query)

    def _create_result_item(self, name: str, description: str, value: str) -> ExtensionResultItem:
        """Create a result item with copy-to-clipboard action.
        
        Args:
            name: Display name
            description: Item description
            value: Value to copy
            
        Returns:
            Configured ExtensionResultItem
        """
        return ExtensionResultItem(
            icon=ICON_PATH,
            name=name,
            description=description,
            on_enter=CopyToClipboardAction(value)
        )

    def _check_function_hints(self, query: str) -> Optional[RenderResultListAction]:
        """Check if user is typing an incomplete function and show hint.
        
        Shows hint when user types a function name followed by opening bracket,
        but before closing bracket is typed.
        
        Args:
            query: Current query string
            
        Returns:
            Result list with hint or None if no incomplete function
        """
        # Check for incomplete function pattern: name(content without closing paren
        match = RE_INCOMPLETE_FUNC.match(query)
        if not match:
            return None
        
        func_name = match.group(1).lower()
        
        # Check if this is a known function
        if func_name not in FUNCTION_HINTS:
            return None
        
        hint_signature = FUNCTION_HINTS[func_name]
        
        # Show hint item
        return RenderResultListAction([
            ExtensionResultItem(
                icon=ICON_PATH,
                name=f"📝 {hint_signature}",
                description=f"Function hint for {func_name}",
                on_enter=HideWindowAction()
            )
        ])

    def _handle_arithmetic_check(self, normalised: str) -> Optional[RenderResultListAction]:
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
            verdict = "✓ True" if equal else f"✗ False  ({lhs_raw.strip()}={_fmt(lval)}, {rhs_raw.strip()}={_fmt(rval)})"
            return RenderResultListAction([self._create_result_item(verdict, "Arithmetic Verification", verdict)])
        except Exception as e:
            logger.debug(f"Arithmetic check failed: {e}")
            return None

    def _handle_matrix_query(self, query: str) -> RenderResultListAction:
        """Handle matrix query and compute matrix properties.
        
        Args:
            query: Matrix query string
            
        Returns:
            Result list with eigenvalues, determinant, rank, etc.
        """
        try:
            M = parse_matrix_string(query)
            items: List[ExtensionResultItem] = []
            
            # Eigenvalues & eigenvectors
            try:
                evecs = M.eigenvects()
                counter = 1
                for val, mult, vecs in evecs:
                    for v in vecs:
                        v_flat = [str(_fmt(x)) for x in v]
                        v_str = f"[{', '.join(v_flat)}]"
                        items.append(
                            ExtensionResultItem(
                                icon=ICON_PATH,
                                name=f"e{counter}: λ = {_fmt(val)}",
                                description=f"Vector: {v_str}  |  Multiplicity: {mult}",
                                on_enter=CopyToClipboardAction(v_str)
                            )
                        )
                        counter += 1
            except Exception as e:
                logger.debug(f"Eigenvalue computation failed: {e}")
            
            # Matrix properties
            try:
                items.append(self._create_result_item(f"Determinant: {_fmt(M.det())}", "Click to copy determinant", str(M.det())))
            except Exception as e:
                logger.debug(f"Determinant computation failed: {e}")
            
            try:
                items.append(self._create_result_item(f"Rank: {M.rank()}", "Click to copy matrix rank", str(M.rank())))
            except Exception as e:
                logger.debug(f"Rank computation failed: {e}")
            
            try:
                M_inv = M.inv()
                items.append(self._create_result_item(f"Inverse: {_fmt(M_inv)}", "Click to copy inverse matrix", str(M_inv.tolist())))
            except Exception as e:
                logger.debug(f"Inverse computation failed: {e}")

            try:
                items.append(self._create_result_item(f"Trace (Spur): {_fmt(M.trace())}", "Click to copy trace", str(M.trace())))
            except Exception as e:
                logger.debug(f"Trace computation failed: {e}")

            if items:
                return RenderResultListAction(items)
                
        except Exception as e:
            logger.error(f"Matrix query failed: {e}", exc_info=True)
            return RenderResultListAction([ExtensionResultItem(
                icon=ICON_PATH,
                name=f"Matrix Error: {e}",
                description="Check matrix syntax",
                on_enter=HideWindowAction()
            )])

    def _handle_table_query(self, table_match: re.Match) -> Optional[RenderResultListAction]:
        """Generate a value table for one or more functions over a range.
        
        Format: table(function, start, end, step) or table(func1 | func2, start, end, step)
        Example: table(x^2, 0, 5, 1) or table(x^2 | x^3, 0, 5, 1)
        
        Args:
            table_match: Regex match for table pattern
            
        Returns:
            Result list with formatted table rows or None if parsing fails
        """
        func_expr_raw = table_match.group(1).strip()
        start_str = table_match.group(2).strip()
        end_str = table_match.group(3).strip()
        step_str = table_match.group(4).strip()
        
        # Split multiple functions by pipe separator
        func_exprs = [f.strip() for f in func_expr_raw.split("|")]
        
        try:
            # Evaluate boundary values
            start_val = float(eval(preprocess(start_str), SAFE_MATH))
            end_val = float(eval(preprocess(end_str), SAFE_MATH))
            step_val = float(eval(preprocess(step_str), SAFE_MATH))
            
            if step_val <= 0:
                return RenderResultListAction([ExtensionResultItem(
                    icon=ICON_PATH,
                    name="Error: Step must be positive",
                    description="Use a value > 0 for the step parameter",
                    on_enter=HideWindowAction()
                )])
            
            # Build symbol and local scope
            x_sym = sp.Symbol('x')
            local_scope = {"x": x_sym, "pi": sp.pi, "e": sp.E, "sqrt": sp.sqrt, 
                          "sin": sp.sin, "cos": sp.cos, "tan": sp.tan}
            
            # Parse all function expressions
            parsed_funcs = []
            for func_expr in func_exprs:
                try:
                    parsed_func = parse_expr(preprocess(func_expr), transformations=SYMPY_TRANSFORMATIONS, local_dict=local_scope)
                    parsed_funcs.append((func_expr, parsed_func))
                except Exception as e:
                    logger.debug(f"Failed to parse function '{func_expr}': {e}")
                    return RenderResultListAction([ExtensionResultItem(
                        icon=ICON_PATH,
                        name=f"Error parsing: {func_expr}",
                        description=str(e),
                        on_enter=HideWindowAction()
                    )])
            
            # Generate table rows as separate result items
            items: List[ExtensionResultItem] = []
            current = start_val
            
            # Header row
            header_cols = ["x"] + [expr for expr, _ in parsed_funcs]
            header_row = "  │  ".join(header_cols)
            func_list = " | ".join([expr for expr, _ in parsed_funcs])
            items.append(ExtensionResultItem(
                icon=ICON_PATH,
                name=header_row,
                description=f"Table for {func_list} • Range [{_fmt(start_val)}, {_fmt(end_val)}] • Step {_fmt(step_val)}",
                on_enter=HideWindowAction()
            ))
            
            # Data rows
            while current <= end_val + EPSILON:
                try:
                    x_fmt = _fmt(current)
                    row_cols = [x_fmt]
                    copy_vals = [x_fmt]
                    
                    # Evaluate all functions at this x value
                    for _, parsed_func in parsed_funcs:
                        try:
                            y_val = parsed_func.subs(x_sym, current)
                            y_fmt = _fmt(y_val)
                            row_cols.append(y_fmt)
                            copy_vals.append(y_fmt)
                        except Exception as e:
                            logger.debug(f"Failed to evaluate function at x={current}: {e}")
                            row_cols.append("Error")
                            copy_vals.append("Error")
                    
                    row_str = "  │  ".join(row_cols)
                    copy_content = "\t".join(copy_vals)
                    
                    items.append(ExtensionResultItem(
                        icon=ICON_PATH,
                        name=row_str,
                        description=f"Click to copy row",
                        on_enter=CopyToClipboardAction(copy_content)
                    ))
                    
                except Exception as e:
                    logger.debug(f"Failed to process row at x={current}: {e}")
                    error_row = f"{_fmt(current)}  │  Error"
                    items.append(ExtensionResultItem(
                        icon=ICON_PATH,
                        name=error_row,
                        description="Failed to evaluate functions at this point",
                        on_enter=HideWindowAction()
                    ))
                
                current += step_val
            
            if items:
                return RenderResultListAction(items)
            
        except ValueError as e:
            logger.debug(f"Invalid table parameters: {e}")
            return RenderResultListAction([ExtensionResultItem(
                icon=ICON_PATH,
                name="Error: Invalid parameters",
                description="Format: table(func1 | func2, start, end, step)",
                on_enter=HideWindowAction()
            )])
        except Exception as e:
            logger.debug(f"Table generation failed: {e}")
            return RenderResultListAction([ExtensionResultItem(
                icon=ICON_PATH,
                name=f"Table Error: {e}",
                description="Check function and parameter syntax",
                on_enter=HideWindowAction()
            )])

    def _handle_function_call(self, func_match: re.Match, query: str) -> Optional[RenderResultListAction]:
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
                    return RenderResultListAction([self._create_result_item(f"{user_func.title()}: {_fmt(res)}", "Click to copy", str(res))])
            
            if hasattr(sp, resolved_func):
                parsed_arg = parse_expr(preprocess(arg_str), transformations=SYMPY_TRANSFORMATIONS)
                sympy_func = getattr(sp, resolved_func)
                res = sympy_func(parsed_arg)
                return RenderResultListAction([self._create_result_item(str(_fmt(res)), f"Result of {user_func}", str(res))])
        except Exception as e:
            logger.debug(f"Function call failed: {user_func}: {e}")
            return RenderResultListAction([ExtensionResultItem(
                icon=ICON_PATH,
                name=f"Error in {user_func}: {e}",
                description="Check syntax",
                on_enter=HideWindowAction()
            )])
        
        return None

    def _handle_equations(self, query: str) -> Optional[RenderResultListAction]:
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
                formatted = format_solutions(sols, var_names)
                
                return RenderResultListAction([
                    self._create_result_item(
                        str(formatted),
                        f"Solved system for {', '.join(var_names)}",
                        str(sols)
                    )
                ])
        except Exception as e:
            logger.debug(f"Equation solving failed: {e}")
        
        return None

    def _handle_simple_expression(self, query: str) -> RenderResultListAction:
        """Handle simple expression evaluation.
        
        Args:
            query: Expression query string
            
        Returns:
            Result list with computed value
        """
        try:
            parsed_expr = parse_expr(preprocess(query), transformations=SYMPY_TRANSFORMATIONS)
            res_str = _fmt(parsed_expr)
            return RenderResultListAction([
                self._create_result_item(str(res_str), f"{query} = {res_str}", str(parsed_expr))
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


if __name__ == "__main__":
    SolverExtension().run()