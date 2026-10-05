#!/usr/bin/env python3
"""Download official Steam store media for steam_games.txt (slug|appid|category).

Writes images/<slug>/{header,capsule,library_600x900,library_hero}.jpg, ss-NN.jpg (1920x1080
screenshots), gif-NN.png (first frame of GIFs embedded in the store description) and
meta/<slug>.json (trimmed appdetails). Skips files that already exist.
"""
import io, json, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
MAX_SS = 10
MAX_GIF = 3
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
ASSET = "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{app}/{name}"


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None
            if e.code == 429:
                time.sleep(30)
        except Exception:
            pass
        time.sleep(2 * (i + 1))
    return None


def appdetails(app):
    raw = get(f"https://store.steampowered.com/api/appdetails?appids={app}&cc=us&l=english")
    d = json.loads(raw)[str(app)]
    return d["data"] if d.get("success") else None


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def fetch(slug, app, category):
    out = ROOT / "images" / slug
    meta_path = ROOT / "meta" / f"{slug}.json"
    if meta_path.exists():
        d = json.loads(meta_path.read_text())["appdetails"]
    else:
        d = appdetails(app)
        if not d:
            print(f"!! {slug}: no appdetails", flush=True)
            return
    sources = {}
    art = {"header": d.get("header_image"), "capsule": ASSET.format(app=app, name="capsule_616x353.jpg"),
           "library_600x900": ASSET.format(app=app, name="library_600x900.jpg"),
           "library_hero": ASSET.format(app=app, name="library_hero.jpg")}
    for name, url in art.items():
        if not url:
            continue
        p = out / f"{name}.jpg"
        if not p.exists():
            data = get(url)
            if not data:
                continue
            save(p, data)
        sources[p.name] = ("art", url)
    for i, ss in enumerate(d.get("screenshots", [])[:MAX_SS], 1):
        p = out / f"ss-{i:02d}.jpg"
        if not p.exists():
            data = get(ss["path_full"])
            if not data:
                continue
            save(p, data)
        sources[p.name] = ("screenshot", ss["path_full"])
    gifs = re.findall(r'src="(https://[^"]+?\.gif)[^"]*"', d.get("detailed_description", ""))
    n = 0
    for url in dict.fromkeys(gifs):
        if n >= MAX_GIF:
            break
        p = out / f"gif-{n + 1:02d}.png"
        if not p.exists():
            data = get(url)
            if not data:
                continue
            try:
                im = Image.open(io.BytesIO(data))
                if im.width < 300:
                    continue
                im.seek(0)
                p.parent.mkdir(parents=True, exist_ok=True)
                im.convert("RGB").save(p, optimize=True)
            except Exception:
                continue
        sources[p.name] = ("gif-still", url)
        n += 1
    keep = {k: d.get(k) for k in ("name", "steam_appid", "short_description", "developers", "publishers",
                                  "genres", "release_date", "website", "header_image", "screenshots",
                                  "detailed_description", "categories")}
    meta_path.parent.mkdir(exist_ok=True)
    meta_path.write_text(json.dumps({"slug": slug, "appid": app, "category": category,
                                     "appdetails": keep, "sources": sources}, indent=1))
    print(f"ok {slug}: {len(sources)} files", flush=True)


def main():
    rows = [l.strip().split("|") for l in (ROOT / "steam_games.txt").read_text().splitlines() if l.strip()]
    only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
    rows = [r for r in rows if not only or r[0] in only]
    with ThreadPoolExecutor(6) as ex:
        for r in rows:
            ex.submit(fetch, r[0], int(r[1]), r[2])


if __name__ == "__main__":
    main()
