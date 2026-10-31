"""Matrix operations solver."""

import logging
from typing import List

import sympy as sp

from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction

from constants import ICON_PATH
from utils.parser import parse_matrix_string
from utils import formatter

logger = logging.getLogger(__name__)


def handle_matrix_query(query: str) -> RenderResultListAction:
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
                    v_flat = [str(formatter.fmt(x)) for x in v]
                    v_str = f"[{', '.join(v_flat)}]"
                    items.append(
                        ExtensionResultItem(
                            icon=ICON_PATH,
                            name=f"e{counter}: λ = {formatter.fmt(val)}",
                            description=f"Vector: {v_str}  |  Multiplicity: {mult}",
                            on_enter=CopyToClipboardAction(v_str)
                        )
                    )
                    counter += 1
        except Exception as e:
            logger.debug(f"Eigenvalue computation failed: {e}")
        
        # Matrix properties
        try:
            items.append(ExtensionResultItem(
                icon=ICON_PATH,
                name=f"Determinant: {formatter.fmt(M.det())}",
                description="Click to copy determinant",
                on_enter=CopyToClipboardAction(str(M.det()))
            ))
        except Exception as e:
            logger.debug(f"Determinant computation failed: {e}")
        
        try:
            items.append(ExtensionResultItem(
                icon=ICON_PATH,
                name=f"Rank: {M.rank()}",
                description="Click to copy matrix rank",
                on_enter=CopyToClipboardAction(str(M.rank()))
            ))
        except Exception as e:
            logger.debug(f"Rank computation failed: {e}")
        
        try:
            M_inv = M.inv()
            items.append(ExtensionResultItem(
                icon=ICON_PATH,
                name=f"Inverse: {formatter.fmt(M_inv)}",
                description="Click to copy inverse matrix",
                on_enter=CopyToClipboardAction(str(M_inv.tolist()))
            ))
        except Exception as e:
            logger.debug(f"Inverse computation failed: {e}")

        try:
            items.append(ExtensionResultItem(
                icon=ICON_PATH,
                name=f"Trace (Spur): {formatter.fmt(M.trace())}",
                description="Click to copy trace",
                on_enter=CopyToClipboardAction(str(M.trace()))
            ))
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
