"""
Placeholder para Alex.
Genera imágenes AI usando la descripción guardada en data/jsons.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
JSON_DIR = BASE_DIR / "data" / "jsons"
NEWS_DIR = BASE_DIR / "data" / "news"

load_dotenv()


def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GEMINI_API_KEY en el .env")

    gallery_json = JSON_DIR / "reuters_march_2026_gallery.json"
    data = json.loads(gallery_json.read_text(encoding="utf-8"))

    for item in data["items"]:
        prompt = item["short_description"] or item["caption_original"]
        ai_filename = item["filename"].replace("REAL_", "AI_")
        ai_output = NEWS_DIR / ai_filename

        # TODO:
        # 1. Llamar Gemini / Imagen API
        # 2. Generar imagen con base en prompt
        # 3. Guardar el resultado en ai_output
        # 4. Actualizar JSON si quieren guardar ai_prompt, ai_model, etc.

        print(f"Pending AI generation for {ai_filename}")
        print(f"Prompt: {prompt}\n")


if __name__ == "__main__":
    main()
