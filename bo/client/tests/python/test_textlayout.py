import unittest
import larch.reactive as ra
import larch.bo.client.textlayout as tl
import larch.bo.client.grid as grid


class LayoutTest(unittest.TestCase):
    def parse(self, layout):
        return grid.GridParser(layout)

    def test_string_modifiers(self):
        layout = tl.js(css="width:10em") | "[cell]"
        self.assertEqual(layout, "[cell]")
        self.assertEqual(layout.modifiers, {'js': {'css': 'width:10em'}})

    def test_case1(self):
        p = self.parse("""a|(10,1)|[b]""")
        self.assertEqual(repr(
            p.rows), "[[<Label-(0, 0),(0, 0){}>, <Spacer-(1, 1),(0, 0)>, <Field-(2, 2),(0, 0){}>]]")
        self.assertEqual(p.row_count, 1)
        self.assertEqual(p.column_count, 3)
        self.assertEqual(p.row_stretchers, [])
        self.assertEqual(p.column_stretchers, [])

    def test_case2(self):
        p = self.parse("""
a  |(10,1)|[b]
[c]|      |[d]|<1>
   |  <1> |
""")
        self.assertEqual(repr(
            p.rows), "[[<Label-(0, 0),(0, 0){}>, <Spacer-(1, 1),(0, 0)>, <Field-(2, 2),(0, 0){}>], [<Field-(0, 0),(1, 1){}>, <Empty-(1, 1),(1, 1)>, <Field-(2, 2),(1, 1){}>]]")
        self.assertEqual(p.row_count, 2)
        self.assertEqual(p.column_count, 3)
        self.assertEqual(p.row_stretchers, (0, 1.0))
        self.assertEqual(p.column_stretchers, (0, 1.0, 0))

    def test_case3(self):
        p = self.parse("""
a  |(10,1)|[b]
[c]|      | "     |<1>
 " |      |[d]|[e]
   |  <1> |   |<1>|
""")
        self.assertEqual(repr(
            p.rows), "[[<Label-(0, 0),(0, 0){}>, <Spacer-(1, 1),(0, 0)>, <Field-(2, 3),(0, 1){}>], [<Field-(0, 0),(1, 2){}>, <Empty-(1, 1),(1, 1)>], [<Empty-(1, 1),(2, 2)>, <Field-(2, 2),(2, 2){}>, <Field-(3, 3),(2, 2){}>]]")
        self.assertEqual(p.row_count, 3)
        self.assertEqual(p.column_count, 4)
        self.assertEqual(p.row_stretchers, (0, 1.0, 0))
        self.assertEqual(p.column_stretchers, (0, 1.0, 0, 1.0))

    def test_case4(self):
        p = self.parse("""
ad:[active_displays[0]]{cm}|<1>
<1>
""")
        self.assertEqual(repr(p.rows), "[[<Field ad-(0, 0),(0, 0){cm}>]]")
        self.assertEqual(p.rows[0][0].path, "active_displays[0]")
        self.assertEqual(p.row_count, 1)
        self.assertEqual(p.column_count, 1)
        self.assertEqual(p.row_stretchers, [1.0])
        self.assertEqual(p.column_stretchers, [1.0])

    def test_case5(self):
        p = self.parse("""a:a|(10,1)|b:[b]""")
        self.assertEqual(repr(
            p.rows), "[[<Label a-((0, 0),(0, 0)){}>, <Spacer-(1, 1),(0, 0)>, <Field b-((2, 2),(0, 0)){}>]]")
        self.assertEqual(p.row_count, 1)
        self.assertEqual(p.column_count, 3)
        self.assertEqual(p.row_stretchers, [])
        self.assertEqual(p.column_stretchers, [])

    def test_case6(self):
        p = self.parse("""
lvalue:Value{r}|[.value]{l}
               |[.submit]
bottom:this is some button test{cb}|<1>
    <1>        |<1>
""")

        print()
        print(repr(p.rows))

    def test_rowspan_error(self):
        layout = """
col1    |
    | " |
"""
        self.assertRaises(ValueError, self.parse, layout)

    def test_splitter1(self):
        p = self.parse("""
[a] |[c]|<1M>
[b] |[d]|<1>
<1M>|<1M>
""")
        self.assertEqual(p.row_splitters, [])
        self.assertEqual(p.column_splitters, [1])

    def test_splitter2(self):
        p = self.parse("""
[a]|<1>
[b]|<1M>
[c]|<1M>
[d]|<1M>
""")
        self.assertEqual(p.row_splitters, [2, 3])
        self.assertEqual(p.column_splitters, [])


