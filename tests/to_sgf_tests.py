import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hen.hen import Hen

class TestHenToSgf(unittest.TestCase):
    def test_turn_only_white(self):
        h = Hen()
        h.parse('.w')
        self.assertEqual(h.to_sgf(), '(;GM[1]FF[4]CA[UTF-8]SZ[19]PL[W])')

    def test_turn_only_black(self):
        h = Hen()
        h.parse('.b')
        self.assertEqual(h.to_sgf(), '(;GM[1]FF[4]CA[UTF-8]SZ[19]PL[B])')

    def test_arbitrary_position(self):
        hen_str = '.19x19_19bwb2w3_10Kb_8Kbw_7JbwMw_6Kbw_1Cw3bNwb2.L7.K7w.b'
        h = Hen()
        h.parse(hen_str)
        sgf = h.to_sgf()
        self.assertTrue(sgf.startswith('(;GM[1]FF[4]CA[UTF-8]SZ[19]'))
        self.assertIn('PL[B]', sgf)
        self.assertIn('AB[', sgf)
        self.assertIn('AW[', sgf)
        self.assertIn(';W[', sgf)
        self.assertTrue(sgf.endswith(')'))

    def test_ear_reddening_move(self):
        hen_str = (
            '_19Kbw2_18DbKbwNwPw2b_17Cw2FbJwb2w2Pwb_16Mb3Rb_15LbQb2'
            '_14Qbw2_13Ow3b3_12Pbw3b_11KbNbw2b3_10Nw2bRbw'
            '_9CwPwb2w_8Pwbwb_7NwPwbw2_6CwKbMbwPwb'
            '_5GbJwMbwbwbw_4CbEbHbMbw2bRw_3FbwbwLw2b4w2'
            '_2GbwKw2Nwb2Rbw_1JwMwObQbSb.K11b.w'
            '.M6-SQ.M5-SQ.M4-SQ.K6-SQ.J5-CR'
        )
        h = Hen()
        h.parse(hen_str)
        sgf = h.to_sgf()
        self.assertTrue(sgf.startswith('(;GM[1]FF[4]CA[UTF-8]SZ[19]'))
        self.assertIn('AB[', sgf)
        self.assertIn('AW[', sgf)
        self.assertIn(';B[', sgf)
        self.assertIn('SQ[', sgf)
        self.assertIn('CR[', sgf)
        self.assertTrue(sgf.endswith(')'))

    def test_numbered_stones_with_labels(self):
        hen_str = '.9x9_5Gb_4G~3_3E~1b~2~4_2Fw.H3w.b.E2-a'
        h = Hen()
        h.parse(hen_str)
        sgf = h.to_sgf()
        self.assertTrue(sgf.startswith('(;GM[1]FF[4]CA[UTF-8]SZ[9]'))
        self.assertIn('LB[', sgf)
        self.assertIn(':a', sgf)
        self.assertTrue(sgf.endswith(')'))

    def test_empty_board(self):
        h = Hen()
        self.assertEqual(h.to_sgf(), '(;GM[1]FF[4]CA[UTF-8]SZ[19])')

    def test_9x9_size(self):
        h = Hen()
        h.parse('.9x9.b')
        sgf = h.to_sgf()
        self.assertIn('SZ[9]', sgf)

    def test_last_move_pass(self):
        h = Hen()
        h.parse('.pw.b')
        sgf = h.to_sgf()
        self.assertNotIn(';B[', sgf)
        self.assertNotIn(';W[', sgf)

    def test_ko_not_in_sgf(self):
        h = Hen()
        h.parse('.19x19_19Ab.L7.b')
        sgf = h.to_sgf()
        self.assertNotIn('L7', sgf)

if __name__ == '__main__':
    unittest.main()
