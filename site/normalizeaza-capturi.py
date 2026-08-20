"""Make every gallery screenshot the same size.

The gallery box is a fixed 16:9. The captures were not — they ran from 2.23:1
to almost square — so with the picture fitted inside the box, each application
window came out a different size and the row looked ragged.

This pads every gallery image onto one 16:9 canvas, centred, filling the space
with a colour taken from the image's own border so the join is invisible.
Nothing is cropped and nothing is scaled up.

Run it after adding a screenshot; it is safe to run again — an image already at
the right size is left alone.

    python site/normalizeaza-capturi.py
"""
import io
import os
import statistics

from PIL import Image

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
LATIME, INALTIME = 1204, 677          # 16:9, the gallery box

# Only gallery images. The hero on each page sizes itself to its own picture.
GALERIE = [
    "dm-sanatate-bun", "dm-sanatate-rau", "dm-scanare", "dm-verificare",
    "dm-benchmark", "dm-ai-intrebare", "dm-ai-setari", "dm-detectie",
    "dm-drivere", "dm-dll", "dm-test-automat", "dm-armat", "dm-unelte",
    "ob-ardere", "ob-compilatie", "ob-medii", "ob-multidisc", "ob-salvare",
    "ob-iso", "ob-meniu-intunecat",
]


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
    for nume in GALERIE:
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
