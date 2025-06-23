import unittest
import larch.reactive as ra
import larch.bo.client.textlayout as tl
import larch.bo.client.grid as grid
import larch.bo.client.table as table


class GridLayoutTest(unittest.TestCase):
    def parse(self, layout):
        return grid.GridParser(layout)

    def test_case1(self):
        p = self.parse("""a|(10,1)|[b]""")
        self.assertEqual(
            repr(p.rows),
            "[[<Label a-(0, 0),(0, 0){}>, <Spacer spacer-1-0-(1, 1),(0, 0)>, <Field b-(2, 2),(0, 0){}>]]")
        self.assertEqual(p.row_count, 1)
        self.assertEqual(p.column_count, 3)
        self.assertEqual(repr(p.row_stretchers), "[<0>]")
        self.assertEqual(repr(p.column_stretchers), "[<0>, <0>, <0>]")

    def test_case2(self):
        p = self.parse("""
a  |(10,1)|[b]
[c]|      |[d]|<1M>
   |  <1> |
""")
        
        self.assertEqual(
            repr(p.rows),
            ("[[<Label a-(0, 0),(0, 0){}>, <Spacer spacer-1-0-(1, 1),(0, 0)>, <Field b-(2, 2),(0, 0){}>], [<Field c-(0, 0),(1, 1){}>, <Field d-(2, 2),(1, 1){}>]]"))
        self.assertEqual(p.row_count, 2)
        self.assertEqual(p.column_count, 3)
        self.assertEqual(repr(p.row_stretchers), "[<0>, <1.0M>]")
        self.assertEqual(repr(p.column_stretchers), "[<0>, <1.0>, <0>]")

    def test_case3(self):
        p = self.parse("""
a  |(10,1)|[b]
[c]|      | "     |<1>
 " |      |[d]|[e]
   | <1M> |   |<1>|
""")

        self.assertEqual(
            repr(p.rows),
            ("[[<Label a-(0, 0),(0, 0){}>, <Spacer spacer-1-0-(1, 1),(0, 0)>, <Field b-(2, 3),(0, 1){}>], [<Field c-(0, 0),(1, 2){}>], [<Field d-(2, 2),(2, 2){}>, <Field e-(3, 3),(2, 2){}>]]"))
        self.assertEqual(p.row_count, 3)
        self.assertEqual(p.column_count, 4)
        self.assertEqual(repr(p.row_stretchers), "[<0>, <1.0>, <0>]")
        self.assertEqual(repr(p.column_stretchers),
                         "[<0>, <1.0M>, <0>, <1.0>]")

    def test_case4(self):
        p = self.parse("""
ad:[active_displays[0]]{cm}|<1>
<1>
""")
        self.assertEqual(repr(p.rows), "[[<Field ad-(0, 0),(0, 0){cm}>]]")
        self.assertEqual(p.rows[0][0].path, "active_displays[0]")
        self.assertEqual(p.row_count, 1)
        self.assertEqual(p.column_count, 1)
        self.assertEqual(repr(p.row_stretchers), "[<1.0>]")
        self.assertEqual(repr(p.column_stretchers), "[<1.0>]")

    def test_case5(self):
        p = self.parse("""a:a|(10,1)|b:[b]""")
        self.assertEqual(
            repr(p.rows),
            "[[<Label a-(0, 0),(0, 0){}>, <Spacer spacer-1-0-(1, 1),(0, 0)>, <Field b-(2, 2),(0, 0){}>]]")
        self.assertEqual(p.row_count, 1)
        self.assertEqual(p.column_count, 3)
        self.assertEqual(repr(p.row_stretchers), "[<0>]")
        self.assertEqual(repr(p.column_stretchers), "[<0>, <0>, <0>]")

    def test_case6(self):
        p = self.parse("""
lvalue:Value{r}|[.value]{l}
               |[.submit]
bottom:this is some button test{cb}|<1>
    <1>        |<1>
""")

        self.assertEqual(
            repr(p.rows),
            ("[[<Label lvalue-(0, 0),(0, 0){r}>, <Field value-(1, 1),(0, 0){l}>], "
             "[<Field submit-(1, 1),(1, 1){}>], [<Label bottom-(0, 1),(2, 2){cb}>]]"))

    def test_rowspan_error(self):
        layout = """
col1    |
    | " |
"""
        self.assertRaises(ValueError, self.parse, layout)


BUILD_CMP = "                  |      |[.header['udn']]|[.header['created']]|[.header['level']]|[.header['path']]|[.header['line']]|[.header['message']]\n-----\n[.show_additional]|[.rid]|[udn]           |[created]           |[level]           |[path]           |[line]           |[message]           \n[.additional]\n                  |      |                |                    |                  |                 |                 |<1>                 "


class BuildLayoutTest(unittest.TestCase):
    def test_build_rows(self):
        builder = tl.LayoutBuilder()
        columns = ["udn", "created", "level", "path", "line", "message"]
        title = builder.columns(
            "", "", ("[.header['{}']]".format(c) for c in columns))
        body = builder.columns("[.show_additional]",
                               "[.rid]", ("[{}]".format(c) for c in columns))

        index = columns.index("message") + 2
        stretchers = builder.columns()
        stretchers[index] = "<1>"
        table_ = title.join() + "\n-----\n" + body.join()
        table_ += "\n[.additional]"
        table_ += "\n" + stretchers.join()
        self.maxDiff = None
        self.assertEqual(BUILD_CMP, table_)
        self.assertEqual(len(builder), 8)


class MiscTest(unittest.TestCase):
    def test_walk_pointer(self):
        proxy = tl.walk_pointer(ra.Pointer(), "path[0].index['col']")
        cmp_ = "<Pointer-<class 'larch.reactive.pointer.NOTHING'>.path[0].index[col]>"
        self.assertEqual(cmp_, repr(proxy))

    def test_cellparse_error(self):
        self.assertRaises(ValueError, tl.Parser, "cell")

    def test_stretcher(self):
        self.assertFalse(tl.Stretcher())


TLAYOUT1 = """
fn:+First name{rm}|Last name|Email      |
-----
fb:+[first]{rm}   |[last]   |[email]    |[.show()]
[detail]
    <1>           |<1>      |           |
"""

TLAYOUT2 = """
Name         |type  | size  |
---
[icon]|[name]|[type]|[size]|
      |  "   |[.sec]|
"""

TLAYOUT3 = """
------
*|+name     |code |
----
 |[.count()]{r}   |
"""

TLAYOUT4 = """
[[0]]
"""


class TableLayoutTest(unittest.TestCase):
    def parse(self, layout):
        return table.TableParser(layout)

    def print_structure(self, parser):
        print()
        for section in ("header", "body", "footer"):
            print("Section", section)
            for row in getattr(parser, section):
                print(row)
            print()

    def test_layout1(self):
        parser = self.parse(TLAYOUT1)
        self.print_structure(parser)

    def test_layout2(self):
        parser = self.parse(TLAYOUT2)
        self.print_structure(parser)

    def test_layout3(self):
        parser = self.parse(TLAYOUT3)
        self.print_structure(parser)


if __name__ == "__main__":
    unittest.main()
