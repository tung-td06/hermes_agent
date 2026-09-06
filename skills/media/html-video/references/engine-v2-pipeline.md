# Engine v2 — Python pipeline (D:\html-video\engine\)

The repo now has a SECOND, newer pipeline alongside the v1 `scripts/` and
manual-authoring paths. It is config-driven (all knobs in JSON) and generates
1080x1920@60fps HTML frames + narration + music, then composites with bundled
ffmpeg. Prefer this for "tự làm video từ URL bài báo" with the cinematic /
news template workflow, and add new templates here rather than in the JS path.

## Module map (file → responsibility)
- `config_loader.py` — loads `engine/config/*.json` (theme/template/animation/
  voice/music/layout/scene) into one `Config`; `.section(name)` to fetch.
- `crawler.py` — `crawl(url, asset_dir)` -> article dict. SITE_RULES per-domain.
  Downloads images into asset_dir and videos.
- `scene_analyzer.py` — article dict -> frames[] with `scene_type` in
  {title, intro, story, info, images, video, quote, end}.
- `pipeline.py` — orchestrates crawler -> scene_analyzer -> selector -> timeline
  -> voice -> subtitles/karaoke -> asset_manager -> frame_builder -> composer.
- `selector_animation.py` — `assign_templates_and_anims(frames)`; picks a
  template per scene by `templates[scene_type]` in `template.json`, honoring
  `requires` (the tpl needs "image"/"video").
- `frame_builder.py` — `FrameBuilder.build()` renders each frame dict -> a
  self-contained `NN-frame_<scene_type>.html`. One method per template:
  `_tpl_tpl_SLUG` where dash->underscore (e.g. `_tpl_tpl_image_left`). A frame
  dict has keys: scene_type, template, anim{entry,media,title}, images[],
  video, title, subtitle, text, bullets[], highlights[], quote, karaoke[],
  duration.
- `timeline.py / subtitles.py / voice.py / music.py / asset_manager.py /
  project_writer.py / video_composer.py` — duration math, karaoke word spans,
  edge-tts narration (vi-VN-NamMinhNeural), BGM duck, asset normalize
  (scale/upscale, extend video), project.json + manifest, splice/concat/mux.

## Adding a template (data-driven; do not hardcode templates in the builder)
1. `config/template.json` — add id to the relevant `templates[<scene_type>]`
   list and declare media in `requires` (`"tpl-X": ["image"]` or `[]`).
2. `config/layout.json` — optional zones for positioning.
3. `config/animation.json` — any new keyframe recipes the template uses
   (entry/media/loop); builder emits `@keyframes` from these directly.
4. `frame_builder.py` — add `_tpl_tpl_<new-id>` method (underscores for dashes).
   Builder fallback `_tpl_tpl_text_full` if missing.
5. `config/theme.json` — palette/typography used by the method.

## Crawler pitfalls
- **gzip**: several VN news domains (kienthuc.net.vn) return gzip even when the
  client does NOT send `Accept-Encoding`; `urllib` does not auto-decompress, so
  `_fetch` gets binary garbage and the crawl comes back all-empty (title/sapo/
  paras/images all 0). The e.g. `_fetch` must sniff `data[:2] == b"\x1f\x8b"`
  and `gzip.decompress` before `.decode("utf-8", "replace")`.
- **site rule**: kic/... needs `body_selector="article__body"`; on kietthuc the
  `article-footer` sits MID-body, so generic stop markers cut the body too
  early and lose images. Use a `stop_markers` override per-site, e.g.
  `("relate-news-demo", "article__author", "comments?")`.
- **3rd frame only grabs 1 image**: related-story thumbnails (e.g. 210x140 /
  300x200) are article trailers — filter to the article's own full-size images;
  tiny thumbnails are not the article content.
- **Videos are HLS**: some outlets give `.m3u8` (playlist text; `_download`
  saves ~600 bytes of `#EXTM3U`). Don't rely on that file; convert with the
  bundled ffmpeg against the `<source src>` HLS URL, passing a Referer header
  for the CDN:

  `ffmpeg -y -headers "Referer: <article_url>\r\nUser-Agent: Mozilla/5.0\r\n" -i <m3u8> -c copy -bsf:a aac_adtstoasc clip.mp4`

Verify the output with ffprobe (width/height/r_frame_rate/duration) and `-f null`
decode.

## Run / verify
- Quick crawl check without media asset dir: `crawl(url)` then print title/paras/
  images/videos — catches selector + gzip + HLS problems fast.
- The engine's dry-run (main.py `--dry`) and full build: see `main.py` arg
  parsing. Verify final MP4 the same as v1: ffprobe duration/size, full decode
  `-v error -f null -`, and per-scene luma/volume checks.