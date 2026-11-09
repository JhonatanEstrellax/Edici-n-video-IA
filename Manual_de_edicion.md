# Manual de Reglas de Edición Automática de Reels — Edición Oficial MascotaMás (`mascotamas.com`)

Este documento define las reglas de edición y el sistema de diseño oficial de **MascotaMás (`mascotamas.com`)** que aplica el sistema automático en cada ejecución. Todos los parámetros numéricos están sincronizados con `style.json`.

---

## 0. Identidad de Marca: MascotaMás (`mascotamas.com`)
- **Tipografías Oficiales (`fonts/`):**
  - **Títulos, Subtítulos y Métricas (`--font-display`):** `Poppins ExtraBold` (`fonts/Poppins-ExtraBold.ttf`) y `Poppins Bold` (`fonts/Poppins-Bold.ttf`).
  - **Cuerpo y Descripciones (`--font-sans`):** `Open Sans Bold` (`fonts/OpenSans-Bold.ttf`).
- **Paleta de Colores Oficial:**
  - **Fondo Oscuro Principal (`--color-bg-dark`):** `#1B1329` (con malla sutil y resplandor radial violeta).
  - **Tarjetas Glassmorphic:** `#251A38` con borde `1px solid rgba(190, 151, 255, 0.28)` y sombra `rgba(174, 76, 252, 0.14)`.
  - **Violeta Primario de Marca (`--color-primary`):** `#AE4CFC` (`#8A2BE2` dark).
  - **Acento Lavanda para Destacados (`--color-primary-light`):** `#BE97FF` / `#D8B8FF`.
  - **Positivo / Éxito (`--color-success`):** Esmeralda `#10B981`.
  - **Negativo / Alerta (`--color-danger`):** Rojo `#EF4444`.
- **Assets Oficiales Integrados (`assets/mascotamas/` — 76 archivos):**
  - **Logos:** `logo.png`, `logo_dark_bg.png` (`mascota` en blanco + `MÁS` en lavanda `#BE97FF`), `logo_white.png`, `favicon-192x192.png`.
  - **Mascota Animada (`peeking-creature`):** SVG interactivo de la criatura de MascotaMás asomándose en la esquina inferior derecha del panel gráfico con ojos y cejas animados con GSAP.
  - **Capturas Reales de la Plataforma Web & App PWA:** `escritorio_phone.jpg`, `agendas_phone.jpg`, `turnos_phone.jpg`, `hc_phone.jpg`, `reminders_phone.png`, `stats_phone.jpg`, `sala_espera_phone.jpg`, `tutores_phone.jpg`, `media_laptop_transparent.png`, `media_iphone_transparent.png`, `whatsapp_icon.png`.

---

## 1. Formato de Pantalla y Exportación
- **Resolución:** `1080x1920` (formato vertical 9:16).
- **Cuadros por segundo:** `30 fps`.
- **Calidad de exportación:** Compresión única al final del flujo (`libx264`, CRF 18, `yuv420p`) para evitar pérdida de calidad por recompresiones intermedias.
- **Intro y Outro:**
  - **Intro:** Comienza directamente en la primera palabra válida del guion (con margen de `0.05 s`), sin saludos iniciales ni logos de espera.
  - **Outro:** Finaliza exactamente `0.30 s` después de la última palabra del guion corregido.

---

## 2. Reglas de Corte y Selección de Tomas
- **Guion corregido:** Se conservan únicamente las palabras incluidas en el guion corregido. Prohibido alterar el contenido o el tono; solo se permite eliminar titubeos, repeticiones y silencios.
- **Tiempos y márgenes:**
  - **Pausa máxima entre oraciones:** `0.15 s`.
  - **Margen por palabra conservada:** `0.05 s` antes del inicio real de la voz y `0.05 s` después.
  - **Fundido cruzado (Crossfade) de audio:** `10 ms` en cada unión para evitar clics o cortes bruscos.
  - **Duración mínima de fragmento:** `0.12 s` (nunca se generan cortes menores a este umbral).
- **Limpieza de ruidos sin habla:** Se descartan todos los fragmentos menores a `0.60 s` que no contengan palabras (respiraciones, chasquidos de boca, aspiraciones nasales, miradas rápidas al guion).
- **Selección de tomas repetidas:** Cuando una misma frase se haya grabado varias veces, se elige de entre las **últimas tomas** aquella en la que:
  1. Se mire directamente a cámara.
  2. Se hable con mayor fuerza y claridad (mayor volumen RMS).
  3. Se descartan tomas susurradas o leyendo el guion con la vista baja.

