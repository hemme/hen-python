import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hen.hen import Hen

class TestToHen(unittest.TestCase):
    def test_roundtrip_arbitrary_position(self):
        hen_str = '.19x19_19bwb2w3_10Kb_8Kbw_7JbwMw_6Kbw_1Cw3bNwb2.L7.K7w.b'
        h = Hen()
        h.parse(hen_str)
        result = h.to_hen()
        self.assertEqual(result, '_19bwb2w3_10Kb_8Kbw_7JbwMw_6Kbw_1Cw3bNwb2.L7.K7w.b')

    def test_roundtrip_ear_reddening(self):
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
        result = h.to_hen()
        self.assertEqual(result, hen_str)

    def test_roundtrip_numbered_stones(self):
        hen_str = '.9x9_5Gb_4G~3_3E~1b~2~4_2Fw.H3w.b.E2-a'
        h = Hen()
        h.parse(hen_str)
        result = h.to_hen()
        self.assertEqual(result, hen_str)

    def test_turn_only(self):
        h = Hen()
        h.parse('.b')
        self.assertEqual(h.to_hen(), '.b')

    def test_turn_white(self):
        h = Hen()
        h.parse('.w')
        self.assertEqual(h.to_hen(), '.w')

    def test_size_only(self):
        h = Hen()
        h.parse('.9x9.b')
        result = h.to_hen()
        self.assertTrue(result.startswith('.9x9'))
        self.assertIn('.b', result)

    def test_empty_hen_object(self):
        h = Hen()
        result = h.to_hen()
        self.assertEqual(result, '.b')

    def test_ko_point(self):
        h = Hen()
        h.parse('.19x19_19Ab.L7.b')
        result = h.to_hen()
        self.assertIn('.L7', result)

    def test_last_move_pass(self):
        h = Hen()
        h.parse('.pw.b')
        result = h.to_hen()
        self.assertIn('.pw', result)

    def test_marks(self):
        h = Hen()
        h.parse('.19x19_19Ab.A19-CR.A18-SQ.A17-TR.A16-MA.b')
        result = h.to_hen()
        self.assertIn('.A19-CR', result)
        self.assertIn('.A18-SQ', result)
        self.assertIn('.A17-TR', result)
        self.assertIn('.A16-MA', result)

    def test_labels(self):
        h = Hen()
        h.parse('.19x19_19Ab.A19-foo.A18-bar.b')
        result = h.to_hen()
        self.assertIn('.A19-foo', result)
        self.assertIn('.A18-bar', result)

if __name__ == '__main__':
    unittest.main()
