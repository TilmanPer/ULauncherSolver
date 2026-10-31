"""Value table generator solver."""

import logging
import re
from typing import List, Optional

import sympy as sp

from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction

from constants import ICON_PATH, EPSILON, SAFE_MATH, SYMPY_TRANSFORMATIONS
from utils.parser import preprocess
from utils import formatter

logger = logging.getLogger(__name__)


def handle_table_query(table_match: re.Match) -> Optional[RenderResultListAction]:
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
                parsed_func = sp.parsing.sympy_parser.parse_expr(
                    preprocess(func_expr), 
                    transformations=SYMPY_TRANSFORMATIONS, 
                    local_dict=local_scope
                )
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
            description=f"Table for {func_list} • Range [{formatter.fmt(start_val)}, {formatter.fmt(end_val)}] • Step {formatter.fmt(step_val)}",
            on_enter=HideWindowAction()
        ))
        
        # Data rows
        while current <= end_val + EPSILON:
            try:
                x_fmt = formatter.fmt(current)
                row_cols = [x_fmt]
                copy_vals = [x_fmt]
                
                # Evaluate all functions at this x value
                for _, parsed_func in parsed_funcs:
                    try:
                        y_val = parsed_func.subs(x_sym, current)
                        y_fmt = formatter.fmt(y_val)
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
                error_row = f"{formatter.fmt(current)}  │  Error"
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
