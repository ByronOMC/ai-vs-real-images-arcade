import os
import requests
import urllib.parse
import json
import urllib3
import base64
import random
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración
URL_REUTERS = "https://www.reuters.com/world/"

# --- CONFIGURACIÓN DE RUTAS ---
BASE_PROJECT_PATH = Path(__file__).resolve().parent.parent
BASE_DIR = os.path.join(BASE_PROJECT_PATH, "data")
PATH_HTML = os.path.join(BASE_DIR, "html")
PATH_JSON = os.path.join(BASE_DIR, "jsons")
PATH_NEWS = os.path.join(BASE_DIR, "news")

# --- CONFIGURACIÓN DE .ENV ---
dotenv_path = os.path.join(BASE_PROJECT_PATH, ".env.dev")
load_dotenv(dotenv_path)
API_KEY = os.getenv("SCRAPING_ANT_KEY")

# Aseguramos que existan en la ubicación correcta
for folder in [PATH_HTML, PATH_JSON, PATH_NEWS]:
    os.makedirs(folder, exist_ok=True)

def mantenimiento_limpieza_mensual():
    # Usamos las rutas globales definidas al inicio del script
    nombre_json = os.path.join(PATH_JSON, "data.json")
    
    if not os.path.exists(nombre_json):
        return

    hoy = datetime.now()
    # Solo actúa los primeros 3 días del mes
    if hoy.day > 3:
        print(f"--- Hoy es {hoy.strftime('%d/%m')}: No toca limpieza de archivos antiguos ---")
        return

    print("--- INICIANDO MANTENIMIENTO INTEGRAL (Cambio de Mes) ---")
    
    with open(nombre_json, "r", encoding="utf-8") as f:
        try:
            datos = json.load(f)
        except:
            return

    # Definimos el umbral: 3 días atrás desde hoy
    fecha_limite = hoy - timedelta(days=3)
    
    datos_filtrados = []
    imagenes_a_mantener = set()

    # 1. Filtrar el JSON
    for noticia in datos:
        try:
            fecha_noticia = datetime.strptime(noticia["fecha"], "%Y-%m-%d")
            if fecha_noticia >= fecha_limite:
                datos_filtrados.append(noticia)
                if "imagen_real" in noticia:
                    # Guardamos solo el nombre del archivo, sin la ruta completa
                    imagenes_a_mantener.add(os.path.basename(noticia["imagen_real"]))
        except:
            continue

    # 2. Guardar el JSON actualizado (solo si hubo cambios)
    if len(datos_filtrados) < len(datos):
        with open(nombre_json, "w", encoding="utf-8") as f:
            json.dump(datos_filtrados, f, ensure_ascii=False, indent=4)
        print(f"✓ JSON actualizado: Se conservaron {len(datos_filtrados)} noticias.")

        # 3. Limpieza física de imágenes en PATH_NEWS
        archivos_news = os.listdir(PATH_NEWS)
        borrados_img = 0
        for archivo in archivos_news:
            if archivo.endswith(".jpg") and archivo not in imagenes_a_mantener:
                try:
                    os.remove(os.path.join(PATH_NEWS, archivo))
                    borrados_img += 1
                except: pass
        print(f"✓ Imágenes: Se eliminaron {borrados_img} archivos antiguos.")
    else:
        print("--- El JSON ya estaba limpio ---")

    # 4. Limpieza de HTMLs antiguos (opcional pero recomendado)
    # Borramos cualquier HTML que no sea el de hoy para mantener la carpeta PATH_HTML ligera
    archivos_html = os.listdir(PATH_HTML)
    fecha_hoy_str = hoy.strftime("%Y-%m-%d")
    borrados_html = 0
    for html_file in archivos_html:
        if html_file.endswith(".html") and fecha_hoy_str not in html_file:
            try:
                os.remove(os.path.join(PATH_HTML, html_file))
                borrados_html += 1
            except: pass
    
    if borrados_html > 0:
        print(f"✓ Caché HTML: Se eliminaron {borrados_html} archivos de días anteriores.")
    
    print("-------------------------------------------\n")

def generar_configuracion_aleatoria():
    # 1. Países con buenos pools de IPs residenciales
    paises = ['us', 'gb', 'de']

    # 2. Diferentes tiempos de espera (para no ser mecánicos)
    esperas = [5000, 8000, 10000]
    
    # 3. Diferentes User-Agents (Windows, Mac, Linux)
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ]

    return {
        "country": random.choice(paises),
        "wait": random.choice(esperas),
        "ua": random.choice(user_agents),
        "antibot": "true"
    }

