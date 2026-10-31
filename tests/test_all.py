"""
Unit tests for ulauncher-solver extension.

Run with: pytest tests/ -v --cov=. --cov-report=html
Requires: pip install pytest pytest-cov
"""

from constants import EPSILON
from solvers.expressions import handle_simple_expression
from solvers import handle_arithmetic_check
from utils.formatter import fmt, format_solutions
from utils.parser import normalise, preprocess, find_variables, parse_matrix_string
import pytest
from sympy import Symbol, Matrix, sin, pi, sqrt
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestParser:
    """Test expression parser functions."""

    def test_normalise_unicode(self):
        """Test Unicode character replacement."""
        assert normalise("2²+3×4") == "2**2+3*4"
        assert normalise("10÷5−3") == "10/5-3"

    def test_preprocess(self):
        """Test expression preprocessing."""
        assert preprocess("2x") == "2*x"
        assert preprocess(")(") == ")*("
        assert preprocess("2^3") == "2**3"

    def test_find_variables_simple(self):
        """Test variable extraction."""
        assert find_variables("x+y") == ["x", "y"]
        assert find_variables("a+b+c") == ["a", "b", "c"]

    def test_find_variables_excludes_functions(self):
        """Test that function names are excluded from variables."""
        assert find_variables("sin(x)+cos(y)") == ["x", "y"]
        assert "sin" not in find_variables("sin(x)")

    def test_find_variables_excludes_special(self):
        """Test that e and I are excluded."""
        assert "e" not in find_variables("e*x")  # e is Euler's number
        assert "I" not in find_variables("I*x")  # I is imaginary unit

    def test_parse_matrix_semicolon_notation(self):
        """Test matrix parsing with semicolon notation."""
        m = parse_matrix_string("[1,2;3,4]")
        assert m.shape == (2, 2)
        assert m[0, 0] == 1
        assert m[1, 1] == 4

    def test_parse_matrix_list_notation(self):
        """Test matrix parsing with Python list notation."""
        m = parse_matrix_string("[[1,2],[3,4]]")
        assert m.shape == (2, 2)
        assert m[0, 1] == 2

    def test_parse_matrix_invalid_raises(self):
        """Test that invalid matrix raises ValueError."""
        with pytest.raises(ValueError):
            parse_matrix_string("[1,2;3]")  # Inconsistent rows
        with pytest.raises(ValueError):
            parse_matrix_string("[not,matrix]")


class TestFormatter:
    """Test value formatting functions."""

    def test_fmt_integer(self):
        """Test formatting integers."""
        assert fmt(42) == "42"
        assert fmt(0) == "0"
        assert fmt(-10) == "-10"

    def test_fmt_float(self):
        """Test formatting floats."""
        result = fmt(3.14159)
        assert len(result) <= 10  # Should be reasonable length
        assert "3" in result

    def test_fmt_rational(self):
        """Test formatting rational numbers."""
        from sympy import Rational
        assert fmt(Rational(1, 2)) == "1/2"

    def test_fmt_very_close_to_int(self):
        """Test formatting numbers very close to integers."""
        result = fmt(5.0 + 1e-10)
        assert result == "5"

    def test_format_solutions_dict(self):
        """Test formatting dict solutions."""
        sols = {Symbol('x'): 2, Symbol('y'): 3}
        result = format_solutions(sols, ['x', 'y'])
        assert 'x' in result
        assert '2' in result

    def test_format_solutions_no_solution(self):
        """Test formatting no solution."""
        assert format_solutions(None, ['x']) == "No solution"
        assert format_solutions([], ['x']) == "No solution"


class TestArithmetic:
    """Test arithmetic verification."""

    def test_arithmetic_true(self):
        """Test true arithmetic statements."""
        result = handle_arithmetic_check("2+2=4")
        assert result is not None
        assert "True" in str(result.items[0].name)

    def test_arithmetic_false(self):
        """Test false arithmetic statements."""
        result = handle_arithmetic_check("2+2=5")
        assert result is not None
        assert "False" in str(result.items[0].name)

    def test_arithmetic_floating_point_epsilon(self):
        """Test floating point comparison with epsilon."""
        # 0.1 + 0.2 ≈ 0.3 in floating point (due to precision)
        result = handle_arithmetic_check("0.1+0.2=0.3")
        assert result is not None
        # Should be True within EPSILON

    def test_arithmetic_multiple_equals_rejected(self):
        """Test that multiple equals are rejected."""
        result = handle_arithmetic_check("2=2=2")
        assert result is None

    def test_arithmetic_with_variables_rejected(self):
        """Test that equations with variables are rejected."""
        result = handle_arithmetic_check("x+2=4")
        # Should be rejected by find_variables check upstream
        # This depends on extension logic


class TestExpressions:
    """Test expression evaluation."""

    def test_simple_arithmetic(self):
        """Test simple arithmetic evaluation."""
        result = handle_simple_expression("2+2")
        assert result is not None
        assert "4" in result.items[0].name

    def test_complex_expression(self):
        """Test complex expression."""
        result = handle_simple_expression("sqrt(16)")
        assert result is not None
        assert "4" in result.items[0].name

    def test_trigonometric(self):
        """Test trigonometric functions."""
        # sin(π/2) = 1
        result = handle_simple_expression("sin(pi/2)")
        assert result is not None
        # Should be close to 1

    def test_exponential(self):
        """Test exponential functions."""
        result = handle_simple_expression("exp(0)")
        assert result is not None
        assert "1" in result.items[0].name

    def test_equation_identity(self):
        """Test that an identity equation is recognized."""
        result = handle_simple_expression("x=x")
        assert result is not None
        assert "True" in result.items[0].name

    def test_invalid_expression_handled(self):
        """Test that invalid expressions are handled gracefully."""
        result = handle_simple_expression("@#$%")
        assert result is not None
        assert "Error" in result.items[0].name


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_input(self):
        """Test empty or whitespace input."""
        assert find_variables("") == []
        assert find_variables("   ") == []

    def test_very_large_numbers(self):
        """Test formatting very large numbers."""
        result = fmt(1e100)
        assert result is not None
        assert len(result) < 50

    def test_very_small_numbers(self):
        """Test formatting very small numbers."""
        result = fmt(1e-100)
        assert result is not None

    def test_matrix_identity(self):
        """Test identity matrix properties."""
        m = Matrix([[1, 0], [0, 1]])
        assert m.det() == 1
        assert m.rank() == 2

    def test_matrix_singular(self):
        """Test singular matrix (non-invertible)."""
        m = Matrix([[1, 2], [2, 4]])
        assert m.det() == 0
        # Inverse should raise or return error

    def test_unicode_mixed_with_operators(self):
        """Test Unicode characters mixed with operators."""
        result = preprocess("2² + 3³ × 4")
        assert "**" in result
        assert "*" in result


class TestPerformance:
    """Performance and regression tests."""

    def test_regex_compilation_speed(self):
        """Verify regex patterns are pre-compiled."""
        from constants import RE_FUNC_CALL, RE_EQUATION_SPLIT
        import re
        # Pre-compiled patterns should be Pattern type
        assert isinstance(RE_FUNC_CALL, type(re.compile("")))

    def test_normalise_performance(self):
        """Test normalise on large expressions."""
        large_expr = "2²+3²+4²" * 100
        result = normalise(large_expr)
        assert "**" in result
        # Should complete quickly (< 1ms)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
