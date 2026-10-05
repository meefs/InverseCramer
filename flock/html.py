"""Interactive viewer: the stereogram rebuilt live in the browser. -> <builddir>/flock_viewer.html"""
import base64
import sys
from pathlib import Path

build = Path(sys.argv[1] if len(sys.argv) > 1 else "build/flock")
tpl = (Path(__file__).parent / "viewer_template.html").read_text()
uri = lambda p: "data:image/png;base64," + base64.b64encode((build / p).read_bytes()).decode()
html = tpl.replace("__CELL__", uri("cell_ss.png")).replace("__DEPTH__", uri("depth.png"))
(build / "flock_viewer.html").write_text(html)
# a standalone document for the website (the artifact version above is wrapped by its host)
page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n</head>\n<body>\n' + html + '\n</body>\n</html>\n')
(build / "flock_viewer_page.html").write_text(page)
print(build / "flock_viewer.html", round(len(html) / 1e6, 2), "MB")
