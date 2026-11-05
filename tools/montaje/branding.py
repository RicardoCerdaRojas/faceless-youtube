"""Genera avatar (2 direcciones) y banner del canal ¿Cuánto Le Queda?

Uso: python3 branding.py <moneda.png> <panorama.png> <carpeta_salida>
Requiere fonts/anton.ttf y fonts/serif.ttf (los descarga render.py).
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

VERDE, NARANJA, CREMA = (29, 59, 44), (226, 103, 31), (243, 234, 211)


def anton(t):
    return ImageFont.truetype("fonts/anton.ttf", t)


def serif(t, peso=500):
    f = ImageFont.truetype("fonts/serif.ttf", t)
    try:
        f.set_variation_by_axes([peso])
    except Exception:
        pass
    return f


def cubrir(img, w, h):
    r = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * r + 1), int(img.height * r + 1)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def centrar(d, y, txt, f, col, W):
    w = d.textlength(txt, font=f)
    d.text(((W - w) / 2, y), txt, font=f, fill=col)


def avatar_grabado(moneda, out):
    S = 800
    img = cubrir(Image.open(moneda).convert("RGB"), S, S)
    d = ImageDraw.Draw(img)
    f = anton(330)
    txt = "¿?"
    bb = d.textbbox((0, 0), txt, font=f)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    x, y = (S - w) / 2 - bb[0], (S - h) / 2 - bb[1]
    # contorno crema para que el signo se lea sobre la moneda
    d.text((x, y), txt, font=f, fill=VERDE, stroke_width=10, stroke_fill=CREMA)
    img.save(out, quality=95)


def avatar_tipografico(out):
    S = 800
    img = Image.new("RGB", (S, S), CREMA)
    d = ImageDraw.Draw(img)
    d.ellipse([40, 40, S - 40, S - 40], outline=VERDE, width=14)
    centrar(d, 150, "¿CUÁNTO", anton(150), VERDE, S)
    centrar(d, 320, "LE", anton(150), NARANJA, S)
    centrar(d, 490, "QUEDA?", anton(150), VERDE, S)
    img.save(out, quality=95)


def banner(panorama, out):
    W, H = 2560, 1440
    img = cubrir(Image.open(panorama).convert("RGB"), W, H)
    # banda crema en la zona segura (1546 x 423 al centro)
    zona_w, zona_h = 1700, 470
    x0, y0 = (W - zona_w) // 2, (H - zona_h) // 2
    capa = Image.new("L", (W, H), 0)
    ImageDraw.Draw(capa).rounded_rectangle([x0, y0, x0 + zona_w, y0 + zona_h], radius=30, fill=235)
    capa = capa.filter(ImageFilter.GaussianBlur(30))
    img = Image.composite(Image.new("RGB", (W, H), CREMA), img, capa)
    d = ImageDraw.Draw(img)
    centrar(d, y0 + 60, "¿Cuánto Le Queda?", anton(200), VERDE, W)
    centrar(d, y0 + 320, "Cómo ganan dinero los negocios, con números de verdad", serif(58, 600), NARANJA, W)
    img.save(out, quality=92)


if __name__ == "__main__":
    moneda, panorama, carpeta = sys.argv[1:4]
    os.makedirs(carpeta, exist_ok=True)
    avatar_grabado(moneda, f"{carpeta}/avatar-grabado.png")
    avatar_tipografico(f"{carpeta}/avatar-tipografico.png")
    banner(panorama, f"{carpeta}/banner.jpg")
