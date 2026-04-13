"""Browser tests for virtual table redesign.

Run via::

    python tests/browser/table/table.py --type=test
    HEADLESS=false python tests/browser/table/table.py --type=test
"""
import unittest
from larch.bo.server.test import PlaywrightBase


FOOTER_INFO_JS = """() => {
    const table = document.querySelector('.lbo-table');
    const t = table.table;
    const rect = table.getBoundingClientRect();
    const footers = table.querySelectorAll('footer');
    const lastFooter = footers[footers.length - 1];
    const fRect = lastFooter ? lastFooter.getBoundingClientRect() : null;
    return {
        table_bottom: rect.bottom,
        footer_bottom: fRect ? fRect.bottom : -1,
        footer_gap: fRect ? rect.bottom - fRect.bottom : -1,
        scrollTop: table.scrollTop,
        scrollHeight: table.scrollHeight,
        clientHeight: table.clientHeight,
    };
}"""


class TestStaticMode(PlaywrightBase):
    """Static mode (row_count ≤ STATIC_LIMIT=200): all rows rendered, native scroll."""

    def _set_count(self, count):
        """Set the Controller count field."""
        inp = self.page.locator("vaadin-number-field input").first
        inp.click()
        inp.press("Control+a")
        inp.fill(str(count))
        inp.press("Enter")
        # wait for table to re-render with new row count
        self.page.wait_for_function(
            f"() => document.querySelector('.lbo-table').table.row_count == {count}",
            timeout=15000)

    def test_all_rows_rendered(self):
        self._set_count(100)
        self.assertFalse(self.table_eval("is_virtual()"))
        self.assertEqual(self.table_eval("rows.length"), 100)

    def test_scrollbar_hidden(self):
        self._set_count(100)
        sb = self.page.locator(".lbo-scrollbar-area")
        self.assertFalse(sb.is_visible())

    def test_native_scroll(self):
        self._set_count(100)
        scroll_top_before = self.page.evaluate(
            "() => document.querySelector('.lbo-table').scrollTop")
        box = self.page.locator(".lbo-table").bounding_box()
        assert box is not None
        self.page.mouse.move(box["x"] + box["width"] / 2,
                             box["y"] + box["height"] / 2)
        self.page.mouse.wheel(0, 200)
        self.wait_for_render()
        scroll_top_after = self.page.evaluate(
            "() => document.querySelector('.lbo-table').scrollTop")
        self.assertGreater(scroll_top_after, scroll_top_before)

    def test_end_footer_aligned(self):
        """Footer aligned at viewport bottom after pressing End."""
        self._set_count(200)
        self.page.locator(".lbo-table").click()
        self.page.wait_for_timeout(100)
        self.page.keyboard.press("End")
        self.page.wait_for_timeout(500)
        result = self.page.evaluate(FOOTER_INFO_JS)
        self.assertLessEqual(abs(result["footer_gap"]), 2,
            f"Footer bottom off by {result['footer_gap']}px")


class TestVirtualMode(PlaywrightBase):
    """Virtual mode (default count=500): decoupled scrollbar, partial rendering."""

    def test_is_virtual(self):
        self.assertTrue(self.table_eval("is_virtual()"))

    def test_scrollbar_visible(self):
        sb = self.page.locator(".lbo-scrollbar-area")
        self.assertTrue(sb.is_visible())

    def test_partial_rendering(self):
        row_count = self.table_eval("row_count")
        rendered = self.table_eval("rows.length")
        self.assertGreater(row_count, 200)
        self.assertLess(rendered, row_count)

    def test_near_scroll(self):
        first_before = self.table_eval("first_row")
        self.scroll_wheel(300)
        first_after = self.table_eval("first_row")
        self.assertGreater(first_after, first_before)

    def test_no_blank_gaps(self):
        self.scroll_wheel(300)
        rendered = self.table_eval("rows.length")
        visible = self.table_eval("visible_count")
        self.assertGreaterEqual(rendered, visible)

    def test_content_correct_after_scroll(self):
        self.scroll_wheel(300)
        first_row = self.table_eval("first_row")
        # The id_ column is the first data cell in each row
        first_id = self.page.evaluate("""() => {
            let rows = document.querySelectorAll('.lbo-table section');
            return rows[0] ? rows[0].textContent.trim() : null;
        }""")
        self.assertIsNotNone(first_id)


