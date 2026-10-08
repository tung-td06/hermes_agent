# VN News Site Crawling Recipes

Quick reference for extracting article content from Vietnamese news sites. All use `urllib.request` + regex (no bs4 dependency for minimal setups); BeautifulSoup preferred if available.

## baoxaydung.vn

- Title: `<h1>` tag, strip HTML, `html.unescape()`
- Body: all `<p>` tags with text length > 50 chars
- Skip keywords: `['facebook', 'comment', 'tòa soạn', 'giấy phép', 'liên quan', 'tin liên quan']`
- Images: standard `<img src="...">`
- No gzip, no special headers needed

Example:
```python
import urllib.request, ssl, re, html as html_mod

url = "..."
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
    raw = resp.read()
html = raw.decode('utf-8')

title = html_mod.unescape(re.sub(r'<[^>]+>', '', soup.find('h1').get_text(strip=True)))
paras = [html_mod.unescape(re.sub(r'<[^>]+>', '', p).strip())
         for p in re.findall(r'<p[^>]*>(.*?)</p>', html, re.S | re.I)
         if len(html_mod.unescape(re.sub(r'<[^>]+>', '', p).strip())) > 50
         and not any(k in html_mod.unescape(re.sub(r'<[^>]+>', '', p).strip()).lower()
                     for k in ['facebook', 'comment', 'tòa soạn', 'giấy phép'])]
```

## sggp.org.vn ( Saigon Giai Phong )

- Full-size images: URL contains `w1000` — keep those
- Thumbnails (210×140, 300×200): related-story links — SKIP
- Standard `<h1>` + `<p>` structure

## vtcnews.vn

- Videos: HLS `.m3u8` playlist, NOT direct mp4
- The `data-video-src` attribute returns 404 — use `<source src="...">` URL instead
- Must pass Referer header to ffmpeg:
  ```
  ffmpeg -y -headers "Referer: <article_url>\r\nUser-Agent: Mozilla/5.0\r\n" \
      -i <m3u8_url> -c copy -bsf:a aac_adtstoasc clip.mp4
  ```
- Filter related-story `<p>` tail after "FPT Play" promo line

## kienthuc.net.vn ( kic/ )

- **Gzip trap**: server returns `Content-Encoding: gzip` even when client does NOT send `Accept-Encoding`
- Sniff first 2 bytes: `if data[:2] == b'\x1f\x8b': data = gzip.decompress(data)`
- Body selector: `article__body`
- Stop markers override (mid-body footer exists):
  ```python
  stop_markers = ("relate-news-demo", "article__author", "comments?")
  ```
- Otherwise generic stop markers cut body too early and lose images

## General tips

1. Always set `User-Agent` header — many VN sites block python user-agent
2. SSL verification disabled (`CERT_NONE`) needed for some government sites
3. Decode HTML entities with `html.unescape()` after stripping tags
4. For image extraction, prefer regex over BeautifulSoup to avoid bs4 dep
5. Save extracted JSON as `article.json` for the pipeline:
   ```json
   {
     "name": "slug-name",
     "title": "...",
     "sapo": "...",
     "paragraphs": ["...", "..."],
     "images": [{"path": "/abs/path/to/img.jpg", "caption": "..."}],
     "videos": [{"path": "/abs/path/to/clip.mp4", "caption": "..."}],
     "source": "https://...",
     "author": "...",
     "date": "DD/MM/YYYY"
   }
   ```