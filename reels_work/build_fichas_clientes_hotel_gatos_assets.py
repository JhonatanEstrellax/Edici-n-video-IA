# -*- coding: utf-8 -*-
r"""
Genera las capturas y maquetas reales (MacBook Pro 16" M4 + iPhone 16 Pro Max Titanium + Combo Dual)
de la sección `Fichas de Clientes` (`isVete() === false`) configurada para un **Hotel de Gatos**
en `gestion.mascotamas.com`, respetando al 100% la tipografía (Inter/Segoe/Poppins), colores y layout real
del código fuente `src/pages/MedicalRecord/index.tsx`, `ModalViewMedicalRecord.tsx` y `ModalCreateMedicalRecord.tsx`
sobre el lienzo nativo `1440x900`:
1. `01_Listado_y_Buscador_Felino`:
   - Menú lateral activo: `Fichas de Clientes`
   - Header superior: `Hotel de Gatos MichiVIP`
   - Título de página: `Fichas de Clientes`
   - Botón superior derecho: `Agregar Ficha de Cliente`
   - Filtro Especie: `Gato`
   - Listado: `Todas las Fichas de Clientes` con 3 huéspedes felinos (`NANA · Gato · Común eur...`, `Milo · Gato · Siamés`, `Pupi · Gato · Mestizo`).
2. `02_Modal_Ficha_de_Cliente_Gato_NANA`:
   - Modal `Ficha de Cliente de NANA` + botón `Descargar Ficha`
   - Datos del Tutor (`cecilia rivas`) + Datos del Huésped Felino (`NANA · Hembra · Gato · Común europeo · 2 años · Castrado: Sí · Suite Felina VIP`).
3. `03_Modal_Nueva_Ficha_de_Cliente_Gato`:
   - Modal `Nueva Ficha de Cliente` (`Complete los datos del tutor y del gato huésped para el Hotel de Gatos.`).
4. `04_Modal_Notas_Habitos_y_Estadia_Felina`:
   - Modal de `Ficha de Cliente` con pestañas `Notas de la Ficha` / `Estadías en Hotel`, registro de alimentación, hábitos felinos, peso y adjuntos PDF/fotos.
"""
import os
import sys
import subprocess
import pathlib
import json as _json
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
MANUAL_DIR = BASE_DIR / "assets" / "manual_vete_y_marca"

FONT_BOLD = str(BASE_DIR / "fonts" / "Poppins-Bold.ttf")
SEGOE_SEMIBOLD = r"C:\Windows\Fonts\seguisb.ttf"
SEGOE_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
SEGOE_REG = r"C:\Windows\Fonts\segoeui.ttf"


def get_font(path, size):
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    return ImageFont.truetype(FONT_BOLD, size)


