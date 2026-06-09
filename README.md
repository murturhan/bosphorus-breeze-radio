# Bosphorus Breeze Radio

A production-ready 24/7 YouTube live radio setup for an Oracle Cloud Free Tier Ubuntu VPS.

It uses FFmpeg to combine:

- audio files from `music/`
- a still image or looping video background from `assets/background.*`
- your YouTube RTMP stream key from `.env`

The stream runs forever after you start it from the admin panel. For small Oracle Free Tier VPS safety, the heavy streaming service is not enabled on boot by default. The lightweight admin panel can start automatically on reboot.

## Repository Structure

```text
bosphorus-breeze-radio/
|-- music/
|-- assets/
|   |-- background.jpg
|-- logs/
|-- systemd/
|   |-- bosphorus-radio.service
|   |-- bosphorus-radio-admin.service
|-- .env.example
|-- install.sh
|-- radio_admin.py
|-- test_local.sh
|-- update_playlist.sh
|-- stream.sh
|-- README.md
```

## What This System Does

- Runs on Ubuntu 24.04.
- Streams continuously to YouTube Live RTMP.
- Uses FFmpeg for all audio/video processing.
- Reads `.mp3`, `.m4a`, and `.wav` files from `music/`.
- Ignores hidden files and hidden folders.
- Handles spaces in filenames.
- Automatically generates `playlist.txt`.
- Loops the playlist forever.
- Uses an image or video background from `assets/`.
- Supports background images: `background.jpg`, `background.jpeg`, `background.png`.
- Supports background videos: `background.mp4`, `background.mov`, `background.webm`, `background.mkv`.
- Loops video backgrounds automatically.
- Uses safe Oracle Free Tier defaults: 854x480 video at 24fps.
- Uses H.264 video and AAC audio.
- Logs to both local files and `journalctl`.
- Includes systemd services for the radio stream and admin panel.

## Server Requirements

Recommended server:

- Oracle Cloud Free Tier Ubuntu VPS
- Ubuntu 24.04
- At least 1 GB RAM
- A stable internet connection

You also need:

- A YouTube channel with live streaming enabled
- Your YouTube Live stream key

YouTube may require up to 24 hours to enable live streaming on a new channel.

## 1. Clone The Repository

On your Ubuntu server:

```bash
git clone https://github.com/murturhan/bosphorus-breeze-radio.git
cd bosphorus-breeze-radio
```

## 2. Run The Installer

```bash
sudo ./install.sh
```

The installer will:

- install FFmpeg
- create required folders
- create `.env` from `.env.example` if needed
- install the systemd services
- enable only the lightweight admin panel on reboot
- keep the heavy stream service disabled until you start it yourself

The installer does not start streaming immediately. Add music, add a background, and configure your stream key first.

## 3. Open The Admin Panel

Start the admin panel service:

```bash
sudo systemctl start bosphorus-radio-admin
```

From your Windows computer, open PowerShell and run this. Replace `YOUR_SERVER_IP` with your Oracle public IP, and change the key filename if Oracle downloaded a different key:

```powershell
ssh -o ConnectTimeout=120 -i "$env:USERPROFILE\Downloads\ssh-key-2026-06-08.key" -L 8788:127.0.0.1:8788 ubuntu@YOUR_SERVER_IP
```

Then open this address in your browser:

```text
http://127.0.0.1:8788
```

Use the panel to:

- save your YouTube stream key
- upload music files
- upload an image or video background
- regenerate the playlist
- run the safe local FFmpeg test
- start, restart, or stop the stream

## 4. Add Music

Copy audio files into:

```text
music/
```

Supported formats:

- `.mp3`
- `.m4a`
- `.wav`

Examples:

```text
music/Song One.mp3
music/Evening Set.m4a
music/live recording.wav
```

Hidden files are ignored. For example, `.secret.mp3` will not be added to the playlist.

## 5. Add Background Image Or Video

Use exactly one of these names in `assets/`:

```text
assets/background.jpg
assets/background.jpeg
assets/background.png
assets/background.mp4
assets/background.mov
assets/background.webm
assets/background.mkv
```

The admin panel handles this automatically. When you upload a new background, it removes the old `background.*` file and saves the new one with the correct extension.

Recommended:

- Use 16:9 content.
- 1920x1080 is fine for artwork, but the micro VPS streams at safe lower defaults.
- For video backgrounds, use short compressed MP4 loops when possible.
- Avoid very large 4K videos on the Always Free micro VPS.

## 6. Add Your YouTube Stream Key

The easiest method is the admin panel.

Manual method:

```bash
sudo nano .env
```