---

## 3. Audio, Nivelación, Efectos de Sonido (SFX) y Música (BGM)
- **Nivelación de voz por secciones:** Ajuste dinámico entre segmentos con un aumento máximo de `+6 dB` y una reducción máxima de `-3 dB`.
- **Volumen maestro final:** Normalizado a `-14 LUFS` (True Peak `-1.0 dBTP`).
- **Efectos de sonido (SFX):**
  - `whoosh / swoosh`: Al cambiar de escena o de tema.
  - `pop`: En palabras destacadas con rebote (máximo 1 vez cada 4–6 segundos).
  - `ding`: Al aparecer el título de llamado a la acción (CTA) para comentar.
  - **Sincronización:** Se colocan `0.05 s` antes del inicio de la palabra/evento, respetando un espacio mínimo de `1.2 s` entre efectos de sonido.
- **Música de fondo (BGM):**
  - Ritmo suave posicionado aproximadamente `18 dB` por debajo de la voz, aplicando *ducking* adicional mientras se habla.
  - **Fade in:** `0.3 s` al inicio.
  - **Fade out:** `0.8 s` al final.
  - Si existe un archivo de audio en la carpeta `bgm/`, se utiliza automáticamente esa pista.

---

## 4. Cámara y Zoom Dinámico
- **Encuadre:** Rostro centrado automáticamente mediante detección facial.
- **Zoom en cortes:** Transición suave `1.00x → 1.05x` en cada corte.
- **Zoom de énfasis:** `1.15x` sincronizado con palabras clave de rebote o frases de énfasis.

---

## 5. Subtítulos y Destacados (Estilo MascotaMás)
- **Tipografía:** `Poppins ExtraBold`, tamaño `70 px` (para ancho base 1080).
- **Estilo visual:** Texto blanco luminoso (`#FDFCFF`), borde púrpura oscuro profundo (`#1B1329`) de `6 px` y sombra suave oscura.
- **Estructura de líneas:**
  - Máximo `16 caracteres` por línea.
  - Bloques de `2 a 4 palabras` en sincronía exacta con la voz.
  - **Puntuación:** Se omiten comas (`,`) y puntos finales (`.`); se conservan signos de interrogación (`¿?`) y exclamación (`¡!`).
- **Subtítulos destacados (Color Lavanda/Violeta MascotaMás `#BE97FF`):**
  - Se pintan en `#BE97FF` cada vez que aparecen:
    1. **Números** (dígitos o cantidades).
    2. **Adverbios enfáticos** (*de verdad, sin falta, ahora mismo, todo, siempre, nunca, ilimitado*, etc.).
    3. **Palabras de beneficio y dominio Pet** (*MascotaMás, gratis, automático, turnos, agenda, WhatsApp, recordatorios, veterinaria, peluquería, groomers, clínica, tutores, mascotas*, etc.).
    4. **Palabras clave para comentarios (CTA)**.
  - *Nota:* Solo se colorea la palabra clave; conectores y partículas permanecen en blanco.
- **Rebote de énfasis (Bounce):**
  - Frecuencia: Solo `1 vez cada 4 a 6 segundos` en palabras destacadas.
  - Animación: Escala `100% → 118% → 100%`, acompañada de efecto `pop` y zoom de cámara `1.15x`.

---

## 6. Título Gancho Superior (Top Hook & CTA)
- **Título inicial (Hook):**
  - Extraído de la primera oración en `2 líneas` (~12 caracteres por línea).
  - Fuente `Poppins ExtraBold` de `92 px`, texto blanco con palabras clave en lavanda `#BE97FF` y `1 emoji emotivo`.
  - Visible **únicamente durante la primera oración** y cuando el rostro ocupa el plano completo.
- **Título de Llamado a la Acción (CTA):**
  - Al iniciar la frase de llamado a comentar, muestra: `"Sigue y comenta 'PALABRA_CLAVE'"` con efecto `ding`.
- **Visibilidad:** El título superior se oculta automáticamente en las escenas de pantalla dividida para no tapar los gráficos.

---

## 7. Motion Graphics MascotaMás (Obligatorio: 70% a 85% del video)
- **Distribución del plano:**
  - Entre el **70% y el 85%** de la duración total del video se muestra en formato dividido: **Gráfico superior MascotaMás + Rostro inferior**.
  - Los únicos momentos con plano facial completo son:
    1. La primera frase (gancho inicial).
    2. 1 o 2 frases de énfasis o giro narrativo.
    3. La primera frase del llamado a la acción (CTA) para comentar.