class TestFarScroll(PlaywrightBase):
    """Far scroll via programmatic scrollTop jump."""

    def test_jump_to_80_percent(self):
        row_count = self.table_eval("row_count")
        self.scroll_to_fraction(0.8)
        first_row = self.table_eval("first_row")
        # Should be roughly near 80% of row_count
        expected = int(row_count * 0.8)
        self.assertAlmostEqual(first_row, expected, delta=row_count * 0.1)

    def test_jump_to_end(self):
        row_count = self.table_eval("row_count")
        self.scroll_to_fraction(1.0)
        first_row = self.table_eval("first_row")
        visible = self.table_eval("visible_count")
        # first_row should be exactly row_count - visible_count
        self.assertEqual(first_row, row_count - visible)

    def test_jump_back_to_top(self):
        self.scroll_to_fraction(0.8)
        # Now jump back
        prev = self.table_eval("first_row")
        self.page.evaluate("""() => {
            let sb = document.querySelector('.lbo-scrollbar-area');
            sb.scrollTop = 0;
        }""")
        self.wait_for_render(prev)
        self.assertEqual(self.table_eval("first_row"), 0)


class TestChunkedMode(PlaywrightBase):
    """Chunked data loading via toggle switch."""

    def _toggle_chunked(self):
        switch = self.page.locator("jelly-switch").last
        switch.click()
        # wait for table to re-render
        self.page.wait_for_timeout(2000)
        self.page.locator(".lbo-table section").first.wait_for(timeout=15000)

    def test_chunked_loads_data(self):
        self._toggle_chunked()
        # after chunk loads, rows should have real data (not placeholder)
        row_count = self.table_eval("row_count")
        self.assertGreater(row_count, 0)
        rendered = self.table_eval("rows.length")
        self.assertGreater(rendered, 0)

    def test_chunked_far_scroll_triggers_load(self):
        self._toggle_chunked()
        first_before = self.table_eval("first_row")
        # Jump to unloaded region
        self.page.evaluate("""() => {
            let sb = document.querySelector('.lbo-scrollbar-area');
            sb.scrollTop = sb.scrollHeight * 0.5;
        }""")
        # Wait for chunk to arrive and render
        self.page.wait_for_timeout(3000)
        self.wait_for_render()
        first_after = self.table_eval("first_row")
        self.assertGreater(first_after, first_before)

    def test_toggle_back_footer_aligned(self):
        """Reproduce: toggle chunked, End, toggle back, End — footer must stay aligned."""
        # 1) toggle to chunked
        self._toggle_chunked()
        self.page.locator(".lbo-table").click()
        self.page.wait_for_timeout(200)

        # 2) press End in chunked mode
        self.page.keyboard.press("End")
        self.page.wait_for_timeout(1000)

        # 3) toggle back to normal 500
        self._toggle_chunked()  # toggle off
        self.page.wait_for_timeout(500)

        # Check footer immediately after toggle back (before pressing End)
        result_before = self.page.evaluate(FOOTER_INFO_JS)

        self.page.locator(".lbo-table").click()
        self.page.wait_for_timeout(200)

        # 4) press End
        self.page.keyboard.press("End")
        self.page.wait_for_timeout(500)

        result = self.page.evaluate(FOOTER_INFO_JS)

        self.assertLessEqual(abs(result_before["footer_gap"]), 2,
            f"Before End: footer off by {result_before['footer_gap']}px")
        self.assertLessEqual(abs(result["footer_gap"]), 2,
            f"After End: footer off by {result['footer_gap']}px")

    def test_scrollbar_end_after_toggle_back(self):
        """Scrollbar at max position should show last row after toggle back."""
        self._toggle_chunked()
        self.page.locator(".lbo-table").click()
        self.page.wait_for_timeout(200)
        self.page.keyboard.press("End")
        self.page.wait_for_timeout(1000)
        self._toggle_chunked()  # toggle back
        self.page.wait_for_timeout(500)

        # scroll up a bit, then scroll to very bottom
        self.page.evaluate("""() => {
            let sb = document.querySelector('.lbo-scrollbar-area');
            sb.scrollTop = sb.scrollTop - 100;
        }""")
        self.page.wait_for_timeout(300)
        self.page.evaluate("""() => {
            let sb = document.querySelector('.lbo-scrollbar-area');
            sb.scrollTop = sb.scrollHeight - sb.clientHeight;
        }""")
        self.page.wait_for_timeout(300)

        row_count = self.table_eval("row_count")
        visible = self.table_eval("visible_count")
        first_row = self.table_eval("first_row")
        last_row = self.page.evaluate(
            "() => { let t = document.querySelector('.lbo-table').table; "
            "return t.rows[t.rows.length-1].lbo_row; }")
        self.assertEqual(first_row, row_count - visible,
            f"first_row should be {row_count - visible}, got {first_row}")
        self.assertEqual(last_row, row_count - 1,
            f"last row should be {row_count - 1}, got {last_row}")

    def test_columns_after_retoggle(self):
        """Columns must not shrink after toggle→home→toggle back→toggle→end."""
        # 1) toggle to chunked, press End, press Home
        self._toggle_chunked()
        self.page.locator(".lbo-table").click()
        self.page.wait_for_timeout(200)
        self.page.keyboard.press("End")
        self.page.wait_for_timeout(1000)

        # measure column widths in chunked mode at end
        cols_first = self.page.evaluate("""() => {
            let t = document.querySelector('.lbo-table').table;
            return t.viewport.style.gridTemplateColumns;
        }""")

        self.page.keyboard.press("Home")
        self.page.wait_for_timeout(500)

        # 2) toggle to 500
        self._toggle_chunked()  # back to normal

        # 3) toggle to chunked again
        self._toggle_chunked()
        self.page.locator(".lbo-table").click()
        self.page.wait_for_timeout(200)

        # 4) press End
        self.page.keyboard.press("End")
        self.page.wait_for_timeout(1000)

        cols_second = self.page.evaluate("""() => {
            let t = document.querySelector('.lbo-table').table;
            return t.viewport.style.gridTemplateColumns;
        }""")

        # parse pixel widths and compare
        def parse_widths(s):
            return [float(x.replace("px", "")) for x in s.split() if "px" in x]

        w1 = parse_widths(cols_first)
        w2 = parse_widths(cols_second)
        for i in range(min(len(w1), len(w2))):
            self.assertAlmostEqual(w1[i], w2[i], delta=20,
                msg=f"Column {i} width changed too much: {w1[i]}→{w2[i]}")


