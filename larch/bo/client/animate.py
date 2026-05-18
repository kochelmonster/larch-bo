from .browser import loading_modules, executer, get_info, get_metrics

# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.update(["animejs"])
parseFloat = getComputedStyle = Date = console = document = loading_modules
def __pragma__(*args): pass
def __new__(*args): pass
# __pragma__("noskip")


__pragma__("ifdef", "noanimation")


class NoAnimator:
    def set_policy(self, policy_name):
        return self

    def change_style(self, element, style, value, transform=True):
        element.style[style] = value
        return self

    def show(self, element, visible):
        if visible:
            visible = visible if isinstance(visible, str) else "block"
            return self.change_style(element, "display", visible, False)
        else:
            return self.change_style(element, "display", "none")

    def replace(self, old_, new_):
        old_.remove()
        return self


animator = NoAnimator()

__pragma__("else")

anime = None

__pragma__('js', '{}', '''
loading_modules.push((async () => {
    anime = await import("animejs");
})());
''')


class Animator:
    """
    The Animation value where from some document about animations
    in material. (Unfortunatly I do not find it anymore)
    """

    EASE = "cubicBezier(.42,0,.58,1)"
    DEFAULT_POLICIES = {
        "mobile": {
            "style": {
                "ease": "cubicBezier(.42,0,.58,1)",
                "duration": 225,
            },
            "show": {
                "ease": "cubicBezier(.42,0,.58,1)",
                "duration": 225,
            },
            "hide": {
                "ease": "cubicBezier(.42,0,.58,1)",
                "duration": 195,
            },
            "replace": {
                "ease": "cubicBezier(.42,0,.58,1)",
                "duration": 225,
            },
            "style_curve": {
                "short": 225,
                "long": 300,
            },
        },
        "tablet": {
            "style": {
                "ease": "cubicBezier(.42,0,.58,1)",
                "duration": 292,
            },
            "show": {
                "ease": "cubicBezier(.42,0,.58,1)",
                "duration": 225,
            },
            "hide": {
                "ease": "cubicBezier(.42,0,.58,1)",
                "duration": 195,
            },
            "replace": {
                "ease": "cubicBezier(.42,0,.58,1)",
                "duration": 225,
            },
            "style_curve": {
                "short": 292,
                "long": 330,
            },
        },
        "default": {
            "style": {
                "ease": "cubicBezier(.42,0,.58,1)",
                "duration": 200,
            },
            "show": {
                "ease": "cubicBezier(.42,0,.58,1)",
                "duration": 200,
            },
            "hide": {
                "ease": "cubicBezier(.42,0,.58,1)",
                "duration": 150,
            },
            "replace": {
                "ease": "cubicBezier(.42,0,.58,1)",
                "duration": 2000,
            },
            "style_curve": {
                "short": 150,
                "long": 200,
            },
        },
    }

    def __init__(self):
        self.animated_elements = self.pending_ops = None
        info = get_info()
        if info["mobile"]:
            self.set_policy("mobile")
        elif info["tablet"]:
            self.set_policy("tablet")
        else:
            self.set_policy("default")

    def set_policy(self, policy_name):
        selected = self.DEFAULT_POLICIES.get(policy_name)
        if selected is None:
            selected = self.DEFAULT_POLICIES["default"]

        # __pragma__("jsiter")
        self.policy = {
            "style": selected["style"],
            "show": selected["show"],
            "hide": selected["hide"],
            "replace": selected["replace"],
        }
        # __pragma__("nojsiter")

        # from matrial
        short = selected["style_curve"]["short"]
        long = selected["style_curve"]["long"]
        a = (long-short) / 380
        t = short - a*120
        self.calc_animation_duration = lambda size: min(a*size + t, long)
        return self

    def _policy_for(self, op_kind):
        return self.policy[op_kind]

    def _add_op(self, op):
        if self.pending_ops is None:
            self.pending_ops = []
            executer.add(self.start_animation)
        self.pending_ops.append(op)
        return self

    def _queue_style(self, element, style, value, transform=True):
        # __pragma__("jsiter")
        return self._add_op({
            "type": "style",
            "element": element,
            "style": style,
            "value": value,
            "transform": transform,
        })
        # __pragma__("nojsiter")

    def _queue_show(self, element, visible):
        # __pragma__("jsiter")
        return self._add_op({
            "type": "show",
            "element": element,
            "visible": visible,
        })
        # __pragma__("nojsiter")

    def _queue_hide(self, element):
        # __pragma__("jsiter")
        return self._add_op({
            "type": "hide",
            "element": element,
        })
        # __pragma__("nojsiter")

    def _queue_replace(self, old_, new_):
        # __pragma__("jsiter")
        return self._add_op({
            "type": "replace",
            "old": old_,
            "new": new_,
        })
        # __pragma__("nojsiter")

    def change_style(self, element, style, value, transform=True):
        """
        Change a css style property of element, and initiate the corresponding animation.

        Args:
            element (dom element): the element to manipulate
            style (str): the css style name (e.g. "display")
            value (str): the style value
            transform (bool): If True the style will be set to the old value at
                              the beginning of the transformation and set to value at the end.
        """
        if self.animated_elements is not None:
            element.style[style] = value
            return self

        return self._queue_style(element, style, value, transform)

    def show(self, element, visible):
        """
        Shows or hides a element.
        Args:
            element(dom element): the element to manipulate.
            visible (bool/str): if visible is False sets the display style of element to "none".
        """
        if self.animated_elements is not None:
            if visible:
                visible = visible if isinstance(visible, str) else "block"
                element.style.display = visible
                element.style.opacity = ""
            else:
                element.style.display = "none"
                element.style.opacity = ""
            return self

        if visible:
            visible = visible if isinstance(visible, str) else "block"
            return self._queue_show(element, visible)
        else:
            return self._queue_hide(element)

    def replace(self, old_, new_):
        """
        Replaces an old element by a new element, and initiates the corresponding animation.
        Args:
            new_ (dom element): The new element that will appear.
            old_ (dom element): The old Element that will be removed.
        """
        if self.animated_elements is not None:
            old_.remove()
            return self

        return self._queue_replace(old_, new_)

    def _append_animation(self, animations, element, style_id, before, after, op_kind, duration=None):
        if before == after or "auto" in before or "auto" in after:
            return
        policy = self._policy_for(op_kind)
        # __pragma__("jsiter")
        item = {
            "element": element,
            "style": style_id,
            "before": before,
            "after": after,
            "duration": policy["duration"] if duration is None else duration,
            "ease": policy["ease"],
        }
        # __pragma__("nojsiter")
        animations.append(item)

    def _make_show(self, op, animations, finalize):
        element = op["element"]
        visible = op["visible"]
        before_display = getComputedStyle(element).display
        if before_display != "none":
            # already visible
            element.style.display = visible
            element.style.opacity = ""
            return

        element.style.display = visible
        self._append_animation(animations, element, "opacity", "0", "1", "show")
        element.style.opacity = "0"
        finalize.append(lambda: _finalize_visible(element, visible))

    def _make_hide(self, op, animations, finalize):
        element = op["element"]
        before_display = getComputedStyle(element).display
        if before_display == "none":
            element.style.display = "none"
            element.style.opacity = ""
            return

        before_opacity = getComputedStyle(element).opacity
        self._append_animation(animations, element, "opacity", before_opacity, "0", "hide")
        finalize.append(lambda: _finalize_hidden(element))

    def _make_replace(self, op, animations, finalize):
        old_ = op["old"]
        new_ = op["new"]
        if old_.parentElement is None:
            return

        self._append_animation(animations, new_, "opacity", "0", "1", "replace")
        old_opacity = getComputedStyle(old_).opacity
        self._append_animation(animations, old_, "opacity", old_opacity, "0", "hide")
        new_.style.opacity = "0"
        finalize.append(lambda: _finalize_replace(old_, new_))

    def _make_style(self, op, animations, finalize):
        element = op["element"]
        style_id = op["style"]
        value = op["value"]
        transform = op["transform"]

        if style_id == "display":
            element.style.display = value
            return

        before = getComputedStyle(element)[style_id]
        element.style[style_id] = value
        after = getComputedStyle(element)[style_id]

        if before == after or not transform:
            return

        policy = self._policy_for("style")
        duration = policy["duration"]
        delta_size = calc_animation_size(before, after)
        if delta_size:
            dp_size = delta_size * 2.22 / get_metrics().pt_height
            duration = self.calc_animation_duration(dp_size)

        self._append_animation(animations, element, style_id, before, after, "style", duration)
        element.style[style_id] = before
        finalize.append(lambda: _finalize_style(element, style_id, value))

    def start_animation(self):
        ops = self.pending_ops
        if ops is None:
            return
        self.pending_ops = None

        animations = []
        finalize = []

        for op in ops:
            op_type = op["type"]
            if op_type == "show":
                self._make_show(op, animations, finalize)
            elif op_type == "hide":
                self._make_hide(op, animations, finalize)
            elif op_type == "replace":
                self._make_replace(op, animations, finalize)
            else:
                self._make_style(op, animations, finalize)

        if not len(animations):
            for fn in finalize:
                fn()
            self.animated_elements = None
            return

        if anime is None:
            for props in animations:
                props["element"].style[props["style"]] = props["after"]
            for fn in finalize:
                fn()
            self.animated_elements = None
            return

        self.animated_elements = animations

        # __pragma__("jsiter")
        timeline = anime.createTimeline({"defaults": {"ease": self.EASE}})
        # __pragma__("nojsiter")
        for props in animations:
            # __pragma__("jsiter")
            args = {}
            args[props["style"]] = [props["before"], props["after"]]
            args["duration"] = props["duration"]
            args["ease"] = props["ease"]
            # __pragma__("nojsiter")
            timeline.add(props["element"], args, 0)
            props["element"].style[props["style"]] = props["before"]

        timeline.then(lambda *_: self._transition_end(finalize))

    def _transition_end(self, finalize):
        for fn in finalize:
            fn()
        for props in self.animated_elements:
            props["element"].style[props["style"]] = props["after"]
        self.animated_elements = None


def _finalize_visible(element, visible):
    element.style.display = visible
    element.style.opacity = ""


def _finalize_hidden(element):
    element.style.display = "none"
    element.style.opacity = ""


def _finalize_replace(old_, new_):
    new_.style.opacity = ""
    if old_.parentElement is not None:
        old_.remove()


def _finalize_style(element, style_id, value):
    element.style[style_id] = value


def calc_animation_size(before, after):
    delta = 0
    if "px" in before:
        for b, a in zip(before.split(" "), after.split(" ")):
            delta = max(abs(parseFloat(b) - parseFloat(a)), delta)
    return delta


animator = Animator()

__pragma__("endif")
