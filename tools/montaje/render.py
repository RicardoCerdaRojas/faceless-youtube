#!/usr/bin/env python3
"""Monta un episodio a partir de escenas.json, urls-voz.json y urls-img.json.

Uso: python3 render.py <carpeta_episodio>
La carpeta debe contener escenas.json, urls-voz.json y urls-img.json.
Genera <carpeta>/out/final.mp4 y <carpeta>/out/miniatura.jpg.
"""
import json
import os
import random
import subprocess
import sys
import urllib.request

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
FPS = 30
VERDE = (29, 59, 44)
VERDE_SUAVE = (96, 122, 107)
VERDE_CLARO = (190, 199, 186)
CREMA = (243, 234, 211)
NARANJA = (226, 103, 31)
PAUSA = 0.45  # segundos de aire después de cada toma de voz

FONTS = {
    "anton": "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf",
    "serif": "https://github.com/google/fonts/raw/main/ofl/sourceserif4/SourceSerif4%5Bopsz%2Cwght%5D.ttf",
}


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def bajar(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return
    sh(f"curl -fsSL --retry 3 --retry-all-errors '{url}' -o '{path}'")


def duracion(path):
    out = subprocess.check_output(
        f"ffprobe -v error -show_entries format=duration -of csv=p=0 '{path}'", shell=True)
    return float(out.strip())


# ---------- tipografía ----------
_cache = {}


def fuente(nombre, tam, peso=None):
    key = (nombre, tam, peso)
    if key in _cache:
        return _cache[key]
    path = f"fonts/{nombre}.ttf"
    try:
        f = ImageFont.truetype(path, tam)
        if nombre == "serif":
            try:
                axes = f.get_variation_axes()
                vals = []
                for a in axes:
                    nm = a.get("name", b"")
                    nm = nm.decode() if isinstance(nm, bytes) else str(nm)
                    if "eight" in nm or nm.lower().startswith("wght"):
                        vals.append(max(a["minimum"], min(a["maximum"], peso or 500)))
                    else:
                        vals.append(max(a["minimum"], min(a["maximum"], 32)))
                f.set_variation_by_axes(vals)
            except Exception as ex:
                print("aviso fuente:", ex)
    except Exception:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", tam)
    _cache[key] = f
    return f


def envolver(draw, texto, font, ancho):
    palabras, lineas, actual = texto.split(), [], ""
    for p in palabras:
        prueba = (actual + " " + p).strip()
        if draw.textlength(prueba, font=font) <= ancho:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas


def texto_centrado(draw, y, texto, font, color, ancho=W - 320, interlinea=1.12):
    lineas = envolver(draw, texto, font, ancho)
    alto = font.size * interlinea
    for i, l in enumerate(lineas):
        w = draw.textlength(l, font=font)
        draw.text(((W - w) / 2, y + i * alto), l, font=font, fill=color)
    return y + len(lineas) * alto


# ---------- fondo de papel ----------
_papel = None


def papel():
    global _papel
    if _papel is None:
        crema = Image.new("RGB", (W, H), CREMA)
        ruido = Image.effect_noise((W, H), 40).convert("RGB").filter(ImageFilter.GaussianBlur(0.7))
        img = Image.blend(crema, ruido, 0.05)
        # viñeta suave: bordes un poco más oscuros
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).rectangle([120, 90, W - 120, H - 90], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(140))
        sombra = Image.blend(img, Image.new("RGB", (W, H), (200, 186, 152)), 0.6)
        _papel = Image.composite(img, sombra, mask)
    return _papel.copy()


def fuente_txt(draw, txt):
    if txt:
        draw.text((140, H - 90), txt, font=fuente("serif", 30), fill=VERDE_SUAVE)


def titulo_sup(draw, txt):
    f = fuente("serif", 54, 600)
    w = draw.textlength(txt, font=f)
    draw.text(((W - w) / 2, 110), txt, font=f, fill=VERDE)


