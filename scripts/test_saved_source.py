from pathlib import Path

path = Path("data/jsons/reuters_source.html")
html = path.read_text(encoding="utf-8")

print("File exists:", path.exists())
print("Length:", len(html))
print("Has [1/65]:", "[1/65]" in html)
print("Has Share this photo:", "Share this photo" in html)
print("Has title:", "Pictures of the month: March" in html)