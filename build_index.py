#!/usr/bin/env python3
"""Build games.jsonl, manifest.jsonl, thumbs/ and index.html from images/, shots/ and meta/."""
import hashlib, html, json, time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
Image.MAX_IMAGE_PIXELS = None
CATEGORIES = ["cozy-builder", "cozy-adventure", "stylized-adventure", "stylized-action", "stylized-puzzle",
              "stylized-strategy"]
KIND_ORDER = {"screenshot": 0, "gif-still": 1, "page-image": 2, "art": 3}
ART_ORDER = ["library_hero", "capsule", "header", "library_600x900"]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def thumb(src, name, crop_tall=False):
    t = ROOT / "thumbs" / name
    if not t.exists():
        with Image.open(src) as im:
            im = im.convert("RGB")
            if crop_tall:
                im = im.crop((0, 0, im.width, min(im.height, int(im.width * 2.0))))
            im.thumbnail((480, 960))
            im.save(t, quality=80)
    return f"thumbs/{name}"


def mtime_iso(p):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(p.stat().st_mtime))


games = {}
for line in (ROOT / "steam_games.txt").read_text().splitlines():
    if line.strip():
        slug, app, cat = line.split("|")
        m = json.loads((ROOT / "meta" / f"{slug}.json").read_text())
        d = m["appdetails"]
        games[slug] = dict(slug=slug, name=d["name"], category=cat, source="steam", steam_appid=int(app),
                           url=f"https://store.steampowered.com/app/{app}/", website=d.get("website"),
                           developers=d.get("developers"), publishers=d.get("publishers"),
                           genres=[g["description"] for g in d.get("genres") or []],
                           release_date=(d.get("release_date") or {}).get("date"),
                           short_description=d.get("short_description"), _sources=m["sources"])
for line in (ROOT / "extra_pages.txt").read_text().splitlines():
    if line.strip() and not line.startswith("#"):
        slug, kind, url, cat, name, *gallery = line.split("|")
        games[slug] = dict(slug=slug, name=name, category=cat, source=kind, url=url,
                           gallery_url=gallery[0] if gallery else None, _sources={})

EXCLUDE = {l.split()[0] for l in (ROOT / "exclude.txt").read_text().splitlines()
           if l.strip() and not l.startswith("#")}
(ROOT / "thumbs").mkdir(exist_ok=True)
manifest, rows, cards = [], [], []
for slug, g in games.items():
    page_meta_p = ROOT / "meta" / "pages" / f"{slug}.json"
    pm = json.loads(page_meta_p.read_text()) if page_meta_p.exists() else {}
    page_src = {Path(x["path"]).name: x["source_url"] for x in pm.get("page_images_saved", [])}
    images = []
    img_dir = ROOT / "images" / slug
    for p in sorted(img_dir.glob("*")) if img_dir.exists() else []:
        if str(p.relative_to(ROOT).with_suffix("")) in EXCLUDE:
            continue
        if p.name in g["_sources"]:
            kind, url = g["_sources"][p.name]
        elif p.name in page_src:
            kind, url = "page-image", page_src[p.name]
        else:
            continue
        with Image.open(p) as im:
            w, h = im.size
        images.append(dict(slug=slug, type="image", kind=kind, path=str(p.relative_to(ROOT)), source_url=url,
                           px_width=w, px_height=h, bytes=p.stat().st_size, sha256=sha256(p),
                           captured_at=mtime_iso(p)))
    images.sort(key=lambda r: (KIND_ORDER[r["kind"]],
                               ART_ORDER.index(Path(r["path"]).stem) if r["kind"] == "art" else 0, r["path"]))
    pages = []
    for c in pm.get("captures", []):
        if c.get("error") or not c.get("path") or not (ROOT / c["path"]).exists():
            continue
        p = ROOT / c["path"]
        with Image.open(p) as im:
            w, h = im.size
        pages.append(dict(slug=slug, type="page", kind=f"{pm['kind']}-page", path=c["path"], url=pm["url"],
                          final_url=c.get("final_url"), title=c.get("title"), http_status=c.get("http_status"),
                          width=c["width"], dsf=1, px_width=w, px_height=h,
                          page_css_height=c.get("page_css_height"), truncated=c.get("truncated"),
                          bytes=p.stat().st_size, sha256=sha256(p), captured_at=pm.get("captured_at")))
    pages.sort(key=lambda r: r["width"])
    manifest += images + pages
    g.pop("_sources")
    rec = dict(g, n_images=len(images), n_page_shots=len(pages),
               n_screenshots=sum(r["kind"] in ("screenshot", "gif-still", "page-image") for r in images),
               images=[r["path"] for r in images], page_shots={str(r["width"]): r["path"] for r in pages})
    rows.append(rec)
    if not images and not pages:
        continue
    tiles = []
    for r in images:
        t = thumb(ROOT / r["path"], f"{slug}--{Path(r['path']).stem}.jpg")
        label = Path(r["path"]).stem
        tiles.append(f'<a class="img" href="{r["path"]}" target="_blank"><img loading="lazy" src="{t}" '
                     f'alt="{html.escape(g["name"])} {label}"><span>{label} · {r["px_width"]}×{r["px_height"]}</span></a>')
    ptiles = []
    for r in pages:
        t = thumb(ROOT / r["path"], f"{slug}--page-{r['width']}w.jpg", crop_tall=True)
        ptiles.append(f'<a class="page" href="{r["path"]}" target="_blank"><img loading="lazy" src="{t}" '
                      f'alt="{html.escape(g["name"])} page at {r["width"]}px"><span>{r["width"]}w page</span></a>')
    sub = " · ".join(x for x in [", ".join(g.get("developers") or []), g.get("release_date") or ""] if x)
    cards.append(
        f'<section class="game" data-cat="{g["category"]}"><header><h2>{html.escape(g["name"])}</h2>'
        f'<a href="{g["url"]}" target="_blank">{g["source"]}</a><small>{html.escape(sub)}</small>'
        f'<em>{g["category"]}</em></header>'
        f'<div class="imgs">{"".join(tiles)}</div>'
        f'{"<div class=pages>" + "".join(ptiles) + "</div>" if ptiles else ""}</section>')