def obtener_html_ant(url, forzar=False):
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    archivo_cache = os.path.join(PATH_HTML, f"reuters_{fecha_hoy}.html")
    # 1. Lógica de Caché
    if os.path.exists(archivo_cache) and not forzar:
        print(f"--- Usando caché local ({archivo_cache}) ---")
        with open(archivo_cache, "r", encoding="utf-8") as f:
            return f.read()

    # 2. Generamos los valores aleatorios para hoy
    config = generar_configuracion_aleatoria()
    print(f"--- Configuración del día: País={config['country']}, Espera={config['wait']}ms, AntiBot={config['antibot']} ---")

    # 3. Configuración de ScrapingAnt
    print(f"--- Solicitando a ScrapingAnt... (Espera unos 30-40 segundos) ---")
    encoded_url = urllib.parse.quote(url)
    encoded_ua = urllib.parse.quote(config['ua'])
   
    # JS Snippet para scroll
    js_code = "window.scrollTo(0, document.body.scrollHeight);"
    js_base64 = base64.b64encode(js_code.encode('utf-8')).decode('utf-8')
    js_snippet_param = urllib.parse.quote(js_base64)
    
    # Selector del feed
    selector_param = urllib.parse.quote("section[data-testid='Body']")

    ant_url = (
        f"https://api.scrapingant.com/v2/general?"
        f"url={encoded_url}&"
        f"browser=true&"
        f"proxy_type=residential&"
        f"proxy_country={config['country']}&"
        f"antibot=true&" 
        f"wait_for_selector={selector_param}"
    )
    
    headers = {'x-api-key': API_KEY}
    
    try:
        # Timeout extendido por si el proxy residencial es lento
        res = requests.get(ant_url, headers=headers, timeout=180, verify=False)
        
        if res.status_code == 200:
            html_content = res.text
            
            # Detección de bloqueos (DataDome / Captcha)
            if "captcha-delivery" in html_content or "DataDome" in html_content:
                ruta_bloqueo = os.path.join(PATH_HTML, "bloqueo_captcha.html")
                with open(ruta_bloqueo, "w", encoding="utf-8") as f:
                    f.write(html_content)
                print(f"Bloqueo detectado. HTML de captcha guardado en: {ruta_bloqueo}")
                return None
                
            if len(html_content) < 5000: # Subimos el umbral a 5kb para Reuters
                print("Advertencia: El HTML es sospechosamente corto.")
            
            # Guardamos con éxito
            with open(archivo_cache, "w", encoding="utf-8") as f:
                f.write(html_content)
                
            print(f"HTML guardado exitosamente.")
            return html_content
        
        elif res.status_code == 422:
            print("Error 422: Problema de parámetros.")
            print(f"Detalle: {res.text}")
            return None
            
        else:
            print(f"Error de ScrapingAnt: {res.status_code}")
            error_log = os.path.join(PATH_HTML, f"error_{res.status_code}.html")
            with open(error_log, "w", encoding="utf-8") as f:
                f.write(res.text)
            return None
            
    except requests.exceptions.Timeout:
        print("Error: La petición excedió el tiempo de espera.")
    except Exception as e:
        print(f"Error inesperado: {e}")
        
    return None

def obtener_prompt_maestro(titulo_real, descripcion_real):
    """
    Construye y retorna el prompt maestro inyectando la noticia real.
    """
    prompt = f"""Actúa como un experto en desinformación y psicología de la comunicación.
    Tu objetivo es crear una "noticia falsa de alta fidelidad" basada en una noticia real que te proporcionaré.
    Esta noticia falsa debe servir para un juego de pensamiento crítico donde el usuario debe adivinar cuál es la real.

    REGLAS ESTRICTAS PARA LA NOTICIA FALSA:
    1. Tono: Usa un estilo periodístico serio, neutral y profesional (estilo Reuters o BBC).
    2. Técnica de Distorsión: No inventes algo absurdo. Toma el tema central y cambia la causa o el actor principal por algo verosímil (ej. economía, crisis de vivienda, tecnología, nuevas leyes).
    3. Anclaje en la Realidad: Usa conceptos conocidos (ej. "Gentrificación", "Crisis de suministros", "Nuevos protocolos de la OTAN").

    ESTRUCTURA DE SALIDA REQUERIDA (JSON):
    {{
    "titulo_ia": "Titular impactante pero creíble",
    "descripcion_ia": "Breve explicación de la noticia distorsionada"
    }}

    NOTICIA REAL DE REFERENCIA:
    Título: {titulo_real}
    Descripción: {descripcion_real}
    """
    return prompt

def generar_contenido_ia(titulo_real, descripcion_real):
    full_prompt = obtener_prompt_maestro(titulo_real, descripcion_real)
    
    # --- PRÓXIMAMENTE: Conexión con la API de IA ---
    # response = client.chat.completions.create(prompt=full_prompt...)
    
    # Por ahora, devolvemos un placeholder que respeta la estructura
    return {
        "titulo_ia": "titulo ia por default",
        "descripcion_ia": "descripcion ia por default"
    }

