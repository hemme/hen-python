import unittest
import sys
import os
from io import BytesIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hen.hen import Hen

def _make_png_with_hen(hen_text):
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr_data = b'\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00'
    ihdr_crc = b'\x90wS\xde'
    ihdr = b'\x00\x00\x00\x0d' + b'IHDR' + ihdr_data + ihdr_crc
    text_payload = b'HEN\x00' + hen_text.encode('latin-1')
    text_crc_data = b'tEXt' + text_payload
    import zlib
    text_crc = struct.pack('>I', zlib.crc32(text_crc_data) & 0xffffffff)
    text_chunk = struct.pack('>I', len(text_payload)) + text_crc_data + text_crc
    iend = b'\x00\x00\x00\x00' + b'IEND' + b'\xaeB`\x82'
    return sig + ihdr + text_chunk + iend

import struct
import zlib

class TestFromPng(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample_path = os.path.join(os.path.dirname(__file__), 'test_image_1.png')

    def test_from_png_file_path(self):
        h = Hen.from_png(self.sample_path)
        self.assertEqual(h.size, 13)
        self.assertEqual(h.turn, 'w')
        self.assertIsNotNone(h.last_move)
        self.assertFalse(h.last_move.get('pass', False))

    def test_from_png_test_image_2(self):
        png_path = os.path.join(os.path.dirname(__file__), 'test_image_2.png')
        hen_obj = Hen.from_png(png_path)
        
        expected_hen = "_8QbSb_7NbPbRb_6Pbw_5ObwRw_4Ob2w_3Nw3b4_2Qw4.b"
        self.assertEqual(hen_obj.to_hen(), expected_hen)

    def test_from_png_bytesio(self):
        with open(self.sample_path, 'rb') as f:
            data = f.read()
        h = Hen.from_png(BytesIO(data))
        self.assertEqual(h.size, 13)
        self.assertEqual(h.turn, 'w')

    def test_from_png_file_object(self):
        with open(self.sample_path, 'rb') as f:
            h = Hen.from_png(f)
        self.assertEqual(h.size, 13)

    def test_from_png_roundtrip(self):
        h = Hen.from_png(self.sample_path)
        hen_str = h.to_hen()
        self.assertIn('.A3b', hen_str)
        self.assertIn('.w', hen_str)
        self.assertTrue(hen_str.startswith('.13x13'))

    def test_from_png_invalid_data(self):
        with self.assertRaises(ValueError):
            Hen.from_png(BytesIO(b'not a png'))

    def test_from_png_no_hen_metadata(self):
        sig = b'\x89PNG\r\n\x1a\n'
        ihdr_data = b'\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00'
        ihdr_crc = b'\x90wS\xde'
        ihdr = b'\x00\x00\x00\x0d' + b'IHDR' + ihdr_data + ihdr_crc
        iend = b'\x00\x00\x00\x00' + b'IEND' + b'\xaeB`\x82'
        png = sig + ihdr + iend
        with self.assertRaises(ValueError):
            Hen.from_png(BytesIO(png))

    def test_from_png_synthetic(self):
        hen_text = '.9x9_5Gb_4G~3_3E~1b~2~4_2Fw.H3w.b.E2-a'
        png_data = _make_png_with_hen(hen_text)
        h = Hen.from_png(BytesIO(png_data))
        self.assertEqual(h.size, 9)
        self.assertEqual(h.turn, 'b')
        self.assertTrue(len(h.numbered_stones) > 0)

if __name__ == '__main__':
    unittest.main()
