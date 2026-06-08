#!/usr/bin/env python3
"""
Bosphorus Breeze Radio web admin panel.

This is a small, dependency-free control panel for a beginner-friendly VPS
setup. It listens on 127.0.0.1 only, so it should be opened through an SSH
tunnel instead of being exposed to the public internet.
"""

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from subprocess import run
from urllib.parse import parse_qs
import cgi
import html
import os
import re
import shutil

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
MUSIC_DIR = ROOT / "music"
ASSETS_DIR = ROOT / "assets"
PLAYLIST_FILE = ROOT / "playlist.txt"
SERVICE_NAME = "bosphorus-radio.service"
HOST = "127.0.0.1"
PORT = 8788

ALLOWED_AUDIO = {".mp3", ".m4a", ".wav"}
ALLOWED_BACKGROUND = {".jpg", ".jpeg", ".png", ".mp4", ".mov", ".webm", ".mkv"}
IMAGE_BACKGROUND = {".jpg", ".jpeg", ".png"}
VIDEO_BACKGROUND = {".mp4", ".mov", ".webm", ".mkv"}
SAFE_ENV = {
    "YOUTUBE_RTMP_URL": "rtmp://a.rtmp.youtube.com/live2",
    "FFMPEG_LOG_LEVEL": "info",
    "VIDEO_WIDTH": "854",
    "VIDEO_HEIGHT": "480",
    "VIDEO_FPS": "24",
    "VIDEO_BITRATE": "900k",
    "VIDEO_MAXRATE": "1100k",
    "VIDEO_BUFSIZE": "2200k",
    "X264_PRESET": "ultrafast",
    "FFMPEG_THREADS": "1",
    "AUDIO_BITRATE": "128k",
    "AUDIO_RATE": "44100",
    "AUDIO_CHANNELS": "2",
}


def shell(args):
    return run(args, cwd=ROOT, capture_output=True, text=True, check=False)


def shell_no_block(args):
    return shell(["systemctl", "--no-block", *args])


def service_state():
    result = shell(["systemctl", "is-active", SERVICE_NAME])
    return result.stdout.strip() or "unknown"


def service_enabled():
    result = shell(["systemctl", "is-enabled", SERVICE_NAME])
    return result.stdout.strip() or "unknown"


def recent_logs():
    result = shell(["journalctl", "-u", SERVICE_NAME, "-n", "45", "--no-pager"])
    output = result.stdout.strip() or result.stderr.strip()
    return output[-8000:] if output else "No logs yet."


def stream_key_status():
    if not ENV_FILE.exists():
        return "Missing .env file"
    for line in ENV_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("YOUTUBE_STREAM_KEY="):
            value = line.split("=", 1)[1].strip()
            if not value or value == "replace_with_your_youtube_stream_key":
                return "Empty"
            if len(value) >= 8:
                return f"Saved ({html.escape(value[:4])}...{html.escape(value[-4:])})"
            return "Saved"
    return "Missing YOUTUBE_STREAM_KEY line"


def music_files():
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    for item in sorted(MUSIC_DIR.iterdir(), key=lambda p: p.name.lower()):
        if item.is_file() and not item.name.startswith(".") and item.suffix.lower() in ALLOWED_AUDIO:
            files.append(item)
    return files


def safe_filename(name):
    base = Path(name or "upload").name
    base = re.sub(r"[^A-Za-z0-9._() -]+", "_", base).strip()
    return base or "upload"


def background_file():
    for suffix in (".jpg", ".jpeg", ".png", ".mp4", ".mov", ".webm", ".mkv"):
        candidate = ASSETS_DIR / f"background{suffix}"
        if candidate.exists() and candidate.stat().st_size > 0:
            return candidate
    return None


def remove_existing_backgrounds():
    for item in ASSETS_DIR.glob("background.*"):
        if item.is_file() and item.suffix.lower() in ALLOWED_BACKGROUND:
            item.unlink()


def write_env(stream_key):
    lines = [
        "# Managed by Bosphorus Breeze Radio Admin.",
        "# The stream key is private. Never commit this file to GitHub.",
        f"YOUTUBE_STREAM_KEY={stream_key.strip()}",
        "",
        "# Safe Oracle Free Tier defaults.",
    ]
    lines.extend(f"{key}={value}" for key, value in SAFE_ENV.items())
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(ENV_FILE, 0o600)


def save_safe_settings_only():
    current_key = ""
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("YOUTUBE_STREAM_KEY="):
                current_key = line.split("=", 1)[1].strip()
                break
    write_env(current_key)


