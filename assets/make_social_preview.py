"""Generates assets/social-preview.png (1280x640) for the GitHub social
preview card, using the same cyberpunk palette as src/movie_box/tui/theme.py.

Run: python assets/make_social_preview.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 640
ASSETS = Path(__file__).parent
FONTS = Path("C:/Windows/Fonts")

BG = (0, 0, 0)
SURFACE_LIFT = (24, 24, 27)
TEXT = (245, 243, 255)
MUTED = (139, 135, 149)
NEON = (217, 70, 239)
NEON_HOT = (255, 122, 255)
NEON_SOFT = (192, 132, 252)
VIOLET = (139, 92, 246)
BLUE = (56, 189, 248)
GRADIENT = [NEON_HOT, NEON, NEON_SOFT, VIOLET, BLUE]

title_font = ImageFont.truetype(str(FONTS / "consolab.ttf"), 118)
subtitle_font = ImageFont.truetype(str(FONTS / "consolaz.ttf"), 42)
code_font = ImageFont.truetype(str(FONTS / "consolab.ttf"), 30)
footer_font = ImageFont.truetype(str(FONTS / "consola.ttf"), 20)


def horizontal_gradient(size, colors):
    grad = Image.new("RGB", (len(colors), 1))
    grad.putdata(colors)
    grad = grad.resize(size, Image.BILINEAR)
    return grad


def text_mask(size, text, font, xy, anchor="mm"):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.text(xy, text, font=font, fill=255, anchor=anchor)
    return mask


def glow_layer(canvas_size, mask, color, radius, opacity):
    glow = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    tint = Image.new("RGBA", canvas_size, color + (0,))
    alpha = mask.point(lambda p: int(p * opacity))
    tint.putalpha(alpha)
    glow = Image.alpha_composite(glow, tint)
    return glow.filter(ImageFilter.GaussianBlur(radius))


def main():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Soft radial-ish glow behind the wordmark for depth.
    haze = Image.new("L", (W, H), 0)
    haze_draw = ImageDraw.Draw(haze)
    haze_draw.ellipse((W / 2 - 420, H / 2 - 260, W / 2 + 420, H / 2 + 260), fill=70)
    haze = haze.filter(ImageFilter.GaussianBlur(120))
    tint = Image.new("RGB", (W, H), (40, 10, 50))
    img = Image.composite(tint, img, haze)
    draw = ImageDraw.Draw(img)

    # Faint scanlines for the CRT/terminal feel.
    scan = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    scan_draw = ImageDraw.Draw(scan)
    for y in range(0, H, 3):
        scan_draw.line((0, y, W, y), fill=NEON + (10,))
    img = Image.alpha_composite(img.convert("RGBA"), scan).convert("RGB")

    title_xy = (W / 2, 230)
    mask = text_mask((W, H), "MOVIE-BOX", title_font, title_xy)
    glow = glow_layer((W, H), mask, NEON, radius=14, opacity=200)
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")

    grad = horizontal_gradient((W, H), GRADIENT)
    img.paste(grad, (0, 0), mask)

    draw = ImageDraw.Draw(img)
    draw.text(
        (W / 2, 320), "Be kind. Rewind.", font=subtitle_font, fill=NEON_SOFT,
        anchor="mm",
    )

    code_text = '$ pip install "movie-box-dl[cli]"'
    chip_w, chip_h = 700, 64
    chip_x0, chip_y0 = W / 2 - chip_w / 2, 410
    chip_x1, chip_y1 = chip_x0 + chip_w, chip_y0 + chip_h
    draw.rounded_rectangle(
        (chip_x0, chip_y0, chip_x1, chip_y1), radius=10,
        fill=SURFACE_LIFT, outline=NEON, width=2,
    )
    code_bbox = draw.textbbox((0, 0), code_text, font=code_font)
    code_w = code_bbox[2] - code_bbox[0]
    cursor_w = 16
    text_start_x = W / 2 - (code_w + cursor_w + 10) / 2
    text_y = (chip_y0 + chip_y1) / 2
    draw.text((text_start_x, text_y), code_text, font=code_font, fill=TEXT, anchor="lm")
    cursor_x0 = text_start_x + code_w + 10
    draw.rectangle(
        (cursor_x0, text_y - 18, cursor_x0 + cursor_w, text_y + 18), fill=NEON_HOT,
    )

    draw.text(
        (W - 36, H - 32), "github.com/parthmax2/movie-box",
        font=footer_font, fill=MUTED, anchor="rm",
    )
    draw.text(
        (36, H - 32), "no VLC. no ads. no late fees.",
        font=footer_font, fill=MUTED, anchor="lm",
    )

    out = ASSETS / "social-preview.png"
    img.save(out)
    print(f"wrote {out} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()
