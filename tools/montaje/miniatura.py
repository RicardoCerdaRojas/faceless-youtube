"""Compone la miniatura del episodio: ilustración a la derecha y titular en el panel crema de la izquierda.

Uso: python3 miniatura.py <imagen.png> "<línea verde>" "<línea naranja>" <salida.jpg>
Las fuentes se toman de fonts/ (las descarga render.py).
"""
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
VERDE, NARANJA, CREMA = (29, 59, 44), (226, 103, 31), (243, 234, 211)


def cubrir(img, w, h):
    r = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * r + 1), int(img.height * r + 1)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def ajustar(d, texto, ancho, tam_max, tam_min=60):
    for tam in range(tam_max, tam_min - 1, -4):
        f = ImageFont.truetype("fonts/anton.ttf", tam)
        lineas, linea = [], ""
        for p in texto.split():
            prueba = (linea + " " + p).strip()
            if d.textlength(prueba, font=f) <= ancho:
                linea = prueba
            else:
                lineas.append(linea)
                linea = p
        lineas.append(linea)
        if len(lineas) <= 2:
            return f, lineas
    return f, lineas


def main(src, l1, l2, out):
    base = cubrir(Image.open(src).convert("RGB"), W, H)
    # panel crema a la izquierda con borde difuminado
    panel = Image.new("RGB", (W, H), CREMA)
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    x_solido, x_fin = 520, 680
    md.rectangle([0, 0, x_solido, H], fill=255)
    for x in range(x_solido, x_fin):
        md.line([(x, 0), (x, H)], fill=int(255 * (1 - (x - x_solido) / (x_fin - x_solido))))
    img = Image.composite(panel, base, mask)
    d = ImageDraw.Draw(img)
    ancho = 520
    f1, a = ajustar(d, l1, ancho, 150)
    f2, b = ajustar(d, l2, ancho, 104)
    alto1, alto2 = f1.size * 1.08, f2.size * 1.1
    total = alto1 * len(a) + 24 + alto2 * len(b)
    y = (H - total) / 2 - 10
    for t in a:
        d.text((52, y), t, font=f1, fill=VERDE)
        y += alto1
    y += 24
    for t in b:
        d.text((52, y), t, font=f2, fill=NARANJA)
        y += alto2
    img.save(out, quality=92)


if __name__ == "__main__":
    main(*sys.argv[1:5])
