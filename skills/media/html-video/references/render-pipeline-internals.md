# html-video render pipeline internals (from core/src/project.ts + adapter-hyperframes/src/render.ts)

Verified by reading the D:\html-video source and by end-to-end render this session (7-frame article video, 89s).

## Project store + export entry
- Project lives at `<repo>/.html-video/projects/<id>/project.json` (`providersDir = join(projectRoot, '.html-video', 'projects')`, where projectRoot = cwd of the CLI).
- CLI `project-render <id>` → `orchestrator.exportMp4()`. If `project.frames[]` is non-empty it takes the **multi-frame path**; otherwise the single-frame fast path (needs a real template engine; only used by the studio). For article videos always author `frames[]`.

## exportMp4 multi-frame path (core/src/project.ts ~L379-437)
1. Sorts frames by `order`.
2. `projectEngine = tmpl?.engine ?? 'hyperframes'` — if `templateId` is a hyperframes template, engine = 'hyperframes'. Non-remotion frames resolve to `templateRef = { id, engine, sourcePath: f.htmlPath }` (i.e. YOUR frame HTML is the input). Only frames with `engine:'remotion'` + `nativeTemplateId` take a different path (native Remotion tsx).
3. Per frame: renders `frames/NN.mp4` (zero-padded by order index). Config: `resolution = preferences.resolution ?? 1920x1080`, `fps = preferences.fps ?? 60`, `duration = f.durationSec`, `durationMode:'explicit'`, output to `frames/NN.mp4`. Workdir = project dir.
4. `concatFramesWithFfmpeg(orderedMp4s, outPath, ...)`: **reencode = true if >1 distinct engine** (concat FILTER rebuilds timeline). Single engine → concat demuxer with `-c copy` (fast). Never stream-copy concat across mixed engines (pts/timebase mismatch can balloon duration).
5. `applySoundtrack()` runs only if `project.soundtrack` is configured (MiniMax). Without it the MP4 has NO audio stream — add audio yourself.
6. Total duration = `sum(f.durationSec)`; `-t`/tpad per frame means final stream can be ~0.2s under that sum.

## adapter-hyperframes render.ts (the actual frame recorder)
- Lazy-imports `playwright` (resolvable from the monorepo pnpm store). Launch headless chromium, `browser.newContext({ viewport: {w,h}, recordVideo: {dir, size} })`, `page.goto(file://…, domcontentloaded)`.
- `prepareSourceHtml()`: single-file HTML passes through; multi-composition templates (with `data-composition-src`) get their comps inlined (file:// fetch is blocked in chromium, so comps must be inlined into the HTML).
- **Animation freeze**: an `addInitScript` injects `#__hv_freeze { * { animation-play-state: paused } }` before any CSS runs, holding every animation at frame 0. It waits for stylesheet links + `fonts.load()` every face + `fonts.ready` (capped 8s), then __hvUnfreeze() removes the style. This is why external Google Fonts work but add ~3s latency (and why a system font like Segoe UI is faster/more reliable).
- **Duration probe**: evaluates max non-infinite CSS `animationDuration+Delay` across elements and max finite GSAP tween. Only extends duration when `durationMode !== 'explicit'`. In explicit mode the probe result is IGNORED (hard cap honors user durationSec) — so keep your finite anims short.
- Records `totalDuration` in real time, closes context, picks the freshest `.webm`.
- webm→mp4 ffmpeg: seeks off the dead lead-in (`leadInMs`, backoff 120ms), `tpad=stop_mode=clone:stop_duration=<dur>` when explicit, `-t <dur> -r <fps> -c:v libx264 -pix_fmt yuv420p -preset medium -crf 20 -movflags +faststart`.
- ffmpeg binary resolution (`getFfmpegCmd`): `process.env.FFMPEG_PATH` > walk up from cwd for `<dir>/.html-video/ffmpeg/ffmpeg.exe` (Win) / `ffmpeg` (nix) > `ffmpeg` on PATH.

## Manual-authoring consequences
- Your frame HTML is loaded over `file://` — base64-embed images/audio; no external fetch.
- Bring your own audio after export (render has no audio unless soundtrack configured).
- Frame `htmlPath` must be an absolute single-backslash Windows path (JSON `\`-escaped). Frames do NOT need to reference assets/ in project.json — the frame HTML is fully self-contained.