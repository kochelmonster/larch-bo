"""Provides a layout parser."""
import re
from larch.reactive import Pointer
from bisect import bisect_left as bisect

# __pragma__ ('ecom')


class Cell:
    """base class of all parse cells."""

    columns = [0, 0]
    """the columns the cells span,
    columns = (2, 4) means the cell is in column 2, 3, 4"""

    rows = [0, 0]
    """the rows the cells span"""

    EXPRESSION = ""
    """a compiled regular expression"""

    REGEXP = r"([^\d\W]\w*:)?"
    """regulare expression for cell name"""

    name = ""
    """the unique name of the cell"""

    def __bool__(self):
        """if return False Cell will not be assigned (see Parser)"""
        return False

    # __pragma__("skip")
    def __repr__(self):
        cols = tuple(self.columns)
        rows = tuple(self.rows)
        if self.name:
            return f"<{self.__class__.__name__} {self.name}-{cols},{rows}>"
        else:
            return f"<{self.__class__.__name__}-{cols},{rows}>"
    # __pragma__("noskip")

    @classmethod
    def create_parsed(cls, cell_string, columns):
        mo = cls.EXPRESSION.match(cell_string.strip())
        if mo:
            r = cls.create_cell(mo)
            r.columns = columns
            return r

        return None


class DOMCell(Cell):
    """A cell rendering an html cell, must be mixed in with a DIVCell Mixin."""

    at_top = False
    at_left = False
    at_right = False
    at_bottom = False
    """is the cell at border?"""

    def __bool__(self):
        return True

    def set_css_style(self, style):
        style.gridColumnStart = str(self.columns[0]+1)
        style.gridColumnEnd = str(self.columns[1]+2)
        style.gridRowStart = str(self.rows[0]+1)
        style.gridRowEnd = str(self.rows[1]+2)


class Empty(Cell):
    @classmethod
    def create_parsed(cls, cell_string, columns):
        if not cell_string.strip():
            r = cls()
            r.columns = columns
            return r
        return None


class Stretcher(Cell):
    EXPRESSION = re.compile(r"<(\d+)(M*)>")

    stretch = 0
    """stretch factor"""

    moving = False
    """if True the size of col/row can be changed by the user (splitter control)"""

    def __bool__(self):
        return False

    @classmethod
    def create_cell(cls, mo):
        c = cls()
        c.stretch = float(mo.group(1))
        c.moving = mo.group(2) == "M"
        return c


class RowSpan(Cell):
    EXPRESSION = re.compile(r'"')

    def __bool__(self):
        return False

    @classmethod
    def create_cell(cls, mo):
        return cls()


class AlignedCell(DOMCell):
    REGEXP = r"(\{([lcrj]?[tmbse]?)\})?"

    ALIGN_CODES = {
        'l': 'left', 'r': 'right', 'c': 'center', 'j': 'justify',
        't': 'top', 'm': 'middle', 'b': 'bottom', 's': 'baseline',
        'e': 'stretch'}
    alignment = ''
    """cells alignment"""

    def __repr__(self):
        result = super().__repr__()
        return result[:-1] + "{" + self.alignment + "}>"

    def set_css_style(self, style):
        super().set_css_style(style)

        if "l" in self.alignment:
            style.justifySelf = "start"
        elif "c" in self.alignment:
            style.justifySelf = "center"
        elif "r" in self.alignment:
            style.justifySelf = "end"
        elif "j" in self.alignment:
            style.justifySelf = "stretch"

        if "t" in self.alignment:
            style.alignSelf = "start"
        elif "m" in self.alignment:
            style.alignSelf = "center"
        elif "b" in self.alignment:
            style.alignSelf = "end"
        elif "e" in self.alignment:
            style.alignSelf = "stretch"


