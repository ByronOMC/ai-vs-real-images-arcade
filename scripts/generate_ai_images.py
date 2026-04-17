import os
import json
from google import genai
from google.genai import types
import time

# ==================================================
# CONFIGURACIÓN API
# ==================================================
API_KEY = "AQ.Ab8RN6JQXeosQrJTLn3xC4xHJ8a9GNHzHmfncNX-sM3D28PcOA"
client = genai.Client(api_key=API_KEY)

# ==================================================
# PROMPT FIJO GLOBAL
# ==================================================
PROMPT_FIJO = """
Photorealistic image, captured as if taken by a professional photographer using a Canon EOS R5 with a 50mm lens at f/1.8, natural lighting, realistic shadows and highlights, shallow depth of field with soft background blur (bokeh), accurate skin tones and textures, subtle imperfections, slight film grain, true-to-life colors, high dynamic range, documentary photography style, editorial photo, realistic environment, candid moment, no CGI, no illustration, not stylized
"""


def generar_imagenes_gemini():
    # Carpeta donde está este script
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Subir al directorio raíz del proyecto
    project_dir = os.path.dirname(base_dir)

    # JSON
    json_path = os.path.join(project_dir, "data", "jsons", "image_objects.json")

    # Carpeta destino imágenes
    carpeta = os.path.join(project_dir, "data", "news")
    os.makedirs(carpeta, exist_ok=True)

    # ==================================================
    # LEER JSON
    # ==================================================
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            datos = json.load(f)

        if not isinstance(datos, list) or len(datos) == 0:
            print("JSON vacío o formato incorrecto.")
            return

    except FileNotFoundError:
        print("No se encontró:", json_path)
        return

    except Exception as e:
        print("Error leyendo JSON:", e)
        return

    # ==================================================
    # GENERAR IMÁGENES
    # ==================================================
    for i, item in enumerate(datos):
        prompt_json = item.get("prompt_base", "Un paisaje futurista")
        position = item.get("position", i)

        # Prompt final combinado
        prompt_texto = f"{prompt_json}. {PROMPT_FIJO}"

        print(f"\nGenerando imagen {i+1}/{len(datos)}")
        print("Prompt:", prompt_texto)

        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=prompt_texto,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"]
                )
            )

            if not response.candidates:
                print("Gemini no devolvió resultados.")
                continue

            imagen_guardada = False

            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    nombre = f"AI_{position}.png"
                    ruta = os.path.join(carpeta, nombre)

                    with open(ruta, "wb") as f:
                        f.write(part.inline_data.data)

                    print("Imagen guardada:", ruta)
                    imagen_guardada = True
                    break

            if not imagen_guardada:
                print("No se recibió imagen.")

        except Exception as e:
            print("Error Gemini:", e)

        time.sleep(2)


if __name__ == "__main__":
    generar_imagenes_gemini()