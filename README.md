# AI vs Real Images Arcade

Proyecto base en Python para un arcade interno que compara imágenes reales de noticias vs imágenes generadas por IA.

## Objetivo
1. Descargar las imágenes reales y su metadata desde Reuters.
2. Guardar las imágenes reales con prefijo `REAL_` en `data/news/`.
3. Guardar el JSON consolidado y los JSON individuales en `data/jsons/`.
4. En una segunda fase, generar imágenes sintéticas con prefijo `AI_` a partir de la descripción de cada imagen.
5. En una tercera fase, evaluar frecuencia de ejecución, scheduling y opciones de conexión remota/SSH.

## Estructura

```bash
arcade_ai_vs_real/
├── data/
│   ├── news/                 # imágenes reales y luego imágenes AI
│   └── jsons/                # metadata consolidada e individual
├── scripts/
│   ├── scrape_reuters_gallery.py
│   ├── generate_ai_images.py
│   └── scheduler_notes.py
├── requirements.txt
├── .env.example
└── README.md
```

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
pip install -r requirements.txt
playwright install chromium
```

## Ejecutar Task #1

```bash
python scripts/scrape_reuters_gallery.py
```

## Output esperado

- `data/news/REAL_001.jpg` ... `REAL_065.jpg`
- `data/jsons/reuters_march_2026_gallery.json`
- `data/jsons/REAL_001.json` ... `REAL_065.json`

## Notas
- El script usa Playwright porque Reuters puede renderizar parte del contenido dinámicamente.
- El script intenta capturar:
  - índice
  - caption original
  - caption corto sugerido
  - location
  - image_url
  - local_image_path
  - source_page
- Si luego quieren cortar o reformular la descripción, ya dejé un campo `short_description`.
- Reuters y sus imágenes tienen derechos/licencias. Úsenlo únicamente según las reglas internas y permisos aplicables.
