"""Playwright-based test harness for larch.bo browser tests."""
import os
import unittest
import logging
from playwright.sync_api import sync_playwright

logger = logging.getLogger('larch.bo.server.test')

HEADLESS = os.environ.get("HEADLESS", "true").lower() != "false"


class _Driver:
    """Manages the Playwright lifecycle."""

    def __init__(self):
        self._pw = None
        self._browser = None

    def start(self):
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=HEADLESS)

    @property
    def browser(self):
        if self._browser is None:
            self.start()
        return self._browser

    def shutdown(self):
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._pw:
            self._pw.stop()
            self._pw = None


driver = _Driver()


class PlaywrightBase(unittest.TestCase):
    """Base class for browser tests.

    ``application`` and ``config`` are set by ``run_tests()`` in start.py
    before the test suite runs.
    """

    application = None
    config = None
    server = None

    @classmethod
    def setUpClass(cls):
        address = cls.config.get("address", ("", 0))
        host = address[0] or "127.0.0.1"
        port = address[1]
        cls.base_url = f"http://{host}:{port}/"
        cls.browser = driver.browser
        logger.info("test base url: %s", cls.base_url)

    def setUp(self):
        self.page = self.browser.new_page()
        self.page.goto(self.base_url)
        self.page.locator(".lbo-table section").first.wait_for(timeout=30000)

    def tearDown(self):
        if self.page:
            self.page.close()
            self.page = None

    # -- helpers -----------------------------------------------------------

    def table_eval(self, expr):
        """Evaluate an expression on the Table JS instance.

        Usage::

            self.table_eval("row_count")
            self.table_eval("is_virtual()")
            self.table_eval("first_row")
        """
        return self.page.evaluate(
            f"() => document.querySelector('.lbo-table').table.{expr}")

    def wait_for_render(self, prev_first_row=None, timeout=5000):
        """Wait for the table to re-render after a scroll action.

        If *prev_first_row* is given, waits until ``first_row`` differs.
        Otherwise waits one ``requestAnimationFrame`` + microtask.
        """
        if prev_first_row is not None:
            self.page.wait_for_function(
                f"() => document.querySelector('.lbo-table').table.first_row != {prev_first_row}",
                timeout=timeout)
        else:
            self.page.evaluate("() => new Promise(r => requestAnimationFrame(() => setTimeout(r, 50)))")

    def scroll_wheel(self, delta_y):
        """Send a mouse wheel event to the table and wait for render."""
        prev = self.table_eval("first_row")
        box = self.page.locator(".lbo-table").bounding_box()
        self.page.mouse.move(box["x"] + box["width"] / 2,
                             box["y"] + box["height"] / 2)
        self.page.mouse.wheel(0, delta_y)
        self.wait_for_render(prev)

    def scroll_to_fraction(self, fraction):
        """Jump the decoupled scrollbar to a fraction (0..1) of scroll range."""
        prev = self.table_eval("first_row")
        self.page.evaluate(
            f"""() => {{
                let sb = document.querySelector('.lbo-scrollbar-area');
                sb.scrollTop = sb.scrollHeight * {fraction};
            }}""")
        self.wait_for_render(prev)

    def install_recorder(self):
        """Install recordwright on the current page (optional)."""
        from recordwright import install as install_recorder
        return install_recorder(self.page,
                                path=self.config.get("recording_path", "."))
