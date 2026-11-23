# Derived from https://github.com/irvan-putra/kokok/blob/main/tools/badge_icon.py
# Shared adaptive-aware family geometry; only simak art/palette differ.
#!/usr/bin/env python3
"""Launcher icon generator: one picture plus the shared version badge.

Deterministic. Same version in, same PNGs out. Inputs are pinned: Pillow
PILLOW_PIN and DejaVu Sans Bold with sha256 FONT_SHA256. The script fails
instead of falling back to another font or Pillow version, because a
different rasterizer or font changes the pixels.
    pip install pillow==12.3.0   (the font is vendored in tools/fonts/)

Badge: numbers only, a full-width strip across the bottom 24% of the icon.
Picture safety: every picture pixel is checked to lie inside the circle that
touches the icon edges (shrunk by a margin), so round launcher masks do not
clip it; the version text is checked the same way.

Outputs match the com.vanipy family standard (same geometry as the other
apps' generators):
- legacy mipmap PNGs per density: rounded-square icon with the strip.
- adaptive-icon foreground: the 72dp face (576px) centred on the 108dp
  layer (864px) with 18dp overscan; the strip spans the full layer width
  from 76% of the face so launchers that crop the overscan still show it.
- themed (monochrome) foreground: white silhouette; the numbers are cut
  out of the strip for contrast.
- mipmap-anydpi-v26 XML and the background colour resource.

`--check` regenerates everything into a temp dir and fails if any
committed resource differs, so CI can prove the PNGs came from this
script.
"""
import hashlib, math, os, re, shutil, sys, tempfile
import PIL
from PIL import Image, ImageChops, ImageDraw, ImageFont

PILLOW_PIN = "12.3.0"
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FONT_VENDORED = os.path.join(ROOT, "tools", "fonts", "DejaVuSans-Bold.ttf")
FONT_SYSTEM = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SHA256 = "d1c3ff99f1e1ce1827a33efd4dad81f40babda06bff9e43bd7591c86662a287b"
DENSITIES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
S = 768
STRIP_TOP = 0.76      # strip covers 76%..100% of the icon height
TEXT_SIZE = 0.115     # numeral size, fraction of icon size
SAFE_R = 0.485        # picture and text must stay inside this radius (fraction)

if PIL.__version__ != PILLOW_PIN:
    sys.exit("Pillow %s required, found %s" % (PILLOW_PIN, PIL.__version__))


def font_path():
    # Prefer the vendored, hash-checked font (identical on every machine);
    # fall back to the system install for local runs.
    for path in (FONT_VENDORED, FONT_SYSTEM):
        if os.path.exists(path):
            return path
    sys.exit("missing font: neither " + FONT_VENDORED + " nor " + FONT_SYSTEM)


def font(px):
    path = font_path()
    if hashlib.sha256(open(path, "rb").read()).hexdigest() != FONT_SHA256:
        sys.exit("unexpected font file " + path)
    return ImageFont.truetype(path, px)


def circle_mask(size, r=SAFE_R):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse([size * (.5 - r), size * (.5 - r), size * (.5 + r), size * (.5 + r)], fill=255)
    return m


def assert_inside_circle(layer, what, size=S, r=SAFE_R):
    alpha = layer.getchannel("A").point(lambda v: 255 if v > 8 else 0)
    outside = ImageChops.multiply(alpha, ImageChops.invert(circle_mask(size, r)))
    box = outside.getbbox()
    if box:
        sys.exit("%s leaves the round-mask safe circle at %s" % (what, box))


