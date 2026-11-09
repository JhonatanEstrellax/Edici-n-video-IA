import os
import re
import sys
import json
import difflib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
STYLE_PATH = os.path.join(BASE_DIR, "style.json")

FILLER_WORDS = {
    "eh", "ehh", "ehm", "mmm", "mm", "uh", "um", "ah", "ahh", "este...", "estee"
}

SPELLING_CORRECTIONS = {
    "mascotamas": "MascotaMás",
    "mascota": "Mascota",
    "whatsapp": "WhatsApp",
    "wasap": "WhatsApp",
    "pwa": "PWA",
    "groomer": "Groomer",
    "groomers": "Groomers",
    "clod": "Claude",
    "cloud": "Claude",
    "antigraviti": "Antigravity",
    "anti-gravity": "Antigravity",
    "chat gpt": "ChatGPT",
    "chatgpt": "ChatGPT",
    "ffmpej": "FFmpeg",
    "rils": "Reels",
    "ril": "Reel"
}


def load_style():
    with open(STYLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_token(text: str) -> str:
    return re.sub(r"[^\wáéíóúüñÁÉÍÓÚÜÑ]", "", text.lower()).strip()


def sentence_similarity(a: str, b: str) -> float:
    na = " ".join(normalize_token(x) for x in a.split() if normalize_token(x))
    nb = " ".join(normalize_token(x) for x in b.split() if normalize_token(x))
    if not na or not nb:
        return 0.0
    # Check prefix overlap (common when speaker restarts a sentence) or full similarity
    words_a = na.split()
    words_b = nb.split()
    if len(words_a) >= 2 and len(words_b) >= 2 and words_a[:2] == words_b[:2]:
        return 0.85
    return difflib.SequenceMatcher(None, na, nb).ratio()


def choose_best_take(group: list) -> dict:
    """
    Rule: If the same sentence was read multiple times, keep from among the last takes
    the one where the speaker looks at the camera and speaks loudest (highest RMS).
    Never use whispered takes looking at the script.
    """
    valid_takes = [
        s for s in group
        if not s.get("is_whispering", False) and s.get("looking_at_camera", True)
    ]
    if not valid_takes:
        valid_takes = [s for s in group if not s.get("is_whispering", False)] or group

    # Score combines recency (later take index) + voice RMS strength
    best = max(
        enumerate(valid_takes),
        key=lambda item: (item[1].get("looking_at_camera", True), item[1].get("avg_rms_db", -30.0) + item[0] * 1.2)
    )[1]
    return best


def clean_subtitle_spelling(word_str: str) -> str:
    low = normalize_token(word_str)
    if low in SPELLING_CORRECTIONS:
        # Preserve trailing ! or ?
        suffix = "".join(ch for ch in word_str if ch in "?!¿¡")
        return SPELLING_CORRECTIONS[low] + suffix
    return word_str


def detect_cta_keyword(full_text: str, style: dict) -> str:
    # Check explicit pattern like comenta 'X' or comenta "X" or palabra X
    m = re.search(r"comenta\s+['\"«]?([a-záéíóúñ0-9_]+)['\"»]?", full_text, flags=re.IGNORECASE)
    if m:
        return m.group(1).upper()
    cta_list = style.get("subtitles", {}).get("highlight_rules", {}).get("cta_keywords", [])
    for kw in cta_list:
        if re.search(rf"\b{re.escape(kw)}\b", full_text, flags=re.IGNORECASE):
            return kw.upper()
    return "EDICIÓN"


def detect_feature_screenshot(low_text: str, style: dict):
    shots = style.get("motion_graphics", {}).get("feature_screenshots", {})
    if not shots:
        return None, None
    mapping = [
        (["recordatorio", "whatsapp", "mensaje", "ausencia"], "whatsapp", "WHATSAPP"),
        (["turno", "reserva", "cita", "autogestion"], "turnos", "TURNOS"),
        (["agenda", "calendario", "horario"], "agenda", "AGENDAS"),
        (["historia", "clínica", "clinica", "ficha", "vacuna", "paciente"], "historia_clinica", "FICHAS"),
        (["estadística", "estadistica", "métrica", "metrica", "ranking", "ingreso"], "estadisticas", "MÉTRICAS"),
        (["sala de espera", "recepción", "recepcion", "espera"], "sala_espera", "RECEPCIÓN"),
        (["tutor", "tutores", "cliente", "clientes"], "tutores", "TUTORES"),
        (["escritorio", "panel", "sistema", "mascotamás", "mascotamas"], "escritorio", "MASCOTAMÁS"),
    ]
    for keywords, key, label in mapping:
        if any(k in low_text for k in keywords) and key in shots:
            return shots[key], label
    return shots.get("escritorio"), "APP REAL"


def infer_graphic_template_and_config(phrase_text: str, scene_idx: int, style: dict, cta_keyword: str) -> dict:
    """
    Chooses one of the 6 pre-designed HTML+GSAP templates based on the content of the sentence,
    and populates it directly with the phrase's real content + MascotaMás UI screenshots.
    Templates: before_after, app_connection, counter, checklist, chat_input, comment_to_dm
    """
    low = phrase_text.lower()
    words = [w.strip(".,;: ") for w in phrase_text.split() if w.strip(".,;: ")]
    screenshot_path, screenshot_label = detect_feature_screenshot(low, style)

    # Pick an accent word from the phrase
    accent_word = ""
    for w in words:
        if len(normalize_token(w)) >= 5:
            accent_word = w
            break

    # 1. Comment / DM / CTA pattern
    if any(k in low for k in ["comenta", "comentario", "dm", "envío", "enviar", "palabra clave", "regístrate", "registrate"]):
        return {
            "template": "comment_to_dm",
            "badge": "MASCOTAMÁS · ACCESO DIRECTO",
            "title": phrase_text,
            "accent_word": accent_word,
            "keyword": cta_keyword,
            "dm_text": "Link de Registro + Demo de MascotaMás por DM"
        }

    # 2. WhatsApp / App Connection pattern
    if any(k in low for k in ["whatsapp", "recordatorio", "notificacion", "reprogram", "conecta", "sincroniza"]):
        return {
            "template": "app_connection",
            "badge": "MASCOTAMÁS + WHATSAPP",
            "title": phrase_text,
            "accent_word": accent_word,
            "app_a": "MascotaMás PWA",
            "sub_a": "Turnos, Agendas & Fichas",
            "icon_a": "🐾",
            "app_b": "WhatsApp",
            "sub_b": "Recordatorios Automáticos",
            "use_whatsapp_icon": True,
            "status": "AUTOMÁTICO"
        }

    # 3. Before / After or contrast pattern
    if any(k in low for k in ["antes", "después", "manual", "difícil", "fácil", "horas", "segundos", "papel", "ahora", "olvídate", "olvidate"]):
        mid = max(1, len(words) // 2)
        part1 = " ".join(words[:mid]) or "Agenda manual y ausencias"
        part2 = " ".join(words[mid:]) or "Gestión 100% automatizada"
        return {
            "template": "before_after",
            "badge": "ANTES VS CON MASCOTAMÁS",
            "title": phrase_text,
            "accent_word": accent_word,
            "before_label": "ANTES",
            "before_value": part1[:28],
            "before_desc": "Gestión manual y turnos perdidos",
            "after_label": "CON MASCOTAMÁS",
            "after_value": part2[:28],
            "after_desc": "Turnos y recordatorios automáticos"
        }

    # 4. Numbers / Counter pattern
    num_match = re.search(r"\b(\d+(?:[.,]\d+)?)\b", phrase_text)
    if num_match or any(k in low for k in ["100%", "15k", "ilimitado", "24/7", "dos clics", "minutos", "segundos"]):
        num_val = float(num_match.group(1).replace(",", ".")) if num_match else 100
        suffix = "%" if "%" in phrase_text else ("+" if num_val >= 10 else "x")
        return {
            "template": "counter",
            "badge": "MASCOTAMÁS EN NÚMEROS",
            "title": phrase_text,
            "accent_word": accent_word,
            "target_number": num_val,
            "decimals": 0,
            "prefix": "",
            "suffix": suffix,
            "counter_label": phrase_text[:40],
            "pill_text": "★ 4.8 Rating · Veterinarias y Groomers",
            "screenshot": screenshot_path,
            "screenshot_label": screenshot_label
        }

    # 5. Prompt / Chat / Notification pattern
    if any(k in low for k in ["edítalo", "editalo", "decir", "dile", "frase", "escribe", "pide", "cliente", "tutor", "aviso"]):
        return {
            "template": "chat_input",
            "badge": "NOTIFICACIÓN INTELIGENTE",
            "title": phrase_text,
            "accent_word": accent_word,
            "prompt_text": f"«{phrase_text[:36]}»",
            "reply_text": "✓ Confirmado automáticamente en MascotaMás",
            "screenshot": screenshot_path,
            "screenshot_label": screenshot_label
        }

    # 6. Checklist + Real MascotaMás UI Preview
    chunk_size = max(1, len(words) // 3)
    c1 = " ".join(words[:chunk_size]) or "Turnos y agendas online"
    c2 = " ".join(words[chunk_size:2 * chunk_size]) or "Historias clínicas y fichas"
    c3 = " ".join(words[2 * chunk_size:]) or "Recordatorios por WhatsApp"
    items = [
        {"text": c1[:34], "tag": "TURNOS"},
        {"text": c2[:34], "tag": "FICHAS"},
    ]
    if c3.strip():
        items.append({"text": c3[:34], "tag": "WHATSAPP"})

    fallback_templates = ["checklist", "app_connection", "chat_input", "before_after"]
    chosen_tpl = fallback_templates[scene_idx % len(fallback_templates)]
    if chosen_tpl == "checklist":
        return {
            "template": "checklist",
            "badge": "PLATAFORMA MASCOTAMÁS",
            "title": phrase_text,
            "accent_word": accent_word,
            "items": items,
            "screenshot": screenshot_path,
            "screenshot_label": screenshot_label
        }
    elif chosen_tpl == "app_connection":
        return {
            "template": "app_connection",
            "badge": "ECOSISTEMA PET",
            "title": phrase_text,
            "accent_word": accent_word,
            "app_a": c1[:22] or "MascotaMás Web",
            "sub_a": "Veterinarias & Groomers",
            "icon_a": "🐾",
            "app_b": (c2 + " " + c3).strip()[:22] or "WhatsApp",
            "sub_b": "Fidelización de Tutores",
            "use_whatsapp_icon": True,
            "status": "ACTIVO"
        }
    elif chosen_tpl == "chat_input":
        return {
            "template": "chat_input",
            "badge": "GESTIÓN AUTOMÁTICA",
            "title": phrase_text,
            "accent_word": accent_word,
            "prompt_text": c1[:36] or phrase_text[:36],
            "reply_text": (c2 + " " + c3).strip()[:44] or "✓ Sincronizado en Web y App PWA",
            "screenshot": screenshot_path,
            "screenshot_label": screenshot_label
        }
    else:
        return {
            "template": "before_after",
            "badge": "TRANSFORMACIÓN DIGITAL PET",
            "title": phrase_text,
            "accent_word": accent_word,
            "before_label": "SIN SISTEMA",
            "before_value": c1[:26] or "Gestión manual",
            "before_desc": "Más tiempo administrativo",
            "after_label": "MASCOTAMÁS",
            "after_value": (c2 + " " + c3).strip()[:26] or "Todo ilimitado",
            "after_desc": "Web & App multidispositivo"
        }


def build_hook_title(first_phrase_text: str) -> dict:
    """
    Rule: Extract 2 lines from the first sentence (~12 chars per line),
    92px bold white font, keywords in yellow, and 1 emotive emoji.
    """
    clean = re.sub(r"[,.;:]", "", first_phrase_text).strip()
    words = clean.split()
    if not words:
        return {"line1": "EDICIÓN PRO", "line2": "AUTOMÁTICA 🔥", "keyword": "AUTOMÁTICA", "emoji": "🔥"}

    # Build 2 concise lines around ~12 chars each from the opening words
    line1_words = []
    line2_words = []
    for w in words:
        candidate = (" ".join(line1_words + [w])).strip()
        if len(candidate) <= 13 or not line1_words:
            if len(line2_words) == 0:
                line1_words.append(w)
                continue
        candidate2 = (" ".join(line2_words + [w])).strip()
        if len(candidate2) <= 13 or not line2_words:
            line2_words.append(w)
        else:
            break

    if not line2_words and len(line1_words) > 1:
        line2_words = [line1_words.pop()]
    elif not line2_words:
        line2_words = ["AHORA"]

    line1 = " ".join(line1_words).upper()
    line2 = " ".join(line2_words).upper()

    # Pick longest word in line1/line2 as the yellow keyword
    all_hook_words = line1_words + line2_words
    kw = max(all_hook_words, key=lambda x: len(normalize_token(x))).upper()
    emoji = "🔥" if "!" not in clean else "⚡"
    if emoji not in line2:
        line2 = f"{line2} {emoji}"

    return {
        "line1": line1,
        "line2": line2,
        "keyword": normalize_token(kw).upper(),
        "emoji": emoji
    }


def generate_corrected_script(transcription_path: str = None):
    if transcription_path is None:
        transcription_path = os.path.join(WORK_DIR, "transcription_table.json")

    with open(transcription_path, "r", encoding="utf-8") as f:
        trans = json.load(f)

    style = load_style()
    sentences = trans.get("sentences", [])
    words = trans.get("words", [])
    word_map = {w["word_id"]: w for w in words}

    # 1. Group consecutive repeated/retake sentences
    kept_sentences = []
    deleted_word_ids = []
    deletion_reasons = {}

    i = 0
    while i < len(sentences):
        group = [sentences[i]]
        j = i + 1
        while j < len(sentences):
            sim = sentence_similarity(group[-1]["text"], sentences[j]["text"])
            if sim >= 0.62:
                group.append(sentences[j])
                j += 1
            else:
                break
        if len(group) > 1:
            winner = choose_best_take(group)
            for s in group:
                if s["sentence_id"] != winner["sentence_id"]:
                    for wid in s["word_ids"]:
                        deleted_word_ids.append(wid)
                        deletion_reasons[str(wid)] = "Frase repetida / toma descartada (menor volumen o vista al guion)"
            kept_sentences.append(winner)
        else:
            s = group[0]
            # Check if an isolated tiny fragment is just a whispered false start
            if s.get("is_whispering") and len(s["word_ids"]) <= 2 and len(sentences) > 1:
                for wid in s["word_ids"]:
                    deleted_word_ids.append(wid)
                    deletion_reasons[str(wid)] = "Susurro / lectura de guion descartada"
            else:
                kept_sentences.append(s)
        i = j

    # 2. Within kept sentences, filter out filler words (eh, mmm, etc.) and consecutive stuttered identical words
    final_phrases = []
    kept_word_ids = []

    for s in kept_sentences:
        s_kept_wids = []
        prev_norm = None
        for wid in s["word_ids"]:
            w = word_map[wid]
            norm = normalize_token(w["word"])
            if norm in FILLER_WORDS:
                deleted_word_ids.append(wid)
                deletion_reasons[str(wid)] = f"Titubeo / muletilla ('{w['word']}')"
                continue
            if prev_norm and norm == prev_norm and len(norm) <= 4:
                deleted_word_ids.append(wid)
                deletion_reasons[str(wid)] = f"Repetición inmediata / titubeo ('{w['word']}')"
                continue
            w["subtitle_text"] = clean_subtitle_spelling(w["word"])
            s_kept_wids.append(wid)
            kept_word_ids.append(wid)
            prev_norm = norm

        if s_kept_wids:
            final_phrases.append({
                "phrase_id": len(final_phrases) + 1,
                "word_ids": s_kept_wids,
                "text": " ".join(word_map[wid]["subtitle_text"] for wid in s_kept_wids),
                "start": word_map[s_kept_wids[0]]["real_start"],
                "end": word_map[s_kept_wids[-1]]["end"],
                "duration": round(
                    sum(word_map[wid]["duration"] for wid in s_kept_wids), 3
                )
            })

    # Fallback if video had no speech detected or all filtered: keep all words so pipeline never crashes
    if not final_phrases and words:
        deleted_word_ids = []
        deletion_reasons = {}
        for w in words:
            w["subtitle_text"] = clean_subtitle_spelling(w["word"])
        kept_word_ids = [w["word_id"] for w in words]
        final_phrases = [{
            "phrase_id": 1,
            "word_ids": kept_word_ids,
            "text": " ".join(w["subtitle_text"] for w in words),
            "start": words[0]["real_start"],
            "end": words[-1]["end"],
            "duration": round(sum(w["duration"] for w in words), 3)
        }]

    # 3. Sub-divide long phrases if needed so we have enough granular scenes to achieve 70%-85% Motion Graphics coverage!
    # Rule: 70%~85% of the video MUST be split-screen (Top Graphic + Bottom Face).
    # First phrase is full_face (Hook). If there are <= 3 phrases, split phrases at natural clause boundaries
    # so the opening hook is ~20-25% of the video and the remaining 75-80% has dynamic graphic scenes!
    total_words_count = sum(len(p["word_ids"]) for p in final_phrases)
    if len(final_phrases) < 4 and total_words_count >= 4:
        all_wids = [wid for p in final_phrases for wid in p["word_ids"]]
        hook_count = max(1, int(round(len(all_wids) * 0.22)))
        rem_wids = all_wids[hook_count:]
        # Split remaining into 2 or 3 graphic scenes
        n_graphic_scenes = 2 if len(rem_wids) < 8 else 3
        chunk = max(1, len(rem_wids) // n_graphic_scenes)
        rebuilt = [all_wids[:hook_count]]
        for idx in range(n_graphic_scenes):
            start_i = idx * chunk
            end_i = len(rem_wids) if idx == n_graphic_scenes - 1 else (idx + 1) * chunk
            if rem_wids[start_i:end_i]:
                rebuilt.append(rem_wids[start_i:end_i])

        final_phrases = []
        for idx, wids in enumerate(rebuilt):
            final_phrases.append({
                "phrase_id": idx + 1,
                "word_ids": wids,
                "text": " ".join(word_map[wid]["subtitle_text"] for wid in wids),
                "start": word_map[wids[0]]["real_start"],
                "end": word_map[wids[-1]]["end"],
                "duration": round(word_map[wids[-1]]["end"] - word_map[wids[0]]["real_start"], 3)
            })

    full_kept_text = " ".join(p["text"] for p in final_phrases)
    cta_keyword = detect_cta_keyword(full_kept_text, style)
    hook_title = build_hook_title(final_phrases[0]["text"] if final_phrases else "")

    # 4. Assign layout_mode ("full_face" vs "split_graphic") to guarantee 70% - 85% graphic coverage
    total_dur = max(0.1, sum(max(0.2, p["end"] - p["start"]) for p in final_phrases))
    scenes = []
    for idx, p in enumerate(final_phrases):
        p_dur = max(0.2, p["end"] - p["start"])
        is_cta = any(k in p["text"].lower() for k in ["comenta", "sígueme", "sigue y comenta"])
        scenes.append({
            "scene_id": idx + 1,
            "phrase_id": p["phrase_id"],
            "word_ids": p["word_ids"],
            "text": p["text"],
            "source_start": p["start"],
            "source_end": p["end"],
            "approx_duration": round(p_dur, 3),
            "is_hook": idx == 0,
            "is_cta": is_cta,
            "layout_mode": "full_face" if idx == 0 else "split_graphic",
            "top_title": hook_title if idx == 0 else (
                {
                    "line1": "SIGUE Y COMENTA",
                    "line2": f"'{cta_keyword}' 💬",
                    "keyword": cta_keyword,
                    "emoji": "💬",
                    "is_cta_title": True
                } if is_cta else None
            ),
            "graphic_config": infer_graphic_template_and_config(p["text"], idx, style, cta_keyword)
        })

    # Verify 70% - 85% graphic coverage and adjust if needed
    def calc_graphic_ratio(sc_list):
        g_dur = sum(s["approx_duration"] for s in sc_list if s["layout_mode"] == "split_graphic")
        t_dur = max(0.01, sum(s["approx_duration"] for s in sc_list))
        return g_dur / t_dur

    # If graphic ratio > 0.85 and we have >= 5 scenes, allow 1 emphasis/CTA scene to be full_face
    if len(scenes) >= 5 and calc_graphic_ratio(scenes) > 0.85:
        for cand_idx in range(len(scenes) - 1, 1, -1):
            scenes[cand_idx]["layout_mode"] = "full_face"
            if calc_graphic_ratio(scenes) <= 0.85:
                if calc_graphic_ratio(scenes) < 0.70:
                    scenes[cand_idx]["layout_mode"] = "split_graphic"
                break

    # If graphic ratio < 0.70 (e.g. first scene is too long relative to video), set scene 0 split after first 22% of video
    # (Handled cleanly in step4 renderer as well using exact edited timeline!)

    script_data = {
        "cta_keyword": cta_keyword,
        "hook_title": hook_title,
        "kept_word_ids": kept_word_ids,
        "deleted_word_ids": sorted(list(set(deleted_word_ids))),
        "deletion_reasons": deletion_reasons,
        "approx_graphic_coverage_ratio": round(calc_graphic_ratio(scenes), 3),
        "scenes": scenes,
        "words_cleaned": [word_map[wid] for wid in kept_word_ids]
    }

    json_out = os.path.join(WORK_DIR, "guion_corregido.json")
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)

    md_out = os.path.join(WORK_DIR, "guion_corregido.md")
    md_lines = [
        "# Guion Corregido y Plan de Escenas Visuales",
        f"- **Palabras conservadas:** `{len(kept_word_ids)}`",
        f"- **Palabras eliminadas:** `{len(script_data['deleted_word_ids'])}` (`{script_data['deleted_word_ids']}`)",
        f"- **Cobertura estimada de Motion Graphics:** `{script_data['approx_graphic_coverage_ratio'] * 100:.1f}%` (Objetivo: 70%~85%)",
        f"- **Palabra clave CTA:** `{cta_keyword}`",
        "",
        "## Composición Visual por Frase (Escenas)",
        "| Escena | Modo de Plano | Plantilla Gráfica | Texto del Guion Corregido | IDs de Palabras |",
        "|---:|:---|:---|:---|:---|"
    ]
    for s in scenes:
        tpl_name = s["graphic_config"]["template"] if s["layout_mode"] == "split_graphic" else "Plano Facial Amplio"
        md_lines.append(
            f"| {s['scene_id']} | `{s['layout_mode']}` | `{tpl_name}` | {s['text']} | `{s['word_ids']}` |"
        )

    if script_data["deleted_word_ids"]:
        md_lines.extend([
            "",
            "## Números de Palabra Eliminados",
            "| # Palabra | Texto Original | Motivo de Eliminación |",
            "|---:|:---|:---|"
        ])
        for wid in script_data["deleted_word_ids"]:
            w_orig = word_map.get(wid, {}).get("word", "")
            reason = deletion_reasons.get(str(wid), "Descartado")
            md_lines.append(f"| {wid} | {w_orig} | {reason} |")

    with open(md_out, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print(
        f"[STEP 2 DONE] Kept {len(kept_word_ids)} words, deleted {len(script_data['deleted_word_ids'])} words, "
        f"{len(scenes)} scenes ({script_data['approx_graphic_coverage_ratio']*100:.1f}% graphic coverage) -> {json_out}"
    )
    return script_data


if __name__ == "__main__":
    generate_corrected_script()
