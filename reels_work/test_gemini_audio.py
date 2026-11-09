import os
import json
import urllib.request
import urllib.error

env = {}
with open(r"c:\IA\Edicion de videos\.env", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip("\"'")

api_key = env["GEMINI_API_KEY"]

print("--- Listing Models ---")
req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}")
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read().decode("utf-8"))
    for m in data.get("models", []):
        name = m["name"]
        if any(k in name.lower() for k in ["tts", "lyria", "audio", "flash", "omni", "veo", "argon"]):
            print(f"  {name} -> {m.get('supportedGenerationMethods')}")

print("\n--- Listing Spanish/Argentine Voices ---")
try:
    req_v = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/voices?page_size=100",
        headers={"x-goog-api-key": api_key}
    )
    with urllib.request.urlopen(req_v) as r:
        vdata = json.loads(r.read().decode("utf-8"))
        voices = vdata.get("voices", [])
        print(f"Total voices returned: {len(voices)}")
        for v in voices:
            lang = str(v.get("languageCode", v.get("language_code", ""))).lower()
            acc = str(v.get("accent", "")).lower()
            desc = str(v.get("description", "")).lower()
            if "es" in lang or "arg" in acc or "span" in acc or "lat" in acc or "arg" in desc:
                print("  VOICE:", v)
except urllib.error.HTTPError as e:
    print("Voices list error:", e.code, e.read().decode("utf-8", errors="replace"))
