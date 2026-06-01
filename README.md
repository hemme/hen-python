# hen-python

Python library for converting between [HEN](https://github.com/hemme/hen-spec) and [SGF](https://www.red-bean.com/sgf/) formats.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

---

## What is HEN?

**HEN** (Hemme Notation) is a lightweight, text-based format designed for efficiently encoding and sharing Go board positions.

The formal grammar is defined in [hen-spec](https://github.com/hemme/hen-spec) (EBNF, MIT license).

SGF (Smart Game Format) is the established standard supported by most Go software. This library bridges the two formats, letting you integrate HEN into existing SGF-based workflows.

---

## Installation

You can install the package via pip:

```bash
pip install git+https://github.com/hemme/hen-python.git
```

Requires Python 3.7 or later. No external dependencies.

---

## Quick Start

### SGF → HEN

```python
from hen.hen import sgf2hen

sgf = "(;GM[1]FF[4]SZ[19];B[pd];W[dd];B[qp];W[dp])"

# Converts the SGF string directly to HEN
hen_string = sgf2hen(sgf)
print(hen_string)
```

### HEN → SGF

```python
from hen.hen import Hen

hen_string = ".9x9_7Dw_6Gb_5Eb_4Eb_3Dw2.D7w.b"

hen_obj = Hen()
hen_obj.parse(hen_string)

sgf = hen_obj.to_sgf()
print(sgf)
```

### Parse from PNG metadata

The `Hen` object can also be constructed by reading HEN metadata embedded within a PNG file's `tEXt` chunk:

```python
import urllib.request
from hen.hen import Hen

url = "https://hen.hemme-dev.workers.dev/c/hen.9x9_7Dwb_6Gb_5Eb_4Eb_3Dw2.E7b.w/position.png"
opener = urllib.request.build_opener()
opener.addheaders = [("User-Agent", "Mozilla/5.0")]
urllib.request.install_opener(opener)
path, _ = urllib.request.urlretrieve(url)

hen_obj = Hen.from_png(path)
print(hen_obj.to_hen())  # .9x9_7Dwb_6Gb_5Eb_4Eb_3Dw2.E7b.w
```

### Embed HEN into a PNG

Use `embed` to write the current board state as a `tEXt` chunk into a PNG:

```python
from io import BytesIO
from hen.hen import Hen

hen_obj = Hen()
hen_obj.parse(".9x9_7Dwb_6Gb_5Eb_4Eb_3Dw2.E7b.w")

with open("board.png", "rb") as f:
    png_data = BytesIO(f.read())

output = BytesIO()
hen_obj.embed(png_data, output)
output.seek(0)

with open("board_with_hen.png", "wb") as f:
    f.write(output.read())
```

---

## API Reference

### `class Hen`

The core class representing a HEN game position / board state.

- **`parse(self, hen_string: str)`**
  Parses a HEN string and populates the board state.
  
- **`to_sgf(self) -> str`**
  Converts the current board state to an SGF string.
  
- **`to_hen(self) -> str`**
  Converts the current board state to a HEN string.

- **`from_sgf(self, sgf_string: str, move_num: int = -1)`**
  Parses an SGF string and populates the board state up to `move_num`. If `move_num` is `-1`, it parses the entire main branch.
  
- **`from_png(cls, source: Union[str, BytesIO, BufferedReader]) -> 'Hen'`**
  Class method that reads a PNG file (from a path, `BytesIO`, or file object) and returns a `Hen` object from its embedded `HEN` metadata text chunk.

- **`embed(self, source: Union[str, BytesIO, BufferedReader], output: Union[str, BytesIO])`**
  Reads a PNG, inserts or replaces the `tEXt` chunk with keyword `HEN` containing the current board state, and writes the result to `output` (a file path or `BytesIO`).

---

### `sgf2hen(sgf_string: str, move_num: int = -1) -> str`

A helper function that converts a complete SGF string to its HEN representation.

| Parameter | Type | Description |
|---|---|---|
| `sgf_string` | `str` | Valid SGF content |
| `move_num` | `int` | The specific move number to stop at (default: `-1` for end of main branch) |

Returns a `str` containing the HEN output.

---

## Compatibility

This library targets the HEN grammar as defined in [hen-spec](https://github.com/hemme/hen-spec). Currently, only black (`b`) and white (`w`) stones are supported; multi-color stones (`r`, `g`, `l`, `y`, `p`) are not yet implemented. The conformance test suite from that repository is run on every release.

SGF versions FF[3] and FF[4] are supported for Go (GM[1]). Other game types and SGF properties not directly related to the board position (e.g., comments, game info, side variations) are currently not preserved during conversion.

---

## Contributing

Bug reports and pull requests are welcome. Before opening a PR:

1. Run the test suite: `python3 -m unittest discover -s tests -p '*_tests.py'`
2. Check that your changes pass all existing tests
3. Follow the existing code style.

---

## Related projects

| Project | Description |
|---|---|
| [hen-spec](https://github.com/hemme/hen-spec) | Formal grammar (EBNF) |

---

## License

MIT — see [LICENSE](LICENSE).