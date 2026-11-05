# faceless-youtube

Herramientas para investigar, producir y hacer crecer un canal de YouTube sin presentador en cámara, trabajando con Claude y Higgsfield.

## Herramientas

| Herramienta | Qué hace | Enlace |
|---|---|---|
| Radar de Nichos | Busca los videos más vistos de un tema, mide sus canales (mediana de vistas, dependencia de virales, frecuencia, RPM estimado) y calcula un índice de automatización probable. | [Abrir](https://ricardocerdarojas.github.io/faceless-youtube/tools/radar-nichos/) |

## Seguridad de las keys

Ninguna herramienta guarda keys en este repositorio. La API key de YouTube y la de Anthropic se ingresan en la propia página y quedan solo en el navegador de quien la usa (`localStorage`).

Recomendaciones para la key de YouTube en Google Cloud:

- Restringirla solo a **YouTube Data API v3**.
- Si se quiere restringir por sitio web, agregar `https://ricardocerdarojas.github.io/*`.

## Estructura

```
tools/
  radar-nichos/   Buscador de nichos con la YouTube Data API v3
```

Cada herramienta nueva va en su propia carpeta dentro de `tools/`.
