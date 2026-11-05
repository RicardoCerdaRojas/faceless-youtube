# Guía visual del canal

Estilo validado el 5 de noviembre de 2026: **grabado de billete, sin marco de billete**.

## Paleta

| Uso | Color | Hex (aprox.) |
|---|---|---|
| Tinta principal | Verde botella profundo | `#1D3B2C` |
| Papel | Crema cálido | `#F3EAD3` |
| Acento (un solo elemento por imagen) | Naranja cálido | `#E2671F` |

Regla: el naranja se usa en **un solo elemento** por imagen, el que importa en esa escena (la luz del techo, el combustible, el pastel, la moneda). Es la "flecha" visual del canal.

## Prompt base (bloque de estilo)

Se antepone a cada descripción de escena:

```
Fine intaglio steel-plate engraving illustration: precise parallel hatching, cross-hatching and stippled shading, deep bottle-green ink on warm cream paper, a single warm orange accent used only on {ELEMENTO}. Full-bleed composition fading softly into the paper at the edges. NO ornamental frame, NO border, NO guilloche, NO lettering, NO numbers, not a banknote or certificate layout, no logos.
```

Variante para explicar "cómo funciona":

```
... Isometric cutaway view at 30 degrees, like an engraved technical plate from an old encyclopedia: {ESCENA}, sliced open to reveal {LO QUE NO SE VE}. Thin leader lines pointing to parts but WITHOUT any text or labels.
```

Variante para miniaturas:

```
YouTube thumbnail background in a bold, high-contrast intaglio engraving style: heavy confident hatching, very dark bottle-green ink on bright cream paper, with a single saturated orange accent. Composition designed to read at small sizes: {SUJETO} on the right half. The left 45 percent of the frame is mostly empty cream paper, reserved for headline text added later. NO text, NO lettering, NO numbers, NO frame, no logos.
```

## Reglas

- Nada de texto generado por IA dentro de las imágenes. Los rótulos, cifras y títulos se agregan por código (las líneas guía del corte isométrico quedan vacías a propósito para eso).
- Evitar marcos ornamentales y diseño de billete: se ven como dinero real e inventan letras falsas.
- Personas: dignas y concentradas, nunca caricaturizadas. Toques mexicanos sutiles (bordados, azulejos, palmeras), sin clichés.
- Composición: el sujeto en el centro o en el tercio derecho, con aire alrededor para el movimiento de cámara (zoom y paneo lentos).

## Gráficos de datos (por código)

- Mismos tres colores; números grandes en tipografía condensada pesada (Anton), textos de apoyo en serif (Source Serif 4).
- Fondo crema con textura de papel; las cifras clave en naranja.
- Toda cifra estimada lleva la etiqueta "estimación".

## Miniaturas

- Titular en 2 líneas: la cifra en verde y la pregunta en naranja, en el 40 % izquierdo.
- Probar legibilidad a 168 px de ancho (tamaño de la lista de recomendados en el celular) antes de publicar.

## Imágenes de referencia (Higgsfield)

- Gasolinera de noche: job `080e0143-befb-4da4-9b25-9d3d5ce2db5a`
- Gasolinera en corte isométrico: job `8c982bf0-0720-4c8d-be38-c2ac3ddc5725`
- Cocina con pastel: job `722c89f0-e82b-447f-9105-b85b42664a25`
- Miniatura (manguera y moneda): job `9e41aaef-75e0-42cc-a0e5-b7672a40d530`

Estas imágenes se pueden pasar como referencia de estilo en nuevas generaciones para mantener la consistencia.
