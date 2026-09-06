---
name: html-video
description: Use when making videos from article links via html-video.
---

# html-video — article/link → MP4 via local HTML frames

The `D:\html-video` repo (nexu-io "HTML→Video meta-layer") renders self-contained animated HTML files to real MP4 via headless Chromium (Playwright) + bundled ffmpeg — fully local, no cloud render. The studio's agent loop is OPTIONAL: you can author the whole project by hand for deterministic control. For an agent this is the fast, reliable path (no agent-in-agent recursion), and it's how to satisfy "use images from the article" + "add audio" precisely.

## When to use
- User says "dùng D:\html-video tạo video từ link/bài viết/prompt" (they use it in Vietnamese).
- Goal: MP4 video from a web article, embedding the article's own images, with narration/bgm audio.

## Key facts (learned the hard way)
- Project store: `<repo>/.html-video/projects/<project_id>/`. A project is just three things: `project.json` (frames[] with absolute `htmlPath`, `durationSec`, `order`, optional `engine`), `frames/NN-frame_N.html` (self-contained animated HTML), `content-graph.json` (informational for the studio; NOT read by export).
- Render: `cd D:\html-video && node packages/cli/dist/bin.js project-render <id> [--output D:/path.mp4]`. Multi-frame path records each frame in headless Chromium in REAL TIME (a 12s frame takes ~12s+ overhead), transcodes webm→mp4 (libx264 crf20), then ffmpeg-concats. No soundtrack configured → output has NO audio; you add audio yourself afterwards.
- ffmpeg/ffprobe are bundled at `<repo>/.html-video/ffmpeg/ffmpeg.exe` (the export path auto-finds them). Playwright chromium is already installed under `%LOCALAPPDATA%\ms-playwright`.
- Resolution/fps come from `project.preferences.resolution` / `.fps` (e.g. {width:1920,height:1080}, fps 30). Frames render at their exact `durationSec` (durationMode 'explicit' = hard cap; shortfalls padded by tpad clone, so a frame is never stretched by long animations).

