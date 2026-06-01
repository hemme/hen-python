import unittest
import sys
import os
import struct
import zlib
import tempfile
from io import BytesIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hen.hen import Hen

def _make_png(hen_text=None):
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr_data = b'\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00'
    ihdr_crc = b'\x90wS\xde'
    ihdr = b'\x00\x00\x00\x0d' + b'IHDR' + ihdr_data + ihdr_crc
    chunks = b''
    if hen_text is not None:
        payload = b'HEN\x00' + hen_text.encode('latin-1')
        crc = struct.pack('>I', zlib.crc32(b'tEXt' + payload) & 0xffffffff)
        chunks += struct.pack('>I', len(payload)) + b'tEXt' + payload + crc
    iend = b'\x00\x00\x00\x00' + b'IEND' + b'\xaeB`\x82'
    return sig + ihdr + chunks + iend

class TestEmbed(unittest.TestCase):
    def test_embed_to_file(self):
        hen = Hen()
        hen.parse('_5Gb_4G~3_3E~1b~2~4_2Fw.H3w.b.E2-a')
        png_in = _make_png()
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = f.name
        try:
            hen.embed(BytesIO(png_in), path)
            result = Hen.from_png(path)
            self.assertEqual(result.to_hen(), hen.to_hen())
        finally:
            os.unlink(path)

    def test_embed_to_bytesio(self):
        hen = Hen()
        hen.parse('_5Gb_4G~3_3E~1b~2~4_2Fw.H3w.b.E2-a')
        png_in = _make_png()
        buf = BytesIO()
        hen.embed(BytesIO(png_in), buf)
        buf.seek(0)
        result = Hen.from_png(buf)
        self.assertEqual(result.to_hen(), hen.to_hen())

    def test_embed_from_file_path(self):
        hen = Hen()
        hen.parse('.13x13_7Jb_6Eb_5Ebw_4Ebw.D7w.w')
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(_make_png())
            path_in = f.name
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path_out = f.name
        try:
            hen.embed(path_in, path_out)
            result = Hen.from_png(path_out)
            self.assertEqual(result.to_hen(), hen.to_hen())
        finally:
            os.unlink(path_in)
            os.unlink(path_out)

    def test_embed_replaces_existing_hen(self):
        hen = Hen()
        hen.parse('.w')
        png_in = _make_png('_5Gb_4G~3_3E~1b~2~4_2Fw.H3w.b.E2-a')
        buf = BytesIO()
        hen.embed(BytesIO(png_in), buf)
        buf.seek(0)
        result = Hen.from_png(buf)
        self.assertEqual(result.to_hen(), '.w')

    def test_embed_invalid_png(self):
        hen = Hen()
        hen.parse('.w')
        with self.assertRaises(ValueError):
            hen.embed(BytesIO(b'not a png'), BytesIO())

    def test_embed_preserves_other_text_chunks(self):
        png_in = _make_png('old_hen')
        extra_payload = b'Comment\x00hello world'
        extra_crc = struct.pack('>I', zlib.crc32(b'tEXt' + extra_payload) & 0xffffffff)
        extra_chunk = struct.pack('>I', len(extra_payload)) + b'tEXt' + extra_payload + extra_crc
        full_png = png_in[:33] + extra_chunk + png_in[33:]
        hen = Hen()
        hen.parse('.w')
        buf = BytesIO()
        hen.embed(BytesIO(full_png), buf)
        buf.seek(0)
        data = buf.getvalue()
        comment_found = False
        pos = 8
        while pos < len(data):
            length = struct.unpack('>I', data[pos:pos + 4])[0]
            ctype = data[pos + 4:pos + 8]
            if ctype == b'tEXt':
                cd = data[pos + 8:pos + 8 + length]
                null_idx = cd.index(0)
                kw = cd[:null_idx].decode('latin-1')
                if kw == 'Comment':
                    comment_found = True
            pos += 12 + length
        self.assertTrue(comment_found)

    def test_embed_roundtrip_complex(self):
        hen = Hen()
        hen.parse('.9x9_7Dwb_6Gb_5Eb_4Eb_3Dw2.E7b.w')
        png_in = _make_png()
        buf = BytesIO()
        hen.embed(BytesIO(png_in), buf)
        buf.seek(0)
        result = Hen.from_png(buf)
        self.assertEqual(result.size, 9)
        self.assertEqual(result.turn, 'w')
        self.assertEqual(result.to_hen(), '.9x9_7Dwb_6Gb_5Eb_4Eb_3Dw2.E7b.w')

if __name__ == '__main__':
    unittest.main()
