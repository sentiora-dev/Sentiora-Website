"""Rebuild the two layers of the hero mark.

Two fixes over the first attempt. The lockup file is a 3840-wide canvas with the
artwork floating in the middle of a lot of empty space, so laying it out at the
column width drew the artwork at barely half of it -- trimming to the artwork
makes the mark as large as the space allows without changing any layout. And the
sphere now comes from its own high-resolution render rather than from the 218px
copy baked into the lockup, which was soft and carried a lilac cast.
"""
import os
from collections import deque

from PIL import Image, ImageChops, ImageFilter

LOCKUP = r"D:\CLAUDE\Web Sentiora\Imagini-originale\sentiora-logo-lockup-4k.png"
SFERA_HD = r"D:\CLAUDE\Web Sentiora\Imagini-originale\sentiora-sphere-source.png"
DEST = r"D:\CLAUDE\Web Sentiora\Sentiora-Website\assets"

SFERA = (1850, 708, 2016, 864)   # the sphere inside the lockup, measured earlier
PAD = 30                         # erase a little wider, so no rim is left behind

# ---------- the mark, without its sphere, trimmed to the artwork ----------
im = Image.open(LOCKUP).convert("RGBA")
gol = (SFERA[0] - PAD, SFERA[1] - PAD, SFERA[2] + PAD, SFERA[3] + PAD)
im.paste(Image.new("RGBA", (gol[2] - gol[0], gol[3] - gol[1]), (0, 0, 0, 0)), gol[:2])

# ignore all-but-invisible pixels when deciding where the artwork ends
solid = im.getchannel("A").point(lambda v: 255 if v > 8 else 0)
rama = solid.getbbox()
print("panza originala %dx%d -> artwork %dx%d" % (
    im.width, im.height, rama[2] - rama[0], rama[3] - rama[1]))

marca = im.crop(rama)
MW, MH = marca.size

lat = 1400
marca = marca.resize((lat, round(MH * lat / MW)), Image.LANCZOS)
marca.save(os.path.join(DEST, "marca-s.png"), "PNG", optimize=True)
marca.save(os.path.join(DEST, "marca-s.webp"), "WEBP", quality=93, method=6)

# ---------- the sphere, cut out of its own render by texture ----------
src = Image.open(SFERA_HD).convert("RGB")
W, H = src.size
gri = src.convert("L")
interval = ImageChops.difference(gri.filter(ImageFilter.MaxFilter(9)),
                                 gri.filter(ImageFilter.MinFilter(9)))
t = interval.point(lambda v: 255 if v >= 12 else 0)
t = t.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MaxFilter(9))
t = t.filter(ImageFilter.MinFilter(9)).filter(ImageFilter.MinFilter(9))
pt = t.load()

vazut = [[False] * W for _ in range(H)]
cel_mai_mare = []
for sy in range(H):
    for sx in range(W):
        if not pt[sx, sy] or vazut[sy][sx]:
            continue
        q = deque([(sx, sy)]); vazut[sy][sx] = True; pix = []
        while q:
            x, y = q.popleft(); pix.append((x, y))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = x + dx, y + dy
                if 0 <= a < W and 0 <= b < H and pt[a, b] and not vazut[b][a]:
                    vazut[b][a] = True; q.append((a, b))
        if len(pix) > len(cel_mai_mare):
            cel_mai_mare = pix

masca = Image.new("L", (W, H), 0)
pm = masca.load()
for x, y in cel_mai_mare:
    pm[x, y] = 255
masca = masca.filter(ImageFilter.MinFilter(9)).filter(ImageFilter.GaussianBlur(1.1))

sfera = src.convert("RGBA")
sfera.putalpha(masca)
sfera = sfera.crop(masca.getbbox())
SW, SH = sfera.size

lat_s = 384
sfera = sfera.resize((lat_s, round(SH * lat_s / SW)), Image.LANCZOS)
sfera.save(os.path.join(DEST, "sfera.png"), "PNG", optimize=True)
sfera.save(os.path.join(DEST, "sfera.webp"), "WEBP", quality=93, method=6)

# ---------- where it goes, as a share of the trimmed mark ----------
cx = ((SFERA[0] + SFERA[2]) / 2 - rama[0]) / MW
cy = ((SFERA[1] + SFERA[3]) / 2 - rama[1]) / MH
# the old file was the sphere plus 26px of margin; the new one is cut tight, so
# match the sphere itself, not the old file's outer edge
diametru = (SFERA[2] - SFERA[0]) / MW

print()
print("marca-s  %dx%d  png %.0f KB  webp %.0f KB" % (
    marca.width, marca.height,
    os.path.getsize(os.path.join(DEST, "marca-s.png")) / 1024,
    os.path.getsize(os.path.join(DEST, "marca-s.webp")) / 1024))
print("sfera    %dx%d  png %.0f KB  webp %.0f KB" % (
    sfera.width, sfera.height,
    os.path.getsize(os.path.join(DEST, "sfera.png")) / 1024,
    os.path.getsize(os.path.join(DEST, "sfera.webp")) / 1024))
print()
print("de pus in CSS:")
print("  left:  %.3f%%" % (cx * 100))
print("  top:   %.3f%%" % (cy * 100))
print("  width: %.3f%%" % (diametru * 100))
print("  marca: width=%d height=%d" % (marca.width, marca.height))
print("  sfera: width=%d height=%d" % (sfera.width, sfera.height))