def build_screen1_listado_fichas_gatos():
    """Adapta 06_Historias_Clinicas_y_Fichas__05_Fichas_de_Clientes... (1440x900) al modo real isVete()=false para Hotel de Gatos."""
    src_path = (
        MANUAL_DIR
        / "06_Historias_Clinicas_y_Fichas__05_Fichas_de_Clientes_Comercios_y_Peluqueria__01_Vista_Adaptada_Rubros_No_Veterinarios__04_Raw_Desktop.png"
    )
    im = Image.open(src_path).convert("RGBA")
    draw = ImageDraw.Draw(im)

    f_header = get_font(SEGOE_BOLD, 18)
    f_sidebar = get_font(SEGOE_SEMIBOLD, 13)
    f_page_title = get_font(SEGOE_BOLD, 23)
    f_btn = get_font(SEGOE_SEMIBOLD, 14)
    f_sec_title = get_font(SEGOE_BOLD, 16)
    f_row_name = get_font(SEGOE_BOLD, 15)
    f_row_sub = get_font(SEGOE_REG, 12)
    f_row_val = get_font(SEGOE_BOLD, 12)
    f_input = get_font(SEGOE_REG, 13)

    # 1. Header superior (775, 25, 920, 38): "Veterinaria Bosco" -> "Hotel de Gatos MichiVIP"
    draw.rectangle([740, 18, 980, 46], fill=(255, 255, 255, 255))
    draw.text((755, 21), "Hotel de Gatos MichiVIP", font=f_header, fill=(17, 24, 39, 255))

    # 2. Sidebar izquierdo (66, 341, 169, 350): "Historias Clinicas" -> "Fichas de Clientes"
    draw.rectangle([62, 335, 195, 358], fill=(250, 245, 255, 255))
    draw.text((66, 337), "Fichas de Clientes", font=f_sidebar, fill=(126, 34, 206, 255))

    # 3. PageTitle (282, 96, 462, 113): "Historias Clinicas" -> "Fichas de Clientes"
    draw.rectangle([278, 90, 520, 124], fill=(249, 250, 251, 255))
    draw.text((281, 91), "Fichas de Clientes", font=f_page_title, fill=(31, 41, 55, 255))

    # 4. Botón superior derecho (1187, 144, 1400, 189): "Agregar Historia Clinica" -> "Agregar Ficha de Cliente"
    draw.rounded_rectangle([1178, 144, 1400, 189], radius=8, fill=(126, 34, 206, 255))
    draw.text((1205, 157), "Agregar Ficha de Cliente", font=f_btn, fill=(255, 255, 255, 255))

    # 5. Filtro Especie (862, 398, 895, 407): "Todas" -> "Gato"
    draw.rectangle([858, 393, 940, 414], fill=(255, 255, 255, 255))
    draw.text((862, 394), "Gato", font=f_input, fill=(31, 41, 55, 255))

    # 6. Título de lista (281, 541, 495, 554): "Todas las Historias Clínicas" -> "Todas las Fichas de Clientes"
    draw.rectangle([278, 536, 540, 562], fill=(249, 250, 251, 255))
    draw.text((281, 538), "Todas las Fichas de Clientes", font=f_sec_title, fill=(31, 41, 55, 255))

    # 7. Segunda fila de la lista (reemplazar "tango / Perro / Basenji" por "Milo / Gato / Siamés")
    # Avatar circular en (299, 697, 341, 739)
    draw.rectangle([296, 694, 344, 742], fill=(255, 255, 255, 255))
    draw.ellipse([299, 697, 341, 739], fill=(243, 232, 255, 255))
    draw.text((313, 708), "M", font=f_row_name, fill=(126, 34, 206, 255))

    # Nombre y tutor en fila 2 (352, 702, 462, 732)
    draw.rectangle([348, 698, 510, 738], fill=(255, 255, 255, 255))
    draw.text((352, 699), "Milo", font=f_row_name, fill=(17, 24, 39, 255))
    draw.text((352, 719), "Tutor: jimena arias", font=f_row_sub, fill=(75, 85, 99, 255))

    # Especie (580, 721) y Raza (680, 718) en fila 2
    draw.rectangle([576, 715, 650, 736], fill=(255, 255, 255, 255))
    draw.text((580, 717), "Gato", font=f_row_val, fill=(31, 41, 55, 255))
    draw.rectangle([676, 715, 760, 736], fill=(255, 255, 255, 255))
    draw.text((680, 717), "Siamés", font=f_row_val, fill=(31, 41, 55, 255))

    out_raw = MANUAL_DIR / "06_Historias_Clinicas_y_Fichas__05_Fichas_de_Clientes_Hotel_de_Gatos__01_Listado_y_Buscador_Felino__04_Raw_Desktop.png"
    im.save(out_raw)
    return out_raw


