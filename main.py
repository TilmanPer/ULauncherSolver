"""Ulauncher Solver Extension - Mathematical expression and equation solver."""

import logging

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction

from constants import ICON_PATH, RE_TABLE_CALL, RE_INCOMPLETE_FUNC, RE_FUNC_CALL, FUNCTION_HINTS
from utils.parser import normalise, find_variables
from solvers import handle_arithmetic_check
from solvers.matrix import handle_matrix_query
from solvers.table import handle_table_query
from solvers.functions import handle_function_call
from solvers.equations import handle_equations
from solvers.expressions import handle_simple_expression

logger = logging.getLogger(__name__)


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
            result = handle_arithmetic_check(normalised)
            if result:
                return result

        # MODE 2: Matrix operations
        if query.startswith("[") and query.endswith("]"):
            return handle_matrix_query(query)

        # MODE 3: Value table generation
        table_match = RE_TABLE_CALL.match(query)
        if table_match:
            result = handle_table_query(table_match)
            if result:
                return result

        # MODE 4: Explicit function calls
        func_match = RE_FUNC_CALL.match(query)
        if func_match:
            result = handle_function_call(func_match, query)
            if result:
                return result

        # MODE 5: Equations & systems
        if has_equals:
            result = handle_equations(query)
            if result:
                return result

        # MODE 6: Simple expression evaluation
        return handle_simple_expression(query)

    def _check_function_hints(self, query: str) -> RenderResultListAction:
        """Check if user is typing an incomplete function and show hint.
        
        Shows hint when user types a function name followed by opening bracket,
        but before closing bracket is typed.
        
        Args:
            query: Current query string
            
        Returns:
            Result list with hint or None if no incomplete function
        """
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


if __name__ == "__main__":
    SolverExtension().run()
