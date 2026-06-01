import re
import struct
import urllib.parse
import zlib
from io import BufferedReader, BytesIO
from typing import Union

# Represent HEN game position / board state as Python object.

EMPTY = 0
BLACK = 1
WHITE = 2

HEN_LETTERS = 'ABCDEFGHJKLMNOPQRST'

def hen_letter_to_index(letter: str) -> int:
    return HEN_LETTERS.find(letter.upper())

def hen_index_to_letter(index: int) -> str:
    return HEN_LETTERS[index]

def hen_stone_to_color(ch: str) -> int:
    if ch == 'b': return BLACK
    if ch == 'w': return WHITE
    return EMPTY

def color_to_hen_stone(color: int) -> str:
    if color == BLACK: return 'b'
    if color == WHITE: return 'w'
    return ''

class _SgfParser:
    def __init__(self, sgf: str):
        self.sgf = sgf
        self.pos = 0
        self.length = len(sgf)
    
    def skip_whitespace(self):
        while self.pos < self.length and ord(self.sgf[self.pos]) <= 32:
            self.pos += 1

    def parse_property(self):
        self.skip_whitespace()
        start = self.pos
        while self.pos < self.length and self.sgf[self.pos].isalpha():
            self.pos += 1
        ident = self.sgf[start:self.pos].upper()
        if not ident and (self.pos >= self.length or self.sgf[self.pos] != '['):
            return None
            
        values = []
        self.skip_whitespace()
        while self.pos < self.length and self.sgf[self.pos] == '[':
            self.pos += 1
            val_start = self.pos
            bracket_count = 1
            while self.pos < self.length and bracket_count > 0:
                if self.sgf[self.pos] == '\\':
                    self.pos += 2
                else:
                    if self.sgf[self.pos] == '[': bracket_count += 1
                    elif self.sgf[self.pos] == ']': bracket_count -= 1
                    if bracket_count > 0: self.pos += 1
            val = self.sgf[val_start:self.pos]
            if '\\' in val:
                val = re.sub(r'\\(.)', r'\1', val)
            values.append(val)
            if self.pos < self.length and self.sgf[self.pos] == ']':
                self.pos += 1
            self.skip_whitespace()
            
        return ident, values

    def parse_node(self):
        self.skip_whitespace()
        if self.pos >= self.length or self.sgf[self.pos] != ';':
            return None
        self.pos += 1
        properties = {}
        while self.pos < self.length:
            start_pos = self.pos
            prop = self.parse_property()
            if not prop:
                if self.pos == start_pos: break
                continue
            ident, values = prop
            if ident:
                properties[ident] = values
        return properties

    def parse_tree(self):
        self.skip_whitespace()
        if self.pos >= self.length or self.sgf[self.pos] != '(':
            return None
        self.pos += 1

        first_node = None
        last_node = None

        while self.pos < self.length:
            self.skip_whitespace()
            if self.pos >= self.length: break
            c = self.sgf[self.pos]
            if c == ';':
                node = {'properties': self.parse_node(), 'children': []}
                if node['properties'] is not None:
                    if not first_node:
                        first_node = node
                    if last_node:
                        last_node['children'].append(node)
                    last_node = node
            elif c == '(':
                child_tree = self.parse_tree()
                if child_tree and last_node:
                    last_node['children'].append(child_tree)
            elif c == ')':
                self.pos += 1
                break
            else:
                self.pos += 1
        return first_node