def new_layer(size=S):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def compose(bg, art, version, strip, text, rounded=None, size=S, circle_check=True):
    """Background, then the picture layer, then the badge strip."""
    if circle_check:
        assert_inside_circle(art, "picture", size)
    base = Image.new("RGBA", (size, size), bg) if bg else Image.new("RGBA", (size, size), (0, 0, 0, 0))
    base.alpha_composite(art)
    d = ImageDraw.Draw(base)
    y0 = int(size * STRIP_TOP)
    d.rectangle([0, y0, size, size], fill=strip)
    tl, td = new_layer(size)
    f = font(int(size * TEXT_SIZE))
    td.text((size / 2, (y0 + size) / 2), version, font=f, fill=text, anchor="mm")
    if circle_check:
        assert_inside_circle(tl, "version text", size)
    base.alpha_composite(tl)
    if rounded:
        m = Image.new("L", (size, size), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], radius=rounded * size, fill=255)
        base.putalpha(ImageChops.multiply(base.getchannel("A"), m))
    return base


def parse_version(argv, fallback=None):
    v = argv[1] if len(argv) > 1 else fallback
    if not v or not re.fullmatch(r"\d+\.\d+\.\d+", v):
        sys.exit("version must be X.Y.Z")
    return v


def write_densities(img, res_dir, name="ic_launcher.png"):
    for dens, px in DENSITIES.items():
        out = os.path.join(res_dir, "mipmap-" + dens)
        os.makedirs(out, exist_ok=True)
        img.resize((px, px), Image.LANCZOS).save(os.path.join(out, name), optimize=True)


SIMAK_BG = (16, 49, 43, 255)        # deep teal ink
SIMAK_CARD = (247, 246, 241, 255)   # paper
SIMAK_LINE = (14, 124, 102, 255)    # teal accent
SIMAK_STAR = (232, 161, 61, 255)    # warm gold
SIMAK_STRIP = (10, 35, 32, 255)
SIMAK_LIGHT = (127, 219, 202, 255)  # mint, for the adaptive face


def star(d, cx, cy, r, fill):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.42
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)


def simak_art():
    """Binoculars (simak = watch closely) with a gold star glint in one lens."""
    art, d = new_layer()
    cx, cy = S * .5, S * .52
    r = S * .125
    # bridge between the barrels, with the focus wheel
    d.rounded_rectangle([cx - S * .06, cy - r * .95, cx + S * .06, cy - r * .35],
                        radius=S * .02, fill=SIMAK_CARD)
    d.ellipse([cx - S * .032, cy - r * .78, cx + S * .032, cy - r * .78 + S * .064], fill=SIMAK_LINE)
    # barrels with tapered tops
    for sx in (-1, 1):
        bx = cx + sx * S * .135
        d.rounded_rectangle([bx - r * .55, cy - r * 1.65, bx + r * .55, cy - r * .5],
                            radius=S * .025, fill=SIMAK_CARD)
        d.ellipse([bx - r, cy - r, bx + r, cy + r], fill=SIMAK_CARD)
        d.ellipse([bx - r * .72, cy - r * .72, bx + r * .72, cy + r * .72], fill=SIMAK_LINE)
        d.ellipse([bx - r * .42, cy - r * .42, bx + r * .42, cy + r * .42], fill=SIMAK_BG)
    # star glint in the right lens
    star(d, cx + S * .135, cy, S * .058, SIMAK_STAR)
    return art


def simak(version):
    return compose(SIMAK_BG, simak_art(), version, SIMAK_STRIP, SIMAK_CARD, rounded=.2)


ADAPTIVE_XML = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background" />
    <foreground android:drawable="@drawable/ic_launcher_foreground" />
    <monochrome android:drawable="@drawable/ic_launcher_monochrome" />
</adaptive-icon>
"""

COLORS_XML = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">#10312B</color>
</resources>
"""


