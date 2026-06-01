import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hen.hen import sgf2hen

class TestSgfToHen(unittest.TestCase):
    def test_basic_conversion(self):
        sgf = "(;GM[1]FF[4]CA[UTF-8]SZ[19]PL[W])"
        hen = sgf2hen(sgf)
        self.assertEqual(hen, ".w")

if __name__ == '__main__':
    unittest.main()