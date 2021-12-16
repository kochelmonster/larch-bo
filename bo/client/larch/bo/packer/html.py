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


def create_js_links(urls):
    return "".join(f'<script src="{js}" type="module"></script>' for js in urls)


def create_css_links(urls, themed=False, cdn={}):
    klass = 'class="theme"' if themed else ""
    urls = (cdn.get(u, u) for u in urls)
    return "".join(f'<link rel="stylesheet" href="{u}" {klass}>' for u in urls if u)


def make(linker):
    logger.info("create index.html %r\n%r", linker.path, linker.config)

    js_links = []
    css_links = []
    """
    rp = Path(linker.config["resources_path"])
    for resource in rp.iterdir():
        if resource.suffix == ".js":
            js_links.append(resource)
        elif resource.suffix == ".css":
            css_links.append(resource)
    """

    linker.config.setdefault("title", "Larch Bo")
    linker.config.setdefault("html_head", "")
    root_name = Path(linker.config["root"]).with_suffix(".js").name
    js_links.append(f"./{root_name}")
    html = linker.config.get('template', INDEX).format(
        css_links=create_css_links(css_links), icons=make_icon_list(linker),
        js_links=create_js_links(js_links), **linker.config)

    with open(linker.path/"index.html", "w") as f:
        f.write(html)


def make_icon_list(linker):
    licons = []
    icons = linker.config.get("favicons", [])
    for fname in icons:
        if fname.name != "favicon.ico":
            src = Path(fname)
            dst = linker.path/src.name
            dst.write_bytes(src.read_bytes())
            mime = mimetypes.guess_type(dst)[0]
            licons.append(f'<link rel="icon" href="./{src.name}" type="{mime}">')
        else:
            src = Path(fname)
            dst = linker.path/"dist/favicon.ico"
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())

    return ''.join(licons)
