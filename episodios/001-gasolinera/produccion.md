# Producción del piloto 001 · Gasolinera

Producido el 5 de noviembre de 2026.

## Resultado

- Duración: 7 min 17 s (40 escenas)
- Video: https://d2ol7oe51mr4n9.cloudfront.net/user_3F8cx5xOQu3xSorE9KYyIyN9Uez/bdd07601-ad9f-4b3e-92ad-714301b01d0a.mp4
- Miniatura: https://d2ol7oe51mr4n9.cloudfront.net/user_3F8cx5xOQu3xSorE9KYyIyN9Uez/bfd06f11-03b1-4c4b-86b6-7ae9e188aac0.jpg

## Costo real en créditos de Higgsfield

| Parte | Créditos |
|---|---|
| Narración (38 tomas, Andre/ElevenLabs) | ~40 |
| Imágenes nuevas (15 + 2 regeneradas) | ~34 |
| Imágenes reutilizadas de la prueba de estilo (4) | 0 |
| Gráficos, montaje y miniatura (por código) | 0 |
| **Total del episodio** | **~56** (más las pruebas de voz) |

## Flujo

1. `escenas.json`: narración y visual de cada escena.
2. Narración con `text2speech_v2` (máximo ~6 tomas por llamada para evitar el límite de velocidad).
3. Imágenes con `nano_banana_pro` usando el prompt base de `guia-visual.md`.
4. `urls-voz.json` y `urls-img.json` con los resultados.
5. Montaje en el sandbox de Higgsfield con `tools/montaje/render.py` (descarga los JSON desde este repo).
6. Revisión: hoja de cuadros clave y transcripción con Whisper de las tomas con cifras.
7. Entrega: recompresión a CRF 26 (el archivo a CRF 20 pesaba 216 MB y la subida falló) y subida con `media_upload`.

## Aprendizajes

- El guion de ~1.170 palabras dio 7:17. Para pasar los 8 minutos (anuncios a mitad del video) hacen falta unas 1.300–1.400 palabras.
- El estilo grabado tiende a dibujar autos y personas de época; para escenas actuales hay que pedir explícitamente "present day, modern, 2020s".
- El montaje tarda unos 6 minutos en un sandbox XL; los comandos de espera deben ser cortos (menos de 60 s) para no cortar la conexión.