def build_screen2_modal_ficha_gato_nana():
    """Adapta 06_Historias_Clinicas_y_Fichas__03_Legajo_Clinico_Digital_y_PDF (1440x900) a 'Ficha de Cliente de NANA' (Gato)."""
    src_path = (
        MANUAL_DIR
        / "06_Historias_Clinicas_y_Fichas__03_Legajo_Clinico_Digital_y_PDF__01_Modal_Historial_Completo_y_Descarga_PDF__04_Raw_Desktop.png"
    )
    im = Image.open(src_path).convert("RGBA")
    draw = ImageDraw.Draw(im)

    f_sidebar = get_font(SEGOE_SEMIBOLD, 13)
    f_modal_title = get_font(SEGOE_BOLD, 21)
    f_btn_dl = get_font(SEGOE_SEMIBOLD, 13)
    f_val = get_font(SEGOE_BOLD, 13)
    f_pet_big = get_font(SEGOE_BOLD, 18)
    f_pet_sub = get_font(SEGOE_REG, 12)
    f_badge = get_font(SEGOE_BOLD, 11)

    # Sidebar (66, 341)
    draw.rectangle([62, 335, 195, 358], fill=(148, 145, 153, 255))
    draw.text((66, 337), "Fichas de Clientes", font=f_sidebar, fill=(76, 29, 149, 255))

    # Título del modal (374, 89, 647, 112): "Historia Clínica de tango" -> "Ficha de Cliente de NANA"
    draw.rectangle([370, 84, 680, 118], fill=(255, 255, 255, 255))
    draw.text((374, 87), "Ficha de Cliente de NANA", font=f_modal_title, fill=(17, 24, 39, 255))

    # Botón Descargar (924, 80, 1102, 107): "Descargar Historia" -> "Descargar Ficha"
    draw.rectangle([950, 86, 1094, 112], fill=(255, 255, 255, 255))
    draw.text((955, 91), "Descargar Ficha", font=f_btn_dl, fill=(109, 40, 217, 255))

    # Datos del Tutor: (342, 247) "tomas Pose" -> "cecilia rivas", (726, 247) "Sin DNI" -> "34.892.110"
    draw.rectangle([338, 243, 480, 264], fill=(255, 255, 255, 255))
    draw.text((342, 244), "cecilia rivas", font=f_val, fill=(31, 41, 55, 255))
    draw.rectangle([722, 243, 850, 264], fill=(255, 255, 255, 255))
    draw.text((726, 244), "34.892.110", font=f_val, fill=(31, 41, 55, 255))

    # Selector Mascotas del tutor (355, 460): "tango" -> "NANA (Gato - Suite Felina)"
    draw.rectangle([350, 455, 550, 476], fill=(255, 255, 255, 255))
    draw.text((355, 457), "NANA (Gato - Suite Felina)", font=f_val, fill=(31, 41, 55, 255))

    # Avatar y encabezado de la mascota (342, 552, 420, 630)
    draw.rounded_rectangle([342, 552, 420, 630], radius=12, fill=(243, 232, 255, 255), outline=(216, 180, 254, 255), width=2)
    draw.text((370, 574), "N", font=get_font(SEGOE_BOLD, 26), fill=(126, 34, 206, 255))

    draw.rectangle([434, 568, 680, 622], fill=(255, 255, 255, 255))
    draw.text((438, 572), "NANA", font=f_pet_big, fill=(17, 24, 39, 255))
    draw.rounded_rectangle([502, 574, 560, 595], radius=10, fill=(252, 231, 243, 255))
    draw.text((510, 577), "Hembra", font=f_badge, fill=(190, 24, 93, 255))
    draw.text((438, 601), "Gato  •  Común europeo  •  2 años", font=f_pet_sub, fill=(107, 114, 128, 255))

    # Grilla inferior de datos:
    # Row 1 (y=693): Col1=342 (NOMBRE), Col2=598 (ESPECIE), Col3=854 (RAZA)
    draw.rectangle([338, 689, 980, 712], fill=(255, 255, 255, 255))
    draw.text((342, 690), "NANA", font=f_val, fill=(17, 24, 39, 255))
    draw.text((598, 690), "Gato", font=f_val, fill=(17, 24, 39, 255))
    draw.text((854, 690), "Común europeo", font=f_val, fill=(17, 24, 39, 255))

    # Row 2 (y=753): Col1=342 (SEXO), Col2=598 (FECHA), Col3=854 (EDAD)
    draw.rectangle([338, 749, 980, 772], fill=(255, 255, 255, 255))
    draw.text((342, 750), "Hembra", font=f_val, fill=(17, 24, 39, 255))
    draw.text((598, 750), "14/05/2024", font=f_val, fill=(17, 24, 39, 255))
    draw.text((854, 750), "2 años", font=f_val, fill=(17, 24, 39, 255))

    out_raw = MANUAL_DIR / "06_Historias_Clinicas_y_Fichas__05_Fichas_de_Clientes_Hotel_de_Gatos__02_Modal_Ficha_de_Cliente_Gato_NANA__04_Raw_Desktop.png"
    im.save(out_raw)
    return out_raw


