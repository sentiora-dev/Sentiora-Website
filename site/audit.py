"""Check the whole site the way a careful stranger would.

Everything here is a check that can be answered by looking at the files, so it
can be re-run after any change and will say the same thing. What it cannot see
-- how a page looks, whether the words are true -- is checked by hand and
written up separately; this only covers what a machine can be sure about.

    python site/audit.py
"""
import hashlib
import io
import os
import re
import sys
from collections import Counter, defaultdict
from html.parser import HTMLParser

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://sentiora.dev"

gasite = defaultdict(list)


def spune(nivel, unde, ce):
    gasite[nivel].append((unde, ce))


class Pagina(HTMLParser):
    """Just enough of the page to check it: no dependencies to install."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.text_parts = []
        self._open = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        self._open.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def handle_endtag(self, tag):
        if self._open and tag in self._open:
            while self._open and self._open.pop() != tag:
                pass

    def handle_data(self, data):
        if not self._open or self._open[-1] not in ("script", "style"):
            self.text_parts.append(data)

    def of(self, name):
        return [a for t, a in self.tags if t == name]

    @property
    def text(self):
        return " ".join(self.text_parts)


def citeste(path):
    return io.open(path, encoding="utf-8").read()


def pagini():
    return sorted(f for f in os.listdir(SITE) if f.endswith(".html"))


# ---------------------------------------------------------------- link check

def fisier_pentru(href, dinspre):
    """Where a link points on disk, or None if it is not a local file."""
    if href.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
        return None
    cale = href.split("#")[0].split("?")[0]
    if not cale:
        return None
    if cale.startswith("/"):
        return os.path.join(SITE, cale.lstrip("/"))
    return os.path.join(os.path.dirname(os.path.join(SITE, dinspre)), cale)


def verifica_legaturi(nume, p):
    ancore = set()
    for _, attrs in p.tags:
        if "id" in attrs:
            ancore.add(attrs["id"])

    for tag, attrs in p.tags:
        for camp in ("href", "src"):
            if camp not in attrs:
                continue
            valoare = attrs[camp]
            cale = fisier_pentru(valoare, nume)
            if cale and not os.path.exists(cale):
                spune("rupt", nume, "%s=%s nu există pe disc" % (camp, valoare))
            if valoare.startswith("#") and len(valoare) > 1:
                if valoare[1:] not in ancore:
                    spune("rupt", nume, "ancora %s nu există în pagină" % valoare)

        if "srcset" in attrs:
            for bucata in attrs["srcset"].split(","):
                adresa = bucata.strip().split(" ")[0]
                cale = fisier_pentru(adresa, nume)
                if cale and not os.path.exists(cale):
                    spune("rupt", nume, "srcset=%s nu există" % adresa)


# ------------------------------------------------------------------- images

def verifica_imagini(nume, p):
    try:
        from PIL import Image
    except ImportError:
        spune("nota", nume, "Pillow lipsește — nu pot verifica mărimile")
        return

    for attrs in p.of("img"):
        src = attrs.get("src", "")
        if "alt" not in attrs:
            spune("acces", nume, "<img src=%s> fără alt" % src)

        cale = fisier_pentru(src, nume)
        if not cale or not os.path.exists(cale):
            continue

        if "width" not in attrs or "height" not in attrs:
            spune("aspect", nume,
                  "%s fără width/height — pagina sare la încărcare" % src)
            continue

        try:
            real = Image.open(cale).size
        except Exception:                                     # noqa: BLE001
            continue
        declarat = (int(attrs["width"]), int(attrs["height"]))
        if real != declarat:
            spune("aspect", nume, "%s: fișierul e %dx%d, pagina declară %dx%d"
                  % (src, real[0], real[1], declarat[0], declarat[1]))


# ------------------------------------------------------------------ structure

def verifica_structura(nume, p, brut):
    idi = Counter(a["id"] for _, a in p.tags if "id" in a)
    for cheie, cate in idi.items():
        if cate > 1:
            spune("rupt", nume, "id=%s apare de %d ori" % (cheie, cate))

    titluri = [t for t, _ in p.tags if t in ("h1", "h2", "h3", "h4", "h5", "h6")]
    h1 = titluri.count("h1")
    if h1 == 0:
        spune("seo", nume, "nu are h1")
    elif h1 > 1:
        spune("seo", nume, "are %d titluri h1" % h1)

    nivel_ant = 0
    for t in titluri:
        nivel = int(t[1])
        if nivel_ant and nivel > nivel_ant + 1:
            spune("acces", nume, "sare de la h%d la h%d" % (nivel_ant, nivel))
            break
        nivel_ant = nivel

    html = p.of("html")
    if not html or "lang" not in html[0]:
        spune("acces", nume, "<html> fără lang")

    titlu = re.search(r"<title>(.*?)</title>", brut, re.S)
    if not titlu:
        spune("seo", nume, "fără <title>")
    else:
        lung = len(titlu.group(1).strip())
        if lung > 65:
            spune("seo", nume, "titlu de %d caractere (peste 65 se taie)" % lung)

    descriere = [a for a in p.of("meta") if a.get("name") == "description"]
    if not descriere:
        spune("seo", nume, "fără meta description")
    else:
        lung = len(descriere[0].get("content", ""))
        if lung > 160:
            spune("seo", nume, "meta description de %d caractere (peste 160 se taie)" % lung)
        elif lung < 50 and nume != "404.html":
            spune("seo", nume, "meta description de doar %d caractere" % lung)

    # A missing page must not be indexed. It wants noindex, and specifically
    # does NOT want a canonical or sharing tags: those ask to be indexed and
    # shared, which is the opposite of what a 404 is for.
    if nume == "404.html":
        roboti = [a for a in p.of("meta") if a.get("name") == "robots"]
        if not roboti or "noindex" not in roboti[0].get("content", ""):
            spune("seo", nume, "pagina de 404 ar trebui să aibă noindex")
        return

    canonic = [a for a in p.of("link") if a.get("rel") == "canonical"]
    if not canonic:
        spune("seo", nume, "fără canonical")
    else:
        astept = BASE + "/" + ("" if nume == "index.html" else nume)
        if canonic[0].get("href", "").rstrip("/") != astept.rstrip("/"):
            spune("seo", nume, "canonical zice %s, ar trebui %s"
                  % (canonic[0].get("href"), astept))

    proprietati = {a.get("property") for a in p.of("meta")}
    for cerut in ("og:title", "og:description", "og:image", "og:url"):
        if cerut not in proprietati:
            spune("seo", nume, "lipsește %s" % cerut)

    if not p.of("main") and nume != "404.html":
        spune("acces", nume, "fără <main>")

    for attrs in p.of("a"):
        if attrs.get("target") == "_blank" and "noopener" not in attrs.get("rel", ""):
            spune("siguranta", nume, "target=_blank fără rel=noopener: %s"
                  % attrs.get("href"))

    for attrs in p.of("a"):
        href = attrs.get("href", "")
        if href.startswith(("http://", "https://")) and BASE not in href:
            spune("nota", nume, "legătură în afară: %s" % href)


# ------------------------------------------------------------- fingerprints

def verifica_amprente(nume, brut):
    for adresa in set(re.findall(r'(?:src|href)="(/?assets/[^"]+)"', brut)):
        if "?v=" not in adresa:
            spune("cache", nume, "%s fără amprentă — o schimbare nu ajunge la vizitatori"
                  % adresa)

    for css in set(re.findall(r'href="(/?product\.css[^"]*)"', brut)):
        if "?v=" not in css:
            spune("cache", nume, "%s fără versiune" % css)
        else:
            cerut = hashlib.sha256(
                io.open(os.path.join(SITE, "product.css"), "rb").read()
            ).hexdigest()[:8]
            are = css.split("?v=")[1]
            if are != cerut:
                spune("cache", nume,
                      "product.css are versiunea %s, dar fișierul e %s — rulează build"
                      % (are, cerut))


# ------------------------------------------------------------------ the site

def verifica_sitemap():
    cale = os.path.join(SITE, "sitemap.xml")
    if not os.path.exists(cale):
        spune("seo", "sitemap.xml", "lipsește")
        return
    brut = citeste(cale)
    listate = set(re.findall(r"<loc>%s/([^<]*)</loc>" % re.escape(BASE), brut))
    reale = {f for f in pagini() if f not in ("404.html",)}
    for f in reale:
        cheie = "" if f == "index.html" else f
        if cheie not in listate:
            spune("seo", "sitemap.xml", "%s nu e în sitemap" % f)
    for l in listate:
        if l and not os.path.exists(os.path.join(SITE, l)):
            spune("rupt", "sitemap.xml", "%s e în sitemap dar nu există" % l)


def verifica_fisiere():
    for cerut in ("robots.txt", "404.html", "favicon.ico", "CNAME"):
        if not os.path.exists(os.path.join(SITE, cerut)):
            spune("lipsa", cerut, "nu există")
    robots = os.path.join(SITE, "robots.txt")
    if os.path.exists(robots) and "Sitemap:" not in citeste(robots):
        spune("seo", "robots.txt", "nu trimite către sitemap")


def verifica_greutate():
    total = 0
    mari = []
    for rad, _, fisiere in os.walk(os.path.join(SITE, "assets")):
        for f in fisiere:
            cale = os.path.join(rad, f)
            marime = os.path.getsize(cale)
            total += marime
            if marime > 300 * 1024:
                mari.append((f, marime))
    print("  imagini: %.1f MB în total" % (total / 1024 / 1024))
    for f, marime in sorted(mari, key=lambda x: -x[1]):
        spune("greutate", "assets/" + f, "%.0f KB" % (marime / 1024))


def verifica_lazy():
    """The first picture on a page should not be lazy, the rest should."""
    for nume in pagini():
        brut = citeste(os.path.join(SITE, nume))
        imagini = re.findall(r"<img [^>]*>", brut)
        for i, tag in enumerate(imagini):
            lazy = 'loading="lazy"' in tag
            if i == 0 and lazy:
                spune("aspect", nume, "prima imagine e lazy — întârzie ce se vede întâi")
            if i > 6 and not lazy and "gallery" in brut[max(0, brut.find(tag) - 200):brut.find(tag)]:
                spune("aspect", nume, "imagine din galerie fără loading=lazy")


def main():
    print("Audit Sentiora-Website\n")
    for nume in pagini():
        brut = citeste(os.path.join(SITE, nume))
        p = Pagina()
        p.feed(brut)
        verifica_legaturi(nume, p)
        verifica_imagini(nume, p)
        verifica_structura(nume, p, brut)
        verifica_amprente(nume, brut)

    verifica_sitemap()
    verifica_fisiere()
    verifica_lazy()
    verifica_greutate()

    ordine = ["rupt", "lipsa", "acces", "seo", "cache", "aspect", "siguranta",
              "greutate", "nota"]
    nume_lung = {
        "rupt": "LEGĂTURI RUPTE ȘI FIȘIERE LIPSĂ",
        "lipsa": "FIȘIERE CARE AR TREBUI SĂ EXISTE",
        "acces": "ACCESIBILITATE",
        "seo": "CĂUTARE ȘI PARTAJARE",
        "cache": "MEMORIA BROWSERULUI",
        "aspect": "AȘEZARE ȘI ÎNCĂRCARE",
        "siguranta": "SIGURANȚĂ",
        "greutate": "FIȘIERE GRELE",
        "nota": "DE ȘTIUT",
    }

    total = 0
    for cheie in ordine:
        if not gasite[cheie]:
            continue
        print("\n%s  (%d)" % (nume_lung[cheie], len(gasite[cheie])))
        print("-" * 72)
        for unde, ce in sorted(gasite[cheie]):
            print("  %-24s %s" % (unde, ce))
        if cheie not in ("nota", "greutate"):
            total += len(gasite[cheie])

    print("\n%s" % ("=" * 72))
    print("%d lucruri de reparat" % total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
