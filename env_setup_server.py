#!/usr/bin/env python3
"""
Tiny one-time web form for writing .env on the VPS.

It listens only on 127.0.0.1, so it is not exposed to the public internet.
Use it through an SSH tunnel from your own computer.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs
import html

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
HOST = "127.0.0.1"
PORT = 8787


PAGE = """<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Bosphorus Radio Ayar</title>
  <style>
    body {{
      margin: 0;
      font-family: Arial, sans-serif;
      background: #101820;
      color: #f4f7f8;
      display: grid;
      min-height: 100vh;
      place-items: center;
    }}
    main {{
      width: min(680px, calc(100vw - 32px));
      background: #17242e;
      border: 1px solid #2e4352;
      border-radius: 8px;
      padding: 24px;
      box-sizing: border-box;
    }}
    h1 {{
      margin: 0 0 16px;
      font-size: 24px;
    }}
    label {{
      display: block;
      margin: 16px 0 8px;
      font-weight: 700;
    }}
    input {{
      width: 100%;
      box-sizing: border-box;
      padding: 12px;
      border-radius: 6px;
      border: 1px solid #6b8495;
      background: #0f171d;
      color: #fff;
      font-size: 16px;
    }}
    button {{
      margin-top: 18px;
      padding: 12px 18px;
      border: 0;
      border-radius: 6px;
      background: #22a06b;
      color: white;
      font-weight: 700;
      cursor: pointer;
    }}
    .ok {{
      background: #103c2b;
      border: 1px solid #22a06b;
      padding: 12px;
      border-radius: 6px;
      margin-bottom: 16px;
    }}
    .hint {{
      color: #bdd0da;
      line-height: 1.45;
      margin: 0;
    }}
  </style>
</head>
<body>
  <main>
    {message}
    <h1>Bosphorus Breeze Radio</h1>
    <p class="hint">YouTube yayin anahtarini buraya yapistir. Kaydedince .env dosyasi otomatik guncellenir.</p>
    <form method="post">
      <label for="key">YouTube yayin anahtari</label>
      <input id="key" name="key" type="password" autocomplete="off" required autofocus>
      <button type="submit">Kaydet</button>
    </form>
  </main>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        self.respond("")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        key = parse_qs(body).get("key", [""])[0].strip()

        if not key:
            self.respond("<div class='ok'>Anahtar bos olamaz.</div>")
            return

        ENV_FILE.write_text(
            "YOUTUBE_STREAM_KEY={}\n"
            "YOUTUBE_RTMP_URL=rtmp://a.rtmp.youtube.com/live2\n"
            "FFMPEG_LOG_LEVEL=info\n".format(key),
            encoding="utf-8",
        )

        safe = html.escape(key[:4] + "..." + key[-4:] if len(key) >= 8 else "***")
        self.respond(f"<div class='ok'>Kaydedildi. Anahtar: {safe}</div>")

    def respond(self, message):
        data = PAGE.format(message=message).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    print(f"Open through SSH tunnel: http://127.0.0.1:{PORT}")
    HTTPServer((HOST, PORT), Handler).serve_forever()
