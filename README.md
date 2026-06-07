# Bosphorus Breeze Radio

A beginner-friendly 24/7 YouTube live radio setup for an Oracle Cloud Free Tier Ubuntu 24.04 VPS.

It uses FFmpeg to combine audio files from `music/`, a JPG background from `assets/background.jpg`, and your YouTube RTMP stream key from `.env`.

Important: on a small Oracle VM.Standard.E2.1.Micro instance, 1080p can overload the VPS. This repo now uses safe default settings for that machine: 854x480, 24fps, H.264, AAC 128k, and one FFmpeg thread.

## Repository Structure

```text
bosphorus-breeze-radio/
├── music/
├── assets/
│   └── background.jpg
├── logs/
├── systemd/
│   ├── bosphorus-radio.service
│   └── bosphorus-radio-admin.service
├── .env.example
├── install.sh
├── radio_admin.py
├── test_local.sh
├── update_playlist.sh
├── stream.sh
└── README.md
```

## What It Does

- Runs on Ubuntu 24.04.
- Streams to YouTube Live RTMP.
- Reads `.mp3`, `.m4a`, and `.wav` files from `music/`.
- Ignores hidden files and hidden folders.
- Handles spaces in filenames.
- Automatically generates `playlist.txt`.
- Loops the playlist forever.
- Uses `assets/background.jpg` as the video background.
- Logs to both local log files and `journalctl`.
- Provides a local web admin panel for stream key, music, background, test, start, and stop.

## Install On Ubuntu

```bash
git clone https://github.com/murturhan/bosphorus-breeze-radio.git
cd bosphorus-breeze-radio
sudo ./install.sh
```

The installer installs FFmpeg, creates folders, installs the systemd services, enables only the lightweight admin panel on reboot, and keeps the heavy streaming service disabled until you start it yourself.

## Open The Admin Panel

From your Windows computer, open PowerShell and run this, replacing `YOUR_SERVER_IP` with your Oracle public IP:

```powershell
ssh -o ConnectTimeout=120 -i "$env:USERPROFILE\Downloads\ssh-key-2026-06-06 (1).key" -L 8788:127.0.0.1:8788 ubuntu@YOUR_SERVER_IP
```

Then open:

```text
http://127.0.0.1:8788
```

Use the panel to:

- paste and save your YouTube stream key
- upload music files
- upload a JPG background
- regenerate the playlist
- run the safe local FFmpeg test
- start, restart, or stop the stream

## FFmpeg Defaults

Safe Oracle Free Tier defaults:

- Resolution: `854x480`
- Frame rate: `24fps`
- Video codec: `H.264`
- Video preset: `ultrafast`
- FFmpeg threads: `1`
- Video bitrate: `900k`
- Max video bitrate: `1100k`
- Audio codec: `AAC`
- Audio bitrate: `128k`
- Audio sample rate: `44100 Hz`
- Output: `FLV` to YouTube RTMP

You can raise these values in `.env` only after moving to a stronger VPS.

## Manual Commands

```bash
sudo systemctl status bosphorus-radio-admin
sudo systemctl status bosphorus-radio
sudo journalctl -u bosphorus-radio -f
sudo systemctl start bosphorus-radio
sudo systemctl stop bosphorus-radio
sudo systemctl restart bosphorus-radio
```

## Auto Start Policy

The admin panel is safe to start on reboot:

```bash
sudo systemctl enable bosphorus-radio-admin
```

The stream service is intentionally disabled on reboot for small VPS safety:

```bash
sudo systemctl disable bosphorus-radio
```

If you later use a stronger VPS and want automatic streaming after reboot:

```bash
sudo systemctl enable bosphorus-radio
```

## Troubleshooting

Check the latest stream logs:

```bash
sudo journalctl -u bosphorus-radio -n 100 --no-pager
```

Common causes of failure:

- `.env` is missing
- stream key is empty or still the example value
- `music/` has no supported audio files
- `assets/background.jpg` is missing or invalid
- FFmpeg is not installed
- YouTube live event is not ready

## Security Notes

- Keep `.env` private.
- Do not publish your YouTube stream key.
- If your stream key leaks, reset it in YouTube Studio.
- The admin panel binds to `127.0.0.1` only and should be opened through SSH tunnel, not exposed to the public internet.

## License

MIT License. Use, modify, and deploy freely.
