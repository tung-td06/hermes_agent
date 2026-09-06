# VTC News (vtcnews.vn) article extraction recipe

Site rule for the article→video pipeline, verified 2026-08-07 on the
"Việt Nam 3-1 Campuchia" ASEAN Cup 2026 live-blog article.

## Page structure (live-blog / match-update articles)

- Title: `<title>` / og:title. Sapô: `og:description` (often prefixed
  "Cập nhật tỷ số ..." on match live blogs — reuse as sapo, or drop the prefix).
- Content: `<p>` tags. WARNING: naive `<p>` regex pulls navigation crumbs,
  ad `<script>` text, and a LONG tail of unrelated story teasers (weather,
  crime, other matches, policy news). The article's own paragraphs are the
  first ~12–18; everything after the "Xem ... trực tiếp / FPT Play" promo
  line is other-article headlines — drop it.
- Author/date: byline author; date from the URL path (`/2026/08/07/...`).

## Images (cdn-i.vtcnews.vn)

- Thumb URLs carry a resize segment:
  - `/resize/th/upload/...` → article's own photos
  - `/resize/me//upload/...` → sidebar "related news" thumbnails — SKIP
- Full-size original = drop the `/resize/XX/` segment entirely:
  `https://cdn-i.vtcnews.vn/upload/2026/08/07/<file>.jpg`
  (downloads fine, ~0.5–1.2 MB each).
- Video poster is already full-size at `/upload/.../video-poster-*.jpg`.
- Ignore `rs.vtcnews.vn/...` (icons, logos, svg).

## Video (cdn-v.vtcnews.vn)

- No iframe, no `<video>` tag, no `data-video-src` attribute on VTC.
- Find the clip by regexing the RAW HTML for:
  `https://cdn-v\.vtcnews\.vn/video/YYYY/M/D/<HEXID>/<HEXID>\.mp4`
- Downloads fine via curl + desktop browser UA (observed: 12 MB,
  1280x720 h264+aac, 41 s).
- `cdn-v.vtcnews.vn` = video CDN; `cdn-i.vtcnews.vn` = images.

## Verified run

VN 3-1 Cambodia live blog → 9:16 MP4 via the custom generator pipeline
(`article_video.py` → `project-render` → `build_final.py`): 29 html frames +
1 real video splice (41 s clip placed after frame 6), total 246 s,
1080x1920@30fps, narration -22..-25 dB in every window, decode clean.
