"""Agrega el personaje animado a la invitacion de cumpleanos (1080x1920 @ 30 fps).

Flujo completo:
  1. recorta al personaje de las imagenes de referencia  -> personaje/recortes/*.png
  2. genera las capas animables (cuerpo, mano, sticker)  -> overlay/assets/
  3. mide el video (barridos, marcos de foto, tarjeta)   -> overlay/data/*.json
  4. renderiza la capa del personaje con Chromium + GSAP -> work/ov/ov_####.png
  5. compone sobre el video original con FFmpeg (el audio se copia sin recomprimir)

Uso:
  python invitacion_cumple/build.py <video_original.mp4> [salida.mp4] [--solo-render]

  --solo-render  salta los pasos 1-3 (usa los recortes y mediciones ya guardados);
                 util tras cambiar overlay/config.json (posiciones, tamanos, tiempos).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, 'tools')
OVERLAY = os.path.join(HERE, 'overlay')


def run(cmd, **kw):
    print('>', ' '.join(os.path.basename(str(c)) for c in cmd[:3]), '...', flush=True)
    subprocess.run(cmd, check=True, **kw)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    solo_render = '--solo-render' in sys.argv
    if not args:
        sys.exit(__doc__)
    video = os.path.abspath(args[0])
    out = os.path.abspath(args[1]) if len(args) > 1 else os.path.join(HERE, 'out', 'invitacion_con_personaje.mp4')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    frames_dir = os.path.join(HERE, 'work', 'ov')
    recortes = os.path.join(HERE, 'personaje', 'recortes')
    assets = os.path.join(OVERLAY, 'assets')
    os.makedirs(assets, exist_ok=True)
    py = sys.executable

    if not solo_render:
        run([py, '-I', os.path.join(TOOLS, 'recortar_personaje.py'), os.path.join(HERE, 'personaje', 'originales'), recortes])
        run([py, '-I', os.path.join(TOOLS, 'analizar_video.py'), video, os.path.join(OVERLAY, 'data')])
    run([py, '-I', os.path.join(TOOLS, 'build_assets.py'), recortes, assets])
    run(['node', os.path.join(TOOLS, 'render_overlay.js'), OVERLAY, frames_dir, 'all'], cwd=os.path.dirname(HERE))
    run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-framerate', '30', '-start_number', '0',
         '-i', os.path.join(frames_dir, 'ov_%04d.png'),
         '-filter_complex', '[0:v][1:v]overlay=0:0:format=auto:eof_action=pass[v]', '-map', '[v]', '-map', '0:a',
         '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', '30',
         '-c:a', 'copy', '-movflags', '+faststart', out])
    print('Listo:', out)


if __name__ == '__main__':
    main()
