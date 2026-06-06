#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from http import HTTPStatus
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


def sh(args):
    return run(args, cwd=ROOT, capture_output=True, text=True, check=False)


def service_state():
    r = sh(["systemctl", "is-active", SERVICE_NAME])
    return r.stdout.strip() or "unknown"


def service_enabled():
    r = sh(["systemctl", "is-enabled", SERVICE_NAME])
    return r.stdout.strip() or "unknown"


def recent_logs():
    r = sh(["journalctl", "-u", SERVICE_NAME, "-n", "45", "--no-pager"])
    out = r.stdout.strip() or r.stderr.strip()
    return out[-8000:] if out else "No logs yet."


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
    return [p for p in sorted(MUSIC_DIR.iterdir(), key=lambda x: x.name.lower()) if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in ALLOWED_AUDIO]


def safe_name(name):
    base = Path(name or "upload").name
    base = re.sub(r"[^A-Za-z0-9._() -]+", "_", base).strip()
    return base or "upload"


def write_env(key):
    ENV_FILE.write_text(
        f"YOUTUBE_STREAM_KEY={key.strip()}\n"
        "YOUTUBE_RTMP_URL=rtmp://a.rtmp.youtube.com/live2\n"
        "FFMPEG_LOG_LEVEL=info\n",
        encoding="utf-8",
    )
    os.chmod(ENV_FILE, 0o600)


def page(msg="", kind="ok"):
    tracks = music_files()
    track_items = "".join(f"<li><span>{html.escape(p.name)}</span><small>{p.stat().st_size // 1024} KB</small></li>" for p in tracks)
    if not track_items:
        track_items = "<li><span>No music files yet.</span><small>Add mp3, m4a, or wav</small></li>"
    banner = f"<div class='banner {kind}'>{html.escape(msg)}</div>" if msg else ""
    state = html.escape(service_state())
    enabled = html.escape(service_enabled())
    key = stream_key_status()
    bg = "Found" if BACKGROUND_FILE.exists() and BACKGROUND_FILE.stat().st_size > 0 else "Missing"
    playlist = "Found" if PLAYLIST_FILE.exists() and PLAYLIST_FILE.stat().st_size > 0 else "Missing"
    logs = html.escape(recent_logs())
    return f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bosphorus Breeze Radio Admin</title>
