from pathlib import Path
from html import unescape
import json
import re
import time

import requests

BASE_DIR = Path(__file__).resolve().parents[1]
SOURCE_FILE = BASE_DIR / "data" / "jsons" / "reuters_source.html"
NEWS_DIR = BASE_DIR / "data" / "news"
JSON_DIR = BASE_DIR / "data" / "jsons"

NEWS_DIR.mkdir(parents=True, exist_ok=True)
JSON_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://www.reuters.com/",
    "Accept-Language": "en-US,en;q=0.9",
}


def dedupe_keep_order(items):
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def clean_caption(caption: str) -> str:
    """
    Limpia escapes, espacios y créditos finales.
    """
    if not caption:
        return ""

    text = caption.strip()
    text = text.replace('\\"', '"')
    text = re.sub(r"\s+", " ", text).strip()

    # quita créditos tipo REUTERS/Nombre
    text = re.sub(r"\s+REUTERS\/.*$", "", text, flags=re.IGNORECASE)

    # quita créditos tipo Nombre/Agencia
    text = re.sub(
        r"\s+[A-Z][A-Za-z.\-']+(?:\s+[A-Z][A-Za-z.\-']+)*\/[A-Z].*$",
        "",
        text
    )

    return text.strip()


def is_caption_incomplete(caption: str) -> bool:
    """
    Detecta captions sospechosamente cortados.
    """
    if not caption:
        return True

    text = caption.strip()

    bad_endings = ('\\', '/', ' for "', ' for', ' at "', ' wins the Oscar for Best Cinematography for "')
    if text.endswith('"') or text.endswith("\\"):
        return True

    for ending in bad_endings:
        if text.endswith(ending):
            return True

    # demasiado corto para ser útil
    if len(text) < 30:
        return True

    return False


def build_prompt_base(caption: str) -> str:
    """
    Prompt base para Alex. Si el caption viene incompleto,
    devolvemos algo utilizable pero conservador.
    """
    cleaned = clean_caption(caption)

    if is_caption_incomplete(cleaned):
        return "A realistic documentary-style news photo of a real-world event, captured by a professional photojournalist."

    return cleaned


def extract_urls_from_preload(html: str) -> list[str]:
    """
    Extract highest-res Reuters image URL from imageSrcSet preload tags.
    Prefer width=1920 when present.
    """
    html = unescape(html)

    pattern = re.compile(
        r'imageSrcSet="([^"]+)"',
        re.IGNORECASE
    )

    urls = []
    for match in pattern.finditer(html):
        srcset = match.group(1)
        parts = [p.strip() for p in srcset.split(",") if p.strip()]

        best_url = None
        for part in parts:
            candidate = part.split(" ")[0].strip()
            if "reuters.com/resizer/v2/" not in candidate or ".jpg" not in candidate.lower():
                continue
            if "width=1920" in candidate:
                best_url = candidate
                break
            if best_url is None:
                best_url = candidate

        if best_url:
            urls.append(best_url)

    return dedupe_keep_order(urls)


def extract_metadata_from_imageobjects(html: str) -> list[dict]:
    """
    Extract Reuters ImageObject entries from the saved HTML.
    """
    html = unescape(html)

    pattern = re.compile(
    r'\{"@type":"ImageObject".+?"contentUrl":"(https://www\.reuters\.com/resizer/v2/[^"]+?)".+?"caption":"((?:\\.|[^"\\])*)".+?"position":(\d+)',
    re.DOTALL
    )

    records = []
    for match in pattern.finditer(html):
        url = match.group(1)
        caption_raw = bytes(match.group(2), "utf-8").decode("unicode_escape").strip()
        caption_clean = clean_caption(caption_raw)
        position = int(match.group(3))

        records.append({
            "position": position,
            "contentUrl": url,
            "caption": caption_raw.replace('\\"', '"'),
            "caption_clean": caption_clean,
            "caption_incomplete": is_caption_incomplete(caption_clean),
            "prompt_base": build_prompt_base(caption_raw),
        })

    records.sort(key=lambda x: x["position"])
    return records


def save_urls(urls: list[str]) -> None:
    (JSON_DIR / "image_urls.txt").write_text("\n".join(urls), encoding="utf-8")
    (JSON_DIR / "image_urls.json").write_text(json.dumps(urls, indent=2), encoding="utf-8")


def download_images(urls: list[str]) -> int:
    downloaded = 0

    for idx, url in enumerate(urls[:65]):
        output = NEWS_DIR / f"REAL_{idx}.jpg"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=90)
            resp.raise_for_status()
            output.write_bytes(resp.content)
            downloaded += 1
            print(f"Downloaded {output.name}")
            time.sleep(1.2)
        except Exception as exc:
            print(f"Failed {output.name}: {exc}")

    return downloaded


def main():
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Missing file: {SOURCE_FILE}")

    html = SOURCE_FILE.read_text(encoding="utf-8", errors="ignore")

    preload_urls = extract_urls_from_preload(html)
    image_objects = extract_metadata_from_imageobjects(html)

    print(f"Preload URLs found: {len(preload_urls)}")
    print(f"ImageObject records found: {len(image_objects)}")

    imageobject_urls = [item["contentUrl"] for item in image_objects if item.get("contentUrl")]
    final_urls = dedupe_keep_order(imageobject_urls + preload_urls)

    print(f"Unique final URLs: {len(final_urls)}")

    incomplete_count = sum(1 for item in image_objects if item.get("caption_incomplete"))
    print(f"Incomplete captions detected: {incomplete_count}")

    save_urls(final_urls)
    (JSON_DIR / "image_objects.json").write_text(
        json.dumps(image_objects, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    if not final_urls:
        raise RuntimeError("No image URLs found in saved source file.")

    downloaded = download_images(final_urls)

    print("\nDone.")
    print(f"Downloaded images: {downloaded}")
    print(f"Saved URL list to: {JSON_DIR / 'image_urls.txt'}")
    print(f"Saved metadata to: {JSON_DIR / 'image_objects.json'}")


if __name__ == "__main__":
    main()