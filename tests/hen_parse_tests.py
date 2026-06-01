import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hen.hen import Hen, EMPTY, BLACK, WHITE

class TestHenParse(unittest.TestCase):
    def test_empty_board(self):
        h = Hen()
        result = h.parse("")
        self.assertIsNone(result)
        # Board remains unchanged from initialization
        self.assertEqual(len(h.board), 19)

    def test_simple_parse(self):
        h = Hen()
        h.parse(".w")
        self.assertEqual(h.turn, "w")

    def test_parse_last_move(self):
        h = Hen()
        h.parse(".Q16b")
        self.assertIsNotNone(h.last_move)
        self.assertEqual(h.last_move['col'], 15)
        self.assertEqual(h.last_move['row'], 3)
        self.assertEqual(h.last_move['color'], BLACK)

    def test_parse_ko_point(self):
        h = Hen()
        h.parse(".K10")
        self.assertIsNotNone(h.ko_point)
        self.assertEqual(h.ko_point['col'], 9)
        self.assertEqual(h.ko_point['row'], 9)

    def test_parse_stones(self):
        h = Hen()
        # _19b18 -> row 19, col 0 is black, remaining empty
        h.parse("_19b")
        self.assertEqual(h.board[0][0], BLACK)
        self.assertEqual(h.board[0][1], EMPTY)

    def test_parse_multiple_stones(self):
        h = Hen()
        # row 16, start at C (index 2), 2 black, D is next (col 3)
        h.parse("_16Cb2")
        self.assertEqual(h.board[3][2], BLACK)
        self.assertEqual(h.board[3][3], BLACK)
        self.assertEqual(h.board[3][4], EMPTY)

    def test_parse_marks(self):
        h = Hen()
        h.parse(".D4-CR.E5-A")
        self.assertEqual(len(h.marks), 1)
        self.assertEqual(h.marks[0]['col'], 3)
        self.assertEqual(h.marks[0]['row'], 15)
        self.assertEqual(h.marks[0]['mark'], 'CR')

        self.assertEqual(len(h.labels), 1)
        self.assertEqual(h.labels[0]['col'], 4)
        self.assertEqual(h.labels[0]['row'], 14)
        self.assertEqual(h.labels[0]['letter'], 'A')

    def test_numbered_stones(self):
        h = Hen()
        h.parse("_16D~1_15D~2")
        self.assertEqual(len(h.numbered_stones), 2)
        self.assertEqual(h.numbered_stones[0]['row'], 3)
        self.assertEqual(h.numbered_stones[0]['col'], 3)
        self.assertEqual(h.numbered_stones[0]['number'], 1)

        self.assertEqual(h.numbered_stones[1]['row'], 4)
        self.assertEqual(h.numbered_stones[1]['col'], 3)
        self.assertEqual(h.numbered_stones[1]['number'], 2)
        
        # Check board color parsing
        self.assertEqual(h.board[3][3], BLACK) # move 1 is black
        self.assertEqual(h.board[4][3], WHITE) # move 2 is white

if __name__ == '__main__':
    unittest.main()
