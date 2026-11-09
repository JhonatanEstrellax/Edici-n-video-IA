import os
import re
import json
import math

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
STYLE_PATH = os.path.join(BASE_DIR, "style.json")


def load_style():
    with open(STYLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def strip_subtitle_punct(word_str: str, remove_list: list) -> str:
    res = word_str
    for ch in remove_list:
        res = res.replace(ch, "")
    return res.strip()


def normalize_clean(w: str) -> str:
    return re.sub(r"[^\wáéíóúüñÁÉÍÓÚÜÑ0-9%]", "", w.lower()).strip()


def is_highlighted_word(word_str: str, next_word_str: str, style: dict, cta_keyword: str):
    """
    Rule: Numbers, emphatic adverbs (de verdad, sin falta, ahora mismo, todo),
    benefit words (gratis, automático) and CTA comment keywords must be painted yellow
    every time they appear (ONLY the keyword, connectors/particles stay white).
    """
    rules = style["subtitles"]["highlight_rules"]
    norm = normalize_clean(word_str)
    if not norm:
        return False, False

    # Connectors/particles must NEVER be highlighted on their own
    connectors = {
        "de", "sin", "el", "la", "los", "las", "un", "una", "y", "o", "en", "con",
        "por", "para", "que", "se", "al", "del", "a", "mi", "tu", "su", "es", "son"
    }

    # Check 2-word emphatic phrases (e.g., "de verdad", "sin falta", "ahora mismo"):
    # Note rule: "únicamente la palabra clave, conectores y partículas en blanco"
    # So in "de verdad" -> "verdad" is yellow, "de" is white; in "sin falta" -> "falta" is yellow, "sin" is white!
    emph_single = {
        "verdad", "falta", "ahora", "mismo", "todo", "todos", "toda", "todas",
        "nunca", "siempre", "jamás", "literalmente", "exactamente", "realmente",
        "totalmente", "completamente", "solo", "únicamente", "increíble"
    }
    benefit_single = set(normalize_clean(x) for x in rules.get("benefit_words", []))
    cta_single = set(normalize_clean(x) for x in rules.get("cta_keywords", []))
    if cta_keyword:
        cta_single.add(normalize_clean(cta_keyword))

    if norm in connectors:
        return False, False

    # 1. Numbers
    if rules.get("highlight_numbers", True) and re.search(r"\d", norm):
        return True, True

    # 2. Emphatic / Benefit / CTA keyword
    if norm in emph_single or norm in benefit_single or norm in cta_single:
        return True, True

    return False, False


def build_subtitle_blocks(edited_words: list, style: dict):
    """
    Groups edited words into blocks of 2 to 4 words, formatted into lines of <= 16 characters.
    Appears and changes in exact sync with the voice.
    """
    sub_cfg = style["subtitles"]
    max_chars = sub_cfg.get("max_chars_per_line", 16)
    min_w = sub_cfg.get("words_per_block_min", 2)
    max_w = sub_cfg.get("words_per_block_max", 4)
    rem_punct = sub_cfg.get("remove_punctuation", [",", "."])

    blocks = []
    curr = []

    for idx, w in enumerate(edited_words):
        disp = strip_subtitle_punct(w.get("subtitle_text", w["word"]), rem_punct)
        if not disp:
            continue
        w_copy = dict(w)
        w_copy["display"] = disp
        curr.append(w_copy)

        # Decide whether to close current block (2..4 words)
        next_w = edited_words[idx + 1] if idx + 1 < len(edited_words) else None
        gap_to_next = (next_w["edited_start"] - w["edited_end"]) if next_w else 999.0
        total_chars = sum(len(x["display"]) for x in curr) + max(0, len(curr) - 1)

        raw_word_str = w.get("subtitle_text", w["word"])
        should_close = False
        if len(curr) >= max_w:
            should_close = True
        elif (
            (next_w and next_w.get("scene_id") != w.get("scene_id"))
            or any(ch in raw_word_str for ch in ".?!")
            or gap_to_next > 0.25
        ):
            should_close = True
        elif len(curr) >= min_w and (
            gap_to_next > 0.14
            or total_chars >= max_chars * 1.45
            or any(ch in disp for ch in "?!¿¡")
        ):
            should_close = True
        elif next_w is None:
            should_close = True

        if should_close:
            # Wrap curr words into lines of <= max_chars (max 2 lines per block)
            lines = []
            current_line = []
            for item in curr:
                cand_str = " ".join([x["display"] for x in current_line] + [item["display"]])
                if current_line and len(cand_str) > max_chars:
                    lines.append(current_line)
                    current_line = [item]
                else:
                    current_line.append(item)
            if current_line:
                lines.append(current_line)

            # If wrapping produced > 2 lines, split into 2 compact lines
            if len(lines) > 2:
                mid = max(1, len(curr) // 2)
                lines = [curr[:mid], curr[mid:]]

            has_bounce = any(x.get("trigger_bounce", False) for x in curr)
            bounce_time = next(
                (x["edited_start"] for x in curr if x.get("trigger_bounce", False)),
                curr[0]["edited_start"]
            )

            blocks.append({
                "block_id": len(blocks) + 1,
                "scene_id": curr[0].get("scene_id", 1),
                "start": round(curr[0]["edited_start"], 4),
                "end": round(curr[-1]["edited_end"], 4),
                "words": curr,
                "lines": [
                    [
                        {
                            "word_id": x["word_id"],
                            "text": x["display"],
                            "is_yellow": x.get("is_yellow", False),
                            "trigger_bounce": x.get("trigger_bounce", False),
                            "start": x["edited_start"],
                            "end": x["edited_end"]
                        }
                        for x in ln
                    ]
                    for ln in lines
                ],
                "has_bounce": has_bounce,
                "bounce_start": round(bounce_time, 4)
            })
            curr = []

    return blocks


def plan_cuts():
    style = load_style()
    with open(os.path.join(WORK_DIR, "transcription_table.json"), "r", encoding="utf-8") as f:
        trans = json.load(f)
    with open(os.path.join(WORK_DIR, "guion_corregido.json"), "r", encoding="utf-8") as f:
        script = json.load(f)

    cuts_cfg = style["cuts"]
    pad_before = cuts_cfg.get("word_padding_before_sec", 0.05)
    pad_after = cuts_cfg.get("word_padding_after_sec", 0.05)
    max_pause = cuts_cfg.get("max_sentence_pause_sec", 0.15)
    min_seg_dur = cuts_cfg.get("min_segment_duration_sec", 0.12)
    crossfade_sec = cuts_cfg.get("audio_crossfade_ms", 10) / 1000.0
    outro_tail = cuts_cfg.get("outro_tail_after_last_word_sec", 0.30)
    orig_dur = trans["original_duration_sec"]

    kept_words = [w for w in script.get("words_cleaned", []) if w.get("keep", True)]
    scenes = script.get("scenes", [])
    word_to_scene = {}
    for sc in scenes:
        for wid in sc["word_ids"]:
            word_to_scene[wid] = sc["scene_id"]

    # 1. Build padded intervals around every kept word
    raw_intervals = []
    for i, w in enumerate(kept_words):
        is_last = (i == len(kept_words) - 1)
        s_t = max(0.0, w["real_start"] - pad_before)
        e_t = min(orig_dur, w["end"] + (outro_tail if is_last else pad_after))
        if e_t - s_t < min_seg_dur:
            e_t = min(orig_dur, s_t + min_seg_dur)
        raw_intervals.append({
            "start": round(s_t, 4),
            "end": round(e_t, 4),
            "words": [w],
            "scene_id": word_to_scene.get(w["word_id"], 1)
        })

    # 2. Merge adjacent word intervals if gap <= max_pause (0.15s)
    # Any non-speech gap > 0.15s (or breaths/pauses < 0.6s without words) is cut out!
    segments = []
    for iv in raw_intervals:
        if not segments:
            segments.append(iv)
            continue
        prev = segments[-1]
        gap = iv["start"] - prev["end"]
        # Merge if overlapping or tiny natural micro-pause <= max_pause (0.15s) WITHIN the same scene & monotonic order
        if iv["start"] >= prev["start"] - 0.05 and gap <= max_pause and iv["scene_id"] == prev["scene_id"]:
            prev["end"] = max(prev["end"], iv["end"])
            prev["words"].extend(iv["words"])
        else:
            segments.append(iv)

    # Enforce min_segment_duration_sec (0.12s) on all segments
    for seg in segments:
        if seg["end"] - seg["start"] < min_seg_dur:
            seg["end"] = min(orig_dur, seg["start"] + min_seg_dur)

    # 3. Map source timestamps to Edited Timeline timestamps (accounting for 10ms crossfade at joins)
    edited_cursor = 0.0
    edited_segments = []
    edited_words = []

    for seg_idx, seg in enumerate(segments):
        src_s = seg["start"]
        src_e = seg["end"]
        dur = round(src_e - src_s, 4)
        if seg_idx > 0:
            edited_cursor = max(0.0, edited_cursor - crossfade_sec)
        ed_s = round(edited_cursor, 4)
        ed_e = round(ed_s + dur, 4)

        seg_rms_vals = [w["rms_db"] for w in seg["words"]]
        avg_seg_rms = float(sum(seg_rms_vals) / len(seg_rms_vals)) if seg_rms_vals else trans.get("median_rms_db", -22.0)

        edited_segments.append({
            "segment_id": seg_idx + 1,
            "source_start": src_s,
            "source_end": src_e,
            "duration": dur,
            "edited_start": ed_s,
            "edited_end": ed_e,
            "avg_rms_db": round(avg_seg_rms, 2),
            "face_center": seg["words"][0].get("face_center", trans["face_metadata"]["default_face_center"]),
            "word_ids": [w["word_id"] for w in seg["words"]]
        })

        for w in seg["words"]:
            # Offset of word inside this segment
            w_rel_s = max(0.0, w["real_start"] - src_s)
            w_rel_e = min(dur, w["end"] - src_s)
            w_ed_s = round(ed_s + w_rel_s, 4)
            w_ed_e = round(max(w_ed_s + 0.06, ed_s + w_rel_e), 4)
            w_item = dict(w)
            w_item["edited_start"] = w_ed_s
            w_item["edited_end"] = w_ed_e
            w_item["scene_id"] = word_to_scene.get(w["word_id"], 1)
            edited_words.append(w_item)

        edited_cursor = ed_e

    total_edited_duration = round(edited_cursor, 4)

    # 4. Highlight detection & Bounce + Pop + 1.15x Zoom scheduling (1 time every 4-6 seconds)
    cta_kw = script.get("cta_keyword", "EDICIÓN")
    bounce_cfg = style["subtitles"]["bounce_emphasis"]
    cooldown_min = bounce_cfg.get("cooldown_min_sec", 4.0)
    last_bounce_time = -999.0

    for i, w in enumerate(edited_words):
        nxt_str = edited_words[i + 1]["word"] if i + 1 < len(edited_words) else ""
        is_yel, can_bounce = is_highlighted_word(w.get("subtitle_text", w["word"]), nxt_str, style, cta_kw)
        w["is_yellow"] = is_yel
        if is_yel and can_bounce and (w["edited_start"] - last_bounce_time >= cooldown_min):
            w["trigger_bounce"] = True
            last_bounce_time = w["edited_start"]
        else:
            w["trigger_bounce"] = False

    # Guarantee at least one bounce+pop emphasis in short videos (~4-12s) if none matched yet
    if edited_words and not any(w.get("trigger_bounce") for w in edited_words):
        mid_idx = len(edited_words) // 2
        edited_words[mid_idx]["is_yellow"] = True
        edited_words[mid_idx]["trigger_bounce"] = True

    # 5. Build Subtitle Blocks
    subtitle_blocks = build_subtitle_blocks(edited_words, style)

    # 6. Build exact Edited Timeline Scenes and enforce 70%~85% Motion Graphics coverage
    ed_word_map = {w["word_id"]: w for w in edited_words}
    edited_scenes = []
    for idx, sc in enumerate(scenes):
        sc_words = [ed_word_map[wid] for wid in sc["word_ids"] if wid in ed_word_map]
        if not sc_words:
            continue
        s_start = 0.0 if idx == 0 else edited_scenes[-1]["edited_end"]
        s_end = total_edited_duration if idx == len(scenes) - 1 else round(sc_words[-1]["edited_end"], 4)
        if s_end <= s_start:
            s_end = round(min(total_edited_duration, s_start + 0.5), 4)
        sc_copy = dict(sc)
        sc_copy["edited_start"] = round(s_start, 4)
        sc_copy["edited_end"] = round(s_end, 4)
        sc_copy["edited_duration"] = round(s_end - s_start, 4)
        edited_scenes.append(sc_copy)

    # Ensure last scene reaches exact end of video
    if edited_scenes:
        edited_scenes[-1]["edited_end"] = total_edited_duration
        edited_scenes[-1]["edited_duration"] = round(
            edited_scenes[-1]["edited_end"] - edited_scenes[-1]["edited_start"], 4
        )

    # Mathematical guarantee: Motion Graphics ("split_graphic") MUST cover 70% to 85% of total_edited_duration!
    if edited_scenes and total_edited_duration > 0:
        g_dur = sum(s["edited_duration"] for s in edited_scenes if s["layout_mode"] == "split_graphic")
        g_ratio = g_dur / total_edited_duration
        if g_ratio < 0.70 or g_ratio > 0.85:
            # Target 78% Motion Graphics coverage: first 22% of video is full_face Hook, remaining 78% is split_graphic
            hook_Split_t = round(total_edited_duration * 0.22, 4)
            rebuilt_scenes = []
            for s in edited_scenes:
                if s["edited_end"] <= hook_Split_t:
                    s["layout_mode"] = "full_face"
                    rebuilt_scenes.append(s)
                elif s["edited_start"] < hook_Split_t < s["edited_end"]:
                    # Split this scene at hook_Split_t into Hook (full_face) + Graphic (split_graphic)
                    s1 = dict(s)
                    s1["edited_end"] = hook_Split_t
                    s1["edited_duration"] = round(hook_Split_t - s1["edited_start"], 4)
                    s1["layout_mode"] = "full_face"

                    s2 = dict(s)
                    s2["scene_id"] = s["scene_id"] + 100
                    s2["edited_start"] = hook_Split_t
                    s2["edited_duration"] = round(s["edited_end"] - hook_Split_t, 4)
                    s2["layout_mode"] = "split_graphic"
                    s2["is_hook"] = False
                    s2["top_title"] = None
                    rebuilt_scenes.extend([s1, s2])
                else:
                    s["layout_mode"] = "split_graphic"
                    rebuilt_scenes.append(s)
            for idx, rs in enumerate(rebuilt_scenes):
                rs["scene_id"] = idx + 1
            edited_scenes = rebuilt_scenes

    final_g_dur = sum(s["edited_duration"] for s in edited_scenes if s["layout_mode"] == "split_graphic")
    final_g_ratio = round(final_g_dur / max(0.01, total_edited_duration), 4)

    # 7. Schedule Sound Effects (SFX: whoosh on scene change, pop on bounce, ding on CTA title)
    # Rule: place 0.05s before the event, with minimum spacing of 1.2s between SFX
    lead = style["audio"]["sfx"].get("lead_time_sec", 0.05)
    min_sfx_gap = style["audio"]["sfx"].get("min_interval_sec", 1.2)
    raw_sfx_events = []

    for sc in edited_scenes:
        if sc["edited_start"] > 0.1:
            if sc.get("is_cta") and sc["layout_mode"] == "full_face":
                raw_sfx_events.append({
                    "time": max(0.0, round(sc["edited_start"] - lead, 4)),
                    "type": "ding",
                    "priority": 3,
                    "reason": "Título CTA"
                })
            else:
                raw_sfx_events.append({
                    "time": max(0.0, round(sc["edited_start"] - lead, 4)),
                    "type": "whoosh",
                    "priority": 1,
                    "reason": f"Cambio a escena {sc['scene_id']}"
                })

    for b in subtitle_blocks:
        if b.get("has_bounce"):
            raw_sfx_events.append({
                "time": max(0.0, round(b["bounce_start"] - lead, 4)),
                "type": "pop",
                "priority": 2,
                "reason": "Subtítulo destacado con rebote"
            })

    # Sort by time and enforce >= 1.2s minimum spacing (keeping higher priority if collision)
    raw_sfx_events.sort(key=lambda x: (x["time"], -x["priority"]))
    sfx_events = []
    for ev in raw_sfx_events:
        if not sfx_events:
            sfx_events.append(ev)
        else:
            prev = sfx_events[-1]
            if ev["time"] - prev["time"] >= min_sfx_gap:
                sfx_events.append(ev)
            elif ev["priority"] > prev["priority"]:
                sfx_events[-1] = ev

    plan = {
        "source_video": trans["safe_video"],
        "source_audio": trans["safe_audio"],
        "original_duration_sec": orig_dur,
        "edited_duration_sec": total_edited_duration,
        "motion_graphics_coverage_ratio": final_g_ratio,
        "cta_keyword": cta_kw,
        "hook_title": script["hook_title"],
        "face_metadata": trans["face_metadata"],
        "median_rms_db": trans["median_rms_db"],
        "segments": edited_segments,
        "words": edited_words,
        "subtitle_blocks": subtitle_blocks,
        "scenes": edited_scenes,
        "sfx_events": sfx_events
    }

    out_path = os.path.join(WORK_DIR, "edit_plan.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    print(
        f"[STEP 3 DONE] Planned {len(edited_segments)} segments ({orig_dur}s -> {total_edited_duration}s), "
        f"{len(subtitle_blocks)} subtitle blocks, {len(sfx_events)} SFX events, "
        f"Motion Graphics coverage: {final_g_ratio * 100:.1f}%"
    )
    return plan


if __name__ == "__main__":
    plan_cuts()