class TableTest:  # (unittest.TestCase):
    def parse(self, layout):
        return table.Parser(layout)

    def test_case1(self):
        p = self.parse("""
col1  ||header{lm}       ||
      ||cols2     |col3  ||
---------------------------------
[col1]||[col2]    |[col3]||[col4]
      ||[body]           ||
--------------------------------
      ||[.sum]           ||
      ||<1>       |      ||
""")

        cmp_ = {
            'cb': "[<Content-(1, 2),(0, 0)-.sum>]",
            'cm': "[<Content-(1, 1),(0, 0)-col2>, <Content-(2, 2),(0, 0)-col3>, <Content-(1, 2),(1, 1)-body>]",
            'ct': "[<Label-(1, 2),0{lm}>, <Label-(1, 1),1{}>, <Label-(2, 2),1{}>]",
            'lb': "[<Empty-(0, 0),(0, 0)>]",
            'lm': "[<Content-(0, 0),(0, 0)-col1>, <Empty-(0, 0),(1, 1)>]",
            'lt': "[<Label-(0, 0),0{}>, <Empty-(0, 0),(1, 1)>]",
            'rb': "[<Empty-(3, 3),(0, 0)>]",
            'rm': "[<Content-(3, 3),(0, 0)-col4>, <Empty-(3, 3),(1, 1)>]",
            'rt': "[<Empty-(3, 3),(0, 0)>, <Empty-(3, 3),(1, 1)>]"}

        for key, repr_ in p.sections.items():
            self.assertEqual(repr(repr_), cmp_[key])

        self.assertEqual(p.column_count, {'c': 2, 'r': 1, 'l': 1})
        self.assertEqual(p.column_stretchers, (0, 1.0, 0, 0))

    def test_case2(self):
        p = self.parse("""
         | Company
--------------------
[.rid]{t}|+[name]{m}
         | <1>
""")

        cmp_ = {
            'cb': "[]",
            'cm': "[<Content-(0, 0),(0, 0)-.rid>, <Content-(1, 1),(0, 0)-name>]",
            'ct': "[<Empty-(0, 0),(0, 0)>, <Label-(1, 1),0{}>]",
            'lb': "[]",
            'lm': "[]",
            'lt': "[]",
            'rb': "[]",
            'rm': "[]",
            'rt': "[]"}

        for key, repr_ in p.sections.items():
            self.assertEqual(repr(repr_), cmp_[key])

        self.assertEqual(p.column_count, {'c': 2, 'r': 0, 'l': 0})
        self.assertEqual(p.column_stretchers, (0, 1.0))


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
        table = title.join() + "\n-----\n" + body.join()
        table += "\n[.additional]"
        table += "\n" + stretchers.join()

        cmp_ = "                  |      |[.header['udn']]|[.header['created']]|[.header['level']]|[.header['path']]|[.header['line']]|[.header['message']]\n-----\n[.show_additional]|[.rid]|[udn]           |[created]           |[level]           |[path]           |[line]           |[message]           \n[.additional]\n                  |      |                |                    |                  |                 |                 |<1>                 "
        self.assertEqual(cmp_, table)
        self.assertEqual(len(builder), 8)


class MiscTest(unittest.TestCase):
    def test_walk_pointer(self):
        proxy = tl.walk_pointer(ra.Pointer(), "path[0].index['col']")
        cmp_ = "<Pointer-<class 'larch.reactive.pointer.NOTHING'>.path[0].index['col']>"
        self.assertEqual(cmp_, repr(proxy))

    def test_cellparse_error(self):
        self.assertRaises(ValueError, tl.Parser, "cell")

    def test_stretcher(self):
        self.assertFalse(tl.Stretcher())


if __name__ == "__main__":
    unittest.main()
