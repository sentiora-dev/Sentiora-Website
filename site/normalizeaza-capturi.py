"""Make every gallery screenshot the same shape.

The gallery box is a fixed 16:9 and the pictures inside it are fitted, not
cropped. So a capture that is not 16:9 sits in the box with bands down the
sides while its neighbour fills the box edge to edge, and the row looks ragged.

This pads every gallery image onto one 16:9 canvas, centred, filling the space
with a colour taken from the image's own border so the join is invisible.
Nothing is cropped, and nothing is scaled up -- every window keeps the size it
was captured at, which is why two captures can still show the application at
different sizes. Only the frame is made to match.

The list of images is read out of the product pages themselves, so a screenshot
added to a page is covered without touching this file.

Run it after adding a screenshot; it is safe to run again -- an image already at
the right size is left alone.

    python site/normalizeaza-capturi.py
"""
import glob
import io
import os
import re
import statistics

from PIL import Image

RADACINA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(RADACINA, "assets")
LATIME, INALTIME = 1204, 677          # 16:9, the gallery box

# Only gallery images -- the hero on each page sizes itself to its own picture.
# Read straight from the pages so nothing can be forgotten here.
def galerie():
    nume = []
    for pagina in sorted(glob.glob(os.path.join(RADACINA, "*.html"))):
        text = io.open(pagina, encoding="utf-8").read()
        # only the cards in the strip: the big picture at the top of each page
        # opens in the lightbox too, but it is sized to its own shape on purpose
        for n in re.findall(
                r'class="gallery-media"[^>]*data-preview-src="assets/([^"]+)\.webp"', text):
            if n not in nume:
                nume.append(n)
    return nume


def culoare_margine(im):
    """The colour to pad with: the median of the outermost ring of pixels, so
    the padding continues whatever the window sits on rather than announcing
    itself as a grey band."""
    w, h = im.size
    margine = []
    for x in range(0, w, max(1, w // 60)):
        margine.append(im.getpixel((x, 0)))
        margine.append(im.getpixel((x, h - 1)))
    for y in range(0, h, max(1, h // 60)):
        margine.append(im.getpixel((0, y)))
        margine.append(im.getpixel((w - 1, y)))
    return tuple(int(statistics.median(c[i] for c in margine)) for i in range(3))


def main():
    print("%-24s %-13s %s" % ("captura", "era", "devine"))
    atinse = sarite = 0
    for nume in galerie():
        sursa = os.path.join(ASSETS, nume + ".jpg")
        if not os.path.exists(sursa):
            print("  LIPSA:", nume)
            continue

        im = Image.open(sursa).convert("RGB")
        if im.size == (LATIME, INALTIME):
            sarite += 1
            continue

        era = "%dx%d" % im.size

        # never enlarge: shrink only if it would not otherwise fit
        k = min(LATIME / im.width, INALTIME / im.height, 1.0)
        if k < 1.0:
            im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)

        panza = Image.new("RGB", (LATIME, INALTIME), culoare_margine(im))
        panza.paste(im, ((LATIME - im.width) // 2, (INALTIME - im.height) // 2))

        tinta = os.path.join(ASSETS, nume)
        panza.save(tinta + ".webp", "WEBP", quality=86, method=6)
        panza.save(tinta + ".jpg", "JPEG", quality=88, optimize=True, progressive=True)
        atinse += 1
        print("%-24s %-13s %dx%d" % (nume, era, LATIME, INALTIME))

    print("\n%d normalizate, %d erau deja bune" % (atinse, sarite))
    print("Atentie: latimea/inaltimea din HTML trebuie sa fie %d si %d." % (LATIME, INALTIME))


if __name__ == "__main__":
    main()
