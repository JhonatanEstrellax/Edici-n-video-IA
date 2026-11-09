# Reglas del Proyecto: Sistema Automático de Edición de Reels

- Cuando el usuario coloque un video en esta carpeta (o en `reels_work`) y diga **«Edítalo»** (o frase equivalente), activa inmediatamente la skill `reels-auto-edit` (`.agents/skills/reels-auto-edit/SKILL.md`) y ejecuta el flujo completo de edición (`step1_transcribe.py` → `step2_build_script.py` → `step3_plan_cuts.py` → `step4_render_and_export.py` → `step5_verify.py`) sin hacer preguntas previas.
- Revisa siempre `verification_grid.jpg` tras exportar para comprobar que los subtítulos no tapen el rostro, el título superior ni los motion graphics, y que los motion graphics cubran entre el 70% y el 85% del video.
- Cuando el usuario pida cualquier cambio de estilo o corrección (ej. «Haz los subtítulos más grandes», «La música está muy fuerte», «Edita como este Reel»), actualiza siempre `style.json` y la tabla **Historial de Feedback** al final de `Manual_de_edicion.md` usando `scripts/update_feedback.py`.
