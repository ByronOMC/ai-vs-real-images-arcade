import os
import json
import time
from datetime import datetime
from google import genai
from google.genai import types

# ==================================================
# CONFIG
# 1- Run in terminal: pip install -U google-genai
# 2- Create an environment variable called "GEMINI_API_KEY" if it does not exist yet
#    (see the key in Google AI Studio)
# 3- Configure the environment variable so the script can read it
# ==================================================

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY does not exist")

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.1-flash-image-preview"
MAX_RETRIES = 3
WAIT_SECONDS = 3

FIXED_PROMPT = """
Photorealistic image, captured as if taken by a professional photographer using a Canon EOS R5 with a 50mm lens at f/1.8, natural lighting, realistic shadows and highlights, shallow depth of field with soft background blur (bokeh), accurate skin tones and textures, subtle imperfections, slight film grain, true-to-life colors, high dynamic range, documentary photography style, editorial photo, realistic environment, candid moment, no CGI, no illustration, not stylized
"""

# ==================================================
# PATHS
# ==================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

JSON_PATH = os.path.join(PROJECT_DIR, "data", "jsons", "image_objects.json")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "data", "news")
STATE_PATH = os.path.join(PROJECT_DIR, "data", "jsons", "image_state.json")
LOG_PATH = os.path.join(PROJECT_DIR, "data", "Image_logs.txt")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==================================================
# HELPERS
# ==================================================
def log(msg):
    print(msg)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - {msg}\n")


def get_last_processed():
    if not os.path.exists(STATE_PATH):
        return -1

    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("last_position", -1)
    except:
        return -1


def save_state(position):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"last_position": position}, f, indent=2)


def load_json():
    if not os.path.exists(JSON_PATH):
        raise FileNotFoundError(f"{JSON_PATH} does not exist")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("The JSON must be a list")

    return data


def get_max_position(data):
    if not data:
        return 0
    return max(item.get("position", 0) for item in data)


# ==================================================
# GENERATE IMAGE
# ==================================================
def generate_image(prompt, position):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log(f"[{position}] Attempt {attempt}")

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"]
                )
            )

            if not response.candidates:
                raise Exception("No candidates")

            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    filename = f"AI_{position}.png"
                    path = os.path.join(OUTPUT_DIR, filename)

                    if os.path.exists(path):
                        log(f"[{position}] {filename} already exists, skipping.")
                        return True

                    with open(path, "wb") as f:
                        f.write(part.inline_data.data)

                    log(f"[{position}] Image saved: {filename}")
                    return True

            raise Exception("No image returned")

        except Exception as e:
            log(f"[{position}] Error: {e}")

            if "401" in str(e) or "UNAUTHENTICATED" in str(e):
                raise Exception("Invalid or unauthorized API KEY")

            time.sleep(WAIT_SECONDS)

    return False


# ==================================================
# MAIN
# ==================================================
def main():
    log("===== START =====")

    try:
        data = load_json()
    except Exception as e:
        log(f"Error loading JSON: {e}")
        return

    if not data:
        log("The JSON is empty.")
        return

    last = get_last_processed()
    log(f"Current last processed: {last}")

    # ==================================================
    # OPTION B:
    # If no state exists, sync to the current latest
    # and DO NOT process historical items
    # ==================================================
    if last == -1:
        max_position = get_max_position(data)
        save_state(max_position)
        log(f"Initial state created at position {max_position}")
        log("Historical images will not be processed.")
        log("===== END =====")
        return

    # Search for new items
    pending = [x for x in data if x.get("position", 0) > last]

    if not pending:
        log("No new images found.")
        log("===== END =====")
        return

    total = len(pending)
    log(f"New images found: {total}")

    for i, item in enumerate(pending, start=1):
        position = item.get("position", i)
        prompt_base = item.get("prompt_base", "404 Error")
        final_prompt = f"{prompt_base}. {FIXED_PROMPT}"

        log(f"\n[{i}/{total}] Processing position {position}")

        try:
            ok = generate_image(final_prompt, position)

            if ok:
                save_state(position)
            else:
                log(f"[{position}] Failed after multiple attempts")

        except Exception as e:
            log(f"CRITICAL ERROR: {e}")
            break

        time.sleep(2)

    log("===== END =====")


if __name__ == "__main__":
    main()