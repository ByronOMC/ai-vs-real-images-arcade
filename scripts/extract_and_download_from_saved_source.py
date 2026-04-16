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
        r'\{"@type":"ImageObject".+?"contentUrl":"(https://www\.reuters\.com/resizer/v2/[^"]+?)".+?"caption":"(.*?)".+?"position":(\d+)',
        re.DOTALL
    )

    records = []
    for match in pattern.finditer(html):
        url = match.group(1)
        caption = match.group(2).replace('\\"', '"').strip()
        position = int(match.group(3))

        records.append({
            "position": position,
            "contentUrl": url,
            "caption": caption,
        })

    # sort by Reuters position
    records.sort(key=lambda x: x["position"])
    return records

def save_urls(urls: list[str]) -> None:
    (JSON_DIR / "image_urls.txt").write_text("\n".join(urls), encoding="utf-8")
    (JSON_DIR / "image_urls.json").write_text(json.dumps(urls, indent=2), encoding="utf-8")

def download_images(urls: list[str]) -> int:
    downloaded = 0

    for idx, url in enumerate(urls[:65], start=1):
        output = NEWS_DIR / f"REAL_{idx:03d}.jpg"
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

    # Prefer ImageObject URLs when available because they also map to positions/captions
    imageobject_urls = [item["contentUrl"] for item in image_objects if item.get("contentUrl")]
    final_urls = dedupe_keep_order(imageobject_urls + preload_urls)

    print(f"Unique final URLs: {len(final_urls)}")

    save_urls(final_urls)
    (JSON_DIR / "image_objects.json").write_text(json.dumps(image_objects, indent=2, ensure_ascii=False), encoding="utf-8")

    if not final_urls:
        raise RuntimeError("No image URLs found in saved source file.")

    downloaded = download_images(final_urls)

    print("\nDone.")
    print(f"Downloaded images: {downloaded}")
    print(f"Saved URL list to: {JSON_DIR / 'image_urls.txt'}")
    print(f"Saved metadata to: {JSON_DIR / 'image_objects.json'}")

if __name__ == "__main__":
    main()