class Hen:
    def __init__(self):
        self.size = 19
        self.board = [[EMPTY for _ in range(19)] for _ in range(19)]
        self.ko_point = None
        self.last_move = None
        self.turn = BLACK
        self.labels = []
        self.marks = []
        self.numbered_stones = []
        self.player_order = ['b', 'w']

    @classmethod
    def from_png(cls, source: Union[str, BytesIO, BufferedReader]) -> 'Hen':
        if isinstance(source, str):
            with open(source, 'rb') as f:
                data = f.read()
        elif isinstance(source, BytesIO):
            data = source.getvalue()
        else:
            data = source.read()

        if data[:8] != b'\x89PNG\r\n\x1a\n':
            raise ValueError('Not a valid PNG file')

        pos = 8
        hen_text = None
        while pos < len(data):
            length = struct.unpack('>I', data[pos:pos + 4])[0]
            chunk_type = data[pos + 4:pos + 8]
            if chunk_type == b'tEXt':
                chunk_data = data[pos + 8:pos + 8 + length]
                null_idx = chunk_data.index(0)
                keyword = chunk_data[:null_idx].decode('latin-1')
                if keyword == 'HEN':
                    hen_text = chunk_data[null_idx + 1:].decode('latin-1')
                    break
            pos += 12 + length

        if hen_text is None:
            raise ValueError('No HEN metadata found in PNG')

        hen_string = urllib.parse.unquote(hen_text)
        obj = cls()
        obj.parse(hen_string)
        return obj

    def embed(self, source: Union[str, BytesIO, BufferedReader], output: Union[str, BytesIO]):
        if isinstance(source, str):
            with open(source, 'rb') as f:
                data = f.read()
        elif isinstance(source, BytesIO):
            data = source.getvalue()
        else:
            data = source.read()

        if data[:8] != b'\x89PNG\r\n\x1a\n':
            raise ValueError('Not a valid PNG file')

        hen_string = self.to_hen()
        chunk_data = b'HEN\x00' + hen_string.encode('latin-1')
        text_chunk = (struct.pack('>I', len(chunk_data)) + b'tEXt' +
                      chunk_data + struct.pack('>I', zlib.crc32(b'tEXt' + chunk_data) & 0xFFFFFFFF))

        pos = 8
        ihdr_length = struct.unpack('>I', data[pos:pos + 4])[0]
        ihdr_end = pos + 12 + ihdr_length

        remaining = bytearray()
        scan = ihdr_end
        while scan < len(data):
            length = struct.unpack('>I', data[scan:scan + 4])[0]
            ctype = data[scan + 4:scan + 8]
            if ctype == b'tEXt':
                cd = data[scan + 8:scan + 8 + length]
                null_idx = cd.index(0) if 0 in cd else -1
                if null_idx >= 0 and cd[:null_idx] == b'HEN':
                    scan += 12 + length
                    continue
            remaining.extend(data[scan:scan + 12 + length])
            scan += 12 + length

        result = data[:ihdr_end] + text_chunk + bytes(remaining)

        if isinstance(output, str):
            with open(output, 'wb') as f:
                f.write(result)
        else:
            output.write(result)
        return output

    def parse(self, hen_string: str):
        if not hen_string:
            return None
            
        hen = urllib.parse.unquote(hen_string).strip()
        hen = re.sub(r'[\s\n\r]+', '', hen)
        
        self.size = 19
        self.board = None
        self.ko_point = None
        self.last_move = None
        self.turn = None
        self.labels = []
        self.marks = []
        self.numbered_stones = []
        self.player_order = None

        i = 0
        length = len(hen)
        
        while i < length:
            if hen[i] == '.':
                i += 1
                part_start = i
                while i < length:
                    if hen[i] == '.' or hen[i] == '_':
                        break
                    if hen[i] == '~':
                        if i + 1 < length and hen[i + 1] in 'bwrglyp':
                            break
                    i += 1
                part = hen[part_start:i]
                self._parse_hen_dot_part(part)
            elif hen[i] == '_':
                i += 1
                row_start = i
                while i < length:
                    if hen[i] == '_' or hen[i] == '.':
                        break
                    if hen[i] == '~':
                        if i + 1 < length and '0' <= hen[i + 1] <= '9':
                            i += 1
                            continue
                        break
                    i += 1
                row_part = hen[row_start:i]
                self._parse_hen_row(row_part)
            elif hen[i] == '~':
                i += 1
                po_start = i
                while i < length and hen[i] not in ('.', '_', '~'):
                    i += 1
                po_part = hen[po_start:i]
                self.player_order = []
                for pi in range(len(po_part)):
                    if po_part[pi] in 'bwrglyp':
                        self.player_order.append(po_part[pi])
            else:
                i += 1
                
        if self.board is None:
            self.board = [[EMPTY for _ in range(self.size)] for _ in range(self.size)]
            
        if len(self.numbered_stones) > 0:
            po = self.player_order if self.player_order else ['b', 'w']
            for ns in self.numbered_stones:
                color_idx = (ns['number'] - 1) % len(po)
                stone_char = po[color_idx]
                self.board[ns['row']][ns['col']] = hen_stone_to_color(stone_char)
                
        return self

    def _parse_hen_dot_part(self, part: str):
        if not part:
            return
            
        size_match = re.match(r'^(\d+)x(\d+)$', part)
        if size_match:
            self.size = int(size_match.group(1))
            if self.board is None:
                self.board = [[EMPTY for _ in range(self.size)] for _ in range(self.size)]
            return
            
        if part == 'b' or part == 'w':
            self.turn = part
            return
            
        if len(part) >= 2 and part[0] == 'p':
            pass_stone = part[1]
            if pass_stone in ('b', 'w'):
                self.last_move = {'color': hen_stone_to_color(pass_stone), 'pass': True}
                return
                
        last_move_match = re.match(r'^([A-HJ-T])(\d+)([bw])$', part)
        if last_move_match:
            col = hen_letter_to_index(last_move_match.group(1))
            row = self.size - int(last_move_match.group(2))
            stone_color = hen_stone_to_color(last_move_match.group(3))
            self.last_move = {'row': row, 'col': col, 'color': stone_color, 'pass': False}
            return
            
        ko_match = re.match(r'^([A-HJ-T])(\d+)$', part)
        if ko_match:
            ko_col = hen_letter_to_index(ko_match.group(1))
            ko_row = self.size - int(ko_match.group(2))
            self.ko_point = {'row': ko_row, 'col': ko_col}
            return
            
        label_mark_match = re.match(r'^([A-HJ-T])(\d+)-(.+)$', part)
        if label_mark_match:
            lm_col = hen_letter_to_index(label_mark_match.group(1))
            lm_row = self.size - int(label_mark_match.group(2))
            val = label_mark_match.group(3)
            if val in ('CR', 'SQ', 'TR', 'MA'):
                self.marks.append({'row': lm_row, 'col': lm_col, 'mark': val})
            else:
                self.labels.append({'row': lm_row, 'col': lm_col, 'letter': val})
            return

    def _parse_hen_row(self, part: str):
        if not part:
            return
            
        row_start = 0
        while row_start < len(part) and '0' <= part[row_start] <= '9':
            row_start += 1
            
        if row_start == 0:
            return
            
        row_num_str = part[0:row_start]
        row_num = self.size - int(row_num_str)
        if row_num < 0 or row_num >= self.size:
            return
            
        if self.board is None:
            self.board = [[EMPTY for _ in range(self.size)] for _ in range(self.size)]
            
        j = row_start
        col = -1
        prev_stone = None
        
        if j < len(part) and 'A' <= part[j] <= 'T' and part[j] != 'I':
            col = hen_letter_to_index(part[j])
            j += 1
        else:
            col = 0
            
        while j < len(part):
            ch = part[j]
            if 'A' <= ch <= 'T' and ch != 'I':
                col = hen_letter_to_index(ch)
                j += 1
            elif ch == 'b' or ch == 'w':
                if col < self.size:
                    self.board[row_num][col] = hen_stone_to_color(ch)
                prev_stone = ch
                col += 1
                j += 1
            elif '0' <= ch <= '9' and prev_stone:
                num_start = j
                while j < len(part) and '0' <= part[j] <= '9':
                    j += 1
                count = int(part[num_start:j])
                for _ in range(1, count):
                    if col < self.size:
                        self.board[row_num][col] = hen_stone_to_color(prev_stone)
                    col += 1
            elif ch == '~':
                j += 1
                mv_num_start = j
                while j < len(part) and '0' <= part[j] <= '9':
                    j += 1
                if mv_num_start < j:
                    move_num = int(part[mv_num_start:j])
                    if move_num > 0:
                        self.numbered_stones.append({'row': row_num, 'col': col, 'number': move_num})
                prev_stone = None
                col += 1
            else:
                j += 1

    @staticmethod
    def _to_sgf_coord(row, col):
        return chr(97 + col) + chr(97 + row)

    def to_sgf(self):
        if self.board is None:
            return ''

        blacks = []
        whites = []
        last_move_r = -1
        last_move_c = -1
        if self.last_move and not self.last_move.get('pass', False):
            last_move_r = self.last_move['row']
            last_move_c = self.last_move['col']

        for r in range(self.size):
            for c in range(self.size):
                if r == last_move_r and c == last_move_c:
                    continue
                if self.board[r][c] == BLACK:
                    blacks.append(self._to_sgf_coord(r, c))
                elif self.board[r][c] == WHITE:
                    whites.append(self._to_sgf_coord(r, c))

        sgf = '(;GM[1]FF[4]CA[UTF-8]SZ[' + str(self.size) + ']'

        if self.turn == 'b':
            sgf += 'PL[B]'
        elif self.turn == 'w':
            sgf += 'PL[W]'

        if blacks:
            sgf += 'AB[' + ']['.join(blacks) + ']'
        if whites:
            sgf += 'AW[' + ']['.join(whites) + ']'

        if self.last_move and not self.last_move.get('pass', False):
            move_color = 'B' if self.last_move['color'] == BLACK else 'W'
            sgf += ';' + move_color + '[' + self._to_sgf_coord(self.last_move['row'], self.last_move['col']) + ']'

        if self.labels:
            sgf += 'LB[' + ']['.join(
                self._to_sgf_coord(l['row'], l['col']) + ':' + l['letter']
                for l in self.labels
            ) + ']'

        if self.numbered_stones:
            ns_labels = [
                self._to_sgf_coord(ns['row'], ns['col']) + ':' + str(ns['number'])
                for ns in self.numbered_stones
            ]
            if self.labels:
                sgf += '[' + ']['.join(ns_labels) + ']'
            else:
                sgf += 'LB[' + ']['.join(ns_labels) + ']'

        if self.marks:
            for m in self.marks:
                sgf += m['mark'] + '[' + self._to_sgf_coord(m['row'], m['col']) + ']'

        sgf += ')'
        return sgf

    def to_hen(self):
        if self.board is None:
            return ''

        parts = []

        number_map = {}
        has_numbers = False
        po = self.player_order or ['b', 'w']

        if self.numbered_stones:
            sorted_nums = sorted(self.numbered_stones, key=lambda ns: ns['number'])
            if sorted_nums:
                has_numbers = True
                first_stone_str = color_to_hen_stone(self.board[sorted_nums[0]['row']][sorted_nums[0]['col']])
                if first_stone_str == 'w':
                    po = ['w', 'b']
                elif first_stone_str == 'b':
                    po = ['b', 'w']

                for a in sorted_nums:
                    color_idx = (a['number'] - 1) % len(po)
                    expected_stone = po[color_idx]
                    actual_stone = color_to_hen_stone(self.board[a['row']][a['col']])
                    if expected_stone == actual_stone and actual_stone != '':
                        number_map[str(a['row']) + ',' + str(a['col'])] = a['number']

        if self.size != 19:
            parts.append('.' + str(self.size) + 'x' + str(self.size))

        for r in range(self.size):
            row_stones = []
            for c in range(self.size):
                if self.board[r][c] != EMPTY:
                    row_stones.append({'col': c, 'color': self.board[r][c]})
            if not row_stones:
                continue

            row_hen = '_' + str(self.size - r)
            prev_col = -2
            run_color = None
            run_count = 0

            def flush_run():
                nonlocal row_hen, run_count
                if run_count == 0:
                    return
                stone = color_to_hen_stone(run_color)
                if run_count == 1:
                    row_hen += stone
                else:
                    row_hen += stone + str(run_count)

            for si, stone in enumerate(row_stones):
                key = str(r) + ',' + str(stone['col'])
                num_val = number_map.get(key)

                if num_val is not None:
                    flush_run()
                    run_color = None
                    run_count = 0

                    if si == 0 and stone['col'] != 0:
                        row_hen += hen_index_to_letter(stone['col'])
                    elif si > 0 and stone['col'] != prev_col + 1:
                        row_hen += hen_index_to_letter(stone['col'])

                    row_hen += '~' + str(num_val)
                    prev_col = stone['col']
                    continue

                continues_run = run_color is not None and stone['color'] == run_color and stone['col'] == prev_col + 1

                if continues_run:
                    run_count += 1
                else:
                    flush_run()
                    if si == 0:
                        if stone['col'] != 0:
                            row_hen += hen_index_to_letter(stone['col'])
                    elif stone['col'] != prev_col + 1:
                        row_hen += hen_index_to_letter(stone['col'])
                    run_color = stone['color']
                    run_count = 1

                prev_col = stone['col']

            flush_run()
            parts.append(row_hen)

        if has_numbers and po[0] == 'w':
            parts.append('~wb')

        if self.ko_point:
            parts.append('.' + hen_index_to_letter(self.ko_point['col']) + str(self.size - self.ko_point['row']))

        if self.last_move and not self.last_move.get('pass', False):
            mv_stone = color_to_hen_stone(self.last_move['color'])
            parts.append('.' + hen_index_to_letter(self.last_move['col']) + str(self.size - self.last_move['row']) + mv_stone)
        elif self.last_move and self.last_move.get('pass', False):
            parts.append('.p' + color_to_hen_stone(self.last_move['color']))

        turn_str = self.turn if isinstance(self.turn, str) else color_to_hen_stone(self.turn) if self.turn else None
        if turn_str:
            parts.append('.' + turn_str)

        for l in self.labels:
            parts.append('.' + hen_index_to_letter(l['col']) + str(self.size - l['row']) + '-' + l['letter'])

        for ns in self.numbered_stones:
            key = str(ns['row']) + ',' + str(ns['col'])
            if key not in number_map:
                parts.append('.' + hen_index_to_letter(ns['col']) + str(self.size - ns['row']) + '-' + str(ns['number']))

        for m in self.marks:
            parts.append('.' + hen_index_to_letter(m['col']) + str(self.size - m['row']) + '-' + m['mark'])

        return ''.join(parts)

    def from_sgf(self, sgf_string: str, move_num: int = -1):
        if not sgf_string:
            return self
            
        parser = _SgfParser(sgf_string)
        root = None
        while parser.pos < parser.length:
            parser.skip_whitespace()
            if parser.pos < parser.length and parser.sgf[parser.pos] == '(':
                root = parser.parse_tree()
                if root:
                    break
            else:
                parser.pos += 1
                
        if not root:
            return self
            
        main_line = []
        curr = root
        while curr:
            if curr['properties'] is not None:
                main_line.append(curr['properties'])
            if curr['children']:
                curr = curr['children'][0]
            else:
                break
                
        if main_line and 'SZ' in main_line[0]:
            try:
                self.size = int(main_line[0]['SZ'][0])
            except ValueError:
                pass
                
        self.board = [[EMPTY for _ in range(self.size)] for _ in range(self.size)]
        
        def get_group_and_liberties(r, c):
            color = self.board[r][c]
            if color == EMPTY:
                return [], 0
            group = []
            liberties = set()
            visited = set()
            stack = [(r, c)]
            visited.add((r, c))
            while stack:
                curr_r, curr_c = stack.pop()
                group.append((curr_r, curr_c))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = curr_r + dr, curr_c + dc
                    if 0 <= nr < self.size and 0 <= nc < self.size:
                        if self.board[nr][nc] == EMPTY:
                            liberties.add((nr, nc))
                        elif self.board[nr][nc] == color and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            stack.append((nr, nc))
            return group, len(liberties)

        def apply_move(r, c, color):
            if r < 0 or r >= self.size or c < 0 or c >= self.size:
                return
            self.board[r][c] = color
            opponent = WHITE if color == BLACK else BLACK
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.size and 0 <= nc < self.size and self.board[nr][nc] == opponent:
                    group, libs = get_group_and_liberties(nr, nc)
                    if libs == 0:
                        for gr, gc in group:
                            self.board[gr][gc] = EMPTY
            group, libs = get_group_and_liberties(r, c)
            if libs == 0:
                for gr, gc in group:
                    self.board[gr][gc] = EMPTY
                    
        def from_sgf_coord(s):
            if not s or len(s) < 2: return None
            col = ord(s[0].lower()) - 97
            row = ord(s[1].lower()) - 97
            if col < 0 or col >= self.size or row < 0 or row >= self.size:
                return None
            return row, col
            
        current_move = 0
        
        for i, node in enumerate(main_line):
            is_move_node = ('B' in node) or ('W' in node)
            if is_move_node and move_num != -1 and current_move >= move_num:
                break
                
            if 'PL' in node:
                val = node['PL'][0].upper()
                if val == 'W':
                    self.turn = 'w'
                elif val == 'B':
                    self.turn = 'b'

            if 'AB' in node:
                for val in node['AB']:
                    coord = from_sgf_coord(val)
                    if coord:
                        self.board[coord[0]][coord[1]] = BLACK
            if 'AW' in node:
                for val in node['AW']:
                    coord = from_sgf_coord(val)
                    if coord:
                        self.board[coord[0]][coord[1]] = WHITE
                        
            if 'B' in node:
                coord = from_sgf_coord(node['B'][0])
                if coord:
                    apply_move(coord[0], coord[1], BLACK)
                    self.last_move = {'row': coord[0], 'col': coord[1], 'color': BLACK, 'pass': False}
                else:
                    self.last_move = {'color': BLACK, 'pass': True}
                self.turn = 'w'
            elif 'W' in node:
                coord = from_sgf_coord(node['W'][0])
                if coord:
                    apply_move(coord[0], coord[1], WHITE)
                    self.last_move = {'row': coord[0], 'col': coord[1], 'color': WHITE, 'pass': False}
                else:
                    self.last_move = {'color': WHITE, 'pass': True}
                self.turn = 'b'

            if is_move_node:
                current_move += 1
                
            self.labels = []
            self.marks = []
            
            if 'LB' in node:
                for val in node['LB']:
                    parts = val.split(':', 1)
                    if len(parts) >= 2:
                        coord = from_sgf_coord(parts[0])
                        if coord:
                            self.labels.append({'row': coord[0], 'col': coord[1], 'letter': parts[1]})
            for mark_prop, mark_val in [('CR', 'CR'), ('SQ', 'SQ'), ('TR', 'TR'), ('MA', 'MA')]:
                if mark_prop in node:
                    for val in node[mark_prop]:
                        coord = from_sgf_coord(val)
                        if coord:
                            self.marks.append({'row': coord[0], 'col': coord[1], 'mark': mark_val})
                            
            if move_num != -1 and current_move == move_num:
                break

        return self

def sgf2hen(sgf_string: str, move_num: int = -1) -> str:
    hen = Hen()
    hen.from_sgf(sgf_string, move_num)
    return hen.to_hen()