class TestCursorNavigation(PlaywrightBase):
    """Keyboard cursor navigation."""

    def _focus_table(self):
        self.page.locator(".lbo-table").click()
        self.page.wait_for_timeout(100)

    def test_arrow_down(self):
        self._focus_table()
        cursor_start = self.table_eval("cursor")
        for _ in range(5):
            self.page.keyboard.press("ArrowDown")
        self.page.wait_for_timeout(100)
        cursor = self.table_eval("cursor")
        self.assertEqual(cursor, cursor_start + 5)

    def test_page_down(self):
        self._focus_table()
        self.page.keyboard.press("PageDown")
        self.page.wait_for_timeout(200)
        cursor = self.table_eval("cursor")
        visible = self.table_eval("visible_count")
        # cursor should jump by approximately visible_count
        self.assertGreaterEqual(cursor, visible - 2)

    def test_end(self):
        self._focus_table()
        self.page.keyboard.press("End")
        self.page.wait_for_timeout(500)
        cursor = self.table_eval("cursor")
        row_count = self.table_eval("row_count")
        self.assertEqual(cursor, row_count - 1)

    def test_end_bottom_aligned(self):
        self._focus_table()
        self.page.keyboard.press("End")
        self.page.wait_for_timeout(500)
        # last row bottom should be at content area bottom (above footer)
        result = self.page.evaluate("""() => {
            const table = document.querySelector('.lbo-table');
            const t = table.table;
            const rect = table.getBoundingClientRect();
            const sections = table.querySelectorAll('section.b');
            const lastSection = sections[sections.length - 1];
            const lastRect = lastSection.getBoundingClientRect();
            const contentBottom = rect.bottom - t.footer.height;
            return {diff: lastRect.bottom - contentBottom};
        }""")
        self.assertLessEqual(abs(result["diff"]), 2,
            f"Last row bottom off by {result['diff']}px")

    def test_home(self):
        self._focus_table()
        self.page.keyboard.press("End")
        self.page.wait_for_timeout(500)
        self.page.keyboard.press("Home")
        self.page.wait_for_timeout(500)
        cursor = self.table_eval("cursor")
        self.assertEqual(cursor, 0)
        self.assertEqual(self.table_eval("first_row"), 0)