def simak_adaptive(version):
    """Foreground + monochrome layers with the family strip on the face.

    The 72dp face is 576px centred on the 108dp 864px layer (18dp
    overscan). Strip and text use the same 76%/88%/11.5% face geometry as
    the legacy icon, so masked and unmasked launchers show the same badge.
    The themed numbers are cut out of the strip for contrast.
    """
    T, F, I = 864, 576, 144
    art = simak_art()
    art.paste(SIMAK_LIGHT, (0, 0, S, S), art.getchannel("A"))
    art = art.resize((F, F), Image.LANCZOS)
    fg, d = new_layer(T)
    fg.alpha_composite(art, (I, I))
    y = I + int(F * STRIP_TOP)
    d.rectangle([0, y, T, T], fill=SIMAK_STRIP)
    text, td = new_layer(T)
    td.text((T / 2, I + F * .88), version, font=font(int(F * TEXT_SIZE)),
            fill=(255, 255, 255, 255), anchor="mm")
    fg.alpha_composite(text)
    alpha = Image.new("L", (T, T), 0)
    alpha.paste(art.getchannel("A"), (I, I))
    ImageDraw.Draw(alpha).rectangle([0, y, T, T], fill=255)
    alpha = ImageChops.subtract(alpha, text.getchannel("A"))
    mono = Image.new("RGBA", (T, T), (255, 255, 255, 255))
    mono.putalpha(alpha)
    return fg, mono


def write_all(version, res_dir):
    write_densities(simak(version), res_dir)
    write_densities(simak(version), res_dir, "ic_launcher_round.png")
    fg, mono = simak_adaptive(version)
    drawables = os.path.join(res_dir, "drawable-xxxhdpi")
    os.makedirs(drawables, exist_ok=True)
    fg.resize((432, 432), Image.LANCZOS).save(
        os.path.join(drawables, "ic_launcher_foreground.png"), optimize=True)
    mono.resize((432, 432), Image.LANCZOS).save(
        os.path.join(drawables, "ic_launcher_monochrome.png"), optimize=True)
    anydpi = os.path.join(res_dir, "mipmap-anydpi-v26")
    os.makedirs(anydpi, exist_ok=True)
    for name in ("ic_launcher.xml", "ic_launcher_round.xml"):
        with open(os.path.join(anydpi, name), "w") as fh:
            fh.write(ADAPTIVE_XML)
    values = os.path.join(res_dir, "values")
    os.makedirs(values, exist_ok=True)
    with open(os.path.join(values, "colors.xml"), "w") as fh:
        fh.write(COLORS_XML)


def written_paths(res_dir):
    paths = [os.path.join("mipmap-" + d, n) for d in DENSITIES
             for n in ("ic_launcher.png", "ic_launcher_round.png")]
    paths += [
        os.path.join("drawable-xxxhdpi", "ic_launcher_foreground.png"),
        os.path.join("drawable-xxxhdpi", "ic_launcher_monochrome.png"),
        os.path.join("mipmap-anydpi-v26", "ic_launcher.xml"),
        os.path.join("mipmap-anydpi-v26", "ic_launcher_round.xml"),
        os.path.join("values", "colors.xml"),
    ]
    return [os.path.join(res_dir, p) for p in paths]


def check(version, res_dir):
    """Fail unless every committed resource matches this script's output."""
    tmp = tempfile.mkdtemp(prefix="simak-icons-")
    try:
        write_all(version, tmp)
        bad = []
        for generated in written_paths(tmp):
            committed = os.path.join(res_dir, os.path.relpath(generated, tmp))
            if not os.path.exists(committed) or open(committed, "rb").read() != open(generated, "rb").read():
                bad.append(os.path.relpath(committed, res_dir))
        if bad:
            sys.exit("committed launcher resources differ from the generator: " + ", ".join(bad))
        print("launcher resources match the generator for", version)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def default_version():
    with open(os.path.join(ROOT, "app", "build.gradle.kts")) as fh:
        text = fh.read()
    for pattern in (r'versionName\s*=\s*"([^"]+)"', r'appVersionName\s*=\s*"([^"]+)"'):
        m = re.search(pattern, text)
        if m:
            return m.group(1)
    sys.exit("could not read the app version from app/build.gradle.kts")


def main():
    check_mode = "--check" in sys.argv[1:]
    argv = [a for a in sys.argv[1:] if a != "--check"]
    version = parse_version(["badge_icon.py"] + argv, fallback=default_version())
    res_dir = os.path.join(ROOT, "app", "src", "main", "res")
    if check_mode:
        check(version, res_dir)
    else:
        write_all(version, res_dir)
        print("wrote icons for", version)


if __name__ == "__main__":
    main()
