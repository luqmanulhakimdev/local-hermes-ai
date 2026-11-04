import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.tools.calculator import calculate


class TestCalculator(unittest.TestCase):
    def test_basic_arithmetic(self):
        self.assertEqual(calculate("2 + 3"), 5)
        self.assertEqual(calculate("10 - 4"), 6)
        self.assertEqual(calculate("4 * 5"), 20)
        self.assertEqual(calculate("15 / 3"), 5.0)
        self.assertEqual(calculate("10 % 3"), 1)
        self.assertEqual(calculate("2 ** 3"), 8)

    def test_unary_operators(self):
        self.assertEqual(calculate("-5"), -5)
        self.assertEqual(calculate("+7"), 7)
        self.assertEqual(calculate("-(-4)"), 4)

    def test_parentheses_and_order_of_operations(self):
        self.assertEqual(calculate("2 + 3 * 4"), 14)
        self.assertEqual(calculate("(2 + 3) * 4"), 20)
        self.assertEqual(calculate("((10 - 2) / 2) + 1"), 5.0)

    def test_floating_point_numbers(self):
        self.assertAlmostEqual(calculate("3.5 + 2.5"), 6.0)
        self.assertAlmostEqual(calculate("7.5 / 2.5"), 3.0)

    def test_expression_too_long(self):
        long_expr = "1 + " * 70 + "1"  # > 200 chars
        with self.assertRaises(ValueError) as ctx:
            calculate(long_expr)
        self.assertIn("Expression is too long.", str(ctx.exception))

    def test_exponent_too_large(self):
        with self.assertRaises(ValueError) as ctx:
            calculate("2 ** 11")
        self.assertIn("Exponent is too large.", str(ctx.exception))

    def test_negative_exponent_within_limit(self):
        self.assertEqual(calculate("2 ** -2"), 0.25)

    def test_result_too_large(self):
        with self.assertRaises(ValueError) as ctx:
            calculate("1e101 + 1")
        self.assertIn("Result is too large.", str(ctx.exception))

    def test_unsupported_nodes_and_functions(self):
        with self.assertRaises((ValueError, SyntaxError)):
            calculate("__import__('os').system('ls')")

        with self.assertRaises(ValueError) as ctx:
            calculate("len([1, 2, 3])")
        self.assertIn("Unsupported expression.", str(ctx.exception))

    def test_unsupported_operators(self):
        with self.assertRaises(ValueError) as ctx:
            calculate("1 << 2")
        self.assertIn("Unsupported expression.", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            calculate("1 == 1")
        self.assertIn("Unsupported expression.", str(ctx.exception))

    def test_division_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            calculate("5 / 0")


if __name__ == "__main__":
    unittest.main()

