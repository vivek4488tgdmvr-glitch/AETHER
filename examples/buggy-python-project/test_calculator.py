import unittest
from calculator import average, normalize_name, is_even


class CalculatorTests(unittest.TestCase):
    def test_average_preserves_fraction(self):
        self.assertEqual(average([1, 2]), 1.5)

    def test_normalize_name(self):
        self.assertEqual(normalize_name("  ada LOVELACE "), "Ada Lovelace")

    def test_is_even(self):
        self.assertTrue(is_even(4))
        self.assertFalse(is_even(5))


if __name__ == "__main__":
    unittest.main()
