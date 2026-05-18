from larch.reactive import Cell
from larch.bo.client.browser import start_main
from larch.bo.client.animate import animator
from larch.bo.client.command import label
from larch.bo.client.grid import Grid
from larch.bo.client.session import Session
from larch.bo.client.wc.vaadin.vinput import register as input_register
from larch.bo.client.wc.vaadin.vbutton import register as button_register



# __pragma__("skip")
window = document = animator

def __pragma__(*args):
    pass
# __pragma__("noskip")


input_register()
button_register()

class AnimatorGrid(Grid):
    layout = """
replace_target:|[.replace_value]     |[.replace]
show_target:   |[.show_value]@text   |[.toggle_show]
rotate_target: |[.rotate_value]@text |[.rotate]
    (0,100px)  |                     |
"""

    replace_value = Cell("replace")
    show_value = Cell("visible")
    rotate_value = Cell("rotate: 0")

    def __init__(self, cv=None):
        super().__init__(cv)
        self._replace_count = 0
        self._visible = False
        self._angle = 0

    def modify_controls(self):
        self.container("replace_value").id = "animator-replace-target"
        self.container("show_value").id = "animator-show-target"
        rotate_target = self.container("rotate_value")
        rotate_target.id = "animator-rotate-target"
        rotate_target.style.display = "inline-block"
        rotate_target.style.transformOrigin = "center center"

    @label("Replace")
    def replace(self):
        if isinstance(self.replace_value, str):
            self.replace_value = 10
        else:
            self.replace_value = "replace"

    @label("Hide")
    def toggle_show(self):
        if self.show_value == "visible":
            self.show_value = "hidden"
            self.contexts["toggle_show"].set("label", "Show")
            animator.show(self.container("show_value"), False)
        else:
            self.show_value = "visible"
            self.contexts["toggle_show"].set("label", "Hide")
            animator.show(self.container("show_value"), True)

    @label("Rotate")
    def rotate(self):
        self._angle = (self._angle + 90) % 360
        self.rotate_value = f"rotate: {self._angle}"
        animator.change_style(
            self.container("rotate_value"),
            "transform",
            f"rotate({self._angle}deg)")


def main():
    session = Session(AnimatorGrid()).boot()
    grid = session.root

    # __pragma__("jsiter")
    window.animator_test = {
        "toggle_show": grid.toggle_show,
        "replace": grid.replace,
        "rotate": grid.rotate,
    }
    # __pragma__("nojsiter")


start_main(main)
