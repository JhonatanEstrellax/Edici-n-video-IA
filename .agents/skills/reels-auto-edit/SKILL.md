---
name: reels-auto-edit
description: >-
  Sistema automático de edición de Reels (9:16 1080x1920 @ 30fps). Activa esta skill inmediatamente cuando el usuario entregue o mencione un video y diga «Edítalo», cuando pida editar un Reel automáticamente, cuando dé feedback de edición (ej. «Haz los subtítulos más grandes», «La música está muy fuerte»), o cuando pida «Edita como este Reel» junto a un enlace.
---

# Sistema Automático de Edición de Reels (`reels-auto-edit`)

Esta skill ejecuta el flujo completo de edición automática de Reels en `c:\IA\Edicion de videos` siguiendo estrictamente `Manual_de_edicion.md` y `style.json`.

## Ubicación del Entorno y Herramientas
- **Carpeta de trabajo:** `c:\IA\Edicion de videos` (y subcarpeta limpia `c:\IA\Edicion de videos\reels_work`).
- **Python (.venv):** `c:\IA\Edicion de videos\.venv\Scripts\python.exe`
- **FFmpeg local:** `c:\IA\Edicion de videos\bin\ffmpeg\ffmpeg.exe`
- **Configuración numérica:** `c:\IA\Edicion de videos\style.json`
- **Manual de reglas:** `c:\IA\Edicion de videos\Manual_de_edicion.md`
- **Catálogo de Assets Reales (MacBook Pro + iPhone 16 Pro Max) y Pack Avatar 360° (11 Poses):** `.agents/skills/mascotamas-assets/SKILL.md` (`c:\IA\Edicion de videos\assets\mascotamas_real_mockups\` y `c:\IA\Edicion de videos\assets\avatar_veterinaria_360\`).

---

## Flujo Obligatorio al recibir «Edítalo»

Sigue **exactamente este orden** sin hacer preguntas intermedias al usuario:

### Paso ①: Transcripción por palabra + Análisis de Voz y Rostro
Ejecuta:
```powershell
& "c:\IA\Edicion de videos\.venv\Scripts\python.exe" "c:\IA\Edicion de videos\scripts\step1_transcribe.py" "<ruta_del_video>"
```
- Usa `faster-whisper` (`large-v3-turbo`) con marcas de tiempo por palabra y recorte automático del silencio previo según el nivel de voz real.
- Detecta posición facial y mirada a cámara con OpenCV YuNet (`models/face_detection_yunet_2023mar.onnx`).
- Genera `reels_work/transcription_table.json` y `reels_work/transcription_table.md`.

### Paso ②: Generación y Revisión del Guion Corregido + Escenas Visuales
Ejecuta:
```powershell
& "c:\IA\Edicion de videos\.venv\Scripts\python.exe" "c:\IA\Edicion de videos\scripts\step2_build_script.py"
```
- Revisa `reels_work/transcription_table.md` y `reels_work/guion_corregido.json`.
- **Regla de oro:** Solo está permitido borrar titubeos, silencios y tomas repetidas (conservando de entre las últimas tomas aquella donde se mire a cámara y se hable con mayor volumen; nunca uses tomas susurradas mirando al guion). Jamás alteres el contenido ni el tono de las palabras.
- Si detectas una errata de transcripción en nombres propios o términos técnicos, corrige únicamente `subtitle_text` en `reels_work/guion_corregido.json` y personaliza los textos de `graphic_config` por escena (`before_after`, `app_connection`, `counter`, `checklist`, `chat_input`, `comment_to_dm`) para que reflejen exactamente lo que dice cada frase, asegurando un **70%~85% de cobertura de Motion Graphics**.

### Paso ③: Planificación de Cortes, Subtítulos, Destacados y SFX
Ejecuta:
```powershell
& "c:\IA\Edicion de videos\.venv\Scripts\python.exe" "c:\IA\Edicion de videos\scripts\step3_plan_cuts.py"
```
- Aplica pausa máxima de `0.15 s` entre oraciones, margen de `0.05 s` antes/después de cada palabra, crossfade de `10 ms`, mínimo `0.12 s` por fragmento, y descarta fragmentos sin habla menores a `0.6 s`.
- Programa palabras clave en amarillo y rebote (`100→118→100%` + `pop` + zoom `1.15x`) máximo 1 vez cada 4–6 segundos.

### Paso ④ y ⑤: Renderizado HTML+GSAP (Playwright) y Exportación Única en Alta Calidad
Ejecuta:
```powershell
& "c:\IA\Edicion de videos\.venv\Scripts\python.exe" "c:\IA\Edicion de videos\scripts\step4_render_and_export.py" "<ruta_salida.mp4>"
```
- Renderiza las escenas gráficas con Playwright + GSAP (`templates/motion_graphics.html`), nivela voz (`+6 dB` / `-3 dB`), mezcla SFX y BGM (`-18 dB` bajo la voz con ducking), normaliza a `-14 LUFS`, y exporta en `1080x1920 @ 30fps` sin recompresiones intermedias.

### Paso ⑥: Autoverificación Obligatoria
Ejecuta:
```powershell
& "c:\IA\Edicion de videos\.venv\Scripts\python.exe" "c:\IA\Edicion de videos\scripts\step5_verify.py" "<ruta_salida.mp4>"
```
- Re-transcribe el video final para confirmar precisión de subtítulos, ausencia de clics de audio o pantallas negras/congeladas, y genera `verification_grid.jpg`.
- Inspecciona `verification_grid.jpg` con `read_file` para confirmar visualmente que los subtítulos no tapen la cara, el título ni los gráficos y que los motion graphics cubran entre el 70% y el 85%.
- Entrega al usuario el reporte breve (duración original → duración final, cantidad de palabras eliminadas y correcciones aplicadas).

*(Atajo de un solo comando para ejecutar todos los pasos seguidos: `& "c:\IA\Edicion de videos\.venv\Scripts\python.exe" "c:\IA\Edicion de videos\scripts\edit_reel.py"`)*

---

## Registro de Feedback y «Edita como este Reel»

Cuando el usuario pida ajustes (ej. *«los subtítulos son chicos»*, *«la música está muy fuerte»*) o pase un enlace diciendo *«Edita como este Reel»*:
1. Ejecuta:
   ```powershell
   & "c:\IA\Edicion de videos\.venv\Scripts\python.exe" "c:\IA\Edicion de videos\scripts\update_feedback.py" --request "<pedido>" --key "<clave_style_json>" --value "<nuevo_valor>"
   ```
   O para adaptar un enlace de Reel:
   ```powershell
   & "c:\IA\Edicion de videos\.venv\Scripts\python.exe" "c:\IA\Edicion de videos\scripts\update_feedback.py" --analyze-url "<url_del_reel>"
   ```
2. Esto actualiza automáticamente `style.json` y la tabla **Historial de Feedback** en `Manual_de_edicion.md`.
3. Si hay un video en la carpeta y el usuario pidió corregir el resultado actual, vuelve a renderizar con los nuevos parámetros.