def build_screen3_modal_nueva_ficha_gato():
    """Adapta 06_Historias_Clinicas_y_Fichas__02_Modal_Nueva_Historia_Clinica (1440x900) a 'Nueva Ficha de Cliente' (Hotel de Gatos)."""
    src_path = (
        MANUAL_DIR
        / "06_Historias_Clinicas_y_Fichas__02_Modal_Nueva_Historia_Clinica__01_Formulario_Datos_Paciente_Especie_Raza_y_Tutor__04_Raw_Desktop.png"
    )
    im = Image.open(src_path).convert("RGBA")
    draw = ImageDraw.Draw(im)

    f_sidebar = get_font(SEGOE_SEMIBOLD, 13)
    f_modal_title = get_font(SEGOE_BOLD, 21)
    f_sub = get_font(SEGOE_REG, 13)
    f_input = get_font(SEGOE_SEMIBOLD, 13)

    # Sidebar
    draw.rectangle([62, 335, 195, 358], fill=(148, 145, 153, 255))
    draw.text((66, 337), "Fichas de Clientes", font=f_sidebar, fill=(76, 29, 149, 255))

    # Título del modal (374, 89, 618, 106): "Nueva Historia Clínica" -> "Nueva Ficha de Cliente"
    draw.rectangle([370, 84, 680, 116], fill=(255, 255, 255, 255))
    draw.text((374, 87), "Nueva Ficha de Cliente", font=f_modal_title, fill=(17, 24, 39, 255))

    # Subtítulo (325, 130, 728, 142)
    draw.rectangle([322, 125, 860, 148], fill=(255, 255, 255, 255))
    draw.text((325, 127), "Complete los datos del tutor y del gato huésped para el Hotel de Gatos.", font=f_sub, fill=(107, 114, 128, 255))

    # Pre-llenar campos con ejemplo real de Hotel de Gatos
    # Tutor input (359, 276)
    draw.rectangle([355, 270, 660, 292], fill=(255, 255, 255, 255))
    draw.text((359, 272), "Cecilia Rivas", font=f_input, fill=(17, 24, 39, 255))

    # Email input (739, 276)
    draw.rectangle([735, 270, 1040, 292], fill=(255, 255, 255, 255))
    draw.text((739, 272), "cecilia.rivas@correo.com", font=f_input, fill=(17, 24, 39, 255))

    # Nombre de la mascota input (360, 776)
    draw.rectangle([355, 770, 660, 792], fill=(255, 255, 255, 255))
    draw.text((360, 772), "NANA (Gato - Suite Felina VIP)", font=f_input, fill=(17, 24, 39, 255))

    out_raw = MANUAL_DIR / "06_Historias_Clinicas_y_Fichas__05_Fichas_de_Clientes_Hotel_de_Gatos__03_Modal_Nueva_Ficha_de_Cliente_Gato__04_Raw_Desktop.png"
    im.save(out_raw)
    return out_raw


def build_screen4_modal_evolucion_y_estadia_gato():
    """Adapta 06_Historias_Clinicas_y_Fichas__04_Evolucion_Clinica... (1440x900) a Ficha de Cliente y Observaciones de Hotel de Gatos."""
    src_path = (
        MANUAL_DIR
        / "06_Historias_Clinicas_y_Fichas__04_Evolucion_Clinica_y_Vacunacion__01_Modal_Nuevo_Registro_Clinico_y_Vacunas__04_Raw_Desktop.png"
    )
    im = Image.open(src_path).convert("RGBA")
    draw = ImageDraw.Draw(im)

    f_sidebar = get_font(SEGOE_SEMIBOLD, 13)
    f_val = get_font(SEGOE_BOLD, 13)
    f_obs = get_font(SEGOE_SEMIBOLD, 12)
    f_tab = get_font(SEGOE_SEMIBOLD, 13)
    f_txt = get_font(SEGOE_REG, 13)

    # Sidebar
    draw.rectangle([62, 335, 195, 358], fill=(148, 145, 153, 255))
    draw.text((66, 337), "Fichas de Clientes", font=f_sidebar, fill=(76, 29, 149, 255))

    # Datos superiores del gato NANA (y=42 y y=103)
    draw.rectangle([338, 42, 980, 60], fill=(255, 255, 255, 255))
    draw.text((342, 42), "NANA", font=f_val, fill=(17, 24, 39, 255))
    draw.text((598, 42), "Gato", font=f_val, fill=(17, 24, 39, 255))
    draw.text((854, 42), "Común europeo", font=f_val, fill=(17, 24, 39, 255))

    draw.rectangle([338, 99, 980, 120], fill=(255, 255, 255, 255))
    draw.text((342, 100), "Hembra", font=f_val, fill=(17, 24, 39, 255))
    draw.text((598, 100), "14/05/2024", font=f_val, fill=(17, 24, 39, 255))
    draw.text((854, 100), "2 años", font=f_val, fill=(17, 24, 39, 255))

    # Último peso (351, 232)
    draw.rectangle([348, 228, 560, 250], fill=(255, 255, 255, 255))
    draw.text((351, 229), "4.2 kg (Control Ingreso)", font=f_val, fill=(17, 24, 39, 255))

    # Observaciones de Hotel de Gatos (342..1084, 272..328)
    draw.rounded_rectangle([342, 274, 1084, 326], radius=8, fill=(250, 245, 255, 255))
    draw.text((358, 282), "Observaciones Hotel de Gatos: Dieta Urinary 60g/día • Arena sílice • Suite Felina VIP #3", font=f_obs, fill=(109, 40, 217, 255))
    draw.text((358, 302), "Vacuna Triple Felina y Antirrábica al día • Pipeta aplicada • Muy sociable y tranquila", font=f_obs, fill=(75, 85, 99, 255))

    # Pestañas (y=398): "Historias Clínicas" -> "Notas de la Ficha" | "Turnos Agendados" -> "Estadías en Hotel"
    draw.rectangle([362, 394, 472, 418], fill=(255, 255, 255, 255))
    draw.text((366, 396), "Notas de la Ficha", font=f_tab, fill=(126, 34, 206, 255))
    draw.rectangle([522, 394, 650, 418], fill=(255, 255, 255, 255))
    draw.text((525, 396), "Estadías en Hotel", font=f_tab, fill=(75, 85, 99, 255))

    # Texto de nota de estadía en textarea (372, 487)
    draw.rectangle([368, 482, 1040, 560], fill=(255, 255, 255, 255))
    draw.text((372, 485), "Check-in Suite Felina VIP: Ingresa con su manta y rascador propio.", font=f_txt, fill=(31, 41, 55, 255))
    draw.text((372, 509), "Alimentación húmeda a las 09:00 y 20:00 hs. Enviar video diario por WhatsApp a Cecilia.", font=f_txt, fill=(31, 41, 55, 255))

    out_raw = MANUAL_DIR / "06_Historias_Clinicas_y_Fichas__05_Fichas_de_Clientes_Hotel_de_Gatos__04_Modal_Notas_Habitos_y_Estadia_Felina__04_Raw_Desktop.png"
    im.save(out_raw)
    return out_raw


