#!/usr/bin/env python3
"""Publicador de YouTube para varios canales.

Sube un episodio (video + miniatura + metadatos) desde su ficha.json y lo deja
programado. Las credenciales viven fuera del repo, en ~/.config/publicador-youtube/
(o en la carpeta que indique PUBLICADOR_YT_DIR):

    client_secret.json      credencial OAuth del proyecto de Google Cloud
    tokens/<canal>.json     autorización de cada canal (la crea `autorizar`)

Uso:
    python3 tools/publicar/publicar.py autorizar cuantolequeda
    python3 tools/publicar/publicar.py revisar episodios/001-gasolinera
    python3 tools/publicar/publicar.py subir episodios/001-gasolinera
    python3 tools/publicar/publicar.py subir episodios/00*            (varios)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",  # para miniaturas y leer el canal
]
CONFIG = Path(os.environ.get("PUBLICADOR_YT_DIR", Path.home() / ".config" / "publicador-youtube"))


# ---------------------------------------------------------------- credenciales
def _client_secret() -> Path:
    p = CONFIG / "client_secret.json"
    if not p.exists():
        sys.exit(f"Falta {p}. Descarga la credencial OAuth (Aplicación de escritorio) y guárdala ahí.")
    return p


def _token_path(canal: str) -> Path:
    return CONFIG / "tokens" / f"{canal}.json"


def autorizar(canal: str) -> None:
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(str(_client_secret()), SCOPES)
    print("Se abrirá el navegador. Elige la cuenta y, si te lo pregunta, el canal correcto.")
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    tp = _token_path(canal)
    tp.parent.mkdir(parents=True, exist_ok=True)
    tp.write_text(creds.to_json())
    os.chmod(tp, 0o600)
    yt = _servicio(canal)
    ch = yt.channels().list(part="snippet", mine=True).execute()["items"][0]
    _verificar_canal(canal, ch["id"])
    print(f"Listo: '{canal}' quedó autorizado para el canal «{ch['snippet']['title']}» ({ch['id']}).")


def _servicio(canal: str):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    tp = _token_path(canal)
    if not tp.exists():
        sys.exit(f"El canal '{canal}' no está autorizado. Ejecuta: publicar.py autorizar {canal}")
    creds = Credentials.from_authorized_user_file(str(tp), SCOPES)
    if not creds.valid:
        creds.refresh(Request())
        tp.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def _verificar_canal(canal: str, canal_id: str) -> None:
    cfg = Path(__file__).resolve().parents[2] / "canales" / f"{canal}.json"
    if cfg.exists():
        esperado = json.loads(cfg.read_text()).get("canal_id")
        if esperado and esperado != canal_id:
            sys.exit(f"La autorización '{canal}' apunta al canal {canal_id}, pero se esperaba {esperado}. "
                     f"Vuelve a ejecutar: publicar.py autorizar {canal}")


# ---------------------------------------------------------------- fichas
def cargar_ficha(carpeta: Path) -> dict:
    p = carpeta / "ficha.json"
    if not p.exists():
        sys.exit(f"No existe {p}")
    return json.loads(p.read_text())


def validar(f: dict) -> list[str]:
    err: list[str] = []
    for k in ("canal", "titulo", "descripcion", "video_url", "miniatura_url", "publicar_en"):
        if not f.get(k):
            err.append(f"falta '{k}'")
    if len(f.get("titulo", "")) > 100:
        err.append(f"título de {len(f['titulo'])} caracteres (máx. 100)")
    if len(f.get("descripcion", "").encode()) > 5000:
        err.append("descripción sobre 5.000 bytes")
    for campo in ("titulo", "descripcion"):
        if "<" in f.get(campo, "") or ">" in f.get(campo, ""):
            err.append(f"'{campo}' no puede tener < ni >")
    tags = f.get("etiquetas", [])
    largo_tags = sum(len(t) + (2 if " " in t else 0) for t in tags) + max(len(tags) - 1, 0)
    if largo_tags > 500:
        err.append(f"etiquetas suman {largo_tags} caracteres (máx. 500)")
    try:
        cuando = datetime.fromisoformat(f["publicar_en"])
        if cuando.tzinfo is None:
            err.append("publicar_en debe incluir zona horaria (ej. 2026-11-09T18:00:00-06:00)")
        elif cuando <= datetime.now(timezone.utc):
            err.append(f"publicar_en ({f['publicar_en']}) ya pasó")
    except (KeyError, ValueError):
        err.append("publicar_en no es una fecha ISO válida")
    return err


def _cuerpo(f: dict) -> dict:
    cuando = datetime.fromisoformat(f["publicar_en"]).astimezone(timezone.utc)
    return {
        "snippet": {
            "title": f["titulo"],
            "description": f["descripcion"],
            "tags": f.get("etiquetas", []),
            "categoryId": str(f.get("categoria", 27)),
            "defaultLanguage": f.get("idioma", "es"),
            "defaultAudioLanguage": f.get("idioma_audio", "es-419"),
        },
        "status": {
            "privacyStatus": "private",  # obligatorio para programar con publishAt
            "publishAt": cuando.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": bool(f.get("contenido_sintetico", True)),
            "embeddable": True,
            "license": "youtube",
        },
    }


def _bajar(url: str, destino: Path) -> Path:
    print(f"  bajando {url.rsplit('/', 1)[-1]} …")
    urllib.request.urlretrieve(url, destino)
    return destino


# ---------------------------------------------------------------- acciones
def revisar(carpeta: Path) -> bool:
    f = cargar_ficha(carpeta)
    err = validar(f)
    estado = "OK" if not err else "ERROR"
    print(f"[{estado}] {carpeta.name} → canal '{f.get('canal')}', {f.get('publicar_en')}")
    print(f"        {f.get('titulo')}")
    for e in err:
        print(f"        - {e}")
    if (carpeta / "publicado.json").exists():
        print(f"        (ya publicado: {json.loads((carpeta / 'publicado.json').read_text())['url']})")
    return not err


def subir(carpeta: Path, forzar: bool = False) -> None:
    from googleapiclient.http import MediaFileUpload

    f = cargar_ficha(carpeta)
    registro = carpeta / "publicado.json"
    if registro.exists() and not forzar:
        print(f"{carpeta.name}: ya se subió ({json.loads(registro.read_text())['url']}). Usa --forzar para repetir.")
        return
    err = validar(f)
    if err:
        sys.exit(f"{carpeta.name}: la ficha tiene errores:\n  - " + "\n  - ".join(err))

    yt = _servicio(f["canal"])
    ch = yt.channels().list(part="snippet", mine=True).execute()["items"][0]
    _verificar_canal(f["canal"], ch["id"])
    print(f"{carpeta.name} → «{ch['snippet']['title']}», programado para {f['publicar_en']}")

    with tempfile.TemporaryDirectory() as tmp:
        video = _bajar(f["video_url"], Path(tmp) / "video.mp4")
        mini = _bajar(f["miniatura_url"], Path(tmp) / ("mini" + Path(f["miniatura_url"]).suffix))

        media = MediaFileUpload(str(video), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
        req = yt.videos().insert(part="snippet,status", body=_cuerpo(f), media_body=media, notifySubscribers=True)
        resp = None
        while resp is None:
            estado, resp = req.next_chunk()
            if estado:
                print(f"  subiendo video: {int(estado.progress() * 100)} %", end="\r")
        vid = resp["id"]
        print(f"\n  video subido: https://youtu.be/{vid}")

        aviso = None
        try:
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(mini))).execute()
            print("  miniatura lista")
        except Exception as e:  # suele fallar si el canal no está verificado por teléfono
            aviso = f"miniatura no subida: {e}"
            print(f"  AVISO: {aviso}")

        if f.get("playlist_id"):
            yt.playlistItems().insert(part="snippet", body={"snippet": {
                "playlistId": f["playlist_id"], "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
            print("  agregado a la lista de reproducción")

    registro.write_text(json.dumps({
        "video_id": vid, "url": f"https://youtu.be/{vid}", "canal": f["canal"],
        "canal_id": ch["id"], "publicar_en": f["publicar_en"],
        "subido": datetime.now(timezone.utc).isoformat(timespec="seconds"), "aviso": aviso,
    }, ensure_ascii=False, indent=2) + "\n")
    print(f"  registro en {registro} (haz commit para que quede en el repo)")


def personalizar(canal: str, simular: bool = False) -> None:
    """Aplica descripción, palabras clave, país, idioma y banner desde canales/<canal>.json."""
    from googleapiclient.http import MediaFileUpload

    raiz = Path(__file__).resolve().parents[2]
    cfg = json.loads((raiz / "canales" / f"{canal}.json").read_text())
    kw = " ".join(f'"{k}"' if " " in k else k for k in cfg.get("palabras_clave", []))
    if len(cfg.get("descripcion", "").encode()) > 1000:
        sys.exit("La descripción del canal supera 1.000 caracteres.")
    if simular:
        print(json.dumps({"descripcion": cfg["descripcion"], "keywords": kw, "pais": cfg.get("pais"),
                          "idioma": cfg.get("idioma"), "banner": cfg.get("banner_url")}, ensure_ascii=False, indent=2))
        return

    yt = _servicio(canal)
    ch = yt.channels().list(part="brandingSettings", mine=True).execute()["items"][0]
    _verificar_canal(canal, ch["id"])
    print(f"Canal «{ch['brandingSettings']['channel'].get('title')}» ({ch['id']})")
    bs = ch["brandingSettings"]
    bs.setdefault("channel", {})
    bs["channel"]["description"] = cfg["descripcion"]
    bs["channel"]["keywords"] = kw
    if cfg.get("pais"):
        bs["channel"]["country"] = cfg["pais"]
    if cfg.get("idioma"):
        bs["channel"]["defaultLanguage"] = cfg["idioma"]

    if cfg.get("banner_url"):
        with tempfile.TemporaryDirectory() as tmp:
            b = _bajar(cfg["banner_url"], Path(tmp) / ("banner" + Path(cfg["banner_url"]).suffix))
            r = yt.channelBanners().insert(media_body=MediaFileUpload(str(b))).execute()
            bs.setdefault("image", {})["bannerExternalUrl"] = r["url"]
            print("  banner subido")

    yt.channels().update(part="brandingSettings", body={"id": ch["id"], "brandingSettings": bs}).execute()
    print("  descripción, palabras clave, país e idioma actualizados")
    print("  Falta a mano: foto de perfil (Studio → Personalización → Imagen de marca).")


def main() -> None:
    ap = argparse.ArgumentParser(description="Publicador de YouTube para varios canales")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("autorizar", help="autoriza un canal (una vez por canal)")
    a.add_argument("canal", help="nombre corto del canal, ej. cuantolequeda")
    r = sub.add_parser("revisar", help="valida fichas sin subir nada")
    r.add_argument("carpetas", nargs="+", type=Path)
    s = sub.add_parser("subir", help="sube y programa episodios")
    s.add_argument("carpetas", nargs="+", type=Path)
    s.add_argument("--forzar", action="store_true", help="vuelve a subir aunque exista publicado.json")
    p = sub.add_parser("personalizar", help="aplica descripción, palabras clave, país y banner del canal")
    p.add_argument("canal")
    p.add_argument("--simular", action="store_true", help="muestra lo que aplicaría sin tocar el canal")
    args = ap.parse_args()

    if args.cmd == "autorizar":
        autorizar(args.canal)
    elif args.cmd == "personalizar":
        personalizar(args.canal, args.simular)
    elif args.cmd == "revisar":
        ok = [revisar(c) for c in args.carpetas]
        sys.exit(0 if all(ok) else 1)
    else:
        for c in args.carpetas:
            subir(c, args.forzar)


if __name__ == "__main__":
    main()