Change this:

```bash
YOUTUBE_STREAM_KEY=replace_with_your_youtube_stream_key
```

to your real stream key from YouTube Studio.

Do not add spaces around the key. Do not commit `.env` to GitHub.

## 7. Test Without YouTube

Run the safe local test. It checks the playlist, background image or video, and FFmpeg pipeline without streaming to YouTube:

```bash
./test_local.sh
```

If this passes, the local FFmpeg pipeline is working.

## 8. Start Streaming

Recommended beginner method: use the admin panel and click `Start`.

Manual method:

```bash
sudo systemctl start bosphorus-radio
```

Check status:

```bash
sudo systemctl status bosphorus-radio
```

Watch live logs:

```bash
sudo journalctl -u bosphorus-radio -f
```

Stop streaming:

```bash
sudo systemctl stop bosphorus-radio
```

Restart streaming:

```bash
sudo systemctl restart bosphorus-radio
```

## 9. Auto Start On Reboot

The installer enables the lightweight admin panel on reboot:

```bash
sudo systemctl enable bosphorus-radio-admin
```

The installer intentionally keeps the heavy stream service disabled on reboot:

```bash
sudo systemctl disable bosphorus-radio
```

That protects small 1 GB VPS instances from starting FFmpeg automatically after a reboot before you can check the panel.

If you later move to a stronger VPS and really want the stream itself to start on reboot:

```bash
sudo systemctl enable bosphorus-radio
```

## Logs

System logs:

```bash
sudo journalctl -u bosphorus-radio -f
```

Local logs:

```text
logs/stream.log
logs/playlist.log
logs/test.log
```

Systemd is the best place to watch production logs because it captures everything from the service.

## Health Checks

Before streaming, `stream.sh` checks that:

- `.env` exists
- `YOUTUBE_STREAM_KEY` is set
- the stream key is not the example value
- the stream key does not contain spaces
- a supported `assets/background.*` file exists
- FFmpeg and FFprobe are installed
- `playlist.txt` can be generated
- FFmpeg can read the background image or video
- FFmpeg can read the generated playlist

If a check fails, the script exits cleanly with a useful error message.

## FFmpeg Output Settings

The default stream uses YouTube-friendly settings that are safe for Oracle Cloud Free Tier VM.Standard.E2.1.Micro:

- Resolution: `854x480`
- Frame rate: `24fps`
- Video codec: `H.264`
- Pixel format: `yuv420p`
- GOP/keyframe interval: `2 seconds`
- Video bitrate: `900k`
- Audio codec: `AAC`
- Audio bitrate: `128k`
- Audio sample rate: `44100 Hz`
- Output format: `FLV`
- Destination: YouTube RTMP

The original 1080p target is technically possible on a stronger VPS, but it is not safe on a 1 OCPU / 1 GB RAM Always Free micro instance. Use a larger VPS before raising these values.

## Updating Music Or Background

To apply changes immediately:

```bash
sudo systemctl stop bosphorus-radio
./update_playlist.sh
sudo systemctl start bosphorus-radio
```

If you use the admin panel, it can regenerate the playlist and restart the service for you.

## Troubleshooting

### The Service Starts And Then Stops

Check logs:

```bash
sudo journalctl -u bosphorus-radio -n 100 --no-pager
```

Common causes:

- `.env` is missing
- stream key is still the example value
- `music/` has no supported audio files
- `assets/background.*` is missing or invalid
- FFmpeg is not installed

### YouTube Says No Data

Check:

- the service is running
- your stream key is correct
- your YouTube live event is ready
- your VPS has outbound internet access
- logs do not show RTMP connection errors

### Audio Filename Has Spaces

Spaces are supported. This is fine:

```text
music/Istanbul Night Mix.mp3
```

### Hidden Files Are Ignored

These are ignored:

```text
music/.hidden.mp3
music/.archive/old-song.mp3
```

## Security Notes

- Keep `.env` private.
- Do not publish your YouTube stream key.
- If your stream key is leaked, reset it in YouTube Studio.
- The admin panel binds to localhost and should be reached through SSH tunnel.
- Run updates regularly:

```bash
sudo apt update
sudo apt upgrade
```

## Useful Commands

```bash
./update_playlist.sh
./test_local.sh
./stream.sh
sudo systemctl start bosphorus-radio-admin
sudo systemctl start bosphorus-radio
sudo systemctl stop bosphorus-radio
sudo systemctl restart bosphorus-radio
sudo systemctl status bosphorus-radio
sudo journalctl -u bosphorus-radio -f
```

## License

MIT License. Use, modify, and deploy freely.
