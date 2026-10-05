# stylized-cozy-3d-games-v1

Images of 39 **very stylized 3D** games: cozy builders and diorama toys (Townscaper, Cloud Gardens, Tiny Glade,
ISLANDERS, Dorfromantik), cozy adventures (A Short Hike, Alba, Lil Gator Game, Untitled Goose Game, TOEM),
flat-shaded / painterly / cel-shaded adventures (Sable, Journey, ABZU, Firewatch, TUNIC, Okami HD), stylized
shooters and action games (SUPERHOT + MIND CONTROL DELETE, all four Lovely Planet titles, Hi-Fi RUSH, Katamari
Damacy REROLL), puzzle games (Return of the Obra Dinn, The Witness, Viewfinder, COCOON) and Bad North.
Photoreal and flat 2D games were excluded. Collected 2026-10-05 from the public Steam store; no login needed.

- **478 images** from 39 Steam store entries: 324 official gameplay screenshots (306 at 1920x1080), and
  154 pieces of official key art (library hero 1920x620, main capsule 616x353, header 460x215, library
  portrait 300x450). Every game has 5–10 screenshots.
- **Categories:** `stylized-adventure` (11), `stylized-action` (10), `cozy-adventure` (7), `cozy-builder` (6),
  `stylized-puzzle` (4), `stylized-strategy` (1).
- No store-page screenshots this time (the lowpoly-block-games-v1 page-capture step was skipped).

## Layout

```
images/<slug>/ss-NN.jpg              Steam screenshots, full size, store order
images/<slug>/library_hero.jpg       Steam library hero banner (1920x620)
images/<slug>/capsule.jpg            Steam main capsule (616x353)
images/<slug>/header.jpg             Steam header capsule (460x215)
images/<slug>/library_600x900.jpg    Steam library portrait art (served at 300x450)
thumbs/                              480px previews used by index.html
games.jsonl                          one row per game: slug, name, category, steam_appid, url, website,
                                     developers, publishers, genres, release_date, short_description,
                                     n_images, n_screenshots, images[]
manifest.jsonl                       one row per image: slug, kind (screenshot|art), path, source_url,
                                     px_width, px_height, bytes, sha256, captured_at
index.html                           static gallery with category filter and text search
meta/<slug>.json                     trimmed Steam appdetails response + source URL of every file
steam_games.txt                      slug|appid|category
```

## Procedure

App ids were resolved with the public Steam `storesearch` API (`resolve.py`, input `games.txt`) and checked
by hand. `fetch_steam.py` calls `store.steampowered.com/api/appdetails` per app and downloads up to 10
`path_full` screenshots plus the four standard capsule/library images from the Steam CDN. `build_index.py`
writes `games.jsonl`, `manifest.jsonl`, `thumbs/` and `index.html`. Scripts are shared with
lowpoly-block-games-v1.

```
python3 fetch_steam.py      # needs pillow; skips existing files
python3 build_index.py
```

All images are the property of their respective developers and publishers. They were collected from
public store pages for research use only.
