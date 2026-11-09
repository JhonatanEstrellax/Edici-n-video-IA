---
name: mascotamas-assets
description: >-
  Catálogo oficial y proceso de selección de assets reales de MascotaMás (maquetas fotográficas reales de MacBook Pro 16" y iPhone 16 Pro Max Titanium con capturas de gestion.mascotamas.com, y el Pack Avatar 360° de 11 poses de la Veterinaria generada con Gemini 3 Pro). Activa esta skill siempre que vayas a crear, editar o planificar un video o Reel comercial/instructivo de MascotaMás.
---

# Catálogo y Proceso de Selección de Assets Reales de MascotaMás (`mascotamas-assets`)

Esta skill documenta de dónde obtener las capturas de pantalla reales en maquetas fotográficas de **MacBook Pro 16" Space Gray** y **iPhone 16 Pro Max Titanium**, así como el **Pack Avatar 360° (11 Poses)** de la portavoz veterinaria de MascotaMás, y cómo elegir el asset exacto según lo que diga cada escena del guion.

---

## 1. Ubicación de los Repositorios de Assets

### A. Copia Curada en el Proyecto de Videos (Uso Directo en `templates/motion_graphics.html`)
- **90 Paquetes Jerárquicos + Storyboards + MicroVideos Reales de `Manual De Usuario Vete y Marca`:**
  `c:\IA\Edicion de videos\assets\manual_vete_y_marca\`
  *(Contiene los 527 archivos oficiales: `*__01_MacBook_Pro_Real.png`, `*__02_iPhone_16_Pro_Max_Real.png`, `*__03_Combo_MacBook_e_iPhone.png`, `*__04_Raw_Desktop.png`, `*__05_Raw_Mobile.png`, `storyboard_01..06.png`, `2026_01..14_*.png` y `MicroVideo_01..05.mp4`).*
- **Maquetas Fotográficas Reales (MacBook Pro + iPhone 16 Pro Max en PNG transparente RGBA):**
  `c:\IA\Edicion de videos\assets\mascotamas_real_mockups\`
- **Pack Completo Avatar Veterinaria 360° (11 Poses + Hojas Maestras en `Gemini 3 Pro`):**
  `c:\IA\Edicion de videos\assets\avatar_veterinaria_360\`
- **Logos, Íconos y Sonidos de Marca:**
  `c:\IA\Edicion de videos\assets\mascotamas\` (`logo.png`, `whatsapp_icon.png`, etc.)

### B. Repositorio Maestro Completo (Origen: Conversación `Manual De Usuario Vete y Marca`)
Si un video futuro requiere una pantalla específica adicional de las **56 vistas jerárquicas** del sistema o del sitio comercial, búscala en:
- **Raíz del Kit de Marca y Manual 2026:**
  `c:\DEV\Mascotamas\Manual_de_Marca_y_Kit_MascotaMas_2026\`
- **Chasis Reales Base (sin fondo):**
  `c:\DEV\Mascotamas\Manual_de_Marca_y_Kit_MascotaMas_2026\04_Maquetas_Dispositivos_Reales\equipos_reales_png\`
  - `chasis_real_macbook_pro.png` (`2048x1364` RGBA)
  - `chasis_real_iphone_16_pro_max.png` (`1006x2100` RGBA)
  - `dynamic_island_overlay.png`
- **56 Carpetas Jerárquicas del Sistema (`gestion.mascotamas.com`):**
  `c:\DEV\Mascotamas\Manual_de_Marca_y_Kit_MascotaMas_2026\04_Maquetas_Dispositivos_Reales\Capturas_Jerarquicas_Sitio_Seccion_Componente_Detalle\gestion.mascotamas.com\`
  *(Cada subcarpeta contiene `01_MacBook_Pro_Real.png`, `02_iPhone_16_Pro_Max_Real.png`, `03_Captura_Web_Pura.png` y `04_Captura_Mobile_Pura.png`).*
- **19 Carpetas Jerárquicas de la Web Comercial (`mascotamas.com`):**
  `c:\DEV\Mascotamas\Manual_de_Marca_y_Kit_MascotaMas_2026\04_Maquetas_Dispositivos_Reales\Capturas_Jerarquicas_Sitio_Seccion_Componente_Detalle\mascotamas.com\`

---

## 2. Tabla de Selección de Maquetas Reales según el Tema del Guion

Al armar `reels_work/guion_corregido.json`, selecciona `laptop_screenshot` y `phone_screenshot` apuntando a `../assets/mascotamas_real_mockups/<archivo>.png` de acuerdo con lo que hable la escena:

| Tema / Funcionalidad en el Diálogo | Maqueta Real MacBook Pro 16" (`laptop_screenshot`) | Maqueta Real iPhone 16 Pro Max (`phone_screenshot`) |
| :--- | :--- | :--- |
| **Migración al Sistema / Escritorio General / Resumen del Día** | `../assets/mascotamas_real_mockups/mac_dashboard_tutores_pacientes.png` | `../assets/mascotamas_real_mockups/iphone_dashboard_tutores_pacientes.png` |
| **Historias Clínicas / Legajo PDF / Ficha del Paciente / Vacunas** | `../assets/mascotamas_real_mockups/mac_historias_clinicas_legajo_pdf.png` | `../assets/mascotamas_real_mockups/iphone_evolucion_y_vacunas.png` *(o `real_iphone_04_historia_clinica.png`)* |
| **Directorio de Clientes (Tutores) y Contacto por WhatsApp** | `../assets/mascotamas_real_mockups/mac_directorio_tutores_whatsapp.png` | `../assets/mascotamas_real_mockups/iphone_directorio_tutores_whatsapp.png` |
| **Recordatorios Automáticos por WhatsApp (Vacunas / Controles)** | `../assets/mascotamas_real_mockups/mac_recordatorios_programados.png` | `../assets/mascotamas_real_mockups/iphone_recordatorios_programados.png` |
| **Sala de Espera en Vivo / Recepción del Consultorio** | `../assets/mascotamas_real_mockups/mac_sala_de_espera.png` | `../assets/mascotamas_real_mockups/real_iphone_05_sala_espera.png` *(o `iphone_sala_de_espera.png`)* |
| **4 Tipos de Calendarios / Agendas Inteligentes** | `../assets/mascotamas_real_mockups/mac_4_tipos_agenda.png` *(o `real_macbook_agendas_modal.png`)* | `../assets/mascotamas_real_mockups/iphone_4_tipos_agenda.png` *(o `real_iphone_02_agendas.png`)* |
| **Cobro de Seña Automática con Mercado Pago*** | `../assets/mascotamas_real_mockups/real_macbook_cobro_sena_mp.png` *(o `mac_sena_mercadopago_15min.png`)* | `../assets/mascotamas_real_mockups/real_iphone_03_turnos.png` |
| **Guardería / Estadías por Rango de Fechas (Check-in / Check-out)** | `../assets/mascotamas_real_mockups/mac_guarderia_estadias.png` | `../assets/mascotamas_real_mockups/iphone_guarderia_estadias.png` |

> **Importante sobre renderizado en `templates/motion_graphics.html`:**
> Como los archivos de `assets/mascotamas_real_mockups/` **ya traen el chasis fotográfico real de la MacBook Pro 16" (con teclado y bisel) y del iPhone 16 Pro Max Titanium (con Dynamic Island y botones físicos) sobre fondo transparente RGBA**, `motion_graphics.html` detecta automáticamente la ruta `mascotamas_real_mockups` y los renderiza como dispositivos fotográficos flotantes (`.real-photo-laptop` y `.real-photo-iphone`) sin encerrarlos en bordes CSS artificiales.

---

## 3. Catálogo del Pack Avatar Veterinaria 360° (11 Poses — `Gemini 3 Pro`)

Ubicación: `c:\IA\Edicion de videos\assets\avatar_veterinaria_360\`

| # | Archivo | Ángulo / Pose | Uso Recomendado en Videos (`gemini-omni-1.2-flash`) |
| :-: | :--- | :--- | :--- |
| **1** | `avatar_360_1_frente.png` | **Frente (`0°`)** | Hook inicial a cámara (`full_face`), mensajes centrales y cierre CTA. |
| **2** | `avatar_360_2_tres_cuartos_izq.png` | **3/4 Izquierda (`-45°`)** | Escenas con maquetas a la derecha/abajo o cambios de cámara dinámicos. |
| **3** | `avatar_360_3_lateral_izq.png` | **Lateral Izquierdo (`-90°`)** | Tomas de perfil / B-roll atendiendo en consultorio. |
| **4** | `avatar_360_4_tres_cuartos_der.png` | **3/4 Derecha (`+45°`)** | Alternancia multicámara natural para evitar cortes estáticos. |
| **5** | `avatar_360_5_lateral_der.png` | **Lateral Derecho (`+90°`)** | Tomas de perfil derecho / interacción con pantalla lateral. |
| **6** | `avatar_360_6_espalda.png` | **De Espalda (`180°`)** | Tomas de seguimiento entrando al consultorio. |
| **7** | `avatar_360_7_espalda_puntitas.png` | **De Espalda en Puntitas** | Alcanzando insumos en estantes altos de la clínica. |
| **8** | `avatar_360_8_espalda_agachada.png` | **De Espalda Agachada** | Atendiendo pacientes o buscando material en estantes bajos. |
| **9** | `avatar_360_9_frente_agachada.png` | **De Frente Agachada** | Saludando a una mascota a nivel de camilla baja con mirada a cámara. |
| **10** | `avatar_360_10_cuclillas_frente.png` | **En Cuclillas de Frente** | A la altura de un cachorro en el piso mirando a cámara. |
| **11** | `avatar_360_11_cuclillas_espalda.png` | **En Cuclillas de Espalda** | Revisando una mascota en el piso con giro de rostro sobre el hombro. |

### Videos Maestros 360° + 11 Poses en Movimiento Natural (`gemini-omni-1.2-flash`, `1080p` `9:16`):
- **`Avatar_Veterinaria_360_y_11_Poses_Movimiento_Natural_IA_Omni_1080p.mp4` (`39.0s`, `1080x1920 @ 30fps`):** Giro 360° continuo completo + las **11 poses completas sin omitir ningún movimiento** (`Poses 1 a 11`) con transiciones lentas, pausadas y naturales. (Google Drive ID: `1gnt6q1SJV_3fzdXRc-b0YfjD86yhhX6T`).
- **`Avatar_Veterinaria_360_y_11_Poses_Completo_IA_Omni_30s_1080p.mp4` (`30.0s`, `1080x1920 @ 24fps`):** Salida directa encadenada de `30.0s` de `gemini-omni-1.2-flash` con el giro 360° y todas las poses dinámicas. (Google Drive ID: `1uID9S9QYF4NQXW_WKCZNg0YMkyx81lt9`).
- **`Avatar_Veterinaria_360_IA_Omni_Giro_Continuo_15s_1080p.mp4` (`15.0s`, `1080x1920 @ 24fps`):** Giro 360° continuo puro de cuerpo entero. (Google Drive ID: `11F2RKARB1I4ifZG4CtCR_NQaFG3eMF4_`).

### Reglas de Locución, Lip-Sync y Ritmo Natural con el Avatar:
1. **Voz Oficial Argentina (`es-AR`):** Usar `gemini-3.8-flash-tts` con `voice_7j8i5jtcagb0` (femenina rioplatense cálida, natural y enérgica).
2. **Cero Frases Cortadas (`sin que se corten frases, pausado natural`):**
   - Generar cada oración por separado a velocidad `1.00x` (sin acelerar) y añadir `0.40s` de pausa natural de respiración al final de cada oración antes de ajustar al compás de `125 BPM` (`0.48s` por beat) de `Lyria 3`.
   - Al generar los clips de video en `gemini-omni-1.2-flash` (`15s` por clip), incluir **máximo 2 oraciones (~9 a 10 segundos de habla)** dentro de cada clip de `15s`. Así el avatar termina de pronunciar cada sílaba con más de 4 segundos de margen y jamás se corta una frase.