## Custom generator pipeline (9:16 portrait, many frames, flexible durations) — PREFERRED
For "nhiều text hơn, nhiều frame hơn, duration linh động" requests, use the custom
generator scripts in `D:\html-video\scripts\` — they auto-split an article into
title/sapo/paragraph-sentence/image/video/endcard frames, auto-fit font-size so long
text still fits, and compute each frame's duration from its TTS narration length.

Workflow (article.json → MP4):
1. Fetch article, download its images (full-size) + video clips (sggp videos 404 on
   `data-video-src`; use the `<source src>` URL that carries the CDN token).
2. Write `article.json` (fields: name,title,sapo,paragraphs[],images[{path,caption}],
   videos[{path,caption}],source,author,date).
3. `cd D:/html-video && python scripts/article_video.py <article.json> proj_<id>`
   → writes project.json (html frames ONLY) + manifest.json (full timeline incl.
   video splices) + frames/*.html + frames/narr-NN.mp3 (edge-tts, retry built in).
   NOTE: on 0-byte narr-NN.mp3 (all 3 TTS retries failed) regenerate manually and
   re-run; manifest durations are already fixed so just regenerate the mp3.
4. `node packages/cli/dist/bin.js project-render proj_<id> --output ...` (foreground;
   background can exit(1) silently on this machine).
5. `python scripts/build_final.py proj_<id> --out D:/.../final.mp4` — splices the
   real article videos (blurred-bg 9:16 + burned VN caption via drawtext with
   seguisb.ttf, relative paths + cwd to dodge Windows colons in filters), pads each
   narration to its frame, concats video+audio, muxes.
6. Verify (section below). 9:16 = preferences.resolution {1080,1920}, fps 30.

Current rules baked into `article_video.py` (do not regress):
- Image frames MUST narrate `"Hình ảnh: {caption}"` (user requirement: standalone
  images get the spoken lead-in "Hình ảnh" + caption; min_dur 3.6, pad 1.0).
- Font fitting uses REAL font metrics (Pillow ImageFont + Segoe UI Bold
  `C:\Windows\Fonts\segoeuib.ttf`, cached per size) + `margin=0.92` safety box,
  NOT the old char-width heuristic (`char_w=0.56` overflowed in Chromium's
  synthetic bold and clipped whole characters off the frame).
- Ops log for this pipeline lives IN THE PROJECT at
  `D:\html-video\notes\2026-08-07-custom-generator-pipeline.md` — clone-friendly;
  keep it in sync whenever the generator changes.

Pitfalls specific to this pipeline:
- **Image-frame narration = user preference**: for a lone/standalone image frame the TTS MUST read
  `"Hình ảnh: <caption>"` (not the bare caption). Generator sets `narr=f"Hình ảnh: {im['caption']}"`
  (min_dur ~3.6, pad 1.0). Keep this — user explicitly asked for it once.
- **Text overflows frames when font-size is guessed**: never size text with a char-width heuristic
  (`char_w=0.56`). Vietnamese diacritics + weight-800/600 synthetic-bold make real glyphs wider than
  the guess, so text bleeds past the right edge / drops out of the frame in Chromium. Fix in
  `article_video.py fit_font_size()`: measure the REAL wrapped line height/width with Pillow
  (`ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", fs).getlength(...)`, word-wrap per line) and
  binary-search the largest fs that fits `avail_w = max_w*0.92` / `avail_h = max_h*0.92` (0.92 margin
  absorbs Chromium's slightly-wider synthetic-bold). Cap at 8 lines. Do NOT trust the old heuristic.
- ffmpeg filter_complex with Windows paths: drive-letter colons break drawtext —
  copy the font + caption textfile into the work dir and use relative filenames with
  cwd=work. `-vf` + `-map [label]` fails ("Unrecognized option 'map [v]'") — use
  `-filter_complex` instead.
- `scale=w=iw*min(...)` expression parsing fails; use
  `scale=W:H:force_original_aspect_ratio=decrease` for the foreground and
  `...=increase,crop=W:H` for the blurred bg.
- Video concat: all segments must share codec/res (libx264 yuv420p 1080x1920@30);
  the html frames and converted clips both use crf20 preset medium → `-c copy` concat
  is safe.

## Manual authoring workflow (bypasses studio/agent loop)
1. **Fetch article**: `curl -sL -A "Mozilla/5.0..." <url>`, strip `<p>` paragraphs + `<title>`/og:title with Python regex; drop footer boilerplate. Images: keep only the article's OWN content images (e.g. full-size `w1000` URLs on sggp; `300x200` thumbnails are related-story links — skip). Grab their `<figcaption>` text for credits.
2. **Download images**; embed into HTML as base64 `data:image/...;base64,` URIs. Frames load over `file://` where external fetch is blocked — base64 always works, no CORS, no network at render time.
3. **Build N self-contained frame HTMLs**: exactly 1920x1080 (or target res) absolutely-positioned `.f` wrapper, inline CSS only, CSS keyframe animations, SYSTEM fonts only ('Segoe UI' fully covers Vietnamese — skip Google Fonts links to keep render fast and glyph-correct). See `templates/frame-skeleton.html`. Keep every finite animation < frame duration; use `animation-iteration-count: infinite` only for ambient bg motion (the duration probe ignores infinite).
4. **Create project dir** `.html-video/projects/proj_<hex>/` with `frames/` + `project.json`. Absolute `htmlPath` with single backslashes (let `json.dumps` escape them). Set `templateId` to any hyperframes template (e.g. `frame-kinetic-type`) — non-remotion frames fall back to the project engine with `sourcePath = f.htmlPath`.
5. **Render** in FOREGROUND with a generous timeout (~2 min/frame incl. overhead; 7×~12s frames ≈ 10–15 min total). Background `project-render` can exit(1) silently on this machine — if it does, rerun foreground (works).
6. **Add audio** (recipe below), then verify.

## Narration audio recipe (TTS chunks synced to frames)
- Write one narration sentence per frame. Generate per-chunk: `edge-tts --voice vi-VN-NamMinhNeural --rate=+5% --text "..." --write-media chunkN.mp3` (edge-tts at `C:\Users\Admin\.local\bin\edge-tts.exe`). Transient network failures are common — retry loop (3 attempts, 2s sleep); output is deterministic (same byte size on regen).
- Measure chunk durations (ffprobe) FIRST, then set each frame's `durationSec = chunk + ~1.4s` padding (min 6s) so narration fits its frame.
- Build one track: pad each chunk to its frame length (`-af apad=whole_dur=<frameDur> -t <frameDur> -ar 48000 -ac 2 seg.wav`), concat all segments via concat demuxer list, then mux:
  `ffmpeg -i video.mp4 -i narration.mp3 -filter_complex "[1:a]apad[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -t <total> out.mp4`
- Prefer pad+concat over amix+anullsrc layering — simpler, reliable, and each chunk lands exactly at its frame start.

## Verification (always run all)
- `ffprobe` duration/size (expect video ≈ sum of durationSec; container gets audio length via -t).
- Full decode: `ffmpeg -v error -i out.mp4 -f null -` (must exit 0).
- Not-black check: extract 1 frame per scene with ffmpeg, load with PIL — mean luma > ~20 with max 255; image frames should show saturation mean ~60–80/255 (photos visible).
- Narration placement: `ffmpeg -ss <frameStart> -t 2 -i out.mp4 -vn -af volumedetect -f null -` → mean_volume ≈ −20 to −25 dB in every frame window.
- **Text-overflow proof (real render, not just metrics)**: a Pillow measurement can still under-report
  Chromium's width, so render each frame at EXACT resolution with the bundled headless chromium and
  check the bright-text pixel bbox stays inside the frame:
  ```
  CHROME="C:/Users/<user>/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe"
  "$CHROME" --headless --disable-gpu --no-sandbox --window-size=1080,1920 --force-device-scale-factor=1 \
      --virtual-time-budget=4000 --hide-scrollbars --screenshot=out.png file:///D:/.../frames/NN-text.html
  ```
  Then with numpy: `text = img.mean(axis=2) > 120`, take cols/rows where `text.any()`, assert left
  margin >3 and right/bottom margins >3. `--virtual-time-budget` is REQUIRED or opacity:0 CSS
  animation frames render blank. 28/29 headless shots can exit(1)/segfault transiently — just re-run
  the failed one alone.

## Pitfalls
- **MSYS path gotcha**: native Windows exes (ffmpeg/ffprobe) cannot read `/d/...` MSYS paths — always pass `D:/...`.
- Background `project-render` can exit(1) with zero output ("bash: no job control"); rerun in foreground.
- Generated TTS files may get truncated/deleted by stray processes — back up chunks immediately after generation, or just regenerate (deterministic output).
- Don't rely on `stat -c%s` alone in git-bash for these files; confirm with `ls -la`.
- Renderer freezes ALL CSS animations at document-parse and unfreezes only after fonts are ready, right before recording — animation delays are relative to unfreeze, so keep delays short and total animation < frame duration.
- The video stream can come out ~0.2s shorter than sum(durationSec) (per-frame -t rounding). Harmless; audio tail covers it.

## Engine v2 (preferred for article → MP4 from a URL)
The repo also ships a second, config-driven Python pipeline at
`D:\html-video\engine\` (data-driven JSON config + scene_analyzer + frame_builder
templates + crawler). Use it for "tự làm video từ link bài báo" with templates/
cinematic touch, and add new templates there (config template/animation/theme +
a `_tpl_*` method in frame_builder). Requires `kienth`-family crawler fixes
(gzip decompress + site rule). See `references/engine-v2-pipeline.md`.

## References
- `references/engine-v2-pipeline.md` — module map, how to add a data-driven template, crawler pitfalls (gzip, per-site stop_markers, filter small thumbs), HLS→mp4 recipe, run/verify.
- `references/vtcnews-extraction.md` — VTC News site rule (live-blog/match articles): full-size image URLs = drop the `/resize/XX/` segment; video clip found by regexing raw HTML for `cdn-v.vtcnews.vn/.../mp4` (VTC has no iframe/video/data-video-src); filter the unrelated `<p>` tail after the "FPT Play" promo line.
- `references/render-pipeline-internals.md` — exportMp4 flow, JSX resolution, media probe + freeze probe behavior (concat rules).
- `templates/frame-skeleton.html` — known-good starter frame (1920x1080, bg image, headline, caption, rise/ken-burns animations).
- `references/article-shorts-spec.md` — NEXT-generation spec (user requirements): scene engine (not per-paragraph), per-scene duration (NOT fixed 5s; depends on chars ÷ reading speed + image/video count), random layout templates A–J, animations list, image/video handling rules (never convert video→image; upscale small images; D:\Gen Image Free fallback), natural-voice TTS with punctuation pauses, 1080x1920@60fps. Build these into the generator when user asks for "high-quality Shorts/Reels/TikTok from article" — the current generator is the v1 baseline for it.
