import os
from flask import Flask, request
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

app = Flask(__name__)
UA = "Mozilla/5.0 (Linux; Android 10) Chrome/120 Mobile Safari/537.36"
# Clave opcional: defínela en Render > Environment como KEY. Si no existe, no se pide.
KEY = os.environ.get("KEY", "")

HOME = """<html><head><title>Nube</title></head><body>
<form action="/" method="get">
<input name="u" value="https://">
<input type="hidden" name="k" value="{k}">
<input type="submit" value="Ir"></form>
<p><a href="/?k={k}&u=https%3A%2F%2Fhtml.duckduckgo.com%2Fhtml%2F%3Fq%3Dnoticias">Buscar</a></p>
</body></html>"""


@app.route("/")
def index():
    k = request.args.get("k", "")
    if KEY and k != KEY:
        return "<html><body>Acceso denegado. Agrega ?k=tuclave a la URL.</body></html>", 403

    u = request.args.get("u")
    show_img = request.args.get("img", "0") == "1"
    if not u:
        return HOME.format(k=k)
    if not u.startswith("http"):
        u = "https://" + u

    try:
        r = requests.get(u, headers={"User-Agent": UA}, timeout=15)
    except Exception as e:
        return f"<p>Error: {e}</p><a href='/?k={k}'>Inicio</a>"

    soup = BeautifulSoup(r.text, "html.parser")
    for t in soup(["script", "style", "iframe", "svg", "noscript",
                   "video", "audio", "canvas", "link", "meta"]):
        t.decompose()
    if not show_img:
        for t in soup("img"):
            t.decompose()

    for tag in soup.find_all(True):
        keep = {a: v for a, v in tag.attrs.items() if a in ("href", "src", "alt")}
        if tag.name == "a" and "href" in keep:
            full = urljoin(r.url, keep["href"])
            keep["href"] = "/?k=" + quote(k) + "&u=" + quote(full, safe="")
        tag.attrs = keep

    body = soup.body.decode_contents() if soup.body else str(soup)
    return f"<html><body><a href='/?k={k}'>[Inicio]</a><hr>{body}</body></html>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
