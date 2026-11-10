# -*- coding: utf-8 -*-
r"""
Genera los 4 paquetes de capturas y maquetas reales (MacBook Pro 16" M4 + iPhone 16 Pro Max Titanium + Combo Dual)
de la sección `Turnos` configurada para una **Peluquería Canina** (`Peluquería Canina GroomingVIP`, `isVete() === false`)
en `gestion.mascotamas.com` sobre el lienzo nativo `1440x900`:
1. `01_Tablero_por_Groomer_y_Servicios`:
   - Header: `Peluquería Canina GroomingVIP`
   - Sidebar: `Turnos` (activo) y `Fichas de Clientes`
   - Calendario seleccionado: `PELUQUERÍA CANINA (SERVICIOS)`
   - `Agenda por Servicios y Bloques` · `Tablero por Profesional` (`maria gonzalez • peluquera`, `juan perez • peluquero`)
   - Simulador de encaje por duración (`Baño y corte Rzas CHICAS 45m`, `Baño y corte Rzas GDES 120m`).
2. `02_Agenda_Diaria_Turnos_Confirmados_y_Sena_MP`:
   - Grilla de turnos del día con turno activo de Peluquería Canina (`15:00 hs · 45 min · Luna (Caniche Toy) · En Peluquería · Seña acreditada ($15.000) · Servicio: Baño, Corte Higiénico y Deslanado`).
3. `03_Catalogo_Servicios_Duracion_y_Precios_Grooming`:
   - Modal `Servicios y Profesionales · PELUQUERÍA CANINA` (`Baño y corte Rzas CHICAS 45 min`, `Baño y corte Rzas GDES 120 min`).
4. `04_Sena_Automatica_MercadoPago_Peluqueria`:
   - Confirmación automática de turno de Peluquería Canina con Seña Mercado Pago (`Luna · Caniche Toy · Baño Medicado, Corte Higiénico y Deslanado`).
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


def build_screen1_tablero_groomers_y_servicios():
    src_path = (
        MANUAL_DIR
        / "03_Turnos_y_Agenda__02_Tablero_por_Profesional_y_Servicios__01_Simulador_Encaje_por_Servicio_y_Bloques__04_Raw_Desktop.png"
    )
    im = Image.open(src_path).convert("RGBA")
    draw = ImageDraw.Draw(im)

    f_header = get_font(SEGOE_BOLD, 18)
    f_sidebar = get_font(SEGOE_SEMIBOLD, 13)
    f_cal = get_font(SEGOE_REG, 13)

    # 1. Header superior: "Veterinaria Bosco" -> "Peluquería Canina GroomingVIP"
    draw.rectangle([720, 18, 1020, 46], fill=(255, 255, 255, 255))
    draw.text((735, 21), "Peluquería Canina GroomingVIP", font=f_header, fill=(17, 24, 39, 255))

    # 2. Sidebar inactivo en y=337: "Historias Clinicas" -> "Fichas de Clientes" (isVete() === false)
    draw.rectangle([62, 335, 195, 358], fill=(255, 255, 255, 255))
    draw.text((66, 337), "Fichas de Clientes", font=f_sidebar, fill=(75, 85, 99, 255))

    # 3. Selector de calendario (338, 247): "SERVICIOS PELUQUERIA xx" -> "PELUQUERÍA CANINA (SERVICIOS)"
    draw.rectangle([335, 242, 560, 263], fill=(255, 255, 255, 255))
    draw.text((338, 243), "PELUQUERÍA CANINA (SERVICIOS)", font=f_cal, fill=(31, 41, 55, 255))

    out_raw = MANUAL_DIR / "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__01_Tablero_por_Groomer_y_Servicios__04_Raw_Desktop.png"
    im.save(out_raw)
    return out_raw


def build_screen2_agenda_diaria_turnos_grooming():
    src_path = (
        MANUAL_DIR
        / "03_Turnos_y_Agenda__05_Modal_Detalle_de_Turno__01_Ficha_de_Turno_Acciones_WhatsApp_y_Estado__04_Raw_Desktop.png"
    )
    im = Image.open(src_path).convert("RGBA")
    draw = ImageDraw.Draw(im)

    f_header = get_font(SEGOE_BOLD, 18)
    f_sidebar = get_font(SEGOE_SEMIBOLD, 13)
    f_pet = get_font(SEGOE_BOLD, 14)
    f_badge = get_font(SEGOE_BOLD, 11)
    f_sub = get_font(SEGOE_REG, 12)
    f_btn = get_font(SEGOE_BOLD, 12)

    # 1. Header superior
    draw.rectangle([720, 18, 1020, 46], fill=(255, 255, 255, 255))
    draw.text((735, 21), "Peluquería Canina GroomingVIP", font=f_header, fill=(17, 24, 39, 255))

    # 2. Sidebar inactivo: "Fichas de Clientes"
    draw.rectangle([62, 335, 195, 358], fill=(255, 255, 255, 255))
    draw.text((66, 337), "Fichas de Clientes", font=f_sidebar, fill=(75, 85, 99, 255))

    # 3. Adaptar la tarjeta del turno de las 15:00 hs a un turno real de Peluquería Canina
    # Duración: "30 min" -> "45 min • Groomer: María"
    draw.rectangle([728, 808, 860, 825], fill=(251, 250, 249, 255))
    draw.text((730, 808), "45 min • Groomer", font=get_font(SEGOE_REG, 11), fill=(107, 114, 128, 255))

    # Paciente y badges en (880..1230, 764..786)
    draw.rectangle([878, 762, 1235, 788], fill=(251, 250, 249, 255))
    draw.text((881, 766), "Luna (Caniche)", font=f_pet, fill=(17, 24, 39, 255))

    draw.rounded_rectangle([995, 764, 1094, 785], radius=10, fill=(243, 232, 255, 255))
    draw.text((1005, 767), "En Peluquería", font=f_badge, fill=(109, 40, 217, 255))

    draw.rounded_rectangle([1102, 764, 1236, 785], radius=10, fill=(209, 250, 229, 255))
    draw.text((1110, 767), "Seña MP ($15.000)", font=f_badge, fill=(4, 120, 87, 255))

    # Botón "Ver HC" -> "Ver Ficha"
    draw.rounded_rectangle([1245, 768, 1314, 799], radius=6, fill=(139, 92, 246, 255))
    draw.text((1253, 776), "Ver Ficha", font=f_btn, fill=(255, 255, 255, 255))

    # Motivo / Servicio en (881, 822)
    draw.rectangle([878, 820, 1235, 840], fill=(251, 250, 249, 255))
    draw.text((881, 822), "Servicio: Baño y Corte Razas Chicas + Corte Higiénico y Deslanado", font=f_sub, fill=(55, 65, 81, 255))

    out_raw = MANUAL_DIR / "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__02_Agenda_Diaria_Turnos_Confirmados_y_Sena_MP__04_Raw_Desktop.png"
    im.save(out_raw)
    return out_raw


def build_screen3_catalogo_servicios_grooming():
    src_path = (
        MANUAL_DIR
        / "02_Calendarios_y_Modalidades__04_Catalogo_Servicios_y_Profesionales__01_Configuracion_Duracion_y_Precios_por_Servicio__04_Raw_Desktop.png"
    )
    im = Image.open(src_path).convert("RGBA")
    draw = ImageDraw.Draw(im)

    f_sidebar = get_font(SEGOE_SEMIBOLD, 13)
    f_modal = get_font(SEGOE_BOLD, 20)
    f_input = get_font(SEGOE_SEMIBOLD, 13)

    # Sidebar: "Fichas de Clientes"
    draw.rectangle([62, 335, 195, 358], fill=(148, 145, 153, 255))
    draw.text((66, 337), "Fichas de Clientes", font=f_sidebar, fill=(55, 65, 81, 255))

    # Título del modal (341, 67, 847, 104): limpiar "xx" -> "Servicios y Profesionales • PELUQUERÍA CANINA"
    draw.rectangle([342, 66, 880, 98], fill=(255, 255, 255, 255))
    draw.text((346, 69), "Servicios y Profesionales • PELUQUERÍA CANINA", font=f_modal, fill=(17, 24, 39, 255))

    # Pre-llenar input Nombre del Servicio con ejemplo activo (343, 292)
    draw.rectangle([340, 286, 680, 310], fill=(255, 255, 255, 255))
    draw.text((343, 288), "Baño, Corte de Raza y Deslanado Completo", font=f_input, fill=(17, 24, 39, 255))

    out_raw = MANUAL_DIR / "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__03_Catalogo_Servicios_Duracion_y_Precios_Grooming__04_Raw_Desktop.png"
    im.save(out_raw)
    return out_raw


def build_screen4_sena_mercadopago_grooming():
    src_path = (
        MANUAL_DIR
        / "03_Turnos_y_Agenda__06_Flujo_Reserva_con_Sena_MercadoPago__03_Card_Estado_2_Sena_Acreditada_Confirmado__04_Raw_Desktop.png"
    )
    im = Image.open(src_path).convert("RGBA")
    draw = ImageDraw.Draw(im)

    f_header = get_font(SEGOE_BOLD, 16)
    f_val = get_font(SEGOE_BOLD, 13)

    # Header: "VeteBosco" -> "Peluquería Canina GroomingVIP"
    draw.rectangle([270, 22, 820, 52], fill=(255, 255, 255, 255))
    draw.text((276, 28), "Peluquería Canina GroomingVIP • Turnos con Seña Mercado Pago", font=f_header, fill=(31, 41, 55, 255))

    # Limpiar superposición leve en PRESTACIÓN / SERVICIO e IMPORTE Y LIQUIDACIÓN (y ~ 444..468)
    draw.rectangle([326, 444, 922, 472], fill=(248, 247, 253, 255))
    draw.text((331, 448), "Baño Medicado, Corte Higiénico y Deslanado", font=f_val, fill=(17, 24, 39, 255))
    draw.text((616, 448), "$15.000 ARS Acreditados (Seña Mercado Pago)", font=f_val, fill=(109, 40, 217, 255))

    out_raw = MANUAL_DIR / "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__04_Sena_Automatica_MercadoPago_Peluqueria__04_Raw_Desktop.png"
    im.save(out_raw)
    return out_raw


def wrap_all_in_real_macbook_and_iphone(raw_paths):
    node_code = r"""
