# Sistema Automático de Edición y Producción de Videos IA — MascotaMás (2026)

Repositorio oficial del motor de edición y producción audiovisual con IA para **MascotaMás** (`mascotamas.com` / `gestion.mascotamas.com`).

## 1. Arquitectura y Capacidades Principales
- **Formato Reels (9:16 `1080x1920 @ 30fps`) e Instructivos Desktop (`1920x1080`):**
  - Subtítulos palabra por palabra renderizados en Chromium con **Google Fonts `Poppins`** (`600/700/800`) y resaltado de palabras clave en violeta oficial (`#AE4CFC`).
  - **Avatar Oficial Veterinaria 360° (11 Poses — `Gemini 3 Pro`):** Ubicado en `assets/avatar_veterinaria_360/` (Frente `0°`, 3/4 Izquierda `-45°`, Lateral Izquierdo `-90°`, 3/4 Derecha `+45°`, Lateral Derecho `+90°`, Espalda `180°`, Espalda en Puntitas, Espalda Agachada, Frente Agachada, Cuclillas de Frente y Cuclillas de Espalda).
  - **Locución Argentina Rioplatense (`es-AR`) + Lip-Sync PCHIP:** Voz natural generada con `gemini-3.8-flash-tts` (`voice_7j8i5jtcagb0`), pausas de respiración naturales (`0.42s..0.74s` entre oraciones para que jamás se corte una frase) y sincronización labial con `gemini-omni-1.2-flash` + curva monótona PCHIP.
  - **Música House Sincronizada al Beat (`Lyria 3` @ `125 BPM`):** Transiciones de escena, *risers*, *kick drops* y efectos de sonido (`whoosh`, `pop`, `ding`) bloqueados exactamente a la grilla de `0.48s` por pulso y masterizados a `-14.0 LUFS`.
  - **Maquetas Fotográficas Reales (`MacBook Pro 16"` + `iPhone 16 Pro Max Titanium`):** 35 maquetas reales en PNG RGBA transparente en `assets/mascotamas_real_mockups/` provenientes del repositorio jerárquico de `Manual De Usuario Vete y Marca`.

## 2. Skills del Agente Incluidas en este Repositorio
- **`.agents/skills/reels-auto-edit/SKILL.md`:** Flujo automático completo de 5 pasos (`step1_transcribe.py` → `step2_build_script.py` → `step3_plan_cuts.py` → `step4_render_and_export.py` → `step5_verify.py`).
- **`.agents/skills/mascotamas-assets/SKILL.md`:** Catálogo y tabla de decisión para elegir automáticamente las maquetas reales de **MacBook Pro 16"** y **iPhone 16 Pro Max** y la pose del **Avatar 360°** según lo que hable cada escena del guion.

## 3. Estructura de Carpetas
- `assets/avatar_veterinaria_360/` — Pack completo de 11 poses 360° de la Veterinaria (`Gemini 3 Pro`) y láminas maestras comparativas.
- `assets/mascotamas_real_mockups/` — Maquetas fotográficas reales de MacBook Pro 16" y iPhone 16 Pro Max Titanium con capturas de `gestion.mascotamas.com`.
- `assets/mascotamas/` — Logo original, íconos y recursos de marca.
- `templates/motion_graphics.html` — Motor HTML5 + GSAP de tarjetas flotantes, titulares comerciales en `Poppins`, maquetas reales y mascota animada.
- `scripts/` — Pipeline principal (`step1`..`step5`, `update_feedback.py`, `render_mg.js`).
- `style.json` y `Manual_de_edicion.md` — Configuración numérica y manual vivo con historial de feedback.
- `invitacion_cumple/` — Montaje de un personaje animado sobre una invitación de cumpleaños ya editada (recorte sin IA, animación GSAP al compás, enmascarado tras las fotos y los barridos). Ver `invitacion_cumple/README.md`.
