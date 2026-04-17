import os
import json
from datetime import datetime
from google import genai
from google.genai import types
import time

# ==================================================
# CONFIGURACIÓN API
# ==================================================
API_KEY = "AIzaSyD4_wC1fTKtaKzz9bjjLwdjZZHoZbVzyyU"
client = genai.Client(api_key=API_KEY)


def generar_imagenes_gemini():
    # Carpeta donde está este script
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Si el script está dentro de una subcarpeta y quieres subir al proyecto raíz:
    project_dir = os.path.dirname(base_dir)

    # JSON en proyecto/data/jsons/ImagesData.json
    json_path = os.path.join(project_dir, "data", "jsons", "image_objects.json")

    # Imágenes en proyecto/data/news
    carpeta = os.path.join(project_dir, "data", "news")
    os.makedirs(carpeta, exist_ok=True)

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

    for i, item in enumerate(datos):
        prompt_texto = item.get("prompt_base", "Un paisaje futurista")
        position = item.get("position", i)

        print(f"\nGenerando imagen {i+1}/{len(datos)}")
        print("Prompt:", prompt_texto)

        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=str(prompt_texto),
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
                    nombre = f"AI_{position}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
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