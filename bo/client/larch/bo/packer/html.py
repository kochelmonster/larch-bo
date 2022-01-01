import logging
import mimetypes
from pathlib import Path

logger = logging.getLogger("larch.bo.packer")


INDEX = """
<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="Content-Type" content="text/html;charset=UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  {icons}
  {html_head}
  {css_links}
  {js_links}
</head>
<body tabindex="-1" id="body">
</body>
</html>
""".strip()


def create_js_links(*files, type_=""):
    files = (f.with_suffix(".js") for f in files)
    files = (f for f in files if f.exists())
    return "".join(f'<script src="./{f.name}" type="{type_}"></script>' for f in files)


def create_css_links(*files):
    files = (f.with_suffix(".css") for f in files)
    files = (f for f in files if f.exists())
    return "".join(f'<link rel="stylesheet" href="./{f.name}">' for f in files)


def make(linker):
    logger.info("create index.html %r\n%r", linker.path, linker.config)

    linker.config.setdefault("title", "Larch Bo")
    linker.config.setdefault("html_head", "")

    root = linker.config["resource_path"]/Path(linker.config["root"]).name

    print("**options args", linker.config["args"])
    if linker.config["args"].no_module:
        jstype = "text/Javascript"
        make_strict(linker)
    else:
        jstype = "module"

    js_links = create_js_links(root, type_=jstype)
    css_links = create_css_links(root)

    html = linker.config.get('template', INDEX).format(
        css_links=css_links, icons=make_icon_list(linker),
        js_links=js_links, **linker.config)

    with open(linker.config["resource_path"]/"index.html", "w") as f:
        f.write("".join(line.strip() for line in html.splitlines()))


def make_strict(linker):
    """add use strict to the main output"""
    for f in linker.config["resource_path"].iterdir():
        print("make strict", f, f.suffix)
        if f.suffix == ".js":
            f.write_text("'use strict';\n" + f.read_text())


def make_icon_list(linker):
    licons = []
    icons = linker.config.get("favicons", [])
    dst_path = linker.path / "dist"
    dst_path.mkdir(parents=True, exist_ok=True)

    for fname in icons:
        src = Path(fname)
        dst = dst_path/src.name
        print("copy icon", src, dst)
        dst.write_bytes(src.read_bytes())
        if fname.name != "favicon.ico":
            mime = mimetypes.guess_type(dst)[0]
            licons.append(f'<link rel="icon" href="./{src.name}" type="{mime}">')

    return ''.join(licons)
