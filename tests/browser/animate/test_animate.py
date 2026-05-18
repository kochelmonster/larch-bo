import unittest
from larch.bo.server.test import PlaywrightBase


class TestAnimatorStandalone(PlaywrightBase):
    """Standalone browser tests for Animator behavior."""

    def setUp(self):
        self.page = self.browser.new_page()
        self.page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}", flush=True))
        self.page.goto(self.base_url, wait_until="networkidle")

    def tearDown(self):
        if self.page:
            self.page.close()
            self.page = None  # type: ignore[assignment]

    def test_show_hide(self):
        self.page.locator("#animator-show-target").wait_for(
            state="attached", timeout=30000)

        self.page.evaluate("""() => { window.animator_test.toggle_show(); }""")

        self.page.wait_for_function(
            """() => getComputedStyle(document.querySelector('#animator-show-target')).display !== 'none'""",
            timeout=10000,
        )

        self.page.evaluate("""() => { window.animator_test.toggle_show(); }""")

        self.page.wait_for_function(
            """() => getComputedStyle(document.querySelector('#animator-show-target')).display === 'none'""",
            timeout=10000,
        )

    def test_replace(self):
        self.page.evaluate("""() => { window.animator_test.replace(); }""")
        self.page.wait_for_function(
            """() => {
                const node = document.querySelector('#animator-replace-target');
                return !!node && !!node.querySelector('vaadin-number-field');
            }""",
            timeout=10000,
        )

    def test_rotate(self):
        self.page.evaluate("""() => { window.animator_test.rotate(); }""")
        self.page.wait_for_function(
            """() => {
                const node = document.querySelector('#animator-rotate-target');
                return !!node && node.textContent.includes('rotate: 90');
            }""",
            timeout=10000,
        )

if __name__ == "__main__":
    unittest.main()
