# Publicador de YouTube

Sube cada episodio con su miniatura, título, descripción, etiquetas y fecha programada, todo tomado de `episodios/NNN-slug/ficha.json`. Sirve para varios canales: cada ficha dice a qué canal va (`"canal": "cuantolequeda"`).

Las credenciales **nunca entran al repo**. Viven en tu computador, en `~/.config/publicador-youtube/`.

## Configuración (una sola vez, ~15 min)

### 1. Crear el proyecto en Google Cloud

1. Entra a https://console.cloud.google.com/ con tu cuenta de Google (la misma que administra los canales, idealmente).
2. Arriba, en el selector de proyectos → **Proyecto nuevo**. Nombre: `Publicador YouTube Ricardo`. Crear y seleccionarlo.

### 2. Activar la API

1. Menú → **APIs y servicios** → **Biblioteca**.
2. Busca **YouTube Data API v3** → **Habilitar**.

### 3. Configurar la pantalla de consentimiento

1. Menú → **APIs y servicios** → **Pantalla de consentimiento de OAuth** (en la consola nueva aparece como **Google Auth Platform**).
2. Tipo de usuario: **Externo**. Nombre de la app: `Publicador YouTube Ricardo`. Correo de asistencia y de contacto: el tuyo.
3. En **Permisos** (Data Access / Scopes) no hace falta agregar nada: el script los pide solo.
4. En **Público** (Audience), agrega tu correo como usuario de prueba y luego presiona **Publicar app** para pasarla a **En producción**.
   - **Ojo:** si la dejas en modo de prueba, la autorización vence cada 7 días.
   - No pidas la verificación de Google. La app queda "no verificada", y eso está bien para uso propio.

### 3b. Información de la marca (para pasar a producción)

Las páginas están en `publicador/` del repo, servidas por GitHub Pages:

- Página principal: https://ricardocerdarojas.github.io/faceless-youtube/publicador/
- Política de privacidad: https://ricardocerdarojas.github.io/faceless-youtube/publicador/privacidad.html
- Condiciones: https://ricardocerdarojas.github.io/faceless-youtube/publicador/terminos.html
- Dominio autorizado: `ricardocerdarojas.github.io`

Después de publicar la app, vuelve a ejecutar `autorizar`: las autorizaciones dadas en modo Prueba siguen venciendo a los 7 días.

### 4. Crear la credencial

1. **APIs y servicios** → **Credenciales** → **Crear credenciales** → **ID de cliente de OAuth**.
2. Tipo de aplicación: **App de escritorio**. Nombre: `publicar.py`.
3. **Descargar JSON**, renómbralo como `client_secret.json` y muévelo a:

```bash
mkdir -p ~/.config/publicador-youtube
mv ~/Downloads/client_secret_*.json ~/.config/publicador-youtube/client_secret.json
chmod 600 ~/.config/publicador-youtube/client_secret.json
```

### 5. Instalar dependencias

```bash
cd ~/dev/faceless-youtube && git pull
python3 -m venv .venv && source .venv/bin/activate
pip install -r tools/publicar/requirements.txt
```

### 6. Autorizar el canal

```bash
python3 tools/publicar/publicar.py autorizar cuantolequeda
```

Se abre el navegador:
- Elige tu cuenta. Si administras varios canales, elige **¿Cuánto Le Queda?**.
- Aparece "Google no verificó esta app": **Configuración avanzada** → **Ir a Publicador YouTube Ricardo (no seguro)**. Es tu propia app.
- Acepta los permisos.

El script termina diciendo a qué canal quedó conectado. Revisa que sea el correcto. Para otro canal, repite este paso con otro nombre (`autorizar dosfilos`) y pon ese nombre en el campo `canal` de sus fichas.

### 7. Verificar el canal por teléfono

Para subir miniaturas propias, el canal tiene que estar verificado: https://www.youtube.com/verify. Si no lo está, el video se sube igual y el script avisa que faltó la miniatura.

## Personalizar el canal

```bash
python3 tools/publicar/publicar.py personalizar cuantolequeda --simular   # muestra lo que haría
python3 tools/publicar/publicar.py personalizar cuantolequeda
```

Aplica la descripción, las palabras clave, el país, el idioma y el banner desde `canales/<canal>.json`. La foto de perfil no se puede cambiar por API: se sube a mano en Studio → Personalización → Imagen de marca (`avatar_url` del mismo archivo).

`canales/<canal>.json` guarda además el `canal_id`. Si una autorización apunta a otro canal, el script se detiene antes de tocar nada.

## Uso

```bash
# Revisar fichas sin subir nada (largos, fechas, campos que faltan)
python3 tools/publicar/publicar.py revisar episodios/00*

# Subir y programar
python3 tools/publicar/publicar.py subir episodios/001-gasolinera episodios/002-pasteleria-casa
```

Cada video queda **privado y programado** para la hora de `publicar_en` (hora de CDMX, `-06:00`). Al terminar, el script escribe `publicado.json` en la carpeta del episodio. Haz commit de ese archivo: así no se sube dos veces y queda el enlace en el repo.

**Cuota:** cada subida cuesta 1 de las 100 diarias del proyecto, compartidas entre todos los canales. La miniatura y la lista de reproducción usan la cuota general de 10.000 unidades.

## Lo que queda manual en YouTube Studio

- **Pantalla final**: la API no la permite. Agrega el video sugerido y el botón de suscripción en los últimos 6 segundos.
- **Revisar que todo quedó bien** antes de la hora de publicación: miniatura, capítulos y el aviso de uso de IA.

## Campos de `ficha.json`

| Campo | Qué es |
|---|---|
| `canal` | Nombre del token autorizado (`cuantolequeda`) |
| `titulo` | Máx. 100 caracteres, sin número de episodio |
| `descripcion` | Con capítulos y fuentes, máx. 5.000 bytes, sin `<` ni `>` |
| `etiquetas` | Lista, máx. 500 caracteres en total |
| `publicar_en` | Fecha ISO con zona horaria, ej. `2026-11-09T18:00:00-06:00` |
| `video_url`, `miniatura_url` | Enlaces de Higgsfield (miniatura ≤ 2 MB) |
| `categoria` | 27 = Educación |
| `contenido_sintetico` | Aviso de contenido alterado o sintético. `false` en este canal: solo va `true` si hay personas reales imitadas, grabaciones reales alteradas, escenas fotorrealistas que no ocurrieron o música generada como foco |
| `playlist_id` | Opcional: lista donde se agrega el video |