- **Tecnología y estética MascotaMás:**
  - Renderizado con **HTML + GSAP** capturado en navegador headless (**Playwright**).
  - Barra superior con el logo oficial `mascotaMÁS` (`logo_dark_bg.png`) y badge de categoría.
  - Mascota animada (`peeking-creature`) en la esquina inferior derecha siguiendo la escena con la mirada.
  - Vista previa integrada de las pantallas reales de la App (`turnos`, `agendas`, `historia clínica`, `recordatorios de WhatsApp`, `estadísticas`, `sala de espera`, `tutores`).

---

## 8. Autoverificación Obligatoria
1. Re-transcripción del video exportado con `faster-whisper` (`large-v3-turbo`).
2. Detección de anomalías de audio y video.
3. Generación y revisión de `verification_grid.jpg`.
4. Entrega de reporte final.

---

## 9. Historial de Feedback

| Fecha | Solicitud del usuario | Parámetro actualizado en `style.json` | Estado |
| :--- | :--- | :--- | :--- |
| 2026-11-04 | Configuración base inicial del sistema | Todos los parámetros por defecto v1.0.0 | Activo |
| 2026-11-04 | Configura el estilo de la web de mascotamas.com, fonts, assets, estilo, todo | `brand=MascotaMás`, `fonts=Poppins+OpenSans`, `palette=#AE4CFC/#BE97FF/#1B1329/#10B981`, `assets=76 archivos de mascotamas.com + criatura animada` | Activo |
| 2026-11-04 | No dividir pantalla arriba/abajo, no tapar la cara, quitar ruido de fondo y realzar la voz, sin fondo violeta, respetar 100% logo original y animar criatura de mascotamas.com en esquina inferior izquierda, orden 1-2-3 | `camera.full_screen_only = true` | Activo |
| 2026-11-04 | Nueva versión v2 añadiendo capturas de pantalla reales de mascotamas.com (laptop + iPhone mockups) en grande sin importar tapar la cara | `motion_graphics.show_large_screenshots = true` | Activo |
| 2026-11-04 | Versión v3 sacando el fondo blanco del recuadro que tiene los mockups del sistema (mockups flotando directo sobre el video) | `motion_graphics.mockup_container_background = "transparent"` | Activo |
| 2026-11-04 | Nueva versión v4 usando la tipografía de mascotamas.com (Poppins + Open Sans) y resaltando las palabras clave con el tono violeta de la web (#AE4CFC) | `subtitles.color_highlight = "#AE4CFC"` | Activo |
| 2026-11-04 | Resaltar palabras clave de títulos y tarjetas con el tono violeta de mascotamas.com (#AE4CFC) | `top_title.color_keyword = "#AE4CFC"` | Activo |
| 2026-11-04 | Nueva versión v5 usando 100% la fuente Poppins limpia en todo el video (subtítulos, títulos y tarjetas) sin trazo grueso que deforme la tipografía | `subtitles.font_family = "Poppins Bold"` | Activo |
| 2026-11-04 | Subtítulos en Poppins-Bold.ttf con contorno fino de 2px y sombra suave para preservar la geometría pura de Poppins | `subtitles.font_path = "fonts/Poppins-Bold.ttf"` | Activo |
| 2026-11-04 | Contorno de subtítulos reducido a 2px para no deformar la fuente Poppins | `subtitles.stroke_width_px = 2` | Activo |
| 2026-11-04 | Utilizar la fuente oficial Poppins directamente desde Google Fonts (renderizada en Chromium sin trazo negro) para subtítulos, títulos y tarjetas | `subtitles.font_family = "Google Fonts Poppins"` | Activo |
| 2026-11-04 | Versión creativa MIX alternando planos espontáneos de quien habla, celulares individuales/dúo y notebooks manteniendo línea de tiempo y guion | `motion_graphics.mix_modes = "spontaneous,phone_side,phones_duo,notebook_only,combo"` | Activo |
| 2026-11-04 | Usar 100% Google Fonts Poppins en todo, nuevo guion comercial re-secuenciado, titulos comerciales por escena, multicamara, transiciones y muestra completa de celulares y notebooks (Propuesta Comercial Creativa v1) | `motion_graphics.commercial_headlines_poppins = true` | Activo |
| 2026-11-08 | Edición de videos instructivos en formato horizontal de pantalla completa de computadora (1920x1080 16:9) con barra inferior dedicada y tarjetas guía laterales | `video.desktop_tutorial_mode = "1920x1080_fullscreen_dock"` | Activo |
| 2026-11-08 | Mejorar locucion (resaltar voz, cancelar ruido y eco sin ruidos molestos, quitar alargamientos y espacios vacios, coherencia del speak) y generar version con voz argentina premium sincronizada palabra por palabra, versionando cada resultado (v1, v2, v3) | `audio.voice_mode = "studio_clean_v2_and_argentine_neural_v3"` | Activo |
| 2026-11-08 | Ajustar storytelling de instructivos 100% fiel a lo visual y relato inicial sin inventar nada, y generar spots de 30s por cada funcionalidad principal con voz argentina premium sincronizada palabra por palabra | `tutorial_desktop.storytelling_and_spots_30s = true` | Activo |
| 2026-11-08 | Corregir parte inicial de la URL en barra de direccion https://mmas-staging-1a3e2.web.app/ por https://gestion.mascotamas.com/ conservando la ruta nativa en todos los videos | `tutorial_desktop.production_url_prefix = "https://gestion.mascotamas.com/"` | Activo |
| 2026-11-08 | Dejar siempre una copia versionada en las carpetas locales del proyecto /brutos y /editados | `tutorial_desktop.local_folders_brutos_editados = true` | Activo |
| 2026-11-08 | Reel publicitario 9:16 hiperrealista de lo nuevo de MascotaMas (4 tipos de calendario + seña automatica Mercado Pago con aclaracion de posible comision + mockups realistas iPhone 16 Pro Max y MacBook Pro M4 + subtitulos Poppins + voz real argentina con lip-sync IA) | `motion_graphics.realistic_iphone16_macbook_m4_mockups = true` | Activo |
| 2026-11-08 | Comisión de Mercado Pago abajo con * en cursiva tipo TyC sin decirla en voz, locución Gemini TTS acento argentino a ritmo natural, música House Lyria 3 sincronizada con transiciones y cero aspecto IA | `audio.bgm.relative_to_voice_db = -13.5` | Activo |
| 2026-11-08 | La voz un 10, pero perdimos a la veterinaria que nos vendía el sistema: añadirla sincronizando los labios con la voz argentina y la música House con las transiciones y muestras de pantalla | `camera.split_graphic_vert_anchor = 0.255` | Activo |
| 2026-11-08 | Quitar lo de paseos, veterinaria más sexy con mejor boca y mejor sincro de boca, y generar las dos versiones de videos en distintos archivos (v4A y v4B) | `camera.split_graphic_min_y1_ratio = 0.086` | Activo |
| 2026-11-08 | Torso 38D y silueta reloj de arena mas llamativa con plano medio estabilizado en v5A y v5B | `camera.cut_zoom_end = 1.02` | Activo |
| 2026-11-09 | Storytelling argentino de Migracion Gratis en el Dia a MascotaMas con nuevo Avatar 360 (Gemini 3 Pro), lip-sync natural sin cortar frases, maquetas reales de MacBook Pro y iPhone 16 Pro Max desde Manual De Usuario Vete y Marca, skill de assets y versionado en GitHub y Drive | `motion_graphics.real_photo_mockups_and_avatar_360 = true` | Activo |
| 2026-11-09 | Encuadre nativo de cuerpo completo en Avatar 360 Gemini 3 Pro sin recorte superior en split_graphic | `camera.split_graphic_min_y1_ratio = 0.0` | Activo |
| 2026-11-09 | Prohibido congelar cuerpo o pelo con face_mask/Frame 0: movimiento 100% natural y continuo de cuerpo, pelo, hombros y manos entre todas las tomas (Multi-Turn 36s continuo + PCHIP monotónico sin pausas estáticas) y versión en Veterinaria de Palermo caminando de la camilla con perro al mostrador de entrada | `avatar.continuous_full_body_motion_no_face_mask = true` | Activo |
| 2026-11-09 | Sincronización exacta palabra por palabra (PCHIP start/end por palabra sin acumulación de deriva) en las 6 escenas completas incluyendo el cierre CTA, con gestos representativos de lo que dice (ej. contar las 4 agendas con los dedos y abrir las manos en el CTA) sin quedarse quieto al final | `avatar.exact_word_by_word_pchip_anchors_no_drift = true` | Activo |
