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

    acasa(data, produse)
    sitemap(produse)
    print("\n%d pagini generate + index.html + sitemap.xml" % len(produse))


CUVINTE = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six",
           7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten"}


def card(p):
    return (
        '          <a class="product-card" href="%s.html" '
        'style="--product-color:%s;--product-glow:%s;'
        '--product-mark:image-set(url(&quot;assets/%s.webp&quot;) type(&quot;image/webp&quot;),'
        'url(&quot;assets/%s.png&quot;) type(&quot;image/png&quot;))">\n'
        '            <div class="product-card-content">'
        '<span class="product-code">%s</span>'
        '<h4><span class="card-sentiora"><picture>'
        '<source srcset="assets/sentiora-wordmark-4k.webp" type="image/webp">'
        '<img src="assets/sentiora-wordmark-4k.png" alt="Sentiora" width="560" '
        'height="70" decoding="async"></picture></span>%s</h4>'
        '<p>%s</p><span class="product-link">%s</span></div>\n'
        '          </a>\n'
        % (p["slug"], p["culoare"], p["halou"], p["marca"], p["marca"], p["cod"],
           p["nume_card"], p["text_card"], p["link_card"])
    )


def acasa(data, produse):
    """Rewrite the product block on the home page.

    The count in the sentence and every card come from the data, so adding a
    product never leaves the home page describing the old catalogue.
    """
    path = os.path.join(SITE, "index.html")
    html = read(path)
    start, end = "<!-- GENERAT:PRODUSE -->", "<!-- /GENERAT:PRODUSE -->"
    if start not in html:
        print("  (index.html nu are marcaje — sarit)")
        return

    numar = CUVINTE.get(len(produse), str(len(produse)))
    out = [
        start, "\n",
        '        <div class="products-heading" data-reveal>\n',
        '          <h3>Meet the <span class="heading-sentiora"><picture>'
        '<source srcset="assets/sentiora-wordmark-4k.webp" type="image/webp">'
        '<img src="assets/sentiora-wordmark-4k.png" alt="Sentiora" width="560" '
        'height="70" decoding="async"></picture></span> product family.</h3>\n',
        '          <p>%s Windows applications that do their work on your own '
        'machine — no accounts, no uploads, no telemetry.</p>\n' % numar,
        "        </div>\n\n",
    ]

    if data.get("grupeaza_pe_familii"):
        # Worth switching on once the catalogue outgrows a single readable row.
        for fam in sorted(data["familii"], key=lambda f: f["ordine"]):
            membri = [p for p in produse if p["familie"] == fam["id"]]
            if not membri:
                continue
            out.append('        <div class="product-family" data-reveal>\n')
            out.append('          <h4 class="family-name">%s</h4>\n' % fam["nume"])
            out.append('          <div class="product-grid">\n')
            out.extend(card(p) for p in membri)
            out.append("          </div>\n        </div>\n\n")
    else:
        out.append('        <div class="product-grid" data-reveal>\n')
        out.extend(card(p) for p in produse)
        out.append("        </div>\n\n")

    out.append(end)
    block = "".join(out)

    before = html[:html.index(start)]
    after = html[html.index(end) + len(end):]
    write(path, before + block + after)
    print("  index.html (%d carduri)" % len(produse))


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