(ROOT / "games.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
(ROOT / "manifest.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in manifest))

n_games = sum(1 for r in rows if r["n_images"] or r["n_page_shots"])
n_img = sum(r["n_images"] for r in rows)
n_pg = sum(r["n_page_shots"] for r in rows)
opts = "".join(f"<option>{c}</option>" for c in CATEGORIES)
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Stylized / cozy 3D games v1</title>
<style>
:root{{color-scheme:dark;--bg:#0b0b0c;--fg:#ededed;--mut:#8a8a8f;--card:#151517;--line:#26262a}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 ui-sans-serif,system-ui,-apple-system,sans-serif}}
.top{{position:sticky;top:0;z-index:2;background:rgba(11,11,12,.85);backdrop-filter:blur(12px);border-bottom:1px solid var(--line);padding:16px 28px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}}
.top h1{{font-size:16px;margin:0;font-weight:600}}.top p{{margin:0;color:var(--mut)}}
.top input,.top select,.top label{{background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:8px;padding:6px 10px}}
main{{padding:24px 28px;display:grid;gap:28px}}
.game{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}}
.game header{{display:flex;gap:12px;align-items:baseline;flex-wrap:wrap;margin-bottom:14px}}
.game h2{{font-size:17px;margin:0}}.game header a{{color:var(--mut)}}.game small{{color:var(--mut)}}
.game em{{margin-left:auto;font-style:normal;font-size:12px;color:var(--mut);border:1px solid var(--line);border-radius:99px;padding:1px 9px}}
.imgs{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}}
.pages{{display:grid;grid-template-columns:.5fr .8fr 1.2fr;gap:12px;margin-top:14px;align-items:start}}
body.nopages .pages{{display:none}}
a.img,a.page{{display:block;border-radius:8px;overflow:hidden;border:1px solid var(--line);background:#000;position:relative}}
a.img img{{display:block;width:100%;aspect-ratio:16/9;object-fit:cover}}
a.page{{max-height:460px}}a.page img{{display:block;width:100%}}
a.img span,a.page span{{position:absolute;left:6px;bottom:6px;background:rgba(0,0,0,.7);color:#fff;font-size:11px;padding:1px 6px;border-radius:6px}}
@media (max-width:900px){{.pages{{grid-template-columns:1fr 1fr}}}}
</style></head><body>
<div class="top"><h1>Stylized / cozy 3D games v1</h1><p>{n_games} games · {n_img} images</p>
<input id="q" placeholder="Filter…"><select id="cat"><option value="">All categories</option>{opts}</select></div>
<main>{"".join(cards)}</main>
<script>
const q=document.getElementById('q'),c=document.getElementById('cat');
function f(){{const t=q.value.toLowerCase(),k=c.value;document.querySelectorAll('.game').forEach(s=>{{
s.style.display=(!t||s.textContent.toLowerCase().includes(t))&&(!k||s.dataset.cat===k)?'':'none'}})}}
q.oninput=f;c.onchange=f;
</script></body></html>"""
(ROOT / "index.html").write_text(page)
print(f"games: {n_games}, images: {n_img}, "
      f"games with >=3 screenshots: {sum(r['n_screenshots'] >= 3 for r in rows)}")
