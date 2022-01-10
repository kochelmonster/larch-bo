from .browser import loading_modules, executer, get_info, get_metrics

# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.update(["animejs"])
parseFloat = getComputedStyle = Date = console = document = loading_modules
def __pragma__(*args): pass
def __new__(*args): pass
# __pragma__("noskip")


anime = None


__pragma__('js', '{}', '''
loading_modules.push((async () => {
    anime = await import("animejs/lib/anime.es.js");
})());
''')


class Animator:
    """
    The Animation value where from some document about animations
    in material. (Unfortunatly I do not find it anymore)
    """

    animation_objects = {
        ".lbo-grid": ["grid-template-columns", "grid-template-rows"]
    }

    def __init__(self):
        self.animated_elements = self.styles_changed = None
        info = get_info()
        if info["mobile"]:
            self.set_curve(225, 300, 225, 195)
        elif info["tablet"]:
            self.set_curve(292, 330, 225, 195)
        else:
            self.set_curve(150, 200, 200, 150)

    def set_curve(self, short, long, show, hide):
        self.time_short = short
        self.time_long = long
        self.time_show = show
        self.time_hide = hide

        # from matrial
        a = (long-short) / 380
        t = short - a*120
        self.calc_animation_duration = lambda size: min(a*size + t, long)
        return self

    def change_style(self, element, style, value, transform=True):
        current_value = element.style[style]
        if current_value == value:
            return self

        if self.animated_elements is not None:
            element.style[style] = value
            return self

        if self.styles_changed is None:
            self.styles_changed = []
            executer.add(self.start_animation)

        self.styles_changed.append([element, style, current_value if transform else value, value])
        return self

    def show(self, element, visible):
        if visible:
            visible = visible if isinstance(visible, str) else ""
            return self.change_style(element, "display", visible, False)
        else:
            return self.change_style(element, "display", "none")

    def start_animation(self):
        # read state before styles changes
        candidates = []
        for selector, styles in self.animation_objects.items():
            for element in document.querySelectorAll(selector):
                calced = getComputedStyle(element)
                for style_id in styles:
                    before = calced[style_id]
                    if "auto" not in before:   # "auto" -> display == "none"
                        # __pragma__("jsiter")
                        candidates.append({
                            "element": element,
                            "style": style_id,
                            "before": before,
                        })
                        # __pragma__("nojsiter")

        showing_objects = False
        hidding_objects = False

        # apply changes
        for element, style_id, before, after in self.styles_changed:
            element.style[style_id] = after
            if style_id == "display":
                if after == "none":
                    showing_objects = True
                else:
                    hidding_objects = True

        animation_size = 0
        # read state afterwards
        animated = []
        for props in candidates:
            element = props["element"]
            style_id = props["style"]
            calced = getComputedStyle(element)
            after = calced[style_id]
            if "auto" not in after and after != props["before"]:
                props["after"] = after
                props["restore"] = element.style[style_id]
                animation_size = max(calc_animation_size(before, after), animation_size)
                animated.append(props)

        if len(animated):
            # calc animation duration
            if showing_objects == "show":
                duration = self.time_show
            elif hidding_objects:
                duration = self.time_hide
            else:
                dp_size = animation_size * 2.22 / get_metrics().pt_height
                duration = self.calc_animation_duration(dp_size)

            console.log("***start animation", duration, animated)
            self.animated_elements = animated
            # revert_changes
            for element, style, before, after in self.styles_changed:
                element.style[style] = before

            # define animation
            # __pragma__("jsiter")
            timeline = anime["default"].timeline({
                "easing": "cubicBezier(.42,0,.58,1)",
                "duration": duration
            })
            # __pragma__("nojsiter")

            for props in animated:
                # __pragma__("jsiter")
                timeline.add({
                    "targets": props["element"],
                    props["style"]: [props["before"], props["after"]]
                }, 0)
                # __pragma__("nojsiter")

            timeline.finished.then(self._transition_end)
        else:
            self.animated_elements = self.styles_changed = None

    def _transition_end(self):
        console.log("**done animation", self.animated_elements)
        # revert all style settings, changed by animation
        for element, style, before, after in self.styles_changed:
            element.style[style] = after
        for props in self.animated_elements:
            props["element"].style[props["style"]] = props["restore"]
        self.animated_elements = self.styles_changed = None


def calc_animation_size(before, after):
    delta = 0
    if "px" in before:
        for b, a in zip(before.split(" "), after.split(" ")):
            delta = max(abs(parseFloat(b) - parseFloat(a)), delta)
    return delta


animate = Animator()
