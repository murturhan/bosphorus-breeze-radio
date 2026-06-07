#!/usr/bin/env python3
"""
Bosphorus Breeze Radio web admin panel.

The panel binds to 127.0.0.1 only. Open it through an SSH tunnel:
  ssh -L 8788:127.0.0.1:8788 ubuntu@YOUR_SERVER_IP
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
BACKGROUND_FILE = ASSETS_DIR / "background.jpg"
PLAYLIST_FILE = ROOT / "playlist.txt"
SERVICE_NAME = "bosphorus-radio.service"
HOST = "127.0.0.1"
PORT = 8788

ALLOWED_AUDIO = {".mp3", ".m4a", ".wav"}
ALLOWED_BACKGROUND = {".jpg", ".jpeg"}
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


def cmd(args):
    return run(args, cwd=ROOT, capture_output=True, text=True, check=False)


def service_state():
    result = cmd(["systemctl", "is-active", SERVICE_NAME])
    return result.stdout.strip() or "unknown"


def service_enabled():
    result = cmd(["systemctl", "is-enabled", SERVICE_NAME])
    return result.stdout.strip() or "unknown"


def recent_logs():
    result = cmd(["journalctl", "-u", SERVICE_NAME, "-n", "55", "--no-pager"])
    output = result.stdout.strip() or result.stderr.strip()
    return output[-9000:] if output else "No logs yet."


def stream_key_status():
    if not ENV_FILE.exists():
        return "Missing .env"
    for line in ENV_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("YOUTUBE_STREAM_KEY="):
            value = line.split("=", 1)[1].strip()
            if not value or value == "replace_with_your_youtube_stream_key":
                return "Empty"
            if len(value) >= 8:
                return f"Saved ({html.escape(value[:4])}...{html.escape(value[-4:])})"
            return "Saved"
    return "Missing key line"


def music_files():
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    return [
        item for item in sorted(MUSIC_DIR.iterdir(), key=lambda p: p.name.lower())
        if item.is_file() and not item.name.startswith(".") and item.suffix.lower() in ALLOWED_AUDIO
    ]


def safe_name(name):
    base = Path(name or "upload").name
    base = re.sub(r"[^A-Za-z0-9._() -]+", "_", base).strip()
    return base or "upload"


def existing_stream_key():
    if not ENV_FILE.exists():
        return ""
    for line in ENV_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("YOUTUBE_STREAM_KEY="):
            return line.split("=", 1)[1].strip()
    return ""


def write_env(stream_key):
    lines = [
        "# Managed by Bosphorus Breeze Radio Admin.",
        "# Keep this file private. Never commit your YouTube stream key to GitHub.",
        f"YOUTUBE_STREAM_KEY={stream_key.strip()}",
        "",
        "# Safe Oracle Free Tier defaults.",
    ]
    lines.extend(f"{key}={value}" for key, value in SAFE_ENV.items())
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(ENV_FILE, 0o600)


def run_playlist_update():
    return cmd([str(ROOT / "update_playlist.sh")])


def render(message="", kind="ok"):
    state = html.escape(service_state())
    enabled = html.escape(service_enabled())
    key = stream_key_status()
    bg = "Found" if BACKGROUND_FILE.exists() and BACKGROUND_FILE.stat().st_size > 0 else "Missing"
    playlist = "Found" if PLAYLIST_FILE.exists() and PLAYLIST_FILE.stat().st_size > 0 else "Missing"
    tracks = music_files()
    track_rows = "".join(
        f"<li><span>{html.escape(p.name)}</span><small>{p.stat().st_size // 1024} KB</small></li>"
        for p in tracks
    ) or "<li><span>No music files yet.</span><small>Add mp3, m4a, or wav</small></li>"
    logs = html.escape(recent_logs())
    banner = f"<div class='banner {kind}'>{html.escape(message)}</div>" if message else ""

    return f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bosphorus Breeze Radio Admin</title>
<style>
:root{{color-scheme:dark;--bg:#0e1519;--panel:#172128;--line:#2d404c;--text:#f6fafc;--muted:#b8c8d0;--green:#18965f;--red:#cf4b43;--blue:#3b82f6}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font-family:Arial,sans-serif}}header{{padding:18px 24px;border-bottom:1px solid var(--line);background:#111b21}}h1{{margin:0;font-size:22px}}main{{max-width:1120px;margin:0 auto;padding:22px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}section{{border:1px solid var(--line);background:var(--panel);border-radius:8px;padding:18px}}section.full,.banner{{grid-column:1/-1}}h2{{margin:0 0 14px;font-size:18px}}label{{display:block;margin:12px 0 6px;color:var(--muted)}}input[type=password],input[type=file]{{width:100%;padding:11px;border-radius:6px;border:1px solid #536977;background:#0d171d;color:var(--text)}}button{{border:0;border-radius:6px;color:#fff;background:var(--blue);padding:10px 14px;font-weight:700;cursor:pointer;margin:8px 8px 0 0}}button.green{{background:var(--green)}}button.red{{background:var(--red)}}.banner{{padding:12px 14px;border-radius:8px;border:1px solid var(--green);background:#103726;color:#eafff3}}.banner.err{{border-color:var(--red);background:#3a1718}}.stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}}.stat{{border:1px solid var(--line);border-radius:8px;padding:12px;background:#101a20}}.stat small{{display:block;color:var(--muted);margin-bottom:6px}}p{{color:var(--muted);line-height:1.45}}ul{{list-style:none;padding:0;margin:0}}li{{display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid var(--line)}}li:last-child{{border-bottom:0}}small{{color:var(--muted)}}pre{{margin:0;padding:14px;white-space:pre-wrap;max-height:360px;overflow:auto;background:#071016;border:1px solid var(--line);border-radius:8px;color:#d8e6ec;font-size:13px}}@media(max-width:760px){{main{{grid-template-columns:1fr;padding:14px}}.stats{{grid-template-columns:1fr 1fr}}}}
</style>
</head>
<body>
<header><h1>Bosphorus Breeze Radio Admin</h1></header>
<main>
{banner}
<section class="full"><h2>Durum</h2><div class="stats">
<div class="stat"><small>Servis</small><strong>{state}</strong></div>
<div class="stat"><small>Otomatik baslama</small><strong>{enabled}</strong></div>
<div class="stat"><small>Yayin anahtari</small><strong>{key}</strong></div>
<div class="stat"><small>Muzik dosyasi</small><strong>{len(tracks)}</strong></div>
<div class="stat"><small>Arka plan</small><strong>{bg}</strong></div>
<div class="stat"><small>Playlist</small><strong>{playlist}</strong></div>
</div></section>
<section><h2>YouTube Anahtari</h2><form method="post" action="/save-key"><label>Yeni yayin anahtarini yapistir</label><input name="key" type="password" autocomplete="off" required><button class="green" type="submit">Anahtari Kaydet</button></form></section>
<section><h2>Canli Yayin</h2><form method="post" action="/service"><button class="green" name="action" value="start">Baslat</button><button name="action" value="restart">Yeniden Baslat</button><button class="red" name="action" value="stop">Durdur</button></form><form method="post" action="/test"><button type="submit">Guvenli Test Calistir</button></form><form method="post" action="/playlist"><button type="submit">Playlist Yenile</button></form><form method="post" action="/safe-settings"><button type="submit">Guvenli Ayarlari Kaydet</button></form><p>Oracle Free Tier icin 480p guvenli ayarlar kullanilir. 1080p bu makineyi kilitleyebilir.</p></section>
<section><h2>Muzik Yukle</h2><form method="post" action="/upload-music" enctype="multipart/form-data"><label>mp3, m4a veya wav sec</label><input name="music" type="file" accept=".mp3,.m4a,.wav,audio/*" multiple required><button type="submit">Muzik Yukle</button></form></section>
<section><h2>Arka Plan</h2><form method="post" action="/upload-background" enctype="multipart/form-data"><label>JPG arka plan sec</label><input name="background" type="file" accept=".jpg,.jpeg,image/jpeg" required><button type="submit">Arka Plani Kaydet</button></form></section>
<section><h2>Muzikler</h2><ul>{track_rows}</ul></section>
<section class="full"><h2>Son Loglar</h2><pre>{logs}</pre></section>
</main>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def send_html(self, body, status=HTTPStatus.OK):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def show(self, message="", kind="ok"):
        self.send_html(render(message, kind))

    def read_form(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        return parse_qs(body)

    def read_multipart(self):
        return cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": self.headers.get("Content-Type", "")},
        )

    def do_GET(self):
        self.send_html(render())

    def do_POST(self):
        try:
            if self.path == "/save-key":
                key = self.read_form().get("key", [""])[0].strip()
                if len(key) < 8 or re.search(r"\s", key):
                    self.show("Anahtar bos, kisa veya hatali gorunuyor.", "err")
                    return
                write_env(key)
                self.show("YouTube yayin anahtari kaydedildi. Guvenli yayin ayarlari da yazildi.")
                return

            if self.path == "/safe-settings":
                write_env(existing_stream_key())
                self.show("Guvenli yayin ayarlari kaydedildi.")
                return

            if self.path == "/upload-music":
                form = self.read_multipart()
                if "music" not in form:
                    self.show("Muzik dosyasi secilmedi.", "err")
                    return
                item = form["music"]
                fields = item if isinstance(item, list) else [item]
                MUSIC_DIR.mkdir(parents=True, exist_ok=True)
                saved = 0
                for field in fields:
                    name = safe_name(field.filename)
                    if Path(name).suffix.lower() not in ALLOWED_AUDIO:
                        continue
                    with (MUSIC_DIR / name).open("wb") as out:
                        shutil.copyfileobj(field.file, out)
                    saved += 1
                if saved:
                    run_playlist_update()
                    self.show(f"{saved} muzik dosyasi yuklendi.")
                else:
                    self.show("Gecerli muzik dosyasi bulunamadi.", "err")
                return

            if self.path == "/upload-background":
                form = self.read_multipart()
                if "background" not in form:
                    self.show("Arka plan dosyasi secilmedi.", "err")
                    return
                field = form["background"]
                name = safe_name(field.filename)
                if Path(name).suffix.lower() not in ALLOWED_BACKGROUND:
                    self.show("Arka plan JPG veya JPEG olmali.", "err")
                    return
                ASSETS_DIR.mkdir(parents=True, exist_ok=True)
                with BACKGROUND_FILE.open("wb") as out:
                    shutil.copyfileobj(field.file, out)
                self.show("Arka plan kaydedildi.")
                return

            if self.path == "/playlist":
                result = run_playlist_update()
                if result.returncode == 0:
                    self.show("Playlist yenilendi.")
                else:
                    self.show(result.stderr.strip() or result.stdout.strip() or "Playlist yenilenemedi.", "err")
                return

            if self.path == "/test":
                result = cmd(["timeout", "35s", str(ROOT / "test_local.sh")])
                if result.returncode == 0:
                    self.show("Guvenli test basarili. Yayin baslatilabilir.")
                else:
                    output = result.stderr.strip() or result.stdout.strip() or "Guvenli test basarisiz."
                    self.show(output[-1400:], "err")
                return

            if self.path == "/service":
                action = self.read_form().get("action", [""])[0]
                if action not in {"start", "stop", "restart"}:
                    self.show("Bilinmeyen servis islemi.", "err")
                    return
                if action in {"start", "restart"}:
                    cmd(["systemctl", "reset-failed", SERVICE_NAME])
                    run_playlist_update()
                result = cmd(["systemctl", "--no-block", action, SERVICE_NAME])
                if result.returncode == 0:
                    self.show(f"Servis komutu gonderildi: {action}. Durum 10-20 saniye icinde yenilenir.")
                else:
                    self.show(result.stderr.strip() or result.stdout.strip() or "Servis islemi basarisiz.", "err")
                return

            self.show("Bilinmeyen istek.", "err")
        except Exception as exc:
            self.show(f"Hata: {exc}", "err")


if __name__ == "__main__":
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Open through SSH tunnel: http://127.0.0.1:{PORT}")
    HTTPServer((HOST, PORT), Handler).serve_forever()