class Parser:
    """The base class for a layout description parser, it provides functions
    for parsing cells in columns and rows."""

    CELL_TYPES = []
    """A list of possible cells types."""

    row_stretchers = []
    """A sequence of row stretch factors."""

    column_stretchers = []
    """A sequence of column stretch factors."""

    row_splitters = []
    """A sequence of interactive row edges."""

    column_splitters = []
    """A sequence of interactive column edges."""

    def __init__(self, layout_string):
        columns, rows = self._parse_cells(layout_string)
        rows = self._assign_columns(columns, rows)
        self._assign_rows(rows)
        if self._make_stretchers(rows):
            self._assign_rows(rows)  # stretcher could change  rowspans

        """?
        self.rows = [
            [c for _, c in sorted(r.items(), lambda i: int(i[0])) if bool(c)] for r in rows]
        ?"""
        self.rows = [[c for _, c in sorted(r.items()) if bool(c)] for r in rows]  # __: skip
        self._assign_borders()

    def _parse_cells(self, layout_string):
        """find cells in the layout string."""
        cell_rows = []
        columns = set()

        rows = [r for r in layout_string.split("\n") if r.strip()]
        max_row_len = max(map(len, rows))
        for r in rows:
            r = r + ' ' * (max_row_len - len(r))  # __:opov
            string_cells = r.split('|')
            cells = []
            start = 0
            for c in string_cells:
                columns.add(start - 1)
                end = start + len(c)
                cells.append(self._parse_cell(c, (start, end)))
                start = end + 1

            cell_rows.append(cells)

        return columns, cell_rows

    def _parse_cell(self, cell_string, columns):
        for ct in self.CELL_TYPES:
            new_cell = ct.create_parsed(cell_string, columns)
            if new_cell is not None:
                return new_cell

        raise ValueError('Cannot parse cell', cell_string)

    def _is_stretcher(self, cell):
        return isinstance(cell, (Stretcher, Empty))

    def _make_stretchers(self, rows):
        # __pragma__("opov")
        # __pragma__ ("tconv")
        last_col = self.column_count - 1

        # check for column stretchers (in last row)
        is_last_row_stretcher = all(self._is_stretcher(c) for c in rows[-1].values())

        if is_last_row_stretcher:
            col_stretchers = [c for c in rows[-1].values() if isinstance(c, Stretcher)]
            rows.pop()  # remove the stretcher row
        else:
            col_stretchers = []

        self.row_count = len(rows)

        # check for row stretchers
        row_stretchers = [r.get(last_col) for r in rows]
        row_stretchers = [s for s in row_stretchers if isinstance(s, Stretcher)]

        if row_stretchers:
            pos = Pointer().rows[0].__state__.delegate_get
            self.row_stretchers = self._build_stretcher(row_stretchers, self.row_count, pos)
            self.row_splitters = self._build_splitter(row_stretchers, self.row_count, pos)

            # remove the stretcher columns
            self.column_count -= 1
            for r in rows:
                if r.pop(last_col, None) is not None:
                    continue

                # the last column ist spanned!
                for c in r.values():
                    c.columns = [c.columns[0], min(c.columns[1], last_col - 1)]
        else:
            self.row_stretchers = [0 for i in range(self.row_count)]

        if col_stretchers:
            pos = Pointer().columns[0].__state__.delegate_get
            self.column_stretchers = self._build_stretcher(col_stretchers, self.column_count, pos)
            self.column_splitters = self._build_splitter(col_stretchers, self.column_count, pos)
            return True
        else:
            self.column_stretchers = [0 for i in range(self.column_count)]

        # __pragma__("notconv")
        # __pragma__("noopov")
        return False

    def _assign_rows(self, rows):
        """assigns rows indices to the cells."""
        for r, cells in enumerate(rows):
            for c in cells.values():
                c.rows = [r, r]

        row_spans = {}
        for cells in reversed(rows):
            for col, rs in row_spans.items():
                c = cells.get(col)
                if c is not None:
                    c.rows = [c.rows[0], rs.rows[1]]
                else:
                    raise ValueError('wrong row span', rs.columns[0], rs.rows[0])

            row_spans = {col: c for col, c in cells.items() if isinstance(c, RowSpan)}

    def _assign_columns(self, columns, rows):
        """assigns column indices to the cells, columns is a set of column
        separator ("|") positions."""
        # assign the cells to the columns

        columns.add(max(columns) + 10000)
        columns.remove(-1)
        columns = list(columns)
        """?
        columns.sort(int)
        ?"""
        columns.sort()   # __: skip

        for cells in rows:
            for c in cells:
                start = bisect(columns, c.columns[0])
                end = bisect(columns, c.columns[1])
                c.columns = [start, end]

        self.column_count = len(columns)
        self.row_count = len(rows)
        return [{c.columns[0]: c for c in r} for r in rows]

    def _assign_borders(self):
        """determines which cells are at the border."""
        right_col = self.column_count - 1
        bottom_row = self.row_count - 1
        for c in (c for r in self.rows for c in r):
            c.at_left = c.columns[0] == 0
            c.at_right = c.columns[1] == right_col
            c.at_top = c.rows[0] == 0
            c.at_bottom = c.rows[1] == bottom_row

    def _build_stretcher(self, stretchers, size, pos):
        result = [0 for i in range(size)]
        for s in stretchers:
            result[pos(s)] = s.stretch
        return result

    def _build_splitter(self, stretchers, size, pos):
        """returns the moving edges, this must be two consecutive
        moving stretchers. 1 means the edge between row 0 and row 1
        """
        canonic = [False for i in range(size)]
        for s in stretchers:
            canonic[pos(s)] = s.moving
        return [i+1 for i, m in enumerate(canonic[:-1]) if m and canonic[i+1]]


def walk_pointer(pointer, path):
    """returns a new sub pointer defined by path."""
    path = path.strip('.').split('.')
    path = [p.split('[') for p in path]
    for idxs in path:
        name = idxs.pop(0)
        if name:
            pointer = pointer.__class__(pointer.__state__.new_attr(name))

        for i in idxs:
            i = eval(i.strip(']'))
            pointer = pointer.__class__(pointer.__state__.new_item(i))

    return pointer


'''
class LineList(list):
    def join(self):
        def padd(string, size):
            if len(string) < size:
                return string + " "*(size-len(string))
            return string

        return "|".join(padd(c, s) for c, s in zip(self, self.builder.sizes))


class LayoutBuilder:
    def __init__(self):
        self.sizes = []

    def __len__(self):
        return len(self.sizes)

    def columns(self, *cols):
        def iter_cols():
            for col in cols:
                if not isinstance(col, str):
                    for c in col:
                        yield c.strip()
                else:
                    for c in col.split("|"):
                        yield c.strip()

        if not cols:
            result = LineList([""] * len(self.sizes))
        else:
            result = LineList(iter_cols())

        if len(result) > len(self.sizes):
            self.sizes.extend([0]*(len(result)-len(self.sizes)))

        for i, c in enumerate(result):
            self.sizes[i] = max(len(c), self.sizes[i])

        result.builder = self
        return result
'''
