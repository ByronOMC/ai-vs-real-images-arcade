import os
import json
import time
from datetime import datetime
from google import genai
from google.genai import types

# ==================================================
# CONFIG
# 1- Ejecutar en la terminal pip install -U google-genai
# 2- Crear una variable de ambiente llamada "GEMINI_API_KEY" si aun no exite (ver el key en AI Studio Google)
# 3- Configurar la variable de ambiente para que la lea el script
# ==================================================

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("No existe GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.1-flash-image-preview"
MAX_REINTENTOS = 3
ESPERA_SEGUNDOS = 3

PROMPT_FIJO = """
Photorealistic image, captured as if taken by a professional photographer using a Canon EOS R5 with a 50mm lens at f/1.8, natural lighting, realistic shadows and highlights, shallow depth of field with soft background blur (bokeh), accurate skin tones and textures, subtle imperfections, slight film grain, true-to-life colors, high dynamic range, documentary photography style, editorial photo, realistic environment, candid moment, no CGI, no illustration, not stylized
"""

# ==================================================
# PATHS
# ==================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

JSON_PATH = os.path.join(PROJECT_DIR, "data", "jsons", "image_objects.json")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "data", "news")
ESTADO_PATH = os.path.join(PROJECT_DIR, "data", "jsons", "image_state.json")
LOG_PATH = os.path.join(PROJECT_DIR, "data", "Image_logs.txt")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==================================================
# HELPERS
# ==================================================
def log(msg):
    print(msg)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - {msg}\n")


def obtener_ultimo():
    if not os.path.exists(ESTADO_PATH):
        return -1

    try:
        with open(ESTADO_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("ultimo_position", -1)
    except:
        return -1


def guardar_estado(position):
    with open(ESTADO_PATH, "w", encoding="utf-8") as f:
        json.dump({"ultimo_position": position}, f, indent=2)


def cargar_json():
    if not os.path.exists(JSON_PATH):
        raise FileNotFoundError(f"No existe {JSON_PATH}")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("El JSON debe ser una lista")

    return data


def obtener_max_position(datos):
    if not datos:
        return 0
    return max(item.get("position", 0) for item in datos)


# ==================================================
# GENERAR IMAGEN
# ==================================================
def generar_imagen(prompt, position):
    for intento in range(1, MAX_REINTENTOS + 1):
        try:
            log(f"[{position}] Intento {intento}")

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"]
                )
            )

            if not response.candidates:
                raise Exception("Sin candidates")

            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    filename = f"AI_{position}.png"
                    ruta = os.path.join(OUTPUT_DIR, filename)

                    if os.path.exists(ruta):
                        log(f"[{position}] Ya existe {filename}, se omite.")
                        return True

                    with open(ruta, "wb") as f:
                        f.write(part.inline_data.data)

                    log(f"[{position}] Imagen guardada: {filename}")
                    return True

            raise Exception("No vino imagen")

        except Exception as e:
            log(f"[{position}] Error: {e}")

            if "401" in str(e) or "UNAUTHENTICATED" in str(e):
                raise Exception("API KEY inválida o no autorizada")

            time.sleep(ESPERA_SEGUNDOS)

    return False


# ==================================================
# MAIN
# ==================================================
def main():
    log("===== INICIO =====")

    try:
        datos = cargar_json()
    except Exception as e:
        log(f"Error cargando JSON: {e}")
        return

    if not datos:
        log("El JSON está vacío.")
        return

    ultimo = obtener_ultimo()
    log(f"Último procesado actual: {ultimo}")

    # ==================================================
    # OPCIÓN B:
    # Si no existe estado, sincroniza al último actual
    # y NO procesa históricos
    # ==================================================
    if ultimo == -1:
        max_position = obtener_max_position(datos)
        guardar_estado(max_position)
        log(f"Estado inicial creado en position {max_position}")
        log("No se procesan imágenes históricas.")
        log("===== FIN =====")
        return

    # Buscar nuevos elementos
    pendientes = [x for x in datos if x.get("position", 0) > ultimo]

    if not pendientes:
        log("No hay imágenes nuevas.")
        log("===== FIN =====")
        return

    total = len(pendientes)
    log(f"Imágenes nuevas encontradas: {total}")

    for i, item in enumerate(pendientes, start=1):
        position = item.get("position", i)
        prompt_base = item.get("prompt_base", "Error 404")
        prompt_final = f"{prompt_base}. {PROMPT_FIJO}"

        log(f"\n[{i}/{total}] Procesando position {position}")

        try:
            ok = generar_imagen(prompt_final, position)

            if ok:
                guardar_estado(position)
            else:
                log(f"[{position}] Falló después de varios intentos")

        except Exception as e:
            log(f"ERROR CRÍTICO: {e}")
            break

        time.sleep(2)

    log("===== FIN =====")


if __name__ == "__main__":
    main()