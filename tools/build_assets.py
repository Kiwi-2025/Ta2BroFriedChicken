"""Build standalone DST textures and a symbol-only BILD v6 animation archive.

Uses original art only. The idle animation comes from the game's cook_pot_food
bank; this archive supplies three replacement symbols, also used by cookers.
Binary format references are documented in art/README.md.
"""
from __future__ import annotations

import io
from pathlib import Path
import struct
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
NAMES = ["ta2bro_chicken_" + flavor for flavor in ("spicy", "garlic", "soy")]


def sdbm(value: str) -> int:
    result = 0
    for char in value.lower():
        result = (ord(char) + (result << 6) + (result << 16) - result) & 0xFFFFFFFF
    return result


def string(value: str) -> bytes:
    encoded = value.encode("ascii")
    return struct.pack("<I", len(encoded)) + encoded


def texture(image: Image.Image) -> bytes:
    """KTEX: default platform, DXT5/BC3, 2D, full mip chain.

    RGB is premultiplied by alpha as required by the game's texture blending.
    Mipmap descriptors precede all mipmap payloads.
    """
    levels = []
    image = image.convert("RGBA")
    while True:
        w, h = image.size
        rgba = image.copy()
        alpha = rgba.getchannel("A")
        from PIL import ImageChops
        rgba = Image.merge("RGBA", tuple(ImageChops.multiply(rgba.getchannel(c), alpha)
                                         for c in "RGB") + (alpha,))
        # DST's Windows ANGLE renderer requires GPU-compressed textures here.
        # In particular, RGBA8/platform=12 asserts in HWTexture.cpp when the
        # mod selection UI loads the icon (a null renderer cannot catch it).
        dds = io.BytesIO()
        ImageOps.flip(rgba).save(dds, format="DDS", pixel_format="DXT5")
        encoded = dds.getvalue()
        if encoded[:4] != b"DDS " or encoded[84:88] != b"DXT5":
            raise ValueError("Pillow must support DXT5 DDS encoding (Pillow >= 11.2)")
        payload = encoded[128:]
        pitch = max(1, (w + 3) // 4) * 16
        if len(payload) != pitch * max(1, (h + 3) // 4):
            raise ValueError("Unexpected DXT5 block data size")
        levels.append((w, h, pitch, payload))
        if w == 1 and h == 1:
            break
        image = image.resize((max(1, w // 2), max(1, h // 2)), Image.Resampling.LANCZOS)
    # Match the platform/compression fields of shipped game textures: 0 / 2.
    header = (2 << 4) | (1 << 9) | (len(levels) << 13) | (3 << 18) | (4095 << 20)
    return (b"KTEX" + struct.pack("<I", header)
            + b"".join(struct.pack("<HHHI", w, h, pitch, len(data)) for w, h, pitch, data in levels)
            + b"".join(data for _, _, _, data in levels))


def normalized(path: Path, size=(256, 256), bounds=(248, 224)) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    box = image.getchannel("A").getbbox()
    if box is None or image.getchannel("A").getextrema()[0] != 0:
        raise ValueError(f"Expected artwork with transparent background: {path}")
    image = image.crop(box)
    image.thumbnail(bounds, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size)
    canvas.alpha_composite(image, ((size[0] - image.width) // 2, (size[1] - image.height) // 2))
    return canvas


def build_binary() -> bytes:
    # Separate cooker symbols let pot size change without scaling ground art.
    symbols = [(index, name + suffix, scale) for index, name in enumerate(NAMES)
               for suffix, scale in (("", 1.0), ("_pot", 1.1))]
    result = io.BytesIO()
    result.write(b"BILD" + struct.pack("<III", 6, len(symbols), len(symbols)))
    result.write(string("ta2bro_chicken"))
    result.write(struct.pack("<I", 1) + string("atlas-0.tex"))
    ordered = sorted(symbols, key=lambda item: sdbm(item[1]))
    vertices = []
    for index, name, scale in ordered:
        start = len(vertices)
        # A 200-unit square matching the scale of vanilla food symbols.
        left, right, top, bottom = (-100.0 * scale, 100.0 * scale, -136.0 * scale, 64.0 * scale)
        u0, u1 = index / 4, (index + 1) / 4
        quad = [(left, top, u0, 1), (right, top, u1, 1), (left, bottom, u0, 0),
                (right, top, u1, 1), (right, bottom, u1, 0), (left, bottom, u0, 0)]
        vertices.extend((x, y, 0.0, u, v, 0.0) for x, y, u, v in quad)
        result.write(struct.pack("<IIIIffffII", sdbm(name), 1, 0, 1,
                                 0.0, -36.0 * scale, 200.0 * scale, 200.0 * scale, start, 6))
    result.write(struct.pack("<I", len(vertices)))
    for vertex in vertices:
        result.write(struct.pack("<ffffff", *vertex))
    result.write(struct.pack("<I", len(symbols)))
    for _, name, _ in ordered:
        result.write(struct.pack("<I", sdbm(name)) + string(name))
    return result.getvalue()


def atlas_xml(name: str) -> str:
    return (f'<Atlas><Texture filename="{name}.tex"/><Elements>'
            f'<Element name="{name}.tex" u1="0" u2="1" v1="0" v2="1"/>'
            '</Elements></Atlas>\n')


def main() -> None:
    inventory = ROOT / "images/inventoryimages"
    inventory.mkdir(parents=True, exist_ok=True)
    cookbook = ROOT / "images/cookbook"
    cookbook.mkdir(parents=True, exist_ok=True)
    (ROOT / "anim").mkdir(exist_ok=True)
    (ROOT / "art/processed").mkdir(parents=True, exist_ok=True)
    atlas = Image.new("RGBA", (1024, 256))
    preview = Image.new("RGBA", (900, 400), "#38332f")
    draw = ImageDraw.Draw(preview)
    for index, name in enumerate(NAMES):
        image = normalized(ROOT / f"art/source/{name}.png")
        image.save(ROOT / f"art/processed/{name}.png")
        atlas.alpha_composite(image, (index * 256, 0))
        # ItemTile uses native texture dimensions, so inventory art must be
        # 64x64. Keep full-resolution cookbook and world art independent.
        # Crop/fit directly from source, so broad bowl silhouettes occupy the
        # cell rather than inheriting the world texture's transparent padding.
        icon = normalized(ROOT / f"art/source/{name}.png", (64, 64), (62, 62))
        icon.save(ROOT / f"art/processed/{name}_inventory.png")
        (inventory / f"{name}.tex").write_bytes(texture(icon))
        (inventory / f"{name}.xml").write_text(atlas_xml(name), encoding="utf-8")
        (cookbook / f"{name}.tex").write_bytes(texture(image))
        (cookbook / f"{name}.xml").write_text(atlas_xml(name), encoding="utf-8")
        preview.alpha_composite(image, (index * 300 + 22, 0))
        preview.alpha_composite(icon, (index * 300 + 118, 270))
        draw.text((index * 300 + 105, 360), name.removeprefix("ta2bro_chicken_"), fill="#eee4cd")
    atlas.save(ROOT / "art/processed/atlas-0.png")
    preview.convert("RGB").save(ROOT / "art/preview.png")
    # Native-size comparison, generated only when local vanilla references exist.
    references = [ROOT / f"art/reference/{name}.png" for name in ("meatballs", "drumstick")]
    if all(path.exists() for path in references):
        comparison = Image.new("RGBA", (400, 100), "#29271f")
        slots = ImageDraw.Draw(comparison)
        icons = [Image.open(ROOT / f"art/processed/{name}_inventory.png").convert("RGBA") for name in NAMES]
        icons += [Image.open(path).convert("RGBA") for path in references]
        for i, item in enumerate(icons):
            slots.rectangle((i * 80 + 4, 4, i * 80 + 75, 75), fill="#657b40", outline="#aa9979", width=2)
            comparison.alpha_composite(item, (i * 80 + 8, 8))
        comparison.save(ROOT / "art/inventory_preview.png")
    with ZipFile(ROOT / "anim/ta2bro_chicken.zip", "w", ZIP_DEFLATED) as archive:
        for name, data in [("build.bin", build_binary()), ("atlas-0.tex", texture(atlas))]:
            info = ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, data)
    icon = normalized(ROOT / "art/source/ta2bro_chicken_spicy.png")
    (ROOT / "modicon.tex").write_bytes(texture(icon))
    (ROOT / "modicon.xml").write_text(atlas_xml("modicon"), encoding="utf-8")
    print("Built three food atlases, animation symbol build, mod icon and art/preview.png")


if __name__ == "__main__":
    main()
