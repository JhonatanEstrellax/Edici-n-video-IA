# Invitación de cumpleaños — personaje animado sobre video existente

Agrega un personaje (a partir de 3 imágenes de referencia) a una invitación ya editada de `1080x1920 @ 30 fps`,
integrándolo en cada escena **sin tapar textos, fotos ni los animalitos** y sin tocar el audio.

Motor: recorte con `numpy + Pillow` → animación `HTML + GSAP` renderizada en Chromium (Playwright) → composición con FFmpeg.

## Uso

```bash
# flujo completo (recorte + medición del video + render + exportación)
python invitacion_cumple/build.py <invitacion_original.mp4> [salida.mp4]

# solo volver a renderizar tras editar overlay/config.json (posiciones, tamaños, tiempos)
python invitacion_cumple/build.py <invitacion_original.mp4> [salida.mp4] --solo-render
```

El video original y el resultado **no se versionan** (`*.mp4` está en `.gitignore`); se pasa la ruta por argumento.
Las imágenes de referencia del personaje tampoco se versionan: colócalas en `personaje/originales/` como
`saludo.jpg` (de pie saludando, fondo liso), `fiesta.jpg` (bailando, fondo desenfocado) y `gato.jpg`
(ilustración sobre blanco). Los recortes se generan en `personaje/recortes/`.

## Qué hace en cada escena

| Escena (s) | Acción del personaje | Clave en `config.json` |
|---|---|---|
| 0.6 – 3.5 «¡Te invito a mi cumple!» | Aparece con rebote delante del arco iris y saluda (mano articulada en la muñeca) | `s1` |
| 4.6 – 8.3 foto + nombre | Se asoma **por detrás** del marco circular de la foto, saluda y hace un «cucú» | `s2` |
| 11.3 – 13.1 «¡Ven a mi fiesta!» | Baila junto a la torta, con sombra de contacto en el piso | `s3` |
| 14.5 – 17.9 fecha y hora | Sticker (con el gatito) junto al calendario, con contorno blanco troquelado | `s4` |
| 19.3 – 22.7 dirección | Cae sobre el borde de la tarjeta y baila bajo la bola disco | `s5` |
| 23.9 – 27.5 «¡No faltes!» | Se asoma por detrás de la foto y se despide saludando | `s6` |

## Cómo se integra con el video

- **Ritmo:** la música va a 112 BPM y los cortes del video caen en esa grilla; las entradas y los saltos del
  baile usan el mismo compás (`bpm`, `beat0`).
- **Transiciones:** `tools/analizar_video.py` mide cuadro a cuadro el frente del barrido diagonal (recta
  `x = a·y + b`, error < 1 px) y la capa del personaje se recorta con esa misma recta, así el barrido lo tapa
  igual que al resto de la escena.
- **Fotos:** se sigue el centro y el radio del marco circular en cada cuadro (flota y «respira»); el personaje
  se enmascara con ese círculo y se mueve junto con la foto.
- **Tarjeta de dirección:** se sigue su borde superior (deriva unos 8 px) para que los pies queden apoyados.

## Estructura

- `personaje/originales/` — imágenes de referencia · `personaje/recortes/` — PNG con transparencia (ambas fuera de git).
- `tools/recortar_personaje.py`, `tools/matte.py` — recorte y mate con descontaminación de color.
- `tools/build_assets.py` — capas listas para animar (cuerpo, mano, sticker) en `overlay/assets/` (generado).
- `tools/analizar_video.py` — mediciones del video en `overlay/data/*.json`.
- `overlay/index.html` + `overlay/config.json` — animación (usa `templates/gsap.min.js`).
- `tools/render_overlay.js` — render de la capa con transparencia, cuadro a cuadro.

## Verificación de la exportación

- 825 cuadros, 27.5 s, H.264 High `yuv420p`; audio AAC copiado sin recomprimir (MD5 idéntico al original).
- Cuadros sin personaje: PSNR > 50 dB respecto al original.

> Si el personaje de las referencias pertenece a una franquicia con derechos de autor, el montaje es solo para
> uso personal/familiar (invitación), no para uso comercial ni para publicar las imágenes.
