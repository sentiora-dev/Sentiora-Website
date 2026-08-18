"""Build the product pages from produse.json.

The pages in the repo root are OUTPUT. Do not edit them by hand — the next build
overwrites them. Edit `produse.json` (what the product is) or
`vitrine/<slug>.html` (what that one page shows) instead.

Adding a product: one entry in produse.json, one file in vitrine/, run this.
Everything else — head, meta, sharing preview, header, footer links, sitemap —
follows on its own and stays identical across every page.

    python site/construieste.py
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
VITRINE = os.path.join(HERE, "vitrine")
BASE = "https://sentiora.dev"


def read(path):
    return io.open(path, encoding="utf-8").read()


def write(path, text):
    """Newlines stay \\n so the files look the same on every machine."""
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def body_attrs(p):
    parts = []
    if p.get("body_class"):
        parts.append(' class="%s"' % p["body_class"])
    if p.get("body_style"):
        parts.append(' style="%s"' % p["body_style"])
    return "".join(parts)


def header_nav(p):
    return "".join('<a href="%s">%s</a>' % (a["href"], a["text"]) for a in p["nav"])


def footer_nav(p, toate):
    """Support, then every other product. Derived, so adding a product never
    leaves a stale footer on the pages that already exist."""
    links = ['<a href="%s">Support</a>' % p["support_mailto"]] if p.get("support_mailto") else []
    for other in toate:
        if other["slug"] != p["slug"]:
            links.append('<a href="%s.html">%s</a>' % (other["slug"], other["nume_scurt"]))
    return "".join(links)


def build():
    data = json.loads(read(os.path.join(HERE, "produse.json")))
    produse = sorted(data["produse"], key=lambda p: p["ordine"])
    sablon = read(os.path.join(HERE, "sablon-produs.html"))

    for p in produse:
        # The stored fragments have no indent on their first line; every later
        # line keeps the indentation it was written with, so only line one
        # needs putting back where it belongs.
        continut = "    " + read(os.path.join(VITRINE, p["slug"] + ".html")).rstrip("\n")

        dialog = ""
        dpath = os.path.join(VITRINE, p["slug"] + ".dialog.html")
        if os.path.exists(dpath):
            dialog = "\n  " + read(dpath).rstrip("\n") + "\n"

        script = ""
        spath = os.path.join(VITRINE, p["slug"] + ".js")
        if os.path.exists(spath):
            # The stored file has no indent on its first line; the rest keeps
            # the four spaces it was written with, so only line one needs it.
            body = read(spath).rstrip("\n")
            script = "\n  <script>\n    " + body + "\n  </script>\n"

        page = sablon
        for token, value in [
            ("{{SLUG}}", p["slug"]),
            ("{{TITLU}}", p["titlu"]),
            ("{{DESCRIERE}}", p["descriere"]),
            ("{{THEME_COLOR}}", p["theme_color"]),
            ("{{OG_IMAGE}}", p["og_image"]),
            ("{{BODY_ATTRS}}", body_attrs(p)),
            ("{{NAV}}", header_nav(p)),
            ("{{CONTINUT}}", continut),
            ("{{DIALOG}}", dialog),
            ("{{FOOTER_NAV}}", footer_nav(p, produse)),
            ("{{SCRIPT}}", script),
        ]:
            page = page.replace(token, value)

        write(os.path.join(SITE, p["slug"] + ".html"), page)
        print("  %s.html" % p["slug"])

    sitemap(produse)
    print("\n%d pagini generate + sitemap.xml" % len(produse))


def sitemap(produse):
    urls = ['  <url>\n    <loc>%s/</loc>\n    <changefreq>monthly</changefreq>'
            '\n    <priority>1.0</priority>\n  </url>\n' % BASE]
    for p in produse:
        urls.append('  <url>\n    <loc>%s/%s.html</loc>\n    <changefreq>monthly</changefreq>'
                    '\n    <priority>0.8</priority>\n  </url>\n' % (BASE, p["slug"]))
    write(os.path.join(SITE, "sitemap.xml"),
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(urls) + "</urlset>\n")


if __name__ == "__main__":
    build()