const fs = require('fs');
const path = require('path');
const engine = require('C:/DEV/Mascotamas/Manual_de_Marca_y_Kit_MascotaMas_2026/04_Maquetas_Dispositivos_Reales/capturador_web_macbook_iphone.js');
const sharp = require('C:/DEV/Mascotamas/screenshooter/node_modules/sharp');

(async () => {
  const files = JSON.parse(process.argv[1]);
  for (const rawDeskPath of files) {
    const deskBuf = fs.readFileSync(rawDeskPath);
    const cropped = await sharp(deskBuf).extract({ left: 260, top: 0, width: 1140, height: 900 }).png().toBuffer();
    const mobBuf = await sharp(cropped)
      .resize(888, 1920, { fit: 'contain', position: 'top', background: { r: 249, g: 250, b: 251, alpha: 1 } })
      .png()
      .toBuffer();

    const macBuf = await engine.wrapInRealMacBook(deskBuf, false);
    const ipBuf = await engine.wrapInRealIPhone(mobBuf, false);
    const comboBuf = await engine.createComboDualMockup(macBuf, ipBuf, {
      sitio: 'gestion.mascotamas.com',
      seccion: '03_Turnos_Peluqueria_Canina',
      componente: 'Agenda_por_Groomer_y_Servicios',
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
    p1 = build_screen1_tablero_groomers_y_servicios()
    p2 = build_screen2_agenda_diaria_turnos_grooming()
    p3 = build_screen3_catalogo_servicios_grooming()
    p4 = build_screen4_sena_mercadopago_grooming()
    wrap_all_in_real_macbook_and_iphone([p1, p2, p3, p4])
    print("=== 4 PAQUETES DE TURNOS (PELUQUERÍA CANINA) GENERADOS CON ÉXITO ===")


if __name__ == "__main__":
    main()