def wrap_all_in_real_macbook_and_iphone(raw_paths):
    """Usa el motor oficial `capturador_web_macbook_iphone.js` para envolver cada captura en MacBook Pro 16" M4 + iPhone 16 Pro Max + Combo."""
    node_code = r"""
const fs = require('fs');
const path = require('path');
const engine = require('C:/DEV/Mascotamas/Manual_de_Marca_y_Kit_MascotaMas_2026/04_Maquetas_Dispositivos_Reales/capturador_web_macbook_iphone.js');
const sharp = require('C:/DEV/Mascotamas/screenshooter/node_modules/sharp');

(async () => {
  const files = JSON.parse(process.argv[1]);
  for (const rawDeskPath of files) {
    const deskBuf = fs.readFileSync(rawDeskPath);
    // Crear vista mobile centrada de alta resolución para el iPhone 16 Pro Max
    const cropped = await sharp(deskBuf).extract({ left: 260, top: 0, width: 920, height: 900 }).png().toBuffer();
    const mobBuf = await sharp(cropped)
      .resize(888, 1920, { fit: 'contain', position: 'top', background: { r: 249, g: 250, b: 251, alpha: 1 } })
      .png()
      .toBuffer();

    const macBuf = await engine.wrapInRealMacBook(deskBuf, false);
    const ipBuf = await engine.wrapInRealIPhone(mobBuf, false);
    const comboBuf = await engine.createComboDualMockup(macBuf, ipBuf, {
      sitio: 'gestion.mascotamas.com',
      seccion: '06_Fichas_de_Clientes',
      componente: 'Hotel_de_Gatos',
      detalle: path.basename(rawDeskPath).split('__')[2] || 'Vista_Principal',
    });

    const prefix = rawDeskPath.replace('__04_Raw_Desktop.png', '');
    fs.writeFileSync(prefix + '__01_MacBook_Pro_Real.png', macBuf);
    fs.writeFileSync(prefix + '__02_iPhone_16_Pro_Max_Real.png', ipBuf);
    fs.writeFileSync(prefix + '__03_Combo_MacBook_e_iPhone.png', comboBuf);
    fs.writeFileSync(prefix + '__05_Raw_Mobile.png', mobBuf);
    console.log('  -> [MOCKUPS REALES GENERADOS]', path.basename(prefix));
  }
})();
"""
    subprocess.run(
        ["node", "-e", node_code, _json.dumps([str(p) for p in raw_paths])],
        check=True,
    )


def main():
    p1 = build_screen1_listado_fichas_gatos()
    p2 = build_screen2_modal_ficha_gato_nana()
    p3 = build_screen3_modal_nueva_ficha_gato()
    p4 = build_screen4_modal_evolucion_y_estadia_gato()
    wrap_all_in_real_macbook_and_iphone([p1, p2, p3, p4])
    print("=== 4 PAQUETES DE FICHAS DE CLIENTES (HOTEL DE GATOS) GENERADOS CON ÉXITO ===")


if __name__ == "__main__":
    main()