# ---------- gráficos ----------
def graf(v):
    img = papel()
    d = ImageDraw.Draw(img)
    k = v["kind"]
    if k in ("titulo", "pregunta"):
        y = texto_centrado(d, 330, v["texto"], fuente("anton", 128), VERDE)
        texto_centrado(d, y + 40, v["sub"], fuente("serif", 56), NARANJA)
    elif k == "seccion":
        f = fuente("anton", 120)
        w = d.textlength(v["texto"], font=f)
        d.text(((W - w) / 2, 450), v["texto"], font=f, fill=VERDE)
        d.line([(W / 2 - 300, 420), (W / 2 + 300, 420)], fill=NARANJA, width=4)
        d.line([(W / 2 - 300, 620), (W / 2 + 300, 620)], fill=NARANJA, width=4)
    elif k == "barra":
        titulo_sup(d, v["titulo"])
        x0, x1, y0, y1 = 140, W - 140, 440, 600
        x = x0
        tonos = [VERDE, VERDE_SUAVE]
        for i, (nom, pct, foco) in enumerate(v["partes"]):
            ancho = (x1 - x0) * pct / 100
            color = NARANJA if foco else tonos[i % 2]
            if v.get("foco") and not foco:
                color = VERDE_CLARO
            d.rectangle([x, y0, x + ancho, y1], fill=color)
            f = fuente("serif", 40, 600)
            etiqueta = f"{nom}"
            pctxt = f"≈ {pct} %"
            ty = 640 if i % 2 == 0 or not foco else 640
            cx = x + ancho / 2
            if foco:
                d.text((x + ancho - d.textlength(pctxt, font=fuente("anton", 72)), y0 - 110), pctxt, font=fuente("anton", 72), fill=NARANJA)
                lw = d.textlength(etiqueta, font=f)
                d.text((x + ancho - lw, ty + 60), etiqueta, font=f, fill=NARANJA)
                d.line([(x + ancho / 2, y1 + 5), (x + ancho / 2, ty + 55)], fill=NARANJA, width=3)
            else:
                d.text((cx - d.textlength(pctxt, font=fuente("anton", 72)) / 2, y0 - 110), pctxt, font=fuente("anton", 72), fill=VERDE if not v.get("foco") else VERDE_SUAVE)
                lw = d.textlength(etiqueta, font=f)
                d.text((cx - lw / 2, ty), etiqueta, font=f, fill=VERDE if not v.get("foco") else VERDE_SUAVE)
            x += ancho
        fuente_txt(d, v.get("fuente"))
    elif k == "tabla":
        titulo_sup(d, v["titulo"])
        cols, filas = v["cols"], v["filas"]
        xs = [260, 760, 1160, 1560]
        fh = fuente("serif", 44, 600)
        for i, c in enumerate(cols):
            w = d.textlength(c, font=fh)
            d.text((xs[i] - (0 if i == 0 else w / 2), 300), c, font=fh, fill=VERDE_SUAVE)
        d.line([(200, 380), (W - 200, 380)], fill=VERDE, width=3)
        fn = fuente("anton", 110)
        fl = fuente("serif", 64, 700)
        for r, fila in enumerate(filas):
            y = 420 + r * 170
            for i, celda in enumerate(fila):
                if i == 0:
                    d.text((xs[0], y + 25), celda, font=fl, fill=VERDE)
                else:
                    txt = "$" + celda
                    w = d.textlength(txt, font=fn)
                    d.text((xs[i] - w / 2, y), txt, font=fn, fill=NARANJA if i == 3 else VERDE)
        fuente_txt(d, v.get("fuente"))
    elif k == "cifra":
        f = fuente("anton", 230)
        w = d.textlength(v["cifra"], font=f)
        d.text(((W - w) / 2, 270), v["cifra"], font=f, fill=NARANJA)
        texto_centrado(d, 600, v["texto"], fuente("serif", 64), VERDE)
        fuente_txt(d, v.get("fuente"))
    elif k == "cita":
        d.text((200, 160), "“", font=fuente("anton", 320), fill=NARANJA)
        y = 330
        for l in envolver(d, v["texto"], fuente("serif", 78, 600), W - 520):
            d.text((330, y), l, font=fuente("serif", 78, 600), fill=VERDE)
            y += 100
        fuente_txt(d, v.get("fuente"))
    elif k == "resta":
        fn, fl = fuente("anton", 150), fuente("serif", 50)
        filas = [(v["a"], v["a_txt"], VERDE, ""), (v["b"], v["b_txt"], VERDE, "−"), (v["r"], v["r_txt"], NARANJA, "=")]
        ys = [180, 380, 660]
        for (num, txt, col, signo), y in zip(filas, ys):
            w = d.textlength(num, font=fn)
            d.text((1000 - w, y), num, font=fn, fill=col)
            if signo:
                d.text((560, y), signo, font=fn, fill=col)
            d.text((1060, y + 80), txt, font=fl, fill=col)
        d.line([(560, 610), (1500, 610)], fill=VERDE, width=6)
        fuente_txt(d, v.get("fuente"))
    elif k == "concepto":
        y = 300
        for i, l in enumerate(v["lineas"]):
            col = NARANJA if i == len(v["lineas"]) - 1 else VERDE
            y = texto_centrado(d, y, l, fuente("anton", 110), col) + 30
    elif k == "umbral":
        titulo_sup(d, v["titulo"])
        x0, x1, ya = 180, W - 180, 560
        maxv = 500000
        px = lambda val: x0 + (x1 - x0) * val / maxv
        d.rectangle([x0, ya - 30, px(200000), ya + 30], fill=VERDE_CLARO)
        d.rectangle([px(200000), ya - 30, x1, ya + 30], fill=VERDE_SUAVE)
        for t in range(0, maxv + 1, 100000):
            d.line([(px(t), ya + 30), (px(t), ya + 50)], fill=VERDE, width=3)
            lab = "0" if t == 0 else f"{t // 1000} mil"
            fw = d.textlength(lab, font=fuente("serif", 34))
            d.text((px(t) - fw / 2, ya + 60), lab, font=fuente("serif", 34), fill=VERDE_SUAVE)
        for j, (val, lab) in enumerate(v["marcas"]):
            col = NARANJA if j == 2 else VERDE
            d.line([(px(val), ya - 30 - (60 if j != 1 else 0)), (px(val), ya + 30)], fill=col, width=6)
            f = fuente("serif", 40, 600)
            lw = d.textlength(lab, font=f)
            if j == 1:
                d.text((min(px(val) - lw / 2, W - 140 - lw), ya + 130), lab, font=f, fill=col)
            else:
                yy = 330 if j == 0 else 400
                d.text((max(140, min(px(val) - lw / 2, W - 140 - lw)), yy), lab, font=f, fill=col)
        fuente_txt(d, v.get("fuente"))
    elif k == "escenario":
        f = fuente("anton", 120)
        w = d.textlength(v["nombre"], font=f)
        d.text(((W - w) / 2, 120), v["nombre"], font=f, fill=VERDE)
        filas = [("Litros", v["litros"], VERDE), ("Ventas al mes", v["ventas"], VERDE), ("Al dueño le queda", v["gana"], NARANJA)]
        for i, (a, b, col) in enumerate(filas):
            y = 360 + i * 170
            d.text((260, y + 20), a, font=fuente("serif", 52), fill=VERDE_SUAVE)
            fb = fuente("anton", 90)
            if d.textlength(b, font=fb) > 900:
                fb = fuente("anton", 70)
            bw = d.textlength(b, font=fb)
            d.text((W - 260 - bw, y), b, font=fb, fill=col)
            d.line([(260, y + 140), (W - 260, y + 140)], fill=VERDE_CLARO, width=2)
        fuente_txt(d, v.get("fuente"))
    elif k == "proporcion":
        titulo_sup(d, v["titulo"])
        lado, gap = 44, 12
        gx = (W - (20 * lado + 19 * gap)) / 2
        for i in range(100):
            r, c = divmod(i, 20)
            x, y = gx + c * (lado + gap), 300 + r * (lado + gap)
            box = [x, y, x + lado, y + lado]
            if i < 1:
                d.rectangle(box, fill=NARANJA)
            elif i < 4:
                d.rectangle(box, outline=NARANJA, width=5)
            else:
                d.rectangle(box, fill=VERDE_CLARO)
        texto_centrado(d, 680, v["texto"], fuente("anton", 76), NARANJA)
        fuente_txt(d, v.get("fuente"))
    elif k == "barras_h":
        titulo_sup(d, v["titulo"])
        maxv = max(x[1] for x in v["items"])
        for i, (nom, val) in enumerate(v["items"]):
            y = 300 + i * 160
            d.text((140, y + 20), nom, font=fuente("serif", 52, 600), fill=VERDE)
            x0 = 620
            x1 = x0 + (W - 420 - x0) * val / maxv
            col = NARANJA if i in (0, len(v["items"]) - 1) else VERDE_SUAVE
            d.rectangle([x0, y + 10, x1, y + 100], fill=col)
            d.text((x1 + 20, y + 10), f"${val:.1f}", font=fuente("anton", 80), fill=col)
        d.text((620, 950), v["unidad"], font=fuente("serif", 36), fill=VERDE_SUAVE)
        fuente_txt(d, v.get("fuente"))
    elif k == "plazo":
        titulo_sup(d, v["titulo"])
        x0, x1, y = 200, W - 200, 560
        px = lambda a: x0 + (x1 - x0) * a / 10
        d.line([(x0, y), (x1, y)], fill=VERDE, width=6)
        for a in range(0, 11):
            d.line([(px(a), y - 20), (px(a), y + 20)], fill=VERDE, width=4)
            lab = str(a)
            d.text((px(a) - d.textlength(lab, font=fuente("anton", 54)) / 2, y + 40), lab, font=fuente("anton", 54), fill=VERDE)
        d.rectangle([px(v["min"]), y - 60, px(v["max"]), y - 20], fill=NARANJA)
        d.text((x1 - 60, y + 110), "años", font=fuente("serif", 40), fill=VERDE_SUAVE)
        texto_centrado(d, 760, v["texto"], fuente("anton", 76), NARANJA)
        fuente_txt(d, v.get("fuente"))
    elif k == "final":
        foto = Image.open(f"img/{v['_imgfile']}").convert("RGB")
        foto = cubrir(foto, 960, H)
        img.paste(foto, (W - 960, 0))
        y = texto_centrado_izq(d, 380, v["texto"], fuente("serif", 56), NARANJA)
        texto_centrado_izq(d, y + 30, v["sub"], fuente("anton", 92), VERDE, ancho=780)
    return img


