# Article → Shorts/Reels/TikTok — upgraded pipeline spec (user requirements)

User's requirement for the NEXT-generation html-video pipeline (beyond the basic
generator). "No more 1 paragraph = 1 frame." This is the target spec; build these
features into the generator, not a one-off script.

## Output contract
- MP4, 1080x1920 (9:16 portrait), H.264 (libx264), 60 fps, Audio AAC (48k stereo).
- Auto-save project under `.html-video/projects/<id>/`.

## Crawler: collect FULLY
title, sapo, content, headings, image list + image captions, videos (incl postered/embed),
publish time, source, author. If article has video:
- Prefer the original video; if too long, auto-cut the standout/highlight segments.
- Keep the video as a VIDEO (zoom / crop / speed / slow-mo / text overlay allowed).
  NEVER convert a video into a still image.
If article lacks images, generate illustrations with `D:\Gen Image Free` (GoogleFlowTool).

## Scene engine (semantic, NOT per-paragraph)
Analyze meaning, split into themed scenes, e.g. for a fire story:
Title → Mở đầu → Diễn biến → Lực lượng chữa cháy → Thiệt hại → Nguyên nhân → Điều tra → Kết thúc.
Scene count is FLEXIBLE, up to 20–40 frames total (each scene hosts 1–3 child frames).

## Timeline: per-scene duration
NOT a fixed 5s per frame. Duration depends on: number of characters, reading speed,
number of images, number of videos. Example durations given for the Biên Hòa fire article:
- Scene 1 Title = 2s, Scene 2 Intro = 4s, Scene 3 Thông tin quan trọng = 6s,
  Scene 4 Ảnh nhiều (gallery) = 7s, Scene 5 Video = 10s.
Implement duration = f(chars ÷ reading speed) + padding, with min/max, video scenes = real
clip length, image-heavy scenes longer.

## Text: unlimited, structured
One scene may carry: Title + 2–4 paragraphs + highlight line(s) + bullets.
Never truncate meaning to fit a frame — let font size shrink / duration grow instead.

## Layout templates (randomize across video — never one layout everywhere)
- A: full image + title + subtitle
- B: image left, text right
- C: image top, text bottom
- D: two images
- E: three images
- F: video full
- G: video + text overlay
- H: timeline
- I: quote
- J: statistic
Pick randomly per scene so the whole video is varied.

## Animations supported
fade, slide, zoom, parallax, scale, mask reveal, blur reveal, light rotate,
Ken Burns, photo pan, dynamic crop.

## Image handling
- Many images → gallery; single image → zoom; small image → upscale.
- If needed use `D:\Gen Image Free` to generate: illustration / context / transition
  image. (GoogleFlowTool is verified working; prompts/*.txt → outputs/.)

## Audio
- TTS narration reading the article (edge-tts neural, Vietnamese).
- NATURAL voice (Nam Minh / Hoài My), not monotone.
- PAUSE AT PUNCTUATION: insert pauses on `,` `.` `:` `;` `...` before TTS so delivery
  breathes at the right spots.
- (mix: keep/dip source video audio, BGM — to be finalized.)