def descargar_imagen_hd(src, ruta_final):
    if not os.path.exists(ruta_final):
        # Limpiamos la URL para pedir 1200px
        base_url = src.split('?')[0]
        auth = src.split('auth=')[1].split('&')[0] if 'auth=' in src else ""
        url_1200 = f"{base_url}?auth={auth}&width=1200&height=800&quality=100"
        
        try:
            response = requests.get(url_1200, timeout=15, verify=False)
            if response.status_code == 200:
                with open(ruta_final, 'wb') as f:
                    f.write(response.content)
                return True
        except:
            pass
    return False

def procesar_y_actualizar_json(html):
    if not html: return

    nombre_archivo = os.path.join(PATH_JSON, "data.json")

    # 2. Cargar base de datos existente
    if os.path.exists(nombre_archivo):
        with open(nombre_archivo, "r", encoding="utf-8") as f:
            try:
                base_datos = json.load(f)
            except:
                base_datos = []
    else:
        base_datos = []

    links_registrados = {noticia["link"] for noticia in base_datos}
    
    soup = BeautifulSoup(html, "html.parser")
    articulos_html = soup.find_all("li", attrs={"data-testid": "FeedListItem"})
    print(f"Analizando {len(articulos_html)} elementos en el feed...")
    
    nuevas_noticias = []

    for art in articulos_html:
        if len(nuevas_noticias) >= 5: break

        link_tag = art.find("a", attrs={"data-testid": "TitleLink"})
        img_tag = art.find("img")
        
        if not link_tag or not img_tag: continue

        url_relativa = link_tag.get("href", "")
        link_completo = f"https://www.reuters.com{url_relativa}"
        if link_completo in links_registrados: continue

        src = img_tag.get("src", "")
        alt_text = img_tag.get("alt", "").lower()
        
        if "reuters logo" in alt_text or "logo" in alt_text: continue
        if ".png" in src.lower() or "resizer" not in src: continue

        # --- EXTRACCIÓN Y LIMPIEZA ---
        titulo_real = art.find(attrs={"data-testid": "TitleHeading"}).get_text(strip=True)
        titulo_real = titulo_real.replace('\u200c', '').replace('\u200b', '')

        desc_tag = art.find(attrs={"data-testid": "Description"})
        descripcion_real = desc_tag.get_text(strip=True).replace('\u200c', '').replace('\u200b', '') if desc_tag else "Sin descripción"

        time_tag = art.find("time", attrs={"data-testid": "DateLineText"})
        fecha_real = time_tag.get("datetime", "")[:10] if time_tag else ""

        # --- GESTIÓN DE IMAGEN CON SUFIJO _REAL ---
        slug = url_relativa.split('/')[-2] if url_relativa.endswith('/') else url_relativa.split('/')[-1]
        nombre_img = f"{slug[:50]}_real.jpg"
        ruta_local_archivo = os.path.join(PATH_NEWS, nombre_img)

        exito_descarga = descargar_imagen_hd(src, ruta_local_archivo)

        # --- LÓGICA DE POSICIÓN ---
        # La posición es el total de noticias ya guardadas + las que llevamos en este ciclo
        posicion_actual = len(base_datos) + len(nuevas_noticias)

        # Generar contenido IA
        contenido_ia = generar_contenido_ia(titulo_real, descripcion_real)

        #Ruta de la imagen para el JSON (relativa a la carpeta del proyecto)
        ruta_para_json = os.path.join("data", "news", nombre_img).replace("\\", "/")
        
        nueva_noticia = {
            "position": posicion_actual,
            "titulo_real": titulo_real,
            "descripcion_real": descripcion_real,
            "imagen_real": ruta_para_json,
            "titulo_ia": contenido_ia["titulo_ia"],
            "descripcion_ia": contenido_ia["descripcion_ia"],
            "imagen_ia": "pendiente",
            "fecha": fecha_real,
            "link": link_completo
        }

        nuevas_noticias.append(nueva_noticia)
        links_registrados.add(link_completo)
        
        status = "Nueva noticia y FOTO descargada" if exito_descarga else "+ Nueva noticia agregada (La foto ya existía)"
        print(f"  {status}: {titulo_real[:50]}...")

    # 3. Guardado y Reporte
    if nuevas_noticias:
        base_datos.extend(nuevas_noticias)
        with open(nombre_archivo, "w", encoding="utf-8") as f:
            json.dump(base_datos, f, ensure_ascii=False, indent=4)
        print(f"\nÉXITO: Se agregaron {len(nuevas_noticias)} noticias nuevas.")
        print(f"El archivo 'data.json' ahora tiene un total de {len(base_datos)} noticias.")
    else:
        print("\n--- REPORTE FINAL ---")
        print(f"El archivo 'data.json' e imágenes ya están actualizados.")
        print(f"No se encontraron noticias nuevas en el feed actual. Tarea finalizada.")

    print("-------------------------------------------\n")

if __name__ == "__main__":
    # 1. Primero la limpieza
    mantenimiento_limpieza_mensual()
    # 2. Luego el scraping
    html = obtener_html_ant(URL_REUTERS)
    # 3. Finalmente el procesamiento
    if html:
        procesar_y_actualizar_json(html)