def render_page(message="", message_kind="ok"):
    state = html.escape(service_state())
    enabled = html.escape(service_enabled())
    key = stream_key_status()
    bg_file = background_file()
    if bg_file:
        kind = "Video" if bg_file.suffix.lower() in VIDEO_BACKGROUND else "Image"
        bg_status = f"{kind}: {html.escape(bg_file.name)}"
    else:
        bg_status = "Missing"
    playlist_status = "Found" if PLAYLIST_FILE.exists() and PLAYLIST_FILE.stat().st_size > 0 else "Missing"
    tracks = music_files()
    track_items = "\n".join(
        f"<li><span>{html.escape(p.name)}</span><small>{p.stat().st_size // 1024} KB</small></li>"
        for p in tracks
    ) or "<li><span>No music files yet.</span><small>Add mp3, m4a, or wav</small></li>"
    escaped_logs = html.escape(recent_logs())
    banner = f"<div class='banner {message_kind}'>{html.escape(message)}</div>" if message else ""

    return f"""<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Bosphorus Breeze Radio Admin</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0f1519;
      --panel: #172128;
      --line: #2c3d48;
      --text: #f5f8fa;
      --muted: #b8c7cf;
      --green: #1f9d66;
      --red: #d34d45;
      --blue: #3b82f6;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, sans-serif;
    }}
    header {{
      padding: 20px 24px;
      border-bottom: 1px solid var(--line);
      background: #111b21;
    }}
    h1 {{ margin: 0; font-size: 24px; }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 24px;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}
    section {{
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      padding: 18px;
    }}
    section.full {{ grid-column: 1 / -1; }}
    h2 {{ margin: 0 0 14px; font-size: 18px; }}
    label {{ display: block; margin: 12px 0 6px; color: var(--muted); }}
    input[type="password"], input[type="file"] {{
      width: 100%;
      padding: 11px;
      border-radius: 6px;
      border: 1px solid #536977;
      background: #0e171c;
      color: var(--text);
    }}
    button {{
      border: 0;
      border-radius: 6px;
      color: white;
      background: var(--blue);
      padding: 10px 14px;
      font-weight: 700;
      cursor: pointer;
      margin-top: 12px;
      margin-right: 8px;
    }}
    button.green {{ background: var(--green); }}
    button.red {{ background: var(--red); }}
    .banner {{
      grid-column: 1 / -1;
      padding: 12px 14px;
      border-radius: 8px;
      border: 1px solid var(--green);
      background: #113727;
      color: #e9fff4;
    }}
    .banner.err {{ border-color: var(--red); background: #3b1718; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }}
    .stat {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #101a20;
    }}
    .stat small {{ display: block; color: var(--muted); margin-bottom: 6px; }}
    ul {{ list-style: none; padding: 0; margin: 0; }}
    li {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 9px 0;
      border-bottom: 1px solid var(--line);
    }}
    li:last-child {{ border-bottom: 0; }}
    small {{ color: var(--muted); }}
    pre {{
      margin: 0;
      padding: 14px;
      white-space: pre-wrap;
      max-height: 340px;
      overflow: auto;
      background: #071016;
      border: 1px solid var(--line);
      border-radius: 8px;
      color: #d8e6ec;
      font-size: 13px;
    }}
    @media (max-width: 760px) {{
      main {{ grid-template-columns: 1fr; padding: 14px; }}
      .stats {{ grid-template-columns: 1fr 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Bosphorus Breeze Radio Admin</h1>
  </header>
  <main>
    {banner}
    <section class="full">
      <h2>Durum</h2>
      <div class="stats">
        <div class="stat"><small>Servis</small><strong>{state}</strong></div>
        <div class="stat"><small>Otomatik baslama</small><strong>{enabled}</strong></div>
        <div class="stat"><small>Yayin anahtari</small><strong>{key}</strong></div>
        <div class="stat"><small>Muzik dosyasi</small><strong>{len(tracks)}</strong></div>
        <div class="stat"><small>Arka plan</small><strong>{bg_status}</strong></div>
        <div class="stat"><small>Playlist</small><strong>{playlist_status}</strong></div>
      </div>
    </section>

    <section>
      <h2>YouTube Anahtari</h2>
      <form method="post" action="/save-key">
        <label for="key">Yeni yayin anahtarini yapistir</label>
        <input id="key" name="key" type="password" autocomplete="off" required>
        <button class="green" type="submit">Anahtari Kaydet</button>
      </form>
    </section>

    <section>
      <h2>Canli Yayin</h2>
      <form method="post" action="/service">
        <button class="green" name="action" value="start">Baslat</button>
        <button name="action" value="restart">Yeniden Baslat</button>
        <button class="red" name="action" value="stop">Durdur</button>
      </form>
      <form method="post" action="/test">
        <button type="submit">Guvenli Test Calistir</button>
      </form>
      <form method="post" action="/playlist">
        <button type="submit">Playlist Yenile</button>
      </form>
      <form method="post" action="/safe-settings">
        <button type="submit">Guvenli Ayarlari Kaydet</button>
      </form>
      <p><small>Bu panel Oracle Free Tier icin 480p guvenli ayarlari kullanir. 1080p bu makineyi kilitleyebilir.</small></p>
    </section>

    <section>
      <h2>Muzik Yukle</h2>
      <form method="post" action="/upload-music" enctype="multipart/form-data">
        <label>mp3, m4a veya wav sec</label>
        <input name="music" type="file" accept=".mp3,.m4a,.wav,audio/*" multiple required>
        <button type="submit">Muzik Yukle</button>
      </form>
    </section>

    <section>
      <h2>Arka Plan</h2>
      <form method="post" action="/upload-background" enctype="multipart/form-data">
        <label>Gorsel veya video arka plan sec</label>
        <input name="background" type="file" accept=".jpg,.jpeg,.png,.mp4,.mov,.webm,.mkv,image/jpeg,image/png,video/mp4,video/quicktime,video/webm" required>
        <button type="submit">Arka Plani Kaydet</button>
      </form>
      <p><small>Desteklenenler: jpg, jpeg, png, mp4, mov, webm, mkv. Video yuklersen FFmpeg videoyu donguye alir.</small></p>
    </section>

    <section>
      <h2>Muzikler</h2>
      <ul>{track_items}</ul>
    </section>

    <section class="full">
      <h2>Son Loglar</h2>
      <pre>{escaped_logs}</pre>
    </section>
  </main>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def send_html(self, body, status=HTTPStatus.OK):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, message, kind="ok"):
        self.send_html(render_page(message, kind))

    def read_form(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        return parse_qs(body)

    def read_multipart(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers.get("Content-Type", ""),
            },
        )
        return form

    def do_GET(self):
        self.send_html(render_page())

    def do_POST(self):
        try:
            if self.path == "/save-key":
                form = self.read_form()
                key = form.get("key", [""])[0].strip()
                if len(key) < 8 or re.search(r"\s", key):
                    self.redirect("Anahtar bos, kisa veya hatali gorunuyor.", "err")
                    return
                write_env(key)
                self.redirect("YouTube yayin anahtari kaydedildi.")
                return

            if self.path == "/upload-music":
                form = self.read_multipart()
                fields = form["music"] if isinstance(form["music"], list) else [form["music"]]
                saved = 0
                MUSIC_DIR.mkdir(parents=True, exist_ok=True)
                for field in fields:
                    name = safe_filename(field.filename)
                    if Path(name).suffix.lower() not in ALLOWED_AUDIO:
                        continue
                    target = MUSIC_DIR / name
                    with target.open("wb") as out:
                        shutil.copyfileobj(field.file, out)
                    saved += 1
                if saved:
                    shell([str(ROOT / "update_playlist.sh")])
                    self.redirect(f"{saved} muzik dosyasi yuklendi.")
                else:
                    self.redirect("Gecerli muzik dosyasi bulunamadi.", "err")
                return

            if self.path == "/upload-background":
                form = self.read_multipart()
                field = form["background"]
                name = safe_filename(field.filename)
                suffix = Path(name).suffix.lower()
                if suffix not in ALLOWED_BACKGROUND:
                    self.redirect("Arka plan jpg, jpeg, png, mp4, mov, webm veya mkv olmali.", "err")
                    return
                ASSETS_DIR.mkdir(parents=True, exist_ok=True)
                remove_existing_backgrounds()
                target = ASSETS_DIR / f"background{suffix}"
                with target.open("wb") as out:
                    shutil.copyfileobj(field.file, out)
                kind = "video" if suffix in VIDEO_BACKGROUND else "gorsel"
                self.redirect(f"Arka plan {kind} olarak kaydedildi: {target.name}")
                return

            if self.path == "/playlist":
                result = shell([str(ROOT / "update_playlist.sh")])
                if result.returncode == 0:
                    self.redirect("Playlist yenilendi.")
                else:
                    self.redirect(result.stderr.strip() or result.stdout.strip() or "Playlist yenilenemedi.", "err")
                return

            if self.path == "/safe-settings":
                save_safe_settings_only()
                self.redirect("Guvenli yayin ayarlari kaydedildi.")
                return

            if self.path == "/test":
                result = shell(["timeout", "35s", str(ROOT / "test_local.sh")])
                if result.returncode == 0:
                    self.redirect("Guvenli test basarili. Yayin baslatilabilir.")
                else:
                    output = result.stderr.strip() or result.stdout.strip() or "Guvenli test basarisiz."
                    self.redirect(output[-1200:], "err")
                return

            if self.path == "/service":
                form = self.read_form()
                action = form.get("action", [""])[0]
                if action not in {"start", "stop", "restart"}:
                    self.redirect("Bilinmeyen servis islemi.", "err")
                    return
                if action in {"start", "restart"}:
                    shell(["systemctl", "reset-failed", SERVICE_NAME])
                    shell([str(ROOT / "update_playlist.sh")])
                result = shell_no_block([action, SERVICE_NAME])
                if result.returncode == 0:
                    self.redirect(f"Servis komutu gonderildi: {action}. Durum 10-20 saniye icinde yenilenir.")
                else:
                    self.redirect(result.stderr.strip() or result.stdout.strip() or "Servis islemi basarisiz.", "err")
                return

            self.redirect("Bilinmeyen istek.", "err")
        except Exception as exc:
            self.redirect(f"Hata: {exc}", "err")


if __name__ == "__main__":
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Open through SSH tunnel: http://127.0.0.1:{PORT}")
    HTTPServer((HOST, PORT), Handler).serve_forever()