def texto_centrado_izq(draw, y, texto, font, color, ancho=780, x=120):
    alto = font.size * 1.12
    lineas = envolver(draw, texto, font, ancho)
    for i, l in enumerate(lineas):
        draw.text((x, y + i * alto), l, font=font, fill=color)
    return y + len(lineas) * alto


def cubrir(img, w, h):
    r = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * r + 1), int(img.height * r + 1)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


# ---------- clips ----------
def clip_desde_png(png, dur, salida, idx, zoom_out=False, sutil=False):
    frames = max(1, int(round(dur * FPS)))
    z0, z1 = (1.0, 1.035) if sutil else (1.0, 1.10)
    if zoom_out:
        z0, z1 = z1, z0
    paneos = ["iw/2-(iw/zoom/2)", "(iw-iw/zoom)*on/{f}", "(iw-iw/zoom)*(1-on/{f})"]
    px = paneos[idx % 3].format(f=frames) if not sutil else paneos[0]
    zexpr = f"{z0}+({z1}-{z0})*on/{frames}"
    vf = (f"scale=2880:1620,zoompan=z='{zexpr}':x='{px}':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},"
          f"fade=t=in:st=0:d=0.35:color=0xF3EAD3,fade=t=out:st={max(0, dur - 0.35):.3f}:d=0.35:color=0xF3EAD3,format=yuv420p")
    sh(f"ffmpeg -y -loglevel error -loop 1 -i '{png}' -vf \"{vf}\" -t {dur:.3f} -r {FPS} -c:v libx264 -preset veryfast -crf 20 '{salida}'")