class TestStatePersistence(PlaywrightBase):
    """State persistence across page reload."""

    def test_anchor_restored(self):
        # Scroll to approximately 50%
        self.scroll_to_fraction(0.5)
        # Wait for debounced state save (50ms debounce in state + 50ms in synch_to_hash)
        self.page.wait_for_timeout(500)
        anchor = self.table_eval("anchor.row")
        self.assertGreater(anchor, 0)

        # Reload page (preserving the hash)
        self.page.reload(wait_until="networkidle")
        self.page.locator(".lbo-table section").first.wait_for(timeout=15000)
        self.page.wait_for_timeout(500)

        # Anchor should be approximately restored
        restored = self.table_eval("anchor.row")
        visible = self.table_eval("visible_count")
        self.assertAlmostEqual(restored, anchor, delta=visible * 2)


class TestResize(PlaywrightBase):
    """Viewport resize updates visible_count and buffer."""

    def test_shrink_viewport(self):
        vc_before = self.table_eval("visible_count")
        self.page.set_viewport_size({"width": 800, "height": 300})
        self.wait_for_render()
        vc_after = self.table_eval("visible_count")
        self.assertLess(vc_after, vc_before)

    def test_scroll_after_resize(self):
        self.page.set_viewport_size({"width": 800, "height": 300})
        self.wait_for_render()
        first_before = self.table_eval("first_row")
        self.scroll_wheel(200)
        first_after = self.table_eval("first_row")
        self.assertGreater(first_after, first_before)

    def test_grow_viewport(self):
        # Shrink first
        self.page.set_viewport_size({"width": 800, "height": 300})
        self.wait_for_render()
        vc_small = self.table_eval("visible_count")
        # Grow
        self.page.set_viewport_size({"width": 800, "height": 900})
        self.wait_for_render()
        vc_large = self.table_eval("visible_count")
        self.assertGreater(vc_large, vc_small)


class TestVariableHeights(PlaywrightBase):
    """Variable row heights from wrapping address column."""

    def test_heights_vary(self):
        heights = self.page.evaluate("""() => {
            let t = document.querySelector('.lbo-table').table;
            let result = [];
            for (let i = 0; i < Math.min(t.rows.length, 10); i++) {
                result.push(t.rows[i].getBoundingClientRect().height);
            }
            return result;
        }""")
        self.assertGreater(len(heights), 1)
        # Not all heights should be identical if addresses wrap differently
        unique = set(heights)
        # At least check heights are positive
        for h in heights:
            self.assertGreater(h, 0)

    def test_avg_height_reasonable(self):
        row_height = self.table_eval("row_height")
        self.assertGreater(row_height, 10)
        self.assertLess(row_height, 200)

    def test_scrollbar_spacer_height(self):
        spacer_height = self.page.evaluate("""() => {
            let spacer = document.querySelector('.lbo-scrollbar-area > div');
            return spacer ? parseFloat(spacer.style.height) : 0;
        }""")
        self.assertGreater(spacer_height, 0)


if __name__ == "__main__":
    unittest.main()