<style>
:root{{color-scheme:dark;--bg:#0f1519;--panel:#172128;--line:#2c3d48;--text:#f5f8fa;--muted:#b8c7cf;--green:#1f9d66;--red:#d34d45;--blue:#3b82f6}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font-family:Arial,sans-serif}}header{{padding:20px 24px;border-bottom:1px solid var(--line);background:#111b21}}h1{{margin:0;font-size:24px}}main{{max-width:1120px;margin:0 auto;padding:24px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}section{{border:1px solid var(--line);background:var(--panel);border-radius:8px;padding:18px}}section.full,.banner{{grid-column:1/-1}}h2{{margin:0 0 14px;font-size:18px}}label{{display:block;margin:12px 0 6px;color:var(--muted)}}input[type=password],input[type=file]{{width:100%;padding:11px;border-radius:6px;border:1px solid #536977;background:#0e171c;color:var(--text)}}button{{border:0;border-radius:6px;color:white;background:var(--blue);padding:10px 14px;font-weight:700;cursor:pointer;margin-top:12px;margin-right:8px}}button.green{{background:var(--green)}}button.red{{background:var(--red)}}.banner{{padding:12px 14px;border-radius:8px;border:1px solid var(--green);background:#113727;color:#e9fff4}}.banner.err{{border-color:var(--red);background:#3b1718}}.stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}}.stat{{border:1px solid var(--line);border-radius:8px;padding:12px;background:#101a20}}.stat small{{display:block;color:var(--muted);margin-bottom:6px}}ul{{list-style:none;padding:0;margin:0}}li{{display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid var(--line)}}li:last-child{{border-bottom:0}}small{{color:var(--muted)}}pre{{margin:0;padding:14px;white-space:pre-wrap;max-height:340px;overflow:auto;background:#071016;border:1px solid var(--line);border-radius:8px;color:#d8e6ec;font-size:13px}}@media(max-width:760px){{main{{grid-template-columns:1fr;padding:14px}}.stats{{grid-template-columns:1fr 1fr}}}}
</style></head><body><header><h1>Bosphorus Breeze Radio Admin</h1></header><main>
{banner}
<section class="full"><h2>Durum</h2><div class="stats"><div class="stat"><small>Servis</small><strong>{state}</strong></div><div class="stat"><small>Otomatik baslama</small><strong>{enabled}</strong></div><div class="stat"><small>Yayin anahtari</small><strong>{key}</strong></div><div class="stat"><small>Muzik dosyasi</small><strong>{len(tracks)}</strong></div><div class="stat"><small>Arka plan</small><strong>{bg}</strong></div><div class="stat"><small>Playlist</small><strong>{playlist}</strong></div></div></section>
<section><h2>YouTube Anahtari</h2><form method="post" action="/save-key"><label for="key">Yeni yayin anahtarini yapistir</label><input id="key" name="key" type="password" autocomplete="off" required><button class="green" type="submit">Anahtari Kaydet</button></form></section>
<section><h2>Canli Yayin</h2><form method="post" action="/service"><button class="green" name="action" value="start">Baslat</button><button name="action" value="restart">Yeniden Baslat</button><button class="red" name="action" value="stop">Durdur</button></form><form method="post" action="/playlist"><button type="submit">Playlist Yenile</button></form></section>
<section><h2>Muzik Yukle</h2><form method="post" action="/upload-music" enctype="multipart/form-data"><label>mp3, m4a veya wav sec</label><input name="music" type="file" accept=".mp3,.m4a,.wav,audio/*" multiple required><button type="submit">Muzik Yukle</button></form></section>
<section><h2>Arka Plan</h2><form method="post" action="/upload-background" enctype="multipart/form-data"><label>JPG arka plan sec</label><input name="background" type="file" accept=".jpg,.jpeg,image/jpeg" required><button type="submit">Arka Plani Kaydet</button></form></section>
<section><h2>Muzikler</h2><ul>{track_items}</ul></section>
<section class="full"><h2>Son Loglar</h2><pre>{logs}</pre></section>
</main></body></html>"""


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

    def show(self, msg="", kind="ok"):
        self.send_html(page(msg, kind))

    def read_form(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        return parse_qs(body)

    def read_multipart(self):
        return cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": self.headers.get("Content-Type", "")})

    def do_GET(self):
        self.send_html(page())

    def do_POST(self):
        try:
            if self.path == "/save-key":
                key = self.read_form().get("key", [""])[0].strip()
                if len(key) < 8 or re.search(r"\s", key):
                    self.show("Anahtar bos, kisa veya hatali gorunuyor.", "err")
                    return
                write_env(key)
                self.show("YouTube yayin anahtari kaydedildi.")
                return
            if self.path == "/upload-music":
                form = self.read_multipart()
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
                    sh([str(ROOT / "update_playlist.sh")])
                    self.show(f"{saved} muzik dosyasi yuklendi.")
                else:
                    self.show("Gecerli muzik dosyasi bulunamadi.", "err")
                return
            if self.path == "/upload-background":
                field = self.read_multipart()["background"]
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
                r = sh([str(ROOT / "update_playlist.sh")])
                self.show("Playlist yenilendi." if r.returncode == 0 else (r.stderr.strip() or r.stdout.strip() or "Playlist yenilenemedi."), "ok" if r.returncode == 0 else "err")
                return
            if self.path == "/service":
                action = self.read_form().get("action", [""])[0]
                if action not in {"start", "stop", "restart"}:
                    self.show("Bilinmeyen servis islemi.", "err")
                    return
                r = sh(["systemctl", action, SERVICE_NAME])
                self.show(f"Servis islemi tamam: {action}" if r.returncode == 0 else (r.stderr.strip() or r.stdout.strip() or "Servis islemi basarisiz."), "ok" if r.returncode == 0 else "err")
                return
            self.show("Bilinmeyen istek.", "err")
        except Exception as exc:
            self.show(f"Hata: {exc}", "err")


if __name__ == "__main__":
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Open through SSH tunnel: http://127.0.0.1:{PORT}")
    HTTPServer((HOST, PORT), Handler).serve_forever()