def main(carpeta):
    os.chdir(carpeta)
    for dd in ("voz", "img", "graf", "clips", "fonts", "out"):
        os.makedirs(dd, exist_ok=True)
    for n, u in FONTS.items():
        bajar(u, f"fonts/{n}.ttf")
    esc = json.load(open("escenas.json"))["escenas"]
    uv = json.load(open("urls-voz.json"))
    ui = json.load(open("urls-img.json"))

    lista_v, lista_a = [], []
    total = 0.0
    for e in esc:
        i = e["id"]
        if e["voz"]:
            bajar(uv[str(i)], f"voz/{i:02d}.mp3")
            dur_voz = duracion(f"voz/{i:02d}.mp3")
            dur = dur_voz + PAUSA
        else:
            dur = e["dur"]
        v = e["visual"]
        clip = f"clips/{i:02d}.mp4"
        if not os.path.exists(clip):
            if v["tipo"] == "img":
                bajar(ui[str(i)], f"img/{i:02d}.png")
                base = cubrir(Image.open(f"img/{i:02d}.png").convert("RGB"), W, H)
                base.save(f"graf/{i:02d}.png")
                clip_desde_png(f"graf/{i:02d}.png", dur, clip, i, zoom_out=v.get("zoom") == "out")
            else:
                if v["kind"] == "final":
                    bajar(ui[str(i)], f"img/{i:02d}.png")
                    v["_imgfile"] = f"{i:02d}.png"
                graf(v).save(f"graf/{i:02d}.png")
                clip_desde_png(f"graf/{i:02d}.png", dur, clip, i, sutil=True)
        # audio de la escena con duración exacta del clip
        aud = f"clips/{i:02d}.wav"
        if e["voz"]:
            sh(f"ffmpeg -y -loglevel error -i 'voz/{i:02d}.mp3' -af apad -t {dur:.3f} -ar 48000 -ac 2 '{aud}'")
        else:
            sh(f"ffmpeg -y -loglevel error -f lavfi -i anullsrc=r=48000:cl=stereo -t {dur:.3f} '{aud}'")
        lista_v.append(f"file '{clip}'")
        lista_a.append(f"file '{aud}'")
        total += dur
        print(f"escena {i:02d}: {dur:.1f}s", flush=True)

    open("clips/v.txt", "w").write("\n".join(l.replace("clips/", "") for l in lista_v))
    open("clips/a.txt", "w").write("\n".join(l.replace("clips/", "") for l in lista_a))
    sh("ffmpeg -y -loglevel error -f concat -safe 0 -i clips/v.txt -c copy out/video.mp4")
    sh("ffmpeg -y -loglevel error -f concat -safe 0 -i clips/a.txt -c:a pcm_s16le out/audio.wav")
    sh("ffmpeg -y -loglevel error -i out/video.mp4 -i out/audio.wav -map 0:v -map 1:a -c:v copy "
       "-af loudnorm=I=-16:TP=-1.5:LRA=11 -c:a aac -b:a 192k -shortest out/final.mp4")
    print(f"TOTAL {total:.1f